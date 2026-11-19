"""
Training service managing background model training execution and lifecycle.
"""
from __future__ import annotations

import asyncio
import json
import threading
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select, update, desc
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.logging_config import get_logger
from backend.db.database import SessionLocal
from backend.db.models import TrainingRun, ModelVersion
from backend.ml.predictor import get_prediction_service
from backend.ml.anomaly import get_anomaly_detector
from backend.ml.explainer import get_explainer
from backend.services.websocket_manager import ws_manager

logger = get_logger(__name__)


class TrainingManager:
    """Manages asynchronous training jobs."""

    def __init__(self) -> None:
        self.is_training: bool = False
        self.current_run_id: Optional[str] = None
        self._lock = threading.Lock()

    async def start_training(self) -> dict[str, Any]:
        """Trigger a new training run if none is currently executing."""
        with self._lock:
            if self.is_training:
                return {
                    "status": "conflict",
                    "message": "A training job is already in progress.",
                    "run_id": self.current_run_id,
                }
            self.is_training = True

        with SessionLocal() as session:
            run = TrainingRun(
                status="RUNNING",
                progress_percent=0.0,
                current_stage="Initializing training pipeline",
                started_at=datetime.now(timezone.utc),
            )
            session.add(run)
            session.commit()
            session.refresh(run)
            self.current_run_id = run.id

        loop = asyncio.get_running_loop()
        threading.Thread(
            target=self._run_pipeline_worker,
            args=(loop, self.current_run_id),
            daemon=True,
        ).start()

        return {
            "status": "started",
            "run_id": self.current_run_id,
        }

    def _run_pipeline_worker(self, loop: asyncio.AbstractEventLoop, run_id: str) -> None:
        """Worker thread executing the training pipeline and updating DB."""
        def progress_callback(pct: float, stage: str) -> None:
            asyncio.run_coroutine_threadsafe(
                self._update_progress(run_id, pct, stage),
                loop,
            )

        try:
            from backend.ml.train import run_training_pipeline
            results = run_training_pipeline(progress_cb=progress_callback)

            asyncio.run_coroutine_threadsafe(
                self._on_training_complete(run_id, results),
                loop,
            ).result()

        except Exception as e:
            logger.error(f"Training run {run_id} failed: {e}", exc_info=True)
            asyncio.run_coroutine_threadsafe(
                self._on_training_failed(run_id, str(e)),
                loop,
            ).result()

        finally:
            with self._lock:
                self.is_training = False
                self.current_run_id = None

    async def _update_progress(self, run_id: str, pct: float, stage: str) -> None:
        """Update DB and broadcast progress over WebSocket."""
        with SessionLocal() as session:
            stmt = (
                update(TrainingRun)
                .where(TrainingRun.id == run_id)
                .values(progress_percent=pct, current_stage=stage)
            )
            session.execute(stmt)
            session.commit()

        await ws_manager.broadcast(
            "training_progress",
            {"run_id": run_id, "progress_percent": pct, "current_stage": stage},
        )

    async def _on_training_complete(self, run_id: str, results: dict[str, Any]) -> None:
        """Handle training pipeline success."""
        selected_model_name = results.get("selected_model", "RandomForest")
        metrics = results.get("metrics", {})
        selected_metrics = metrics.get(selected_model_name, {})

        with SessionLocal() as session:
            session.execute(
                update(ModelVersion).values(is_active=False)
            )

            model_ver = ModelVersion(
                model_name=selected_model_name,
                version_tag=f"v{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
                is_active=True,
                artifact_path=str(settings.get_model_path("model.pkl")),
                preprocessor_path=str(settings.get_model_path("preprocessor.pkl")),
                feature_schema_json=json.dumps(settings.expected_feature_columns),
                trained_at=datetime.now(timezone.utc),
                test_accuracy=selected_metrics.get("accuracy"),
                test_precision=selected_metrics.get("precision"),
                test_recall=selected_metrics.get("recall"),
                test_f1=selected_metrics.get("f1"),
                test_roc_auc=selected_metrics.get("roc_auc"),
                test_pr_auc=selected_metrics.get("pr_auc"),
                test_fpr=selected_metrics.get("false_positive_rate"),
                inference_latency_ms=selected_metrics.get("latency_ms"),
                comparison_json=json.dumps(metrics),
                selection_rationale=results.get("selection_rationale", "Highest PR-AUC on validation set"),
            )
            session.add(model_ver)
            session.flush()

            stmt = (
                update(TrainingRun)
                .where(TrainingRun.id == run_id)
                .values(
                    status="DONE",
                    progress_percent=100.0,
                    current_stage="Completed successfully",
                    model_version_id=model_ver.id,
                    completed_at=datetime.now(timezone.utc),
                )
            )
            session.execute(stmt)
            session.commit()

        # Reload inference engines
        get_prediction_service().load(force=True)
        get_anomaly_detector().load(force=True)
        if get_prediction_service().is_loaded:
            get_explainer().setup(get_prediction_service()._model)

        logger.info(f"Training run {run_id} completed successfully. Active model: {selected_model_name}")

        await ws_manager.broadcast(
            "training_completed",
            {
                "run_id": run_id,
                "model_name": selected_model_name,
                "metrics": selected_metrics,
            },
        )

    async def _on_training_failed(self, run_id: str, error_msg: str) -> None:
        """Handle training pipeline failure."""
        with SessionLocal() as session:
            stmt = (
                update(TrainingRun)
                .where(TrainingRun.id == run_id)
                .values(
                    status="FAILED",
                    error_message=error_msg,
                    completed_at=datetime.now(timezone.utc),
                )
            )
            session.execute(stmt)
            session.commit()

        await ws_manager.broadcast(
            "training_failed",
            {"run_id": run_id, "error": error_msg},
        )

    def get_latest_run(self, session: Session) -> Optional[TrainingRun]:
        """Fetch the most recent training run."""
        query = select(TrainingRun).order_by(desc(TrainingRun.created_at)).limit(1)
        result = session.execute(query)
        return result.scalar_one_or_none()


training_manager = TrainingManager()
