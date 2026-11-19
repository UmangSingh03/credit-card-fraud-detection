"""
Main FastAPI application entrypoint.
Configures CORS, lifespan hooks, database initialization, and routing.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.core.config import settings, BASE_DIR
from backend.core.logging_config import setup_logging, get_logger
from backend.db.database import init_db
from backend.ml.predictor import get_prediction_service
from backend.ml.anomaly import get_anomaly_detector
from backend.ml.explainer import get_explainer
from backend.services.simulation_service import simulation_service

from backend.api.routes_transactions import router as transactions_router
from backend.api.routes_alerts import router as alerts_router
from backend.api.routes_models import router as models_router
from backend.api.routes_simulation import router as simulation_router
from backend.api.routes_dashboard import router as dashboard_router
from backend.api.routes_websocket import router as ws_router

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup and shutdown lifecycle management."""
    logger.info("Initializing fraud detection backend...")

    # 1. Initialize SQLite database tables
    init_db()

    # 2. Attempt loading ML inference models
    predictor = get_prediction_service()
    if predictor.load():
        logger.info(f"Loaded active model: {predictor.model_name} ({predictor.model_version})")
        # Load anomaly detector
        anomaly = get_anomaly_detector()
        if anomaly.load():
            logger.info("Isolation Forest anomaly detector loaded.")
        # Setup explainer
        explainer = get_explainer()
        if predictor._model is not None:
            explainer.setup(predictor._model)
    else:
        logger.warning(
            "No pre-trained model found at startup. "
            "Use the 'Train Model' feature or execute python -m backend.ml.train"
        )

    yield

    # Shutdown logic
    logger.info("Shutting down fraud detection backend...")
    if simulation_service.is_running:
        await simulation_service.stop()


app = FastAPI(
    title="Real-Time Credit Card Fraud Detection System",
    description="Production-grade ML-powered fraud detection API with real-time inference, anomaly detection, and SHAP explainability.",
    version="1.0.0",
    lifespan=lifespan,
)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    settings.frontend_origin,
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(transactions_router, prefix="/api")
app.include_router(alerts_router, prefix="/api")
app.include_router(models_router, prefix="/api")
app.include_router(simulation_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(ws_router)


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    predictor = get_prediction_service()
    return {
        "status": "healthy",
        "model_loaded": "yes" if predictor.is_loaded else "no",
        "model_name": predictor.model_name,
    }


@app.get("/api/system", tags=["System"])
def system_info() -> dict[str, str]:
    """System info endpoint."""
    return {
        "system": "Real-Time Credit Card Fraud Detection System",
        "docs_url": "/docs",
        "api_prefix": "/api",
        "websocket_url": "/ws",
    }


# Mount frontend dist if built
dist_dir = BASE_DIR / "frontend" / "dist"
if dist_dir.exists():
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="frontend")
else:
    @app.get("/", tags=["Root"])
    def root() -> dict[str, str]:
        return system_info()
