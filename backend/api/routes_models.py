"""
Model registry, comparison, retraining, and reports endpoints.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from backend.api.schemas import ModelVersionResponse, TrainingTriggerResponse
from backend.core.config import settings
from backend.db.database import get_db
from backend.db.models import ModelVersion, TrainingRun
from backend.ml.predictor import get_prediction_service
from backend.ml.explainer import get_explainer
from backend.services.training_service import training_manager

router = APIRouter(prefix="/models", tags=["Models"])


@router.get("/active")
def get_active_model(db: Session = Depends(get_db)) -> Any:
    """Get active model details, metrics, and global feature importance."""
    query = select(ModelVersion).where(ModelVersion.is_active == True).limit(1)
    result = db.execute(query)
    model = result.scalar_one_or_none()

    predictor = get_prediction_service()
    explainer = get_explainer()
    global_imp = explainer.get_global_importance()

    return {
        "is_loaded": predictor.is_loaded,
        "model_name": model.model_name if model else predictor.model_name,
        "version_tag": model.version_tag if model else predictor.model_version,
        "metadata": predictor.metadata,
        "metrics": {
            "accuracy": model.test_accuracy if model else None,
            "precision": model.test_precision if model else None,
            "recall": model.test_recall if model else None,
            "f1": model.test_f1 if model else None,
            "roc_auc": model.test_roc_auc if model else None,
            "pr_auc": model.test_pr_auc if model else None,
            "fpr": model.test_fpr if model else None,
            "latency_ms": model.inference_latency_ms if model else None,
        } if model else None,
        "selection_rationale": model.selection_rationale if model else None,
        "global_feature_importance": global_imp,
    }


@router.get("", response_model=list[ModelVersionResponse])
def list_model_versions(db: Session = Depends(get_db)) -> Any:
    """List all registered model versions."""
    query = select(ModelVersion).order_by(desc(ModelVersion.trained_at))
    result = db.execute(query)
    models = result.scalars().all()
    return [
        {
            "id": m.id,
            "model_name": m.model_name,
            "version_tag": m.version_tag,
            "is_active": m.is_active,
            "trained_at": m.trained_at.isoformat() if m.trained_at else "",
            "test_accuracy": m.test_accuracy,
            "test_precision": m.test_precision,
            "test_recall": m.test_recall,
            "test_f1": m.test_f1,
            "test_roc_auc": m.test_roc_auc,
            "test_pr_auc": m.test_pr_auc,
            "test_fpr": m.test_fpr,
            "inference_latency_ms": m.inference_latency_ms,
            "selection_rationale": m.selection_rationale,
        }
        for m in models
    ]


@router.get("/comparison")
def get_model_comparison(db: Session = Depends(get_db)) -> Any:
    """Get multi-model benchmark evaluation metrics."""
    comparison_file = settings.get_report_path("model_comparison.json")
    if comparison_file.exists():
        try:
            with open(comparison_file, "r") as f:
                return json.load(f)
        except Exception:
            pass

    query = select(ModelVersion).where(ModelVersion.is_active == True).limit(1)
    result = db.execute(query)
    model = result.scalar_one_or_none()
    if model and model.comparison_json:
        try:
            return json.loads(model.comparison_json)
        except Exception:
            pass

    return {"message": "No model comparison data available yet. Please train models first."}


@router.post("/train", response_model=TrainingTriggerResponse)
async def trigger_training() -> Any:
    """Trigger the multi-model training pipeline in the background."""
    return await training_manager.start_training()


@router.get("/train/status")
def get_training_status(db: Session = Depends(get_db)) -> Any:
    """Check the status of the current or most recent training run."""
    run = training_manager.get_latest_run(db)
    if not run:
        return {"status": "IDLE", "progress_percent": 0.0, "current_stage": None}
    return {
        "run_id": run.id,
        "status": run.status,
        "progress_percent": run.progress_percent,
        "current_stage": run.current_stage,
        "error_message": run.error_message,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
    }


@router.get("/reports/{filename}")
def get_report_artifact(filename: str) -> FileResponse:
    """Serve evaluation charts (png files) generated during training."""
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    path = settings.get_report_path(filename)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report artifact not found")

    media_type = "image/png" if filename.endswith(".png") else "application/json"
    return FileResponse(path, media_type=media_type)
