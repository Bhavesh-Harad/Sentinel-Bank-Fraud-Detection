"""
SENTINEL — Reports API router.
POST /api/reports/generate — generate and return a PDF report for a transaction
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.services.transaction_service import TransactionService
from app.services.customer_service import CustomerService
from app.services.report_service import ReportService
from app.models.fraud_prediction import FraudPrediction
from app.models.risk_factor import RiskFactor

router = APIRouter(prefix="/reports", tags=["Reports"])


class ReportRequest(BaseModel):
    transaction_id: str


@router.post("/generate")
async def generate_report(
    request: ReportRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a PDF fraud analysis report for a given transaction_id.
    Returns the PDF as application/pdf bytes.
    """
    # Load transaction detail
    detail = await TransactionService.get_transaction_detail(db, request.transaction_id)
    if not detail:
        raise HTTPException(
            status_code=404,
            detail=f"Transaction '{request.transaction_id}' not found.",
        )

    # Load prediction
    pred_q = select(FraudPrediction).where(
        FraudPrediction.transaction_id == request.transaction_id
    )
    pred = (await db.execute(pred_q)).scalar_one_or_none()
    prediction_dict = None
    if pred:
        prediction_dict = {
            "prediction": pred.prediction,
            "risk_level": pred.risk_level,
            "risk_score": pred.risk_score,
            "anomaly_score": pred.anomaly_score,
            "reconstruction_error": pred.reconstruction_error,
        }

    # Load risk factors
    rf_q = select(RiskFactor).where(RiskFactor.transaction_id == request.transaction_id)
    rf_rows = (await db.execute(rf_q)).scalars().all()
    risk_factors = [
        {
            "factor_name": rf.factor_name,
            "factor_score": rf.factor_score,
            "factor_weight": rf.factor_weight,
            "weighted_contribution": rf.weighted_contribution,
            "explanation": rf.explanation,
        }
        for rf in rf_rows
    ]

    # Load customer profile
    customer_id = detail.get("customer_id", "")
    customer_profile = await CustomerService.get_customer_profile_dict(db, customer_id)

    # Generate PDF
    pdf_bytes = ReportService.generate_transaction_report(
        transaction=detail,
        prediction=prediction_dict,
        risk_factors=risk_factors,
        customer_profile=customer_profile,
    )

    filename = f"SENTINEL_Report_{request.transaction_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
