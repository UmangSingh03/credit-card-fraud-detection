"""
Prediction service: loads trained model and produces fraud predictions.

Design:
- Model and preprocessor are loaded once at startup (or on first call)
- Validates input features against saved schema before predicting
- Returns structured PredictionResult with probability, risk category, and model version
- Distinguishes fraud probability (model output) from risk category (policy threshold)
- Does NOT fabricate predictions when model artifacts are missing
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import joblib
import numpy as np

from backend.core.config import settings
from backend.core.logging_config import get_logger
from backend.ml.preprocessor import validate_prediction_input, FEATURE_COLUMNS

logger = get_logger(__name__)


@dataclass
class PredictionResult:
    """
    Structured output from the fraud prediction engine.

    Note on terminology:
    - fraud_probability: raw model output (calibrated probability if model supports it)
    - risk_category: policy-based classification using configurable thresholds
    - These are model estimates, NOT confirmed fraud outcomes
    """
    predicted_class: int           # 0=legitimate, 1=potentially fraudulent
    fraud_probability: Optional[float]  # 0.0–1.0 if model supports probabilities
    risk_category: str             # LOW, MEDIUM, HIGH
    model_name: str
    model_version: str
    prediction_timestamp: str
    latency_ms: float
    feature_count: int
    supports_probability: bool

    def to_dict(self) -> dict:
        return asdict(self)


class PredictionService:
    """
    Loads and serves the trained fraud detection model.
    Thread-safe for reading (model artifacts are read-only after loading).
    """

    def __init__(self) -> None:
        self._model = None
        self._preprocessor = None
        self._metadata: dict = {}
        self._schema: dict = {}
        self._loaded = False

    def load(self, force: bool = False) -> bool:
        """
        Load model artifacts from disk.

        Args:
            force: If True, reload even if already loaded.

        Returns:
            True if loaded successfully, False if artifacts not found.
        """
        if self._loaded and not force:
            return True

        model_path = settings.get_model_path("model.pkl")
        preprocessor_path = settings.get_model_path("preprocessor.pkl")
        metadata_path = settings.get_model_path("model_metadata.json")
        schema_path = settings.get_model_path("feature_schema.json")

        if not model_path.exists():
            logger.warning(
                f"Model artifact not found at {model_path}. "
                "Run 'python -m backend.ml.train' to train the model first."
            )
            self._loaded = False
            return False

        if not preprocessor_path.exists():
            logger.warning(f"Preprocessor artifact not found at {preprocessor_path}.")
            self._loaded = False
            return False

        try:
            self._model = joblib.load(model_path)
            self._preprocessor = joblib.load(preprocessor_path)

            if metadata_path.exists():
                self._metadata = json.loads(metadata_path.read_text())

            if schema_path.exists():
                self._schema = json.loads(schema_path.read_text())

            # Validate that the loaded model has expected attributes
            if not hasattr(self._model, "predict"):
                raise ValueError("Loaded object does not have a 'predict' method.")

            self._loaded = True
            model_name = self._metadata.get("model_name", "Unknown")
            version = self._metadata.get("version_tag", "v?")
            logger.info(f"Prediction service loaded: {model_name} ({version})")
            return True

        except Exception as e:
            logger.error(f"Failed to load model artifacts: {e}")
            self._loaded = False
            self._model = None
            self._preprocessor = None
            return False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def model_name(self) -> str:
        return self._metadata.get("model_name", "Unknown")

    @property
    def model_version(self) -> str:
        return self._metadata.get("version_tag", "v?")

    @property
    def metadata(self) -> dict:
        return self._metadata

    def predict(self, features: dict[str, Any]) -> PredictionResult:
        """
        Predict fraud probability for a single transaction.

        Args:
            features: Dict of feature_name → numeric_value.
                      Must include all expected features (Time, V1–V28, Amount).

        Returns:
            PredictionResult with prediction details.

        Raises:
            RuntimeError: If model is not loaded.
            ValueError: If features are invalid.
        """
        if not self._loaded:
            raise RuntimeError(
                "Model is not loaded. Run 'python -m backend.ml.train' to train first, "
                "then restart the backend. The API returns a 503 until the model is available."
            )

        t0 = time.perf_counter()

        # Validate and order features
        feature_array = validate_prediction_input(features)  # shape: (n_features,)
        X = feature_array.reshape(1, -1)

        # Apply preprocessing (scale Time and Amount)
        from backend.ml.preprocessor import SCALE_COLUMNS
        import pandas as pd
        scale_indices = [FEATURE_COLUMNS.index(col) for col in SCALE_COLUMNS]
        X_to_scale = pd.DataFrame(X[:, scale_indices], columns=SCALE_COLUMNS)
        X_scaled = X.copy()
        X_scaled[:, scale_indices] = self._preprocessor.transform(X_to_scale)

        # Predict
        predicted_class = int(self._model.predict(X_scaled)[0])

        # Probability
        fraud_prob = None
        supports_prob = hasattr(self._model, "predict_proba")
        if supports_prob:
            try:
                fraud_prob = float(self._model.predict_proba(X_scaled)[0, 1])
            except Exception:
                supports_prob = False

        latency_ms = (time.perf_counter() - t0) * 1000

        # Risk category (policy-based thresholds — documented, not scientific boundaries)
        risk_category = self._classify_risk(fraud_prob, predicted_class)

        return PredictionResult(
            predicted_class=predicted_class,
            fraud_probability=fraud_prob,
            risk_category=risk_category,
            model_name=self.model_name,
            model_version=self.model_version,
            prediction_timestamp=datetime.now(timezone.utc).isoformat(),
            latency_ms=round(latency_ms, 3),
            feature_count=len(FEATURE_COLUMNS),
            supports_probability=supports_prob,
        )

    def predict_batch(self, features_list: list[dict]) -> list[PredictionResult]:
        """Predict for a list of transactions."""
        return [self.predict(f) for f in features_list]

    def _classify_risk(
        self,
        fraud_prob: Optional[float],
        predicted_class: int,
    ) -> str:
        """
        Convert model output to a risk category using configurable thresholds.

        Risk categories are policy decisions, not scientifically established fraud boundaries.
        Thresholds are documented in config and can be adjusted in Settings page.
        """
        if fraud_prob is not None:
            if fraud_prob >= settings.risk_high_threshold:
                return "HIGH"
            elif fraud_prob >= settings.risk_low_threshold:
                return "MEDIUM"
            else:
                return "LOW"
        else:
            # Fallback to predicted class when probability is unavailable
            return "HIGH" if predicted_class == 1 else "LOW"


# Module-level singleton (loaded lazily)
prediction_service = PredictionService()


def get_prediction_service() -> PredictionService:
    """Returns the singleton prediction service, loading it if not already loaded."""
    if not prediction_service.is_loaded:
        prediction_service.load()
    return prediction_service
