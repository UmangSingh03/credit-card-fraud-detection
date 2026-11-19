"""
SHAP-based explainability module.

Provides:
- Global feature importance via SHAP values
- Per-transaction explanation (local interpretability)

Limitations:
- SHAP values show feature contributions to a prediction, NOT causal explanations
- V1-V28 are PCA-transformed; their real-world interpretation is unavailable
- Fallback to built-in feature_importances_ if SHAP is unavailable

Reference: Borketey (2024) uses SHAP summary plots and force plots
for global and local interpretability of the Random Forest model.
"""
from __future__ import annotations

import json
from typing import Any, Optional

import numpy as np

from backend.core.logging_config import get_logger
from backend.ml.data_loader import FEATURE_COLUMNS

logger = get_logger(__name__)


class ExplainerService:
    """SHAP-based explainability for the trained model."""

    def __init__(self) -> None:
        self._explainer = None
        self._model = None
        self._available = False

    def setup(self, model: Any) -> bool:
        """
        Initialize a SHAP explainer for the given model.
        Selects the appropriate explainer type based on model class.
        """
        self._model = model
        try:
            import shap

            model_class = type(model).__name__

            if model_class in ("RandomForestClassifier", "GradientBoostingClassifier",
                               "DecisionTreeClassifier", "XGBClassifier"):
                self._explainer = shap.TreeExplainer(model)
                logger.info(f"SHAP TreeExplainer initialized for {model_class}")
            elif model_class == "LogisticRegression":
                # LinearExplainer requires a background dataset; use model coefficients
                self._explainer = shap.LinearExplainer(
                    model, masker=shap.maskers.Independent(
                        np.zeros((1, len(FEATURE_COLUMNS)))
                    )
                )
                logger.info(f"SHAP LinearExplainer initialized for {model_class}")
            else:
                logger.warning(f"No specialized SHAP explainer for {model_class}. Skipping.")
                return False

            self._available = True
            return True

        except ImportError:
            logger.warning("SHAP library not available. Explainability disabled.")
            return False
        except Exception as e:
            logger.warning(f"Could not initialize SHAP explainer: {e}")
            return False

    @property
    def is_available(self) -> bool:
        return self._available

    def explain_transaction(
        self, X: np.ndarray
    ) -> Optional[dict[str, Any]]:
        """
        Compute SHAP values for a single transaction.

        Args:
            X: Feature array, shape (n_features,) or (1, n_features).

        Returns:
            Dict with:
              - feature_contributions: {feature_name: shap_value}
              - base_value: baseline prediction
              - top_positive: features increasing fraud probability
              - top_negative: features decreasing fraud probability
              - disclaimer: reminder about interpretation limits
        """
        if not self._available:
            return None

        try:
            import shap
            X_2d = X.reshape(1, -1) if X.ndim == 1 else X

            shap_values = self._explainer.shap_values(X_2d)

            # For binary classifiers, shap_values may be a list of [class0, class1]
            if isinstance(shap_values, list):
                # Take class-1 (fraud) SHAP values
                sv = shap_values[1][0]
            else:
                sv = shap_values[0]

            contributions = {
                feat: round(float(val), 6)
                for feat, val in zip(FEATURE_COLUMNS, sv)
            }

            # Sort by absolute contribution
            sorted_contrib = sorted(
                contributions.items(), key=lambda x: abs(x[1]), reverse=True
            )

            top_positive = [
                {"feature": k, "value": v, "direction": "increases_fraud_probability"}
                for k, v in sorted_contrib if v > 0
            ][:5]

            top_negative = [
                {"feature": k, "value": v, "direction": "decreases_fraud_probability"}
                for k, v in sorted_contrib if v < 0
            ][:5]

            base_value = None
            try:
                ev = self._explainer.expected_value
                base_value = float(ev[1]) if isinstance(ev, (list, np.ndarray)) else float(ev)
            except Exception:
                pass

            return {
                "feature_contributions": contributions,
                "base_value": base_value,
                "top_positive_contributors": top_positive,
                "top_negative_contributors": top_negative,
                "method": "SHAP TreeExplainer" if "Tree" in type(self._explainer).__name__ else "SHAP",
                "disclaimer": (
                    "SHAP values show each feature's contribution to this prediction. "
                    "V1-V28 are PCA-transformed; their original real-world meaning is unavailable. "
                    "These are model contributions, not causal explanations. "
                    "A positive SHAP value increases the fraud probability estimate."
                ),
            }

        except Exception as e:
            logger.warning(f"SHAP explanation failed: {e}")
            return None

    def get_global_importance(self) -> Optional[dict[str, float]]:
        """
        Return global feature importance from the model.
        Uses built-in feature_importances_ (not SHAP) as this is more efficient globally.
        """
        if self._model is None:
            return None

        if hasattr(self._model, "feature_importances_"):
            importances = self._model.feature_importances_
            return {
                feat: round(float(imp), 6)
                for feat, imp in sorted(
                    zip(FEATURE_COLUMNS, importances),
                    key=lambda x: x[1], reverse=True
                )
            }

        if hasattr(self._model, "coef_"):
            # Logistic Regression: use absolute coefficients
            coefs = np.abs(self._model.coef_[0])
            total = coefs.sum()
            return {
                feat: round(float(c / total if total > 0 else c), 6)
                for feat, c in sorted(
                    zip(FEATURE_COLUMNS, coefs),
                    key=lambda x: x[1], reverse=True
                )
            }

        return None


# Module-level singleton
explainer_service = ExplainerService()


def get_explainer() -> ExplainerService:
    return explainer_service
