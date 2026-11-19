"""
Integration and route tests for backend API services and endpoints.
"""
import pytest
from backend.main import health_check, system_info
from backend.api.routes_dashboard import get_dashboard_stats, get_risk_distribution
from backend.api.routes_alerts import list_alerts, get_alert_summary
from backend.api.routes_models import get_active_model, list_model_versions
from backend.api.routes_simulation import get_simulation_status
from backend.db.database import SessionLocal, init_db
from backend.ml.predictor import get_prediction_service
from backend.ml.anomaly import get_anomaly_detector
from backend.services.transaction_service import TransactionService


@pytest.fixture(scope="module", autouse=True)
def setup_database_and_models():
    """Ensure DB tables are initialized and model artifacts are loaded before tests run."""
    init_db()
    predictor = get_prediction_service()
    predictor.load()
    anomaly = get_anomaly_detector()
    anomaly.load()


def test_system_info_endpoint():
    res = system_info()
    assert res["system"] == "Real-Time Credit Card Fraud Detection System"
    assert res["api_prefix"] == "/api"


def test_health_check_endpoint():
    res = health_check()
    assert res["status"] == "healthy"
    assert res["model_loaded"] == "yes"
    assert res["model_name"] == "RandomForest"


def test_dashboard_stats_endpoint():
    with SessionLocal() as db:
        stats = get_dashboard_stats(db)
        assert "total_transactions" in stats
        assert "high_risk_count" in stats
        assert "fraud_rate_pct" in stats
        assert "alerts" in stats


def test_risk_distribution_endpoint():
    with SessionLocal() as db:
        distribution = get_risk_distribution(db)
        assert isinstance(distribution, list)


def test_alerts_endpoints():
    with SessionLocal() as db:
        alerts = list_alerts(db=db)
        assert isinstance(alerts, list)
        summary = get_alert_summary(db=db)
        assert "total" in summary
        assert "pending" in summary


def test_models_endpoints():
    with SessionLocal() as db:
        active = get_active_model(db=db)
        assert active["is_loaded"] is True
        assert active["model_name"] == "RandomForest"
        versions = list_model_versions(db=db)
        assert isinstance(versions, list)


def test_simulation_status_endpoint():
    status = get_simulation_status()
    assert "state" in status
    assert status["state"] in ("STOPPED", "RUNNING", "PAUSED")
    assert "interval_seconds" in status


def test_prediction_service_scoring():
    predictor = get_prediction_service()
    assert predictor.is_loaded is True

    # Test scoring with standard feature vector
    sample_features = {
        "Time": 406.0,
        "Amount": 149.62,
        **{f"V{i}": 0.1 for i in range(1, 29)},
    }
    result = predictor.predict(sample_features)
    assert result.predicted_class in (0, 1)
    assert 0.0 <= result.fraud_probability <= 1.0
    assert result.risk_category in ("LOW", "MEDIUM", "HIGH")
    assert result.latency_ms > 0
