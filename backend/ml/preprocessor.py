"""
Preprocessing pipeline for the credit card fraud dataset.

Design decisions (following Paper 1 — Borketey 2024):
- V1–V28 are already PCA-transformed and require no additional scaling
- 'Time' and 'Amount' are scaled with StandardScaler
- SMOTE is applied ONLY to the training split — never to validation or test data
- The fitted scaler is saved alongside the model so inference is consistent
- Feature schema is saved to validate incoming prediction requests
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE

from backend.core.config import settings
from backend.core.logging_config import get_logger
from backend.ml.data_loader import FEATURE_COLUMNS, TARGET_COLUMN

logger = get_logger(__name__)

# Columns that need standard scaling (others are PCA features, already normalized)
SCALE_COLUMNS = ["Time", "Amount"]


def create_splits(
    X: pd.DataFrame,
    y: pd.Series,
    test_size: float = 0.20,
    val_size: float = 0.10,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    """
    Create stratified train / validation / test splits.

    Split rationale:
    - 70% train, 10% validation (for threshold/hyperparam selection), 20% test
    - Stratified on target to preserve class ratio in each split
    - A random split is used because the dataset does not have strong temporal structure
      in the PCA features (V1–V28). The 'Time' feature does exist but the PCA
      transformation obscures temporal ordering. A temporal split would be more realistic
      for production but is impractical with this anonymized dataset.
    - This limitation is documented in docs/limitations.md.

    WARNING: Test data must NOT be used for any training, preprocessing fit,
    oversampling, hyperparameter selection, or threshold tuning.
    """
    logger.info(f"Creating stratified train/val/test splits "
                f"(test={test_size:.0%}, val={val_size:.0%}, train={1-test_size-val_size:.0%})")

    # First split: separate test set
    X_trainval, X_test, y_trainval, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    # Second split: separate validation from training
    # val_size relative to trainval size
    relative_val_size = val_size / (1.0 - test_size)
    X_train, X_val, y_train, y_val = train_test_split(
        X_trainval, y_trainval,
        test_size=relative_val_size,
        random_state=random_state,
        stratify=y_trainval,
    )

    logger.info(f"Train:    {len(X_train):,} rows  (fraud: {y_train.sum():,})")
    logger.info(f"Val:      {len(X_val):,} rows  (fraud: {y_val.sum():,})")
    logger.info(f"Test:     {len(X_test):,} rows  (fraud: {y_test.sum():,})")

    return X_train, X_val, X_test, y_train, y_val, y_test


def fit_scaler(X_train: pd.DataFrame) -> StandardScaler:
    """
    Fit StandardScaler on training data only.
    Only Time and Amount are scaled; V1–V28 are already normalized via PCA.
    """
    scaler = StandardScaler()
    scaler.fit(X_train[SCALE_COLUMNS])
    logger.info(f"StandardScaler fitted on training data for columns: {SCALE_COLUMNS}")
    return scaler


def apply_scaling(X: pd.DataFrame, scaler: StandardScaler) -> pd.DataFrame:
    """Apply a pre-fitted scaler to Time and Amount columns."""
    X = X.copy()
    X[SCALE_COLUMNS] = scaler.transform(X[SCALE_COLUMNS])
    return X


def apply_smote(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    random_state: int = 42,
    sampling_strategy: str | float = "auto",
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Apply SMOTE (Synthetic Minority Oversampling Technique) to training data ONLY.

    SMOTE rationale (following Paper 1 — Borketey 2024):
    - The dataset is severely imbalanced: 0.17% fraud
    - SMOTE generates synthetic fraud samples between existing fraud examples
    - This allows classifiers to learn fraud patterns more effectively
    - Applied AFTER the train/val/test split to prevent test data leakage
    - Applied AFTER scaling so synthetic samples are created in the scaled space

    WARNING: SMOTE must NEVER be applied to validation or test sets.
    """
    fraud_before = int(y_train.sum())
    legit_before = int((y_train == 0).sum())

    logger.info(f"Applying SMOTE to training data:")
    logger.info(f"  Before — Legitimate: {legit_before:,} | Fraud: {fraud_before:,} "
                f"({fraud_before/len(y_train)*100:.2f}%)")

    smote = SMOTE(random_state=random_state, sampling_strategy=sampling_strategy)
    X_resampled, y_resampled = smote.fit_resample(X_train, y_train)

    fraud_after = int(y_resampled.sum())
    legit_after = int((y_resampled == 0).sum())

    logger.info(f"  After  — Legitimate: {legit_after:,} | Fraud: {fraud_after:,} "
                f"({fraud_after/len(y_resampled)*100:.2f}%)")
    logger.info(f"  Synthetic fraud samples added: {fraud_after - fraud_before:,}")

    return pd.DataFrame(X_resampled, columns=X_train.columns), pd.Series(y_resampled, name=TARGET_COLUMN)


def validate_prediction_input(features: dict) -> np.ndarray:
    """
    Validate a single transaction's feature dict for the prediction endpoint.

    Args:
        features: Dict mapping feature names to values.

    Returns:
        1-D numpy array in the correct feature order.

    Raises:
        ValueError: If features are missing, misnamed, or contain invalid values.
    """
    missing = [col for col in FEATURE_COLUMNS if col not in features]
    if missing:
        raise ValueError(f"Missing required features: {missing}")

    extra = [col for col in features if col not in FEATURE_COLUMNS]
    if extra:
        logger.warning(f"Ignoring unknown features in prediction input: {extra}")

    values = []
    for col in FEATURE_COLUMNS:
        val = features[col]
        try:
            val = float(val)
        except (TypeError, ValueError):
            raise ValueError(f"Feature '{col}' must be numeric, got: {repr(val)}")

        if not np.isfinite(val):
            raise ValueError(f"Feature '{col}' contains a non-finite value: {val}")

        values.append(val)

    return np.array(values, dtype=np.float64)


def save_feature_schema(path: Path) -> None:
    """Save the expected feature schema to a JSON file."""
    schema = {
        "feature_columns": FEATURE_COLUMNS,
        "scale_columns": SCALE_COLUMNS,
        "target_column": TARGET_COLUMN,
        "n_features": len(FEATURE_COLUMNS),
        "description": (
            "Features from Kaggle European credit card fraud dataset. "
            "V1-V28 are PCA-transformed. Time and Amount are raw and scaled. "
            "Class is the target (0=legitimate, 1=fraud)."
        ),
    }
    path.write_text(json.dumps(schema, indent=2))
    logger.info(f"Feature schema saved to: {path}")
