"""
Anomaly detection module using Isolation Forest.

Purpose: Identify transactions that differ significantly from patterns
learned on legitimate transaction data. This is SEPARATE from the fraud classifier.

Key distinction (important for accurate communication):
- Fraud classifier: Supervised model trained on labeled data (fraud/legitimate)
  → Produces "fraud probability" based on historical fraud patterns
- Anomaly detector: Unsupervised model trained on legitimate transactions only
  → Produces "anomaly score" indicating how unusual a transaction appears
  → A high anomaly score means "unusual", NOT necessarily "fraudulent"
  → Some anomalies are unusual but legitimate (large purchases, foreign travel)
  → The two scores are complementary, not interchangeable

Reference methodology:
- Paper 1 (Borketey 2024) focuses on supervised classification
- Isolation Forest added here as the unsupervised component
- Not comparable to the supervised model's PR-AUC or F1 on the same test set
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import joblib
import numpy as np

from backend.core.config import settings
from backend.core.logging_config import get_logger
from backend.ml.preprocessor import validate_prediction_input, FEATURE_COLUMNS

logger = get_logger(__name__)


@dataclass
class AnomalyResult:
    """
    Result from the anomaly detection engine.

    anomaly_score: Raw IsolationForest decision function score.
                  More negative = more anomalous.
                  This is NOT a calibrated probability.
    normalized_score: Score normalized to [0,1] where higher = more anomalous.
    is_anomalous: Boolean flag based on the model's contamination threshold.
    """
    anomaly_score: float
    normalized_score: float
    is_anomalous: bool


class AnomalyDetector:
    """
    Isolation Forest-based anomaly detector for transaction data.
    Trained on legitimate transactions only.
    """

    def __init__(self) -> None:
        self._model = None
        self._loaded = False
        # Store approximate score range for normalization
        self._score_min: float = -0.5
        self._score_max: float = 0.5

    def load(self) -> bool:
        """Load the Isolation Forest model from disk."""
        path = settings.get_model_path("anomaly_detector.pkl")

        if not path.exists():
            logger.warning(
                f"Anomaly detector not found at {path}. "
                "Run training pipeline first."
            )
            return False

        try:
            self._model = joblib.load(path)
            self._loaded = True
            logger.info("Anomaly detector loaded.")
            return True
        except Exception as e:
            logger.error(f"Failed to load anomaly detector: {e}")
            return False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def predict(self, features: dict[str, Any]) -> Optional[AnomalyResult]:
        """
        Compute anomaly score for a single transaction.

        Returns None if the detector is not loaded (does not fabricate scores).
        """
        if not self._loaded:
            return None

        try:
            feature_array = validate_prediction_input(features)
            X = feature_array.reshape(1, -1)

            # Apply the same preprocessing as the classifier
            from backend.ml.preprocessor import SCALE_COLUMNS
            from backend.ml.predictor import prediction_service

            if prediction_service.is_loaded and prediction_service._preprocessor is not None:
                import pandas as pd
                scale_indices = [FEATURE_COLUMNS.index(col) for col in SCALE_COLUMNS]
                X_scaled = X.copy()
                X_to_scale = pd.DataFrame(X[:, scale_indices], columns=SCALE_COLUMNS)
                X_scaled[:, scale_indices] = prediction_service._preprocessor.transform(X_to_scale)
            else:
                X_scaled = X  # Use unscaled if preprocessor unavailable

            # IsolationForest.decision_function:
            # Returns the anomaly score; more negative = more anomalous
            raw_score = float(self._model.decision_function(X_scaled)[0])
            is_anomalous = bool(self._model.predict(X_scaled)[0] == -1)

            # Normalize to [0,1] (higher = more anomalous)
            # Approximate normalization — actual range depends on dataset
            normalized = max(0.0, min(1.0, (-raw_score + 0.2) / 0.4))

            return AnomalyResult(
                anomaly_score=round(raw_score, 6),
                normalized_score=round(normalized, 4),
                is_anomalous=is_anomalous,
            )

        except Exception as e:
            logger.warning(f"Anomaly detection failed: {e}")
            return None

    def predict_batch(self, features_list: list[dict]) -> list[Optional[AnomalyResult]]:
        return [self.predict(f) for f in features_list]


# Module-level singleton
anomaly_detector = AnomalyDetector()


def get_anomaly_detector() -> AnomalyDetector:
    """Returns the singleton anomaly detector, loading it if needed."""
    if not anomaly_detector.is_loaded:
        anomaly_detector.load()
    return anomaly_detector
