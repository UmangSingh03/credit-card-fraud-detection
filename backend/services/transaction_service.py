"""
Transaction processing service.
Orchestrates prediction, anomaly detection, local explainability, DB persistence, and alerts.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional, Sequence

from sqlalchemy import select, desc
from sqlalchemy.orm import Session, selectinload

from backend.core.config import settings
from backend.core.logging_config import get_logger
from backend.db.models import Transaction, Prediction, Alert, ModelVersion
from backend.ml.predictor import get_prediction_service
from backend.ml.anomaly import get_anomaly_detector
from backend.ml.explainer import get_explainer
from backend.services.alert_service import AlertService
from backend.services.websocket_manager import ws_manager

logger = get_logger(__name__)


class TransactionService:
    """Service to process transactions through the ML pipeline."""

    @staticmethod
    async def process_transaction(
        session: Session,
        features: dict[str, Any],
        external_id: Optional[str] = None,
        source: str = "api",
        explain: bool = False,
    ) -> dict[str, Any]:
        """
        Process a single transaction:
        1. Predict fraud probability and risk category
        2. Detect anomalies using Isolation Forest
        3. Compute SHAP explanations (if requested or for high risk)
        4. Save transaction and prediction in database
        5. Trigger alert if risk is elevated
        6. Broadcast to real-time clients
        """
        predictor = get_prediction_service()
        anomaly_detector = get_anomaly_detector()
        explainer = get_explainer()

        # 1. Run prediction
        pred_result = predictor.predict(features)

        # 2. Run anomaly detector
        anomaly_res = anomaly_detector.predict(features)
        anomaly_score = anomaly_res.anomaly_score if anomaly_res else None
        is_anomalous = anomaly_res.is_anomalous if anomaly_res else False

        # 3. Compute explanation if requested or if high risk
        explanation_data = None
        should_explain = explain or (pred_result.risk_category in ("HIGH", "MEDIUM"))
        if should_explain and explainer.is_available:
            try:
                explanation = explainer.explain_transaction(features, top_n=6)
                if explanation:
                    explanation_data = explanation.to_dict()
            except Exception as e:
                logger.warning(f"Failed to generate SHAP explanation: {e}")

        # 4. Save to database
        time_sec = float(features.get("Time", 0.0))
        amount = float(features.get("Amount", 0.0))
        pca_features = {k: features[k] for k in features if k.startswith("V")}

        tx = Transaction(
            external_id=external_id,
            time_seconds=time_sec,
            amount=amount,
            features_json=json.dumps(pca_features),
            source=source,
            created_at=datetime.now(timezone.utc),
        )
        session.add(tx)
        session.flush()

        prediction = Prediction(
            transaction_id=tx.id,
            predicted_class=pred_result.predicted_class,
            fraud_probability=pred_result.fraud_probability,
            risk_category=pred_result.risk_category,
            anomaly_score=anomaly_score,
            is_anomalous=is_anomalous,
            explanation_json=json.dumps(explanation_data) if explanation_data else None,
            prediction_latency_ms=pred_result.latency_ms,
            created_at=datetime.now(timezone.utc),
        )
        session.add(prediction)
        session.flush()

        # 5. Evaluate alert condition
        alert_record = None
        if pred_result.risk_category == "HIGH" and is_anomalous:
            alert_record = await AlertService.create_alert(
                session=session,
                transaction_id=tx.id,
                prediction_id=prediction.id,
                severity="CRITICAL",
                alert_reason="both",
            )
        elif pred_result.risk_category == "HIGH":
            alert_record = await AlertService.create_alert(
                session=session,
                transaction_id=tx.id,
                prediction_id=prediction.id,
                severity="HIGH",
                alert_reason="high_fraud_probability",
            )
        elif is_anomalous and pred_result.risk_category == "MEDIUM":
            alert_record = await AlertService.create_alert(
                session=session,
                transaction_id=tx.id,
                prediction_id=prediction.id,
                severity="HIGH",
                alert_reason="anomaly_detected",
            )

        session.commit()

        output = {
            "transaction_id": tx.id,
            "external_id": tx.external_id,
            "time_seconds": tx.time_seconds,
            "amount": tx.amount,
            "source": tx.source,
            "created_at": tx.created_at.isoformat(),
            "prediction": {
                "id": prediction.id,
                "predicted_class": prediction.predicted_class,
                "fraud_probability": prediction.fraud_probability,
                "risk_category": prediction.risk_category,
                "anomaly_score": prediction.anomaly_score,
                "is_anomalous": prediction.is_anomalous,
                "latency_ms": prediction.prediction_latency_ms,
                "model_name": pred_result.model_name,
                "model_version": pred_result.model_version,
                "explanation": explanation_data,
            },
            "alert": {
                "id": alert_record.id,
                "severity": alert_record.severity,
                "alert_reason": alert_record.alert_reason,
                "status": alert_record.status,
            } if alert_record else None,
        }

        # 6. Broadcast over WebSocket
        await ws_manager.broadcast("new_transaction", output)

        return output

    @staticmethod
    async def process_batch(
        session: Session,
        items: list[dict[str, Any]],
        source: str = "batch",
    ) -> list[dict[str, Any]]:
        """Process a list of transactions efficiently."""
        results = []
        for item in items:
            res = await TransactionService.process_transaction(
                session=session,
                features=item,
                external_id=item.get("external_id"),
                source=source,
                explain=False,
            )
            results.append(res)
        return results

    @staticmethod
    def get_recent_transactions(
        session: Session,
        limit: int = 50,
        offset: int = 0,
        risk_category: Optional[str] = None,
    ) -> Sequence[dict[str, Any]]:
        """Retrieve recent transactions with prediction details."""
        query = (
            select(Transaction)
            .options(
                selectinload(Transaction.predictions),
                selectinload(Transaction.alerts),
            )
            .order_by(desc(Transaction.created_at))
        )

        result = session.execute(query.limit(limit).offset(offset))
        transactions = result.scalars().all()

        formatted = []
        for tx in transactions:
            pred = tx.predictions[0] if tx.predictions else None
            alert = tx.alerts[0] if tx.alerts else None

            if risk_category and pred and pred.risk_category != risk_category.upper():
                continue

            expl_data = None
            if pred and pred.explanation_json:
                try:
                    expl_data = json.loads(pred.explanation_json)
                except Exception:
                    pass

            formatted.append({
                "id": tx.id,
                "external_id": tx.external_id,
                "time_seconds": tx.time_seconds,
                "amount": tx.amount,
                "source": tx.source,
                "created_at": tx.created_at.isoformat() if tx.created_at else None,
                "prediction": {
                    "id": pred.id if pred else None,
                    "predicted_class": pred.predicted_class if pred else None,
                    "fraud_probability": pred.fraud_probability if pred else None,
                    "risk_category": pred.risk_category if pred else None,
                    "anomaly_score": pred.anomaly_score if pred else None,
                    "is_anomalous": pred.is_anomalous if pred else None,
                    "latency_ms": pred.prediction_latency_ms if pred else None,
                    "explanation": expl_data,
                } if pred else None,
                "alert": {
                    "id": alert.id,
                    "severity": alert.severity,
                    "status": alert.status,
                    "alert_reason": alert.alert_reason,
                } if alert else None,
            })

        return formatted

    @staticmethod
    def get_transaction_by_id(
        session: Session,
        tx_id: str,
    ) -> Optional[dict[str, Any]]:
        """Fetch full transaction details including features and SHAP explanation."""
        query = (
            select(Transaction)
            .options(
                selectinload(Transaction.predictions),
                selectinload(Transaction.alerts),
            )
            .where(Transaction.id == tx_id)
        )
        result = session.execute(query)
        tx = result.scalar_one_or_none()
        if not tx:
            return None

        pred = tx.predictions[0] if tx.predictions else None
        alert = tx.alerts[0] if tx.alerts else None

        pca_features = {}
        if tx.features_json:
            try:
                pca_features = json.loads(tx.features_json)
            except Exception:
                pass

        expl_data = None
        if pred and pred.explanation_json:
            try:
                expl_data = json.loads(pred.explanation_json)
            except Exception:
                pass

        return {
            "id": tx.id,
            "external_id": tx.external_id,
            "time_seconds": tx.time_seconds,
            "amount": tx.amount,
            "features": {
                "Time": tx.time_seconds,
                "Amount": tx.amount,
                **pca_features,
            },
            "source": tx.source,
            "created_at": tx.created_at.isoformat() if tx.created_at else None,
            "prediction": {
                "id": pred.id if pred else None,
                "predicted_class": pred.predicted_class if pred else None,
                "fraud_probability": pred.fraud_probability if pred else None,
                "risk_category": pred.risk_category if pred else None,
                "anomaly_score": pred.anomaly_score if pred else None,
                "is_anomalous": pred.is_anomalous if pred else None,
                "latency_ms": pred.prediction_latency_ms if pred else None,
                "explanation": expl_data,
            } if pred else None,
            "alert": {
                "id": alert.id,
                "severity": alert.severity,
                "status": alert.status,
                "alert_reason": alert.alert_reason,
                "confirmed_fraud": alert.confirmed_fraud,
                "review_notes": alert.review_notes,
            } if alert else None,
        }
