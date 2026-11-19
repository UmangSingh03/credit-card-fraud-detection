"""
Transaction endpoints for single and batch scoring, history, and inspection.
"""
from __future__ import annotations

import io
from typing import Any, Optional
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session

from backend.api.schemas import TransactionInput, BatchTransactionInput, TransactionResponse
from backend.db.database import get_db
from backend.ml.predictor import get_prediction_service
from backend.services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("", response_model=TransactionResponse)
async def score_transaction(
    payload: TransactionInput,
    db: Session = Depends(get_db),
) -> Any:
    """
    Score a single transaction in real-time.
    Returns fraud probability, risk category, anomaly status, and optional SHAP explanation.
    """
    predictor = get_prediction_service()
    if not predictor.is_loaded:
        raise HTTPException(
            status_code=503,
            detail="Model is not loaded. Please train or load a model first.",
        )

    features = payload.model_dump()
    explain = features.pop("explain", False)
    external_id = features.pop("external_id", None)

    try:
        result = await TransactionService.process_transaction(
            session=db,
            features=features,
            external_id=external_id,
            source="api",
            explain=explain,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/batch")
async def score_batch(
    payload: BatchTransactionInput,
    db: Session = Depends(get_db),
) -> Any:
    """Score a batch of transactions (JSON list)."""
    predictor = get_prediction_service()
    if not predictor.is_loaded:
        raise HTTPException(
            status_code=503,
            detail="Model is not loaded. Please train or load a model first.",
        )

    items = [t.model_dump() for t in payload.transactions]
    results = await TransactionService.process_batch(db, items, source="batch")
    return {"count": len(results), "results": results}


@router.post("/upload-csv")
async def upload_csv_batch(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> Any:
    """Upload a CSV file of transactions to score."""
    predictor = get_prediction_service()
    if not predictor.is_loaded:
        raise HTTPException(
            status_code=503,
            detail="Model is not loaded. Please train or load a model first.",
        )

    try:
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))
        df_sample = df.head(500)
        items = df_sample.to_dict(orient="records")
        results = await TransactionService.process_batch(db, items, source="csv_upload")
        return {
            "filename": file.filename,
            "processed_rows": len(results),
            "results": results,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process CSV: {e}")


@router.get("", response_model=list[dict[str, Any]])
def get_transactions(
    limit: int = 50,
    offset: int = 0,
    risk_category: Optional[str] = None,
    db: Session = Depends(get_db),
) -> Any:
    """Retrieve transaction history with optional risk filter."""
    limit_int = limit if isinstance(limit, int) else 50
    offset_int = offset if isinstance(offset, int) else 0
    risk_str = risk_category if isinstance(risk_category, str) else None
    return TransactionService.get_recent_transactions(
        session=db,
        limit=limit_int,
        offset=offset_int,
        risk_category=risk_str,
    )


@router.get("/{transaction_id}")
def get_transaction_detail(
    transaction_id: str,
    db: Session = Depends(get_db),
) -> Any:
    """Get full details of a specific transaction including features and SHAP explanation."""
    tx = TransactionService.get_transaction_by_id(db, transaction_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return tx
