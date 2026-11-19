"""
Automated model training pipeline.

Run with:
    python -m backend.ml.train

This script:
1. Loads and validates the dataset
2. Creates stratified train/val/test splits
3. Fits preprocessing (scaler) on training data only
4. Applies SMOTE to training data only
5. Trains multiple classifiers and an anomaly detector
6. Evaluates each model on the untouched test set
7. Selects the best model using a documented criterion
8. Saves model artifacts and generates evaluation reports

Model selection criterion (defined before viewing test results):
  Primary:  Highest PR-AUC on validation set
            (PR-AUC is preferred over ROC-AUC for highly imbalanced data
             because it focuses on the minority class performance)
  Tiebreak: Highest F1 score on validation set
  Minimum:  Recall >= 0.70 on validation set
            (Missing fraud is more costly than false alarms in this domain)

Models evaluated:
  - Logistic Regression (baseline, interpretable)
  - Decision Tree (interpretable, prone to overfitting)
  - Random Forest (Paper 1 winner — primary reference)
  - Gradient Boosting (scikit-learn implementation, Paper 1 XGBoost reference)
  - XGBoost (if available)
  - Isolation Forest (unsupervised anomaly detection — separate evaluation)

Reference: Borketey, B. (2024). Real-Time Fraud Detection Using Machine Learning.
  Journal of Data Analysis and Information Processing, 12, 189–209.
  DOI: 10.4236/jdaip.2024.122011
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import (
    GradientBoostingClassifier,
    HistGradientBoostingClassifier,
    IsolationForest,
    RandomForestClassifier,
)
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier

from backend.core.config import settings
from backend.core.logging_config import get_logger, setup_logging
from backend.ml.data_loader import (
    FEATURE_COLUMNS, TARGET_COLUMN, dataset_summary, get_features_and_target, load_and_validate
)
from backend.ml.evaluate import (
    compute_metrics, measure_inference_latency,
    plot_class_distribution, plot_confusion_matrix,
    plot_feature_importance, plot_model_comparison,
    plot_pr_curves, plot_roc_curves, save_comparison_json,
)
from backend.ml.preprocessor import (
    apply_scaling, apply_smote, create_splits, fit_scaler, save_feature_schema
)

setup_logging()
logger = get_logger(__name__)

RANDOM_SEED = settings.random_seed

# Progress callback type for background training jobs
ProgressCallback = Callable[[float, str], None]


def _default_progress(pct: float, stage: str) -> None:
    logger.info(f"[{pct:5.1f}%] {stage}")


def run_training_pipeline(
    progress_cb: ProgressCallback = _default_progress,
    dataset_path: Path | None = None,
) -> dict[str, Any]:
    """
    Execute the full training pipeline.

    Args:
        progress_cb: Called with (percent_complete, stage_description).
        dataset_path: Override the default dataset path.

    Returns:
        Dict containing selected_model, metrics, artifact paths.
    """
    start_time = time.time()
    results: dict[str, Any] = {}

    # =========================================================================
    # STAGE 1: Load and validate dataset
    # =========================================================================
    progress_cb(2.0, "Loading and validating dataset")
    try:
        df = load_and_validate(dataset_path)
    except FileNotFoundError as e:
        raise  # Re-raise so callers can handle gracefully

    summary = dataset_summary(df)
    logger.info(f"Dataset summary: {summary}")

    # =========================================================================
    # STAGE 2: Exploratory data analysis (summary charts)
    # =========================================================================
    progress_cb(5.0, "Generating EDA charts")
    X, y = get_features_and_target(df)

    plot_class_distribution(
        y,
        title=f"Class Distribution (n={len(y):,}, fraud={int(y.sum()):,}, {y.mean()*100:.2f}%)",
        output_path=settings.get_report_path("class_distribution.png"),
    )

    # =========================================================================
    # STAGE 3: Train / Val / Test split
    # =========================================================================
    progress_cb(8.0, "Creating train/val/test splits")
    X_train, X_val, X_test, y_train, y_val, y_test = create_splits(
        X, y, test_size=0.20, val_size=0.10, random_state=RANDOM_SEED
    )

    # =========================================================================
    # STAGE 4: Preprocessing — fit scaler on training data ONLY
    # =========================================================================
    progress_cb(10.0, "Fitting preprocessor (StandardScaler on train only)")
    scaler = fit_scaler(X_train)
    X_train_scaled = apply_scaling(X_train, scaler)
    X_val_scaled = apply_scaling(X_val, scaler)
    X_test_scaled = apply_scaling(X_test, scaler)

    # =========================================================================
    # STAGE 5: Apply SMOTE to training data ONLY
    # =========================================================================
    progress_cb(12.0, "Applying SMOTE to training data only")
    X_train_resampled, y_train_resampled = apply_smote(
        X_train_scaled, y_train, random_state=RANDOM_SEED
    )

    # Store numpy arrays for model training
    Xtr = X_train_resampled.values
    ytr = y_train_resampled.values
    Xval = X_val_scaled.values
    yval = y_val.values
    Xte = X_test_scaled.values
    yte = y_test.values

    # =========================================================================
    # STAGE 6: Train supervised classifiers
    # =========================================================================
    classifiers = _build_classifiers()
    model_results = []
    models_for_charts = []

    n_models = len(classifiers)
    for idx, (model_name, clf) in enumerate(classifiers):
        pct = 15.0 + (idx / n_models) * 50.0
        progress_cb(pct, f"Training {model_name}")
        logger.info(f"\n{'='*60}\nTraining: {model_name}\n{'='*60}")

        t_train_start = time.time()
        clf.fit(Xtr, ytr)
        train_duration = time.time() - t_train_start
        logger.info(f"  Training time: {train_duration:.1f}s")

        # Predictions
        val_pred = clf.predict(Xval)
        test_pred = clf.predict(Xte)

        # Probabilities (if supported)
        val_prob = _get_proba(clf, Xval)
        test_prob = _get_proba(clf, Xte)

        # Metrics
        val_metrics = compute_metrics(yval, val_pred, val_prob, split_name="val")
        test_metrics = compute_metrics(yte, test_pred, test_prob, split_name="test")

        # Inference latency
        latency_ms = measure_inference_latency(clf, Xte)
        logger.info(f"  Inference latency: {latency_ms:.2f} ms/sample")

        model_results.append({
            "model": model_name,
            "clf": clf,
            "val_metrics": val_metrics,
            "test_metrics": test_metrics,
            "train_duration_s": round(train_duration, 2),
            "latency_ms": latency_ms,
            "val_prob": val_prob,
            "test_prob": test_prob,
            "val_pred": val_pred,
            "test_pred": test_pred,
        })

        models_for_charts.append({
            "name": model_name,
            "y_true": yte,
            "y_prob": test_prob,
        })

    # =========================================================================
    # STAGE 7: Train Isolation Forest (anomaly detector — separate task)
    # =========================================================================
    progress_cb(65.0, "Training Isolation Forest anomaly detector")
    logger.info("\n" + "="*60 + "\nTraining: IsolationForest (anomaly detection)\n" + "="*60)

    # Fit on legitimate training transactions only (common practice for anomaly detection)
    # This way the model learns the "normal" distribution
    legit_mask = ytr == 0
    X_legit = Xtr[legit_mask]

    iso_forest = IsolationForest(
        n_estimators=50,
        contamination=0.002,  # approx fraud rate in original dataset
        random_state=RANDOM_SEED,
        n_jobs=-1,
    )
    t_iso = time.time()
    iso_forest.fit(X_legit)
    iso_duration = time.time() - t_iso
    logger.info(f"  IsolationForest training time: {iso_duration:.1f}s")

    # Evaluate anomaly detection using test labels as reference
    # Note: This evaluates how well anomaly scores correlate with fraud labels,
    # NOT as a replacement for the fraud classifier.
    iso_scores = iso_forest.decision_function(Xte)
    # Lower score = more anomalous; convert to "anomaly probability" proxy
    iso_pred = (iso_forest.predict(Xte) == -1).astype(int)  # -1=anomaly → 1
    iso_metrics = compute_metrics(yte, iso_pred, -iso_scores, split_name="test_anomaly")
    logger.info(f"  IsolationForest (vs fraud labels): {iso_metrics}")

    # =========================================================================
    # STAGE 8: Model selection (criterion defined in docstring above)
    # =========================================================================
    progress_cb(68.0, "Selecting best model")
    best_result = _select_best_model(model_results)
    best_name = best_result["model"]
    best_clf = best_result["clf"]
    logger.info(f"\n{'='*60}\nSELECTED MODEL: {best_name}\n{'='*60}")
    logger.info(f"  Val PR-AUC:  {best_result['val_metrics'].get('pr_auc', 'N/A')}")
    logger.info(f"  Val F1:      {best_result['val_metrics'].get('f1', 'N/A')}")
    logger.info(f"  Test PR-AUC: {best_result['test_metrics'].get('pr_auc', 'N/A')}")
    logger.info(f"  Test F1:     {best_result['test_metrics'].get('f1', 'N/A')}")
    logger.info(f"  Test Recall: {best_result['test_metrics'].get('recall', 'N/A')}")

    # =========================================================================
    # STAGE 9: Save model artifacts
    # =========================================================================
    progress_cb(72.0, "Saving model artifacts")

    model_path = settings.get_model_path("model.pkl")
    preprocessor_path = settings.get_model_path("preprocessor.pkl")
    iso_path = settings.get_model_path("anomaly_detector.pkl")
    schema_path = settings.get_model_path("feature_schema.json")

    joblib.dump(best_clf, model_path)
    joblib.dump(scaler, preprocessor_path)
    joblib.dump(iso_forest, iso_path)
    save_feature_schema(schema_path)
    logger.info(f"Model saved: {model_path}")
    logger.info(f"Preprocessor saved: {preprocessor_path}")
    logger.info(f"Anomaly detector saved: {iso_path}")

    # =========================================================================
    # STAGE 10: Generate evaluation charts
    # =========================================================================
    progress_cb(76.0, "Generating evaluation charts")

    # Confusion matrix for selected model
    plot_confusion_matrix(
        yte, best_result["test_pred"],
        model_name=best_name,
        output_path=settings.get_report_path("confusion_matrix.png"),
    )

    # ROC and PR curves for all models
    plot_roc_curves(models_for_charts, settings.get_report_path("roc_curves.png"))
    plot_pr_curves(models_for_charts, settings.get_report_path("pr_curves.png"))

    # Feature importance (if supported)
    if hasattr(best_clf, "feature_importances_"):
        plot_feature_importance(
            best_clf.feature_importances_,
            FEATURE_COLUMNS,
            model_name=best_name,
            output_path=settings.get_report_path("feature_importance.png"),
        )

    # =========================================================================
    # STAGE 11: Build comparison table and save JSON
    # =========================================================================
    progress_cb(88.0, "Saving comparison report")

    comparison = []
    for mr in model_results:
        row = {
            "model": mr["model"],
            "selected": mr["model"] == best_name,
            "train_duration_s": mr["train_duration_s"],
            "latency_ms": mr["latency_ms"],
        }
        # Add test metrics
        for k, v in mr["test_metrics"].items():
            if k != "split":
                row[k] = v
        # Add val metrics with prefix
        for k, v in mr["val_metrics"].items():
            if k != "split":
                row[f"val_{k}"] = v
        comparison.append(row)

    plot_model_comparison(
        [{"model": mr["model"], **mr["test_metrics"]} for mr in model_results],
        settings.get_report_path("model_comparison.png"),
    )
    save_comparison_json(comparison, settings.get_report_path("model_comparison.json"))

    # =========================================================================
    # STAGE 12: Save model metadata
    # =========================================================================
    progress_cb(92.0, "Saving model metadata")

    total_duration = time.time() - start_time
    metadata = _build_metadata(
        best_result, best_name, summary, comparison,
        model_path, preprocessor_path, total_duration
    )
    metadata_path = settings.get_model_path("model_metadata.json")
    metadata_path.write_text(json.dumps(metadata, indent=2, default=str))
    logger.info(f"Model metadata saved: {metadata_path}")

    progress_cb(100.0, "Training pipeline complete")
    logger.info(f"\nTotal pipeline time: {total_duration:.1f}s")

    results = {
        "selected_model": best_name,
        "test_metrics": best_result["test_metrics"],
        "val_metrics": best_result["val_metrics"],
        "comparison": comparison,
        "metadata": metadata,
        "artifacts": {
            "model": str(model_path),
            "preprocessor": str(preprocessor_path),
            "anomaly_detector": str(iso_path),
            "feature_schema": str(schema_path),
            "metadata": str(metadata_path),
        },
    }
    return results


def _build_classifiers() -> list[tuple[str, Any]]:
    """Build the list of classifiers to train."""
    classifiers = [
        (
            "LogisticRegression",
            LogisticRegression(
                max_iter=1000,
                random_state=RANDOM_SEED,
                class_weight="balanced",
                C=1.0,
                solver="lbfgs",
            ),
        ),
        (
            "DecisionTree",
            DecisionTreeClassifier(
                max_depth=10,
                min_samples_split=20,
                random_state=RANDOM_SEED,
                class_weight="balanced",
            ),
        ),
        (
            "RandomForest",
            RandomForestClassifier(
                n_estimators=50,
                max_depth=16,
                min_samples_split=4,
                max_features="sqrt",
                random_state=RANDOM_SEED,
                n_jobs=-1,
                class_weight="balanced",
            ),
        ),
        (
            "GradientBoosting",
            HistGradientBoostingClassifier(
                max_iter=50,
                learning_rate=0.1,
                max_depth=5,
                random_state=RANDOM_SEED,
            ),
        ),
    ]

    # Try to add XGBoost
    try:
        import xgboost as xgb
        classifiers.append((
            "XGBoost",
            xgb.XGBClassifier(
                n_estimators=50,
                learning_rate=0.1,
                max_depth=6,
                eval_metric="logloss",
                random_state=RANDOM_SEED,
                n_jobs=-1,
                scale_pos_weight=1,
            ),
        ))
        logger.info("XGBoost available — added to comparison.")
    except ImportError:
        logger.warning("XGBoost not available. Skipping XGBoost model.")

    return classifiers


def _get_proba(clf, X: np.ndarray) -> np.ndarray | None:
    """Get class-1 probabilities from classifier, or None if not supported."""
    if hasattr(clf, "predict_proba"):
        try:
            return clf.predict_proba(X)[:, 1]
        except Exception:
            pass
    if hasattr(clf, "decision_function"):
        # Normalize decision function scores to [0,1] range for display
        scores = clf.decision_function(X)
        min_s, max_s = scores.min(), scores.max()
        if max_s > min_s:
            return (scores - min_s) / (max_s - min_s)
    return None


def _select_best_model(model_results: list[dict]) -> dict:
    """
    Select best model by validation PR-AUC, then F1.
    Adds test_pred to the result for chart generation.

    The selection criterion is defined before examining test results:
    1. Primary: Highest PR-AUC on the validation set
    2. Tiebreak: Highest F1 on the validation set
    3. Minimum recall >= 0.70 on validation set (prefer catching fraud over precision)

    PR-AUC is used as the primary metric because:
    - The dataset is highly imbalanced (0.17% fraud)
    - ROC-AUC can be misleadingly high even on imbalanced sets
    - PR-AUC directly measures the quality of positive (fraud) predictions
    - This follows the recommendation in Paper 1 (Borketey 2024)
    """
    eligible = [
        r for r in model_results
        if r["val_metrics"].get("recall", 0) >= 0.70
    ]
    if not eligible:
        logger.warning("No model met the minimum recall=0.70 threshold. Using all models.")
        eligible = model_results

    best = max(
        eligible,
        key=lambda r: (
            r["val_metrics"].get("pr_auc") or 0,
            r["val_metrics"].get("f1") or 0,
        ),
    )

    # Add test predictions for confusion matrix generation
    from backend.ml.preprocessor import apply_scaling
    # Predictions are already stored via the training loop — retrieve test pred
    # We need to regenerate predictions with the stored clf
    # (test set Xte is not in scope here, so we store them in model_results)
    # This is handled in run_training_pipeline by adding test_pred below
    return best


def _add_test_pred(model_results: list[dict], Xte: np.ndarray) -> None:
    """Add test predictions to each model result for chart generation."""
    for mr in model_results:
        mr["test_pred"] = mr["clf"].predict(Xte)


def _build_metadata(
    best_result: dict,
    best_name: str,
    summary: dict,
    comparison: list[dict],
    model_path: Path,
    preprocessor_path: Path,
    total_duration: float,
) -> dict:
    return {
        "model_name": best_name,
        "version_tag": "v1.0",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "random_seed": RANDOM_SEED,
        "dataset": {
            "name": "Kaggle European Credit Card Fraud Dataset",
            "source": "https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud",
            "citation": (
                "Andrea Dal Pozzolo, Olivier Caelen, Reid A. Johnson and Gianluca Bontempi. "
                "Calibrating Probability with Undersampling for Unbalanced Classification. "
                "In Symposium on Computational Intelligence and Data Mining (CIDM), IEEE, 2015."
            ),
            **summary,
        },
        "preprocessing": {
            "scaler": "StandardScaler on Time and Amount only",
            "smote": "Applied to training split only",
            "split": "70% train, 10% val, 20% test (stratified)",
        },
        "training_config": {
            "train_duration_seconds": round(total_duration, 2),
            "classifiers_evaluated": [r["model"] for r in comparison],
        },
        "selection_rationale": (
            f"Model selected: {best_name}. "
            f"Selection criterion: highest PR-AUC on validation set (PR-AUC preferred "
            f"over ROC-AUC for imbalanced classification as recommended in the primary "
            f"reference paper — Borketey 2024). Minimum recall threshold: 0.70. "
            f"Val PR-AUC: {best_result['val_metrics'].get('pr_auc', 'N/A')}, "
            f"Val F1: {best_result['val_metrics'].get('f1', 'N/A')}."
        ),
        "val_metrics": best_result["val_metrics"],
        "test_metrics": best_result["test_metrics"],
        "train_duration_seconds": round(best_result["train_duration_s"], 2),
        "inference_latency_ms": best_result["latency_ms"],
        "artifact_paths": {
            "model": str(model_path),
            "preprocessor": str(preprocessor_path),
        },
        "feature_columns": FEATURE_COLUMNS,
        "disclaimer": (
            "These metrics are from an independently trained model on this dataset. "
            "They are not the results reported in any referenced paper. "
            "This system is an educational prototype, not a certified fraud detection system."
        ),
    }


# Patch: add test_pred generation into the main pipeline after training loop
# (Monkeypatch approach — works because _select_best_model is called after the loop)
_original_run = run_training_pipeline


def run_training_pipeline(
    progress_cb: ProgressCallback = _default_progress,
    dataset_path: Path | None = None,
) -> dict[str, Any]:
    """Wrapper that fixes test_pred injection into model results."""
    start_time = time.time()
    results: dict[str, Any] = {}

    progress_cb(2.0, "Loading and validating dataset")
    df = load_and_validate(dataset_path)
    summary = dataset_summary(df)

    progress_cb(5.0, "Generating EDA charts")
    X, y = get_features_and_target(df)

    plot_class_distribution(
        y,
        title=f"Class Distribution (n={len(y):,}, fraud={int(y.sum()):,}, {y.mean()*100:.2f}%)",
        output_path=settings.get_report_path("class_distribution.png"),
    )

    progress_cb(8.0, "Creating train/val/test splits")
    X_train, X_val, X_test, y_train, y_val, y_test = create_splits(
        X, y, test_size=0.20, val_size=0.10, random_state=RANDOM_SEED
    )

    progress_cb(10.0, "Fitting preprocessor (StandardScaler on train only)")
    scaler = fit_scaler(X_train)
    X_train_scaled = apply_scaling(X_train, scaler)
    X_val_scaled = apply_scaling(X_val, scaler)
    X_test_scaled = apply_scaling(X_test, scaler)

    progress_cb(12.0, "Applying SMOTE to training data only")
    X_train_resampled, y_train_resampled = apply_smote(
        X_train_scaled, y_train, random_state=RANDOM_SEED
    )

    Xtr = X_train_resampled.values
    ytr = y_train_resampled.values
    Xval = X_val_scaled.values
    yval = y_val.values
    Xte = X_test_scaled.values
    yte = y_test.values

    classifiers = _build_classifiers()
    model_results = []
    models_for_charts = []

    n_models = len(classifiers)
    for idx, (model_name, clf) in enumerate(classifiers):
        pct = 15.0 + (idx / n_models) * 50.0
        progress_cb(pct, f"Training {model_name}")
        logger.info(f"\n{'='*60}\nTraining: {model_name}\n{'='*60}")

        t_train_start = time.time()
        try:
            clf.fit(Xtr, ytr)
        except Exception as e:
            logger.error(f"Failed to train {model_name}: {e}")
            continue
        train_duration = time.time() - t_train_start
        logger.info(f"  Training time: {train_duration:.1f}s")

        val_pred = clf.predict(Xval)
        test_pred = clf.predict(Xte)

        val_prob = _get_proba(clf, Xval)
        test_prob = _get_proba(clf, Xte)

        val_metrics = compute_metrics(yval, val_pred, val_prob, split_name="val")
        test_metrics = compute_metrics(yte, test_pred, test_prob, split_name="test")

        latency_ms = measure_inference_latency(clf, Xte)
        logger.info(f"  Inference latency: {latency_ms:.2f} ms/sample")

        model_results.append({
            "model": model_name,
            "clf": clf,
            "val_metrics": val_metrics,
            "test_metrics": test_metrics,
            "train_duration_s": round(train_duration, 2),
            "latency_ms": latency_ms,
            "val_prob": val_prob,
            "test_prob": test_prob,
            "test_pred": test_pred,  # stored here for chart generation
        })

        models_for_charts.append({
            "name": model_name,
            "y_true": yte,
            "y_prob": test_prob,
        })

    if not model_results:
        raise RuntimeError("All classifiers failed to train. Check dataset and dependencies.")

    progress_cb(65.0, "Training Isolation Forest anomaly detector")
    legit_mask = ytr == 0
    X_legit = Xtr[legit_mask]
    iso_forest = IsolationForest(
        n_estimators=100,
        contamination=0.002,
        random_state=RANDOM_SEED,
        n_jobs=-1,
    )
    t_iso = time.time()
    iso_forest.fit(X_legit)
    iso_duration = time.time() - t_iso
    logger.info(f"IsolationForest training time: {iso_duration:.1f}s")

    progress_cb(68.0, "Selecting best model")
    best_result = _select_best_model(model_results)
    best_name = best_result["model"]
    best_clf = best_result["clf"]

    logger.info(f"\n{'='*60}\nSELECTED MODEL: {best_name}")
    logger.info(f"Val PR-AUC:  {best_result['val_metrics'].get('pr_auc')}")
    logger.info(f"Val F1:      {best_result['val_metrics'].get('f1')}")
    logger.info(f"Test Metrics: {best_result['test_metrics']}")
    logger.info("="*60)

    progress_cb(72.0, "Saving model artifacts")
    model_path = settings.get_model_path("model.pkl")
    preprocessor_path = settings.get_model_path("preprocessor.pkl")
    iso_path = settings.get_model_path("anomaly_detector.pkl")
    schema_path = settings.get_model_path("feature_schema.json")

    joblib.dump(best_clf, model_path)
    joblib.dump(scaler, preprocessor_path)
    joblib.dump(iso_forest, iso_path)
    save_feature_schema(schema_path)

    progress_cb(76.0, "Generating evaluation charts")
    plot_confusion_matrix(
        yte, best_result["test_pred"], model_name=best_name,
        output_path=settings.get_report_path("confusion_matrix.png"),
    )
    plot_roc_curves(models_for_charts, settings.get_report_path("roc_curves.png"))
    plot_pr_curves(models_for_charts, settings.get_report_path("pr_curves.png"))

    if hasattr(best_clf, "feature_importances_"):
        plot_feature_importance(
            best_clf.feature_importances_, FEATURE_COLUMNS, model_name=best_name,
            output_path=settings.get_report_path("feature_importance.png"),
        )

    progress_cb(88.0, "Saving comparison report")
    comparison = []
    for mr in model_results:
        row = {
            "model": mr["model"],
            "selected": mr["model"] == best_name,
            "train_duration_s": mr["train_duration_s"],
            "latency_ms": mr["latency_ms"],
        }
        for k, v in mr["test_metrics"].items():
            if k != "split":
                row[k] = v
        for k, v in mr["val_metrics"].items():
            if k != "split":
                row[f"val_{k}"] = v
        comparison.append(row)

    plot_model_comparison(
        [{"model": mr["model"], **mr["test_metrics"]} for mr in model_results],
        settings.get_report_path("model_comparison.png"),
    )
    save_comparison_json(comparison, settings.get_report_path("model_comparison.json"))

    progress_cb(92.0, "Saving model metadata")
    total_duration = time.time() - start_time
    metadata = _build_metadata(
        best_result, best_name, summary, comparison,
        model_path, preprocessor_path, total_duration,
    )
    metadata_path = settings.get_model_path("model_metadata.json")
    metadata_path.write_text(json.dumps(metadata, indent=2, default=str))

    progress_cb(100.0, "Training pipeline complete")
    logger.info(f"Total pipeline time: {total_duration:.1f}s")

    return {
        "selected_model": best_name,
        "test_metrics": best_result["test_metrics"],
        "val_metrics": best_result["val_metrics"],
        "comparison": comparison,
        "metadata": metadata,
        "artifacts": {
            "model": str(model_path),
            "preprocessor": str(preprocessor_path),
            "anomaly_detector": str(iso_path),
            "feature_schema": str(schema_path),
            "metadata": str(metadata_path),
        },
    }


if __name__ == "__main__":
    logger.info("Starting automated model training pipeline...")
    try:
        result = run_training_pipeline()
        print(f"\n{'='*60}")
        print(f"TRAINING COMPLETE")
        print(f"{'='*60}")
        print(f"Selected model: {result['selected_model']}")
        print(f"\nTest metrics:")
        for k, v in result["test_metrics"].items():
            if k != "split":
                print(f"  {k}: {v}")
    except FileNotFoundError:
        logger.error("Dataset not found. Please follow the setup instructions in README.md.")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Training pipeline failed: {e}")
        sys.exit(1)
