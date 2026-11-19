"""
Model evaluation: metrics computation and visualization generation.

All metrics computed here come from actual model execution on test data.
Charts are saved to the reports directory.
Metric labels clearly state whether they are from train, val, or test data.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for server use
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix,
    roc_curve, precision_recall_curve, classification_report,
)

from backend.core.config import settings
from backend.core.logging_config import get_logger

logger = get_logger(__name__)

# Consistent color palette
PALETTE = {
    "fraud": "#EF4444",
    "legitimate": "#22C55E",
    "primary": "#3B82F6",
    "secondary": "#8B5CF6",
    "warning": "#F59E0B",
}


def compute_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: np.ndarray | None,
    split_name: str = "test",
) -> dict[str, Any]:
    """
    Compute a comprehensive set of classification metrics.

    Args:
        y_true: Ground-truth labels (0/1).
        y_pred: Predicted labels (0/1).
        y_prob: Predicted probabilities for class 1 (optional).
        split_name: 'train', 'val', or 'test' — used for labelling only.

    Returns:
        Dict of metric names to values.
    """
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()

    metrics: dict[str, Any] = {
        "split": split_name,
        "accuracy": round(accuracy_score(y_true, y_pred), 6),
        "precision": round(precision_score(y_true, y_pred, zero_division=0), 6),
        "recall": round(recall_score(y_true, y_pred, zero_division=0), 6),
        "f1": round(f1_score(y_true, y_pred, zero_division=0), 6),
        "fpr": round(fp / (fp + tn) if (fp + tn) > 0 else 0.0, 6),
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
    }

    if y_prob is not None:
        try:
            metrics["roc_auc"] = round(roc_auc_score(y_true, y_prob), 6)
        except ValueError:
            metrics["roc_auc"] = None
            logger.warning(f"Could not compute ROC-AUC (only one class present in {split_name}?)")

        try:
            metrics["pr_auc"] = round(average_precision_score(y_true, y_prob), 6)
        except ValueError:
            metrics["pr_auc"] = None
    else:
        metrics["roc_auc"] = None
        metrics["pr_auc"] = None

    logger.info(
        f"[{split_name.upper()}] Acc={metrics['accuracy']:.4f} | "
        f"Prec={metrics['precision']:.4f} | Rec={metrics['recall']:.4f} | "
        f"F1={metrics['f1']:.4f} | ROC-AUC={metrics.get('roc_auc', 'N/A')} | "
        f"PR-AUC={metrics.get('pr_auc', 'N/A')}"
    )
    return metrics


def measure_inference_latency(model, X_sample: np.ndarray, n_calls: int = 100) -> float:
    """
    Measure average inference latency in milliseconds.

    Args:
        model: Fitted scikit-learn estimator.
        X_sample: A small sample of features to predict.
        n_calls: Number of prediction calls to average.

    Returns:
        Average latency in milliseconds.
    """
    X_single = X_sample[:1]
    latencies = []
    for _ in range(n_calls):
        t0 = time.perf_counter()
        model.predict(X_single)
        latencies.append((time.perf_counter() - t0) * 1000)
    return round(float(np.mean(latencies[10:])), 3)  # Discard first 10 warm-up


def plot_confusion_matrix(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    model_name: str,
    output_path: Path,
) -> None:
    """Save confusion matrix heatmap."""
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues", ax=ax,
        xticklabels=["Legitimate", "Fraudulent"],
        yticklabels=["Legitimate", "Fraudulent"],
    )
    ax.set_title(f"Confusion Matrix — {model_name} (Test Set)", fontsize=13, pad=12)
    ax.set_ylabel("Actual", fontsize=11)
    ax.set_xlabel("Predicted", fontsize=11)
    plt.tight_layout()
    fig.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"Confusion matrix saved: {output_path}")


def plot_roc_curves(
    models_data: list[dict],  # [{name, y_true, y_prob}]
    output_path: Path,
) -> None:
    """Save ROC curves for all models on one chart."""
    fig, ax = plt.subplots(figsize=(8, 6))
    colors = ["#3B82F6", "#EF4444", "#22C55E", "#F59E0B", "#8B5CF6", "#EC4899"]

    for i, m in enumerate(models_data):
        if m.get("y_prob") is None:
            continue
        try:
            fpr, tpr, _ = roc_curve(m["y_true"], m["y_prob"])
            auc = roc_auc_score(m["y_true"], m["y_prob"])
            ax.plot(fpr, tpr, color=colors[i % len(colors)],
                    label=f"{m['name']} (AUC={auc:.4f})", linewidth=2)
        except Exception as e:
            logger.warning(f"Could not plot ROC for {m['name']}: {e}")

    ax.plot([0, 1], [0, 1], "k--", linewidth=1, label="Random classifier")
    ax.set_title("ROC Curves — All Models (Test Set)", fontsize=13, pad=12)
    ax.set_xlabel("False Positive Rate", fontsize=11)
    ax.set_ylabel("True Positive Rate", fontsize=11)
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    fig.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"ROC curves saved: {output_path}")


def plot_pr_curves(
    models_data: list[dict],
    output_path: Path,
) -> None:
    """Save Precision-Recall curves for all models."""
    fig, ax = plt.subplots(figsize=(8, 6))
    colors = ["#3B82F6", "#EF4444", "#22C55E", "#F59E0B", "#8B5CF6", "#EC4899"]

    for i, m in enumerate(models_data):
        if m.get("y_prob") is None:
            continue
        try:
            precision, recall, _ = precision_recall_curve(m["y_true"], m["y_prob"])
            pr_auc = average_precision_score(m["y_true"], m["y_prob"])
            ax.plot(recall, precision, color=colors[i % len(colors)],
                    label=f"{m['name']} (PR-AUC={pr_auc:.4f})", linewidth=2)
        except Exception as e:
            logger.warning(f"Could not plot PR curve for {m['name']}: {e}")

    ax.set_title("Precision-Recall Curves — All Models (Test Set)", fontsize=13, pad=12)
    ax.set_xlabel("Recall", fontsize=11)
    ax.set_ylabel("Precision", fontsize=11)
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    fig.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"PR curves saved: {output_path}")


def plot_feature_importance(
    importances: np.ndarray,
    feature_names: list[str],
    model_name: str,
    output_path: Path,
    top_n: int = 20,
) -> None:
    """Save horizontal bar chart of top-N feature importances."""
    indices = np.argsort(importances)[-top_n:]
    fig, ax = plt.subplots(figsize=(8, 7))
    bars = ax.barh(
        [feature_names[i] for i in indices],
        importances[indices],
        color=PALETTE["primary"], alpha=0.85
    )
    ax.set_title(f"Top {top_n} Feature Importances — {model_name}", fontsize=13, pad=12)
    ax.set_xlabel("Importance Score", fontsize=11)
    ax.grid(True, axis="x", alpha=0.3)
    plt.tight_layout()
    fig.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"Feature importance chart saved: {output_path}")


def plot_class_distribution(
    y: pd.Series,
    title: str,
    output_path: Path,
) -> None:
    """Bar chart of class distribution."""
    counts = y.value_counts().sort_index()
    labels = ["Legitimate", "Fraudulent"]
    colors = [PALETTE["legitimate"], PALETTE["fraud"]]
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(labels, [counts.get(0, 0), counts.get(1, 0)], color=colors, width=0.5)
    for bar, count in zip(bars, [counts.get(0, 0), counts.get(1, 0)]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 500,
                f"{count:,}", ha="center", va="bottom", fontsize=11)
    ax.set_title(title, fontsize=13, pad=12)
    ax.set_ylabel("Count", fontsize=11)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    plt.tight_layout()
    fig.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"Class distribution chart saved: {output_path}")


def plot_model_comparison(
    comparison: list[dict],
    output_path: Path,
) -> None:
    """Grouped bar chart comparing key metrics across models."""
    metrics_to_show = ["precision", "recall", "f1", "roc_auc", "pr_auc"]
    metric_labels = ["Precision", "Recall", "F1", "ROC-AUC", "PR-AUC"]

    model_names = [m["model"] for m in comparison]
    n_models = len(model_names)
    n_metrics = len(metrics_to_show)

    x = np.arange(n_models)
    width = 0.15
    colors = ["#3B82F6", "#22C55E", "#EF4444", "#F59E0B", "#8B5CF6"]

    fig, ax = plt.subplots(figsize=(max(10, n_models * 2), 6))
    for i, (metric, label) in enumerate(zip(metrics_to_show, metric_labels)):
        vals = []
        for m in comparison:
            val = m.get(metric)
            vals.append(float(val) if val is not None else 0.0)
        ax.bar(x + i * width, vals, width, label=label, color=colors[i], alpha=0.85)

    ax.set_title("Model Comparison — Test Set Metrics", fontsize=13, pad=12)
    ax.set_xticks(x + width * (n_metrics - 1) / 2)
    ax.set_xticklabels(model_names, rotation=15, ha="right")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score", fontsize=11)
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()
    fig.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"Model comparison chart saved: {output_path}")


def save_comparison_json(comparison: list[dict], output_path: Path) -> None:
    """Save model comparison metrics to JSON."""
    output_path.write_text(json.dumps(comparison, indent=2, default=str))
    logger.info(f"Model comparison JSON saved: {output_path}")
