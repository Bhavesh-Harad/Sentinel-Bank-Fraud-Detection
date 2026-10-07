"""
SENTINEL — RiskFactor ORM model.
One row per risk component per transaction — powers the factor breakdown UI.
"""

from sqlalchemy import String, Integer, Float, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RiskFactor(Base):
    __tablename__ = "risk_factors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    transaction_id: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )
    factor_name: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="e.g. autoencoder, geographic_risk"
    )
    factor_score: Mapped[float] = mapped_column(
        Float, nullable=False, comment="Raw factor score 0–1"
    )
    factor_weight: Mapped[float] = mapped_column(
        Float, nullable=False, comment="Weight assigned in WEIGHT_CONFIG"
    )
    weighted_contribution: Mapped[float] = mapped_column(
        Float, nullable=False, comment="factor_score × factor_weight × 100"
    )
    explanation: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Human-readable explanation of this factor"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<RiskFactor {self.factor_name} "
            f"score={self.factor_score:.3f} contrib={self.weighted_contribution:.2f}>"
        )
