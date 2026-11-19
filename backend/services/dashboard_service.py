"""
Dashboard service aggregating operational metrics, fraud distribution, and trends.
"""
from __future__ import annotations

import json
from typing import Any
from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session

from backend.db.models import Transaction, Prediction, Alert, ModelVersion
from backend.services.alert_service import AlertService


class DashboardService:
    """Provides aggregated system statistics for executive and analyst dashboards."""

    @staticmethod
    def get_overview_stats(session: Session) -> dict[str, Any]:
        """Aggregate high-level operational statistics."""
        total_tx = session.execute(select(func.count(Transaction.id))).scalar() or 0

        high_risk_count = (
            session.execute(
                select(func.count(Prediction.id)).where(Prediction.risk_category == "HIGH")
            )
        ).scalar() or 0

        medium_risk_count = (
            session.execute(
                select(func.count(Prediction.id)).where(Prediction.risk_category == "MEDIUM")
            )
        ).scalar() or 0

        low_risk_count = (
            session.execute(
                select(func.count(Prediction.id)).where(Prediction.risk_category == "LOW")
            )
        ).scalar() or 0

        avg_latency = (
            session.execute(select(func.avg(Prediction.prediction_latency_ms)))
        ).scalar() or 0.0

        alert_counts = AlertService.get_alert_counts(session)

        active_model_res = session.execute(
            select(ModelVersion).where(ModelVersion.is_active == True).limit(1)
        )
        active_model = active_model_res.scalar_one_or_none()

        fraud_rate = (high_risk_count / total_tx * 100) if total_tx > 0 else 0.0

        return {
            "total_transactions": total_tx,
            "high_risk_count": high_risk_count,
            "medium_risk_count": medium_risk_count,
            "low_risk_count": low_risk_count,
            "fraud_rate_pct": round(fraud_rate, 2),
            "avg_latency_ms": round(float(avg_latency), 2),
            "alerts": alert_counts,
            "active_model": {
                "name": active_model.model_name if active_model else "Not Loaded",
                "version": active_model.version_tag if active_model else "N/A",
                "pr_auc": active_model.test_pr_auc if active_model else None,
                "roc_auc": active_model.test_roc_auc if active_model else None,
                "f1": active_model.test_f1 if active_model else None,
            } if active_model else None,
        }

    @staticmethod
    def get_risk_distribution(session: Session) -> list[dict[str, Any]]:
        """Get counts grouped by risk category for pie/bar chart."""
        query = (
            select(Prediction.risk_category, func.count(Prediction.id))
            .where(Prediction.risk_category.isnot(None))
            .group_by(Prediction.risk_category)
        )
        result = session.execute(query)
        rows = result.all()
        return [{"name": cat, "value": count} for cat, count in rows]

    @staticmethod
    def get_recent_volume_trend(session: Session, limit: int = 30) -> list[dict[str, Any]]:
        """Fetch the latest transactions for a mini-timeline chart."""
        query = (
            select(Transaction.created_at, Transaction.amount, Prediction.risk_category, Prediction.fraud_probability)
            .join(Prediction, Prediction.transaction_id == Transaction.id, isouter=True)
            .order_by(desc(Transaction.created_at))
            .limit(limit)
        )
        result = session.execute(query)
        rows = result.all()
        return [
            {
                "timestamp": r[0].isoformat() if r[0] else "",
                "amount": round(float(r[1] or 0), 2),
                "risk_category": r[2] or "LOW",
                "fraud_probability": round(float(r[3] or 0), 4),
            }
            for r in reversed(rows)
        ]
