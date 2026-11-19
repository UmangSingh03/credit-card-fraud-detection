"""
Alert service for managing fraud alerts.
Handles alert creation, status transitions, review notes, and fraud confirmation.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional, Sequence

from sqlalchemy import select, update, desc, func
from sqlalchemy.orm import Session

from backend.core.logging_config import get_logger
from backend.db.models import Alert, Transaction, Prediction
from backend.services.websocket_manager import ws_manager

logger = get_logger(__name__)


class AlertService:
    """Service handling fraud alert operations."""

    @staticmethod
    async def create_alert(
        session: Session,
        transaction_id: str,
        prediction_id: Optional[str],
        severity: str,
        alert_reason: str,
    ) -> Alert:
        """Create and persist a new fraud alert, and broadcast it via WebSocket."""
        alert = Alert(
            transaction_id=transaction_id,
            prediction_id=prediction_id,
            status="PENDING",
            severity=severity,
            alert_reason=alert_reason,
        )
        session.add(alert)
        session.flush()

        # Broadcast alert to connected dashboards
        alert_data = {
            "id": alert.id,
            "transaction_id": alert.transaction_id,
            "prediction_id": alert.prediction_id,
            "status": alert.status,
            "severity": alert.severity,
            "alert_reason": alert.alert_reason,
            "created_at": alert.created_at.isoformat() if alert.created_at else None,
        }
        await ws_manager.broadcast("new_alert", alert_data)
        logger.info(f"Alert created: id={alert.id}, severity={severity}, reason={alert_reason}")
        return alert

    @staticmethod
    def get_alerts(
        session: Session,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[Alert]:
        """Fetch alerts with optional filtering."""
        query = select(Alert).order_by(desc(Alert.created_at))
        if status:
            query = query.where(Alert.status == status.upper())
        if severity:
            query = query.where(Alert.severity == severity.upper())
        query = query.limit(limit).offset(offset)

        result = session.execute(query)
        return result.scalars().all()

    @staticmethod
    def get_alert_by_id(
        session: Session,
        alert_id: str,
    ) -> Optional[Alert]:
        """Fetch a single alert by ID."""
        query = select(Alert).where(Alert.id == alert_id)
        result = session.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_alert(
        session: Session,
        alert_id: str,
        status: Optional[str] = None,
        review_notes: Optional[str] = None,
        confirmed_fraud: Optional[bool] = None,
    ) -> Optional[Alert]:
        """Update an alert's triage status, notes, or confirmed fraud status."""
        alert = AlertService.get_alert_by_id(session, alert_id)
        if not alert:
            return None

        if status:
            valid_statuses = {"PENDING", "ACKNOWLEDGED", "RESOLVED", "DISMISSED"}
            normalized_status = status.upper()
            if normalized_status in valid_statuses:
                alert.status = normalized_status
        if review_notes is not None:
            alert.review_notes = review_notes
        if confirmed_fraud is not None:
            alert.confirmed_fraud = confirmed_fraud

        alert.updated_at = datetime.now(timezone.utc)
        session.commit()
        session.refresh(alert)

        # Broadcast update
        await ws_manager.broadcast(
            "alert_updated",
            {
                "id": alert.id,
                "status": alert.status,
                "review_notes": alert.review_notes,
                "confirmed_fraud": alert.confirmed_fraud,
                "updated_at": alert.updated_at.isoformat(),
            },
        )
        return alert

    @staticmethod
    def get_alert_counts(session: Session) -> dict[str, int]:
        """Get count of alerts grouped by status."""
        query = select(Alert.status, func.count(Alert.id)).group_by(Alert.status)
        result = session.execute(query)
        counts = {row[0]: row[1] for row in result.all()}
        return {
            "total": sum(counts.values()),
            "pending": counts.get("PENDING", 0),
            "acknowledged": counts.get("ACKNOWLEDGED", 0),
            "resolved": counts.get("RESOLVED", 0),
            "dismissed": counts.get("DISMISSED", 0),
        }
