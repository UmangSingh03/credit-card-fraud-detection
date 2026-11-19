"""
Pydantic schemas for request validation and API responses.
"""
from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


class TransactionInput(BaseModel):
    """Transaction input features for fraud scoring."""
    Time: float = Field(..., description="Seconds elapsed since first transaction")
    Amount: float = Field(..., ge=0.0, description="Transaction amount")
    V1: float
    V2: float
    V3: float
    V4: float
    V5: float
    V6: float
    V7: float
    V8: float
    V9: float
    V10: float
    V11: float
    V12: float
    V13: float
    V14: float
    V15: float
    V16: float
    V17: float
    V18: float
    V19: float
    V20: float
    V21: float
    V22: float
    V23: float
    V24: float
    V25: float
    V26: float
    V27: float
    V28: float
    external_id: Optional[str] = Field(default=None, description="Client transaction ID")
    explain: bool = Field(default=False, description="Whether to include SHAP explanations")


class BatchTransactionInput(BaseModel):
    """Batch transaction input."""
    transactions: list[TransactionInput]


class PredictionResponse(BaseModel):
    id: Optional[str] = None
    predicted_class: int
    fraud_probability: Optional[float] = None
    risk_category: str
    anomaly_score: Optional[float] = None
    is_anomalous: Optional[bool] = None
    latency_ms: Optional[float] = None
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    explanation: Optional[dict[str, Any]] = None


class AlertSummary(BaseModel):
    id: str
    severity: str
    alert_reason: str
    status: str


class TransactionResponse(BaseModel):
    transaction_id: str
    external_id: Optional[str] = None
    time_seconds: Optional[float] = None
    amount: Optional[float] = None
    source: str
    created_at: str
    prediction: Optional[PredictionResponse] = None
    alert: Optional[AlertSummary] = None


class AlertUpdateRequest(BaseModel):
    status: Optional[str] = Field(default=None, description="PENDING, ACKNOWLEDGED, RESOLVED, DISMISSED")
    review_notes: Optional[str] = Field(default=None, description="Human reviewer notes")
    confirmed_fraud: Optional[bool] = Field(default=None, description="True=fraud, False=legitimate, None=unverified")


class AlertResponse(BaseModel):
    id: str
    transaction_id: str
    prediction_id: Optional[str] = None
    status: str
    severity: str
    alert_reason: str
    review_notes: Optional[str] = None
    confirmed_fraud: Optional[bool] = None
    created_at: str
    updated_at: str


class SimulationConfigRequest(BaseModel):
    interval_seconds: Optional[float] = Field(default=None, ge=0.01, le=10.0)
    batch_size: Optional[int] = Field(default=None, ge=1, le=100)


class SimulationStatusResponse(BaseModel):
    state: str
    interval_seconds: float
    batch_size: int
    total_streamed: int
    total_fraud_detected: int


class TrainingTriggerResponse(BaseModel):
    status: str
    run_id: Optional[str] = None
    message: Optional[str] = None


class ModelVersionResponse(BaseModel):
    id: str
    model_name: str
    version_tag: str
    is_active: bool
    trained_at: str
    test_accuracy: Optional[float] = None
    test_precision: Optional[float] = None
    test_recall: Optional[float] = None
    test_f1: Optional[float] = None
    test_roc_auc: Optional[float] = None
    test_pr_auc: Optional[float] = None
    test_fpr: Optional[float] = None
    inference_latency_ms: Optional[float] = None
    selection_rationale: Optional[str] = None
