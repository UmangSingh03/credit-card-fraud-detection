"""
Dashboard endpoints for aggregated operational metrics.
"""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)) -> Any:
    """Get high-level operational statistics."""
    return DashboardService.get_overview_stats(db)


@router.get("/risk-distribution")
def get_risk_distribution(db: Session = Depends(get_db)) -> Any:
    """Get transaction count by risk category."""
    return DashboardService.get_risk_distribution(db)


@router.get("/trend")
def get_volume_trend(db: Session = Depends(get_db)) -> Any:
    """Get recent transactions for live activity chart."""
    return DashboardService.get_recent_volume_trend(db)
