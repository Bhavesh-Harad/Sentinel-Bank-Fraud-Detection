"""
SENTINEL — FraudPrediction ORM model.
Stores autoencoder output and final risk score for every analysed transaction.
"""

from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class FraudPrediction(Base):
    __tablename__ = "fraud_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # ── Link to transaction ───────────────────────────────────────────────────
    transaction_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("transactions.transaction_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # ── Autoencoder output ────────────────────────────────────────────────────
    anomaly_score: Mapped[float] = mapped_column(
        Float, nullable=False, comment="Normalised autoencoder anomaly score 0–1"
    )
    reconstruction_error: Mapped[float] = mapped_column(
        Float, nullable=False, comment="Raw MSE reconstruction error from autoencoder"
    )

    # ── Hybrid risk output ────────────────────────────────────────────────────
    risk_score: Mapped[float] = mapped_column(
        Float, nullable=False, comment="Final weighted risk score 0–100"
    )
    risk_level: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        comment="NORMAL | SUSPICIOUS | HIGH_RISK | CRITICAL",
    )
    prediction: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="NORMAL | POTENTIAL_FRAUD",
    )

    # ── Ground truth ──────────────────────────────────────────────────────────
    actual_label: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Ground truth from is_fraud column (0 or 1)"
    )

    # ── Metadata ──────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<FraudPrediction txn={self.transaction_id} "
            f"risk={self.risk_score:.1f} level={self.risk_level}>"
        )
