"""
SENTINEL — Data ingestion script.

Reads bank_fraud.csv in chunks of 10,000 rows and:
1. Builds / upserts customer profiles (aggregated stats per customer_id)
2. Batch-inserts Transaction rows
3. Runs autoencoder inference (if model is available)
4. Inserts FraudPrediction, RiskFactor, and Alert rows for high-risk transactions
5. Prints progress every 10,000 rows

Usage:
    cd backend
    python scripts/ingest_data.py [--csv path/to/bank_fraud.csv] [--chunk 10000]
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import uuid
from datetime import datetime, date, time as time_type
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

# ── Path setup ────────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.database import SyncSessionLocal, sync_engine
from app.models.transaction import Transaction
from app.models.customer_profile import CustomerProfile
from app.models.fraud_prediction import FraudPrediction
from app.models.risk_factor import RiskFactor
from app.models.alert import Alert

# Trigger metadata creation
import app.models  # noqa: F401
from app.database import Base
Base.metadata.create_all(sync_engine)

from app.ml.preprocessing import load_and_preprocess, get_city_coordinates
from app.ml.risk_engine import RiskEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

CHUNK_SIZE = 10_000
_risk_engine = RiskEngine()

# ── Model availability ────────────────────────────────────────────────────────
def _try_load_inference():
    """Attempt to load InferenceEngine; return None if model not ready."""
    try:
        from app.ml.inference import InferenceEngine
        return InferenceEngine.get_instance()
    except Exception as exc:
        logger.warning(f"Model not available — skipping inference: {exc}")
        return None


# ── Customer profile builder ──────────────────────────────────────────────────
def build_customer_profiles(df: pd.DataFrame) -> dict[str, dict[str, Any]]:
    """Aggregate per-customer statistics from the full dataset."""
    logger.info("Building customer profiles …")
    profiles: dict[str, dict[str, Any]] = {}

    grouped = df.groupby("customer_id")
    for customer_id, grp in grouped:
        amounts = grp["transaction_amount"].dropna()
        is_fraud_col = grp["is_fraud"] if "is_fraud" in grp.columns else pd.Series([0] * len(grp))

        # Date range for transactions_per_day
        if "transaction_date" in grp.columns:
            try:
                dates = pd.to_datetime(grp["transaction_date"], errors="coerce").dropna()
                day_range = max((dates.max() - dates.min()).days + 1, 1)
            except Exception:
                day_range = 1
        else:
            day_range = 1

        def mode_val(series: pd.Series, default: str = "") -> str:
            s = series.dropna()
            if s.empty:
                return default
            return str(s.mode().iloc[0])

        profiles[str(customer_id)] = {
            "customer_id": str(customer_id),
            "total_transactions": len(grp),
            "avg_amount": float(amounts.mean()) if not amounts.empty else 0.0,
            "median_amount": float(amounts.median()) if not amounts.empty else 0.0,
            "std_amount": float(amounts.std()) if len(amounts) > 1 else 0.0,
            "min_amount": float(amounts.min()) if not amounts.empty else 0.0,
            "max_amount": float(amounts.max()) if not amounts.empty else 0.0,
            "common_city": mode_val(grp.get("city", pd.Series(dtype=str))),
            "common_country": mode_val(grp.get("country", pd.Series(dtype=str))),
            "common_merchant_category": mode_val(grp.get("merchant_category", pd.Series(dtype=str))),
            "common_payment_method": mode_val(grp.get("payment_method", pd.Series(dtype=str))),
            "common_device_type": mode_val(grp.get("device_type", pd.Series(dtype=str))),
            "avg_hour": float(grp["hour_of_day"].mean()) if "hour_of_day" in grp.columns else 12.0,
            "transactions_per_day": round(len(grp) / day_range, 4),
            "fraud_count": int(is_fraud_col.sum()),
            "last_updated": datetime.utcnow(),
        }

    logger.info(f"Built {len(profiles):,} customer profiles")
    return profiles


def upsert_profiles(profiles: dict[str, dict], session) -> None:
    """Insert or update customer profiles in the database."""
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert

    batch = list(profiles.values())
    if not batch:
        return

    chunk_size = 1000
    for i in range(0, len(batch), chunk_size):
        chunk = batch[i:i + chunk_size]
        stmt = sqlite_insert(CustomerProfile.__table__).values(chunk)
        stmt = stmt.on_conflict_do_update(
            index_elements=["customer_id"],
            set_={
                "total_transactions": stmt.excluded.total_transactions,
                "avg_amount": stmt.excluded.avg_amount,
                "median_amount": stmt.excluded.median_amount,
                "std_amount": stmt.excluded.std_amount,
                "min_amount": stmt.excluded.min_amount,
                "max_amount": stmt.excluded.max_amount,
                "common_city": stmt.excluded.common_city,
                "common_country": stmt.excluded.common_country,
                "common_merchant_category": stmt.excluded.common_merchant_category,
                "common_payment_method": stmt.excluded.common_payment_method,
                "common_device_type": stmt.excluded.common_device_type,
                "avg_hour": stmt.excluded.avg_hour,
                "transactions_per_day": stmt.excluded.transactions_per_day,
                "fraud_count": stmt.excluded.fraud_count,
                "last_updated": stmt.excluded.last_updated,
            },
        )
        session.execute(stmt)
    session.commit()
    logger.info(f"Upserted {len(batch):,} customer profiles in chunks")


# ── Row converter ─────────────────────────────────────────────────────────────
def _row_to_transaction(row: pd.Series) -> dict[str, Any]:
    """Convert a DataFrame row to a Transaction-compatible dict."""
    def safe_bool(val) -> bool:
        if isinstance(val, bool):
            return val
        try:
            return bool(int(val))
        except Exception:
            return False

    def safe_int(val, default=0) -> int:
        try:
            return int(val)
        except Exception:
            return default

    def safe_float(val, default=0.0) -> float:
        try:
            return float(val)
        except Exception:
            return default

    def safe_str(val, default="") -> str:
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return default
        return str(val)

    # Parse date/time
    txn_date = None
    txn_time = None
    timestamp = None
    try:
        d_str = safe_str(row.get("transaction_date"))
        t_str = safe_str(row.get("transaction_time"))
        if d_str:
            txn_date = pd.to_datetime(d_str).date()
        if t_str:
            parts = t_str.split(":")
            if len(parts) >= 2:
                txn_time = time_type(int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0)
        if txn_date and txn_time:
            timestamp = datetime.combine(txn_date, txn_time)
        elif txn_date:
            timestamp = datetime.combine(txn_date, time_type(0, 0, 0))
        else:
            timestamp = datetime.utcnow()
    except Exception:
        timestamp = datetime.utcnow()
        txn_date = timestamp.date()
        txn_time = timestamp.time()

    city = safe_str(row.get("city"), "Unknown")
    lat, lon = get_city_coordinates(city)

    # Generate unique transaction_id if missing
    txn_id = safe_str(row.get("transaction_id"))
    if not txn_id:
        txn_id = f"TXN-{uuid.uuid4().hex[:16].upper()}"

    is_fraud_val = row.get("is_fraud")
    is_fraud = None if is_fraud_val is None or (isinstance(is_fraud_val, float) and np.isnan(is_fraud_val)) else safe_bool(is_fraud_val)
    fraud_type_val = row.get("fraud_type")
    fraud_type = None if (fraud_type_val is None or (isinstance(fraud_type_val, float) and np.isnan(fraud_type_val))) else safe_str(fraud_type_val)

    return {
        "transaction_id": txn_id,
        "customer_id": safe_str(row.get("customer_id")),
        "transaction_date": txn_date or datetime.utcnow().date(),
        "transaction_time": txn_time or datetime.utcnow().time(),
        "timestamp": timestamp,
        "hour_of_day": safe_int(row.get("hour_of_day")),
        "is_weekend": safe_bool(row.get("is_weekend")),
        "is_night_transaction": safe_bool(row.get("is_night_transaction")),
        "country": safe_str(row.get("country"), "Unknown"),
        "city": city,
        "latitude": lat,
        "longitude": lon,
        "merchant_category": safe_str(row.get("merchant_category"), "Unknown"),
        "payment_method": safe_str(row.get("payment_method"), "Unknown"),
        "device_type": safe_str(row.get("device_type"), "Unknown"),
        "customer_age": safe_int(row.get("customer_age"), 35),
        "credit_score": safe_int(row.get("credit_score"), 700),
        "account_age_years": safe_float(row.get("account_age_years")),
        "account_balance": safe_float(row.get("account_balance")),
        "transaction_amount": safe_float(row.get("transaction_amount")),
        "num_prev_transactions": safe_int(row.get("num_prev_transactions")),
        "transaction_freq_monthly": safe_int(row.get("transaction_freq_monthly"), 1),
        "distance_from_home_km": safe_float(row.get("distance_from_home_km")),
        "time_since_last_txn_hrs": safe_float(row.get("time_since_last_txn_hrs"), 24.0),
        "is_international": safe_bool(row.get("is_international")),
        "failed_attempts": safe_int(row.get("failed_attempts")),
        "pin_changed_recently": safe_bool(row.get("pin_changed_recently")),
        "is_fraud": is_fraud,
        "fraud_type": fraud_type,
        "created_at": datetime.utcnow(),
    }


# ── Alert type determination ──────────────────────────────────────────────────
def _determine_alert_type(txn_dict: dict, risk_result=None) -> str:
    if risk_result and risk_result.is_impossible_travel:
        return "IMPOSSIBLE_TRAVEL"
    if txn_dict.get("is_international"):
        return "INTERNATIONAL"
    if txn_dict.get("failed_attempts", 0) >= 2:
        return "FAILED_ATTEMPTS"
    if txn_dict.get("pin_changed_recently"):
        return "PIN_CHANGE"
    if txn_dict.get("is_night_transaction"):
        return "NIGHT_TRANSACTION"
    # Check amount spike vs customer average — fallback
    return "BEHAVIORAL"


# ── Main ingestion ────────────────────────────────────────────────────────────
from app.database import Base, sync_engine

def ingest(csv_path: str | Path, chunk_size: int = CHUNK_SIZE) -> None:
    csv_path = Path(csv_path)
    if not csv_path.exists():
        logger.error(f"CSV not found: {csv_path}")
        sys.exit(1)

    Base.metadata.create_all(sync_engine)
    logger.info(f"Starting ingestion from {csv_path}")

    # Load full dataset for customer profile building
    logger.info("Loading full dataset for customer profile aggregation …")
    full_df = pd.read_csv(csv_path, usecols=["customer_id", "transaction_amount", "is_fraud", "transaction_date", "hour_of_day", "city", "country", "merchant_category", "payment_method", "device_type"])
    logger.info(f"Dataset: {len(full_df):,} rows")

    # Build and upsert profiles (full dataset scan)
    profiles = build_customer_profiles(full_df)
    with SyncSessionLocal() as session:
        upsert_profiles(profiles, session)
    del full_df  # free memory

    # Try to load inference engine
    inference_engine = _try_load_inference()

    # Process in chunks
    total_inserted = 0
    total_predictions = 0
    total_alerts = 0
    chunk_num = 0

    for chunk_df in pd.read_csv(csv_path, chunksize=chunk_size, low_memory=False):
        chunk_num += 1
        chunk_df = chunk_df.copy()

        # Fill NaN
        chunk_df = chunk_df.fillna(
            {
                col: 0
                for col in chunk_df.select_dtypes(include=[np.number]).columns
            }
        )
        for col in chunk_df.select_dtypes(include=["object"]).columns:
            chunk_df[col] = chunk_df[col].fillna("Unknown")

        txn_dicts = [_row_to_transaction(row) for _, row in chunk_df.iterrows()]

        # ── Batch insert transactions ────────────────────────────────────────
        with SyncSessionLocal() as session:
            # Skip duplicate transaction_ids
            existing_ids = set(
                row[0]
                for row in session.execute(
                    Transaction.__table__.select().with_only_columns(
                        Transaction.__table__.c.transaction_id
                    ).where(
                        Transaction.__table__.c.transaction_id.in_(
                            [d["transaction_id"] for d in txn_dicts]
                        )
                    )
                ).fetchall()
            )
            new_txns = [d for d in txn_dicts if d["transaction_id"] not in existing_ids]

            if new_txns:
                session.execute(Transaction.__table__.insert(), new_txns)
                session.commit()
            total_inserted += len(new_txns)

        # ── Inference & risk scoring ────────────────────────────────────────
        if inference_engine is None:
            logger.info(f"Chunk {chunk_num}: inserted {len(new_txns):,} txns (no inference)")
            continue

        predictions_to_insert = []
        risk_factors_to_insert = []
        alerts_to_insert = []

        for txn_dict in new_txns:
            try:
                anomaly_score, recon_error = inference_engine.predict_single(txn_dict)
            except Exception:
                anomaly_score, recon_error = 0.3, 0.0

            # Customer profile for risk engine
            cust_id = txn_dict.get("customer_id", "")
            profile = profiles.get(cust_id)

            risk_result = _risk_engine.compute_final_risk(
                transaction=txn_dict,
                customer_profile=profile,
                anomaly_score=anomaly_score,
                reconstruction_error=recon_error,
            )

            actual_label = int(txn_dict["is_fraud"]) if txn_dict["is_fraud"] is not None else None

            predictions_to_insert.append({
                "transaction_id": txn_dict["transaction_id"],
                "anomaly_score": anomaly_score,
                "reconstruction_error": recon_error,
                "risk_score": risk_result.risk_score,
                "risk_level": risk_result.risk_level,
                "prediction": risk_result.prediction,
                "actual_label": actual_label,
                "created_at": datetime.utcnow(),
            })

            for factor in risk_result.factors:
                risk_factors_to_insert.append({
                    "transaction_id": txn_dict["transaction_id"],
                    "factor_name": factor.name,
                    "factor_score": factor.score,
                    "factor_weight": factor.weight,
                    "weighted_contribution": factor.contribution,
                    "explanation": factor.explanation,
                })

            # Generate alert for HIGH_RISK and CRITICAL
            if risk_result.risk_level in ("HIGH_RISK", "CRITICAL"):
                alert_type = _determine_alert_type(txn_dict, risk_result)
                alerts_to_insert.append({
                    "transaction_id": txn_dict["transaction_id"],
                    "customer_id": txn_dict.get("customer_id", ""),
                    "risk_level": risk_result.risk_level,
                    "risk_score": risk_result.risk_score,
                    "alert_type": alert_type,
                    "message": risk_result.explanation[:1000],
                    "city": txn_dict.get("city", ""),
                    "amount": float(txn_dict.get("transaction_amount", 0)),
                    "is_read": False,
                    "created_at": datetime.utcnow(),
                })

        # Batch insert predictions, factors, alerts
        with SyncSessionLocal() as session:
            if predictions_to_insert:
                session.execute(FraudPrediction.__table__.insert(), predictions_to_insert)
            if risk_factors_to_insert:
                # Insert in sub-batches to avoid parameter limit
                for i in range(0, len(risk_factors_to_insert), 1000):
                    session.execute(RiskFactor.__table__.insert(), risk_factors_to_insert[i:i+1000])
            if alerts_to_insert:
                session.execute(Alert.__table__.insert(), alerts_to_insert)
            session.commit()

        total_predictions += len(predictions_to_insert)
        total_alerts += len(alerts_to_insert)

        logger.info(
            f"Chunk {chunk_num} complete | "
            f"txns inserted: {len(new_txns):,} | "
            f"predictions: {len(predictions_to_insert):,} | "
            f"alerts: {len(alerts_to_insert):,} | "
            f"total so far: {total_inserted:,}"
        )

    logger.info(
        f"\n{'='*60}\n"
        f"Ingestion complete!\n"
        f"  Transactions inserted : {total_inserted:,}\n"
        f"  Predictions created   : {total_predictions:,}\n"
        f"  Alerts generated      : {total_alerts:,}\n"
        f"{'='*60}"
    )


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SENTINEL data ingestion script")
    parser.add_argument(
        "--csv",
        type=str,
        default=str(settings.data_path_resolved),
        help="Path to bank_fraud.csv",
    )
    parser.add_argument(
        "--chunk",
        type=int,
        default=CHUNK_SIZE,
        help="Chunk size for batch processing",
    )
    args = parser.parse_args()
    ingest(csv_path=args.csv, chunk_size=args.chunk)
