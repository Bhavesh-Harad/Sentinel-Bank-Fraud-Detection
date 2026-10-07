"""
SENTINEL — Real-time Analyze API router.
POST /api/analyze  — score a new transaction through the full pipeline
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.transaction import Transaction
from app.models.fraud_prediction import FraudPrediction
from app.models.risk_factor import RiskFactor
from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse, RiskFactorDetail
from app.services.customer_service import CustomerService
from app.ml.inference import InferenceEngine, ModelNotReadyError
from app.ml.risk_engine import RiskEngine
from app.ml.preprocessing import get_city_coordinates

router = APIRouter(prefix="/analyze", tags=["Analyze"])
_risk_engine = RiskEngine()


@router.post("", response_model=AnalyzeResponse)
async def analyze_transaction(
    request: AnalyzeRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Score a transaction in real-time through the full 10-component risk pipeline.

    1. Look up customer profile for behavioural baseline
    2. Run autoencoder inference
    3. Compute 10-component hybrid risk score
    4. Return full breakdown + explanation
    """
    t_start = time.time()

    # ── Customer profile lookup ───────────────────────────────────────────────
    customer_profile = await CustomerService.get_customer_profile_dict(db, request.customer_id)
    profile_used = customer_profile is not None

    # ── Build transaction dict for inference + risk engine ────────────────────
    transaction_dict = {
        "customer_id": request.customer_id,
        "amount": request.amount,
        "transaction_amount": request.amount,
        "city": request.city,
        "country": request.country,
        "merchant_category": request.merchant_category,
        "payment_method": request.payment_method,
        "device_type": request.device_type,
        "hour_of_day": request.hour_of_day,
        "is_weekend": int(request.is_weekend),
        "is_night_transaction": int(request.is_night_transaction),
        "is_international": int(request.is_international),
        "failed_attempts": request.failed_attempts,
        "pin_changed_recently": int(request.pin_changed_recently),
        "credit_score": request.credit_score,
        "account_balance": request.account_balance,
        "distance_from_home_km": request.distance_from_home_km,
        "customer_age": request.customer_age or 42,
        "account_age_years": request.account_age_years or 5.0,
        "num_prev_transactions": request.num_prev_transactions or 150,
        "transaction_freq_monthly": request.transaction_freq_monthly or 20,
        # Derived
        "log_amount": 0.0,  # will be computed in preprocessor
        "sin_hour": 0.0,
        "cos_hour": 0.0,
    }

    # ── Autoencoder inference ─────────────────────────────────────────────────
    try:
        engine = InferenceEngine.get_instance()
        anomaly_score, reconstruction_error = engine.predict_single(transaction_dict)
    except ModelNotReadyError:
        # Fall back to heuristic score if model not trained yet
        anomaly_score = 0.3
        reconstruction_error = 0.0

    # ── 10-component risk scoring ─────────────────────────────────────────────
    risk_result = _risk_engine.compute_final_risk(
        transaction=transaction_dict,
        customer_profile=customer_profile,
        anomaly_score=anomaly_score,
        reconstruction_error=reconstruction_error,
    )

    processing_ms = (time.time() - t_start) * 1000.0
    txn_id = f"LIVE-{uuid.uuid4().hex[:12].upper()}"

    # Persist live transaction so PDF reports and audits can be immediately generated
    try:
        now_dt = datetime.utcnow()
        lat, lon = get_city_coordinates(request.city)
        db_txn = Transaction(
            transaction_id=txn_id,
            customer_id=request.customer_id,
            transaction_date=now_dt.date(),
            transaction_time=now_dt.time(),
            timestamp=now_dt,
            hour_of_day=request.hour_of_day,
            is_weekend=request.is_weekend,
            is_night_transaction=request.is_night_transaction,
            country=request.country,
            city=request.city,
            latitude=lat,
            longitude=lon,
            merchant_category=request.merchant_category,
            payment_method=request.payment_method,
            device_type=request.device_type,
            customer_age=request.customer_age or 42,
            credit_score=request.credit_score,
            account_age_years=request.account_age_years or 5.0,
            account_balance=request.account_balance,
            transaction_amount=request.amount,
            num_prev_transactions=request.num_prev_transactions or 150,
            transaction_freq_monthly=request.transaction_freq_monthly or 20,
            distance_from_home_km=request.distance_from_home_km,
            time_since_last_txn_hrs=request.time_since_last_txn_hrs,
            is_international=request.is_international,
            failed_attempts=request.failed_attempts,
            pin_changed_recently=request.pin_changed_recently,
            is_fraud=True if risk_result.prediction == "POTENTIAL_FRAUD" else False,
            fraud_type="ANOMALY_SPIKE" if risk_result.prediction == "POTENTIAL_FRAUD" else None,
        )
        db.add(db_txn)

        db_pred = FraudPrediction(
            transaction_id=txn_id,
            anomaly_score=anomaly_score,
            reconstruction_error=reconstruction_error,
            risk_score=risk_result.risk_score,
            risk_level=risk_result.risk_level,
            prediction=risk_result.prediction,
            actual_label=None,
        )
        db.add(db_pred)

        for f in risk_result.factors:
            db.add(RiskFactor(
                transaction_id=txn_id,
                factor_name=f.name,
                factor_score=f.score,
                factor_weight=f.weight,
                weighted_contribution=f.contribution,
                explanation=f.explanation,
            ))

        await db.commit()
    except Exception:
        await db.rollback()

    risk_factor_details = [
        RiskFactorDetail(
            name=f.name,
            score=round(f.score, 4),
            weight=round(f.weight, 4),
            contribution=round(f.contribution, 4),
            explanation=f.explanation,
        )
        for f in risk_result.factors
    ]

    return AnalyzeResponse(
        transaction_id=txn_id,
        customer_id=request.customer_id,
        anomaly_score=round(anomaly_score, 4),
        reconstruction_error=round(reconstruction_error, 6),
        risk_score=round(risk_result.risk_score, 2),
        risk_level=risk_result.risk_level,
        prediction=risk_result.prediction,
        explanation=risk_result.explanation,
        risk_factors=risk_factor_details,
        customer_profile_used=profile_used,
        processing_time_ms=round(processing_ms, 2),
    )
