"""
Dataset loading and validation module.

Loads the Kaggle European credit card fraud dataset and performs
comprehensive quality checks before any modeling begins.

Dataset: https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud
  - 284,807 transactions over 2 days (September 2013)
  - 492 fraudulent transactions (0.17%)
  - Features: Time, V1–V28 (PCA-transformed), Amount, Class
  - Class: 0 = legitimate, 1 = fraudulent
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd

from backend.core.config import settings
from backend.core.logging_config import get_logger

logger = get_logger(__name__)

# Expected columns in the dataset
REQUIRED_COLUMNS = [
    "Time", "V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9",
    "V10", "V11", "V12", "V13", "V14", "V15", "V16", "V17", "V18",
    "V19", "V20", "V21", "V22", "V23", "V24", "V25", "V26", "V27",
    "V28", "Amount", "Class"
]

FEATURE_COLUMNS = [c for c in REQUIRED_COLUMNS if c != "Class"]
TARGET_COLUMN = "Class"


def load_and_validate(path: Path | None = None) -> pd.DataFrame:
    """
    Load and validate the credit card fraud dataset.

    Args:
        path: Path to creditcard.csv. Defaults to settings.data_raw_path.

    Returns:
        Validated DataFrame.

    Raises:
        FileNotFoundError: If dataset file is missing.
        ValueError: If dataset fails validation checks.
    """
    csv_path = Path(path) if path else settings.data_raw_path

    # --- Check file exists ---
    if not csv_path.exists():
        msg = (
            f"\n{'='*70}\n"
            f"DATASET NOT FOUND: {csv_path}\n"
            f"{'='*70}\n"
            f"The Kaggle European credit card fraud dataset is required.\n\n"
            f"To download it:\n"
            f"  1. Visit https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud\n"
            f"  2. Create a free Kaggle account if you don't have one\n"
            f"  3. Click 'Download' to get archive.zip\n"
            f"  4. Extract creditcard.csv from the archive\n"
            f"  5. Place it at: {csv_path}\n\n"
            f"Expected file size: ~143 MB\n"
            f"Expected rows: ~284,807\n"
            f"{'='*70}\n"
        )
        logger.error(msg)
        raise FileNotFoundError(msg)

    # --- Load CSV ---
    logger.info(f"Loading dataset from: {csv_path}")
    try:
        df = pd.read_csv(csv_path)
    except Exception as exc:
        raise ValueError(f"Failed to read CSV: {exc}") from exc

    logger.info(f"Loaded {len(df):,} rows × {len(df.columns)} columns")

    # --- Column validation ---
    missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_cols:
        raise ValueError(
            f"Dataset is missing required columns: {sorted(missing_cols)}\n"
            f"Found columns: {list(df.columns)}"
        )

    extra_cols = set(df.columns) - set(REQUIRED_COLUMNS)
    if extra_cols:
        logger.warning(f"Dataset contains unexpected extra columns (will be ignored): {extra_cols}")

    # Keep only expected columns in the expected order
    df = df[REQUIRED_COLUMNS].copy()

    # --- Row count check ---
    if len(df) < settings.expected_dataset_rows_min:
        raise ValueError(
            f"Dataset has only {len(df):,} rows. "
            f"Expected at least {settings.expected_dataset_rows_min:,}. "
            f"Please ensure you downloaded the full dataset."
        )

    # --- Data type validation ---
    for col in REQUIRED_COLUMNS:
        if not pd.api.types.is_numeric_dtype(df[col]):
            raise ValueError(
                f"Column '{col}' is expected to be numeric but has dtype {df[col].dtype}"
            )

    # --- Missing value inspection ---
    null_counts = df.isnull().sum()
    total_nulls = null_counts.sum()
    if total_nulls > 0:
        logger.warning(f"Dataset contains {total_nulls:,} missing values:")
        for col, cnt in null_counts[null_counts > 0].items():
            logger.warning(f"  {col}: {cnt:,} nulls ({cnt/len(df)*100:.2f}%)")
        # Drop rows with missing values — log clearly
        before = len(df)
        df = df.dropna()
        after = len(df)
        logger.warning(f"Dropped {before - after:,} rows with missing values. {after:,} rows remain.")
    else:
        logger.info("No missing values detected.")

    # --- Non-finite value check ---
    inf_counts = np.isinf(df.select_dtypes(include=np.number)).sum().sum()
    if inf_counts > 0:
        logger.warning(f"Found {inf_counts:,} infinite values. Replacing with NaN and dropping.")
        df = df.replace([np.inf, -np.inf], np.nan).dropna()

    # --- Duplicate detection ---
    dup_count = df.duplicated().sum()
    if dup_count > 0:
        logger.warning(f"Found {dup_count:,} exact duplicate rows.")
        # Do NOT silently drop duplicates — report them but keep for now
        # (the real dataset does not have true duplicates in the same sense as transaction data)

    # --- Class distribution ---
    class_counts = df[TARGET_COLUMN].value_counts().sort_index()
    total = len(df)
    fraud_count = int(class_counts.get(1, 0))
    legit_count = int(class_counts.get(0, 0))
    fraud_rate = fraud_count / total * 100

    logger.info(f"Class distribution:")
    logger.info(f"  Legitimate (Class=0): {legit_count:,}  ({100 - fraud_rate:.2f}%)")
    logger.info(f"  Fraudulent (Class=1): {fraud_count:,}  ({fraud_rate:.4f}%)")
    logger.info(f"  Imbalance ratio: {legit_count // max(fraud_count, 1)}:1 (legitimate:fraudulent)")

    if fraud_count == 0:
        raise ValueError("No fraudulent transactions found in dataset. Cannot train a fraud classifier.")

    # --- Target column validation ---
    unique_classes = set(df[TARGET_COLUMN].unique())
    if not unique_classes.issubset({0, 1}):
        raise ValueError(
            f"Target column 'Class' should contain only 0 and 1. "
            f"Found: {unique_classes}"
        )

    # --- Amount stats ---
    logger.info(f"Amount statistics:")
    logger.info(f"  Min: ${df['Amount'].min():.2f} | Max: ${df['Amount'].max():.2f} | "
                f"Mean: ${df['Amount'].mean():.2f} | Median: ${df['Amount'].median():.2f}")

    logger.info(f"Dataset validation complete. {len(df):,} valid rows ready for modeling.")
    return df


def get_features_and_target(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Separate features from target column.

    Returns:
        (X, y) where X contains FEATURE_COLUMNS and y is the Class column.
    """
    X = df[FEATURE_COLUMNS].copy()
    y = df[TARGET_COLUMN].copy()
    return X, y


def dataset_summary(df: pd.DataFrame) -> dict:
    """Return a JSON-serializable summary of the dataset."""
    fraud_count = int((df[TARGET_COLUMN] == 1).sum())
    legit_count = int((df[TARGET_COLUMN] == 0).sum())
    total = len(df)
    return {
        "total_rows": total,
        "fraud_count": fraud_count,
        "legitimate_count": legit_count,
        "fraud_rate_pct": round(fraud_count / total * 100, 4),
        "imbalance_ratio": round(legit_count / max(fraud_count, 1), 1),
        "feature_count": len(FEATURE_COLUMNS),
        "feature_names": FEATURE_COLUMNS,
        "amount_min": round(float(df["Amount"].min()), 2),
        "amount_max": round(float(df["Amount"].max()), 2),
        "amount_mean": round(float(df["Amount"].mean()), 2),
        "time_min": round(float(df["Time"].min()), 2),
        "time_max": round(float(df["Time"].max()), 2),
    }


if __name__ == "__main__":
    try:
        df = load_and_validate()
        summary = dataset_summary(df)
        print("\nDataset Summary:")
        for k, v in summary.items():
            print(f"  {k}: {v}")
    except FileNotFoundError as e:
        print(e)
        sys.exit(1)
