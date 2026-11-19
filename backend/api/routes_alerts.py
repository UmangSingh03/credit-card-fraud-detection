"""
Alert management endpoints for fraud triage.
"""
from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.api.schemas import AlertResponse, AlertUpdateRequest
from backend.db.database import get_db
from backend.services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("", response_model=list[AlertResponse])
def list_alerts(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> Any:
    """List fraud alerts with optional status/severity filtering."""
    status_str = status if isinstance(status, str) else None
    severity_str = severity if isinstance(severity, str) else None
    limit_int = limit if isinstance(limit, int) else 50
    offset_int = offset if isinstance(offset, int) else 0

    alerts = AlertService.get_alerts(
        session=db,
        status=status_str,
        severity=severity_str,
        limit=limit_int,
        offset=offset_int,
    )
    return [
        {
            "id": a.id,
            "transaction_id": a.transaction_id,
            "prediction_id": a.prediction_id,
            "status": a.status,
            "severity": a.severity,
            "alert_reason": a.alert_reason,
            "review_notes": a.review_notes,
            "confirmed_fraud": a.confirmed_fraud,
            "created_at": a.created_at.isoformat() if a.created_at else "",
            "updated_at": a.updated_at.isoformat() if a.updated_at else "",
        }
        for a in alerts
    ]


@router.get("/counts")
def get_alert_summary(
    db: Session = Depends(get_db),
) -> Any:
    """Get alert counts grouped by status."""
    return AlertService.get_alert_counts(db)


@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert(
    alert_id: str,
    db: Session = Depends(get_db),
) -> Any:
    """Retrieve details for a single alert."""
    alert = AlertService.get_alert_by_id(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {
        "id": alert.id,
        "transaction_id": alert.transaction_id,
        "prediction_id": alert.prediction_id,
        "status": alert.status,
        "severity": alert.severity,
        "alert_reason": alert.alert_reason,
        "review_notes": alert.review_notes,
        "confirmed_fraud": alert.confirmed_fraud,
        "created_at": alert.created_at.isoformat() if alert.created_at else "",
        "updated_at": alert.updated_at.isoformat() if alert.updated_at else "",
    }


@router.patch("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: str,
    payload: AlertUpdateRequest,
    db: Session = Depends(get_db),
) -> Any:
    """Update alert triage status, review notes, or mark confirmed fraud status."""
    updated = await AlertService.update_alert(
        session=db,
        alert_id=alert_id,
        status=payload.status,
        review_notes=payload.review_notes,
        confirmed_fraud=payload.confirmed_fraud,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {
        "id": updated.id,
        "transaction_id": updated.transaction_id,
        "prediction_id": updated.prediction_id,
        "status": updated.status,
        "severity": updated.severity,
        "alert_reason": updated.alert_reason,
        "review_notes": updated.review_notes,
        "confirmed_fraud": updated.confirmed_fraud,
        "created_at": updated.created_at.isoformat() if updated.created_at else "",
        "updated_at": updated.updated_at.isoformat() if updated.updated_at else "",
    }
