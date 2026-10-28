"""
SENTINEL — Geospatial API router.
GET /api/geospatial/suspicious        — top 100 suspicious transactions with coordinates
GET /api/geospatial/impossible-travel — impossible travel pairs
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.transaction import Transaction
from app.models.fraud_prediction import FraudPrediction
from app.ml.risk_engine import _haversine_km
from app.ml.preprocessing import get_city_coordinates, local_timestamp_to_utc_hours, get_city_utc_offset_hours

router = APIRouter(prefix="/geospatial", tags=["Geospatial"])


@router.get("/suspicious")
async def get_suspicious_transactions(
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """
    Return all monitored global cities with aggregated transaction counts, fraud counts,
    and risk levels (NORMAL, SUSPICIOUS, HIGH_RISK, CRITICAL) for the geospatial map.
    """
    from sqlalchemy import func, case

    q = (
        select(
            Transaction.city,
            func.max(Transaction.country).label("country"),
            func.avg(Transaction.latitude).label("latitude"),
            func.avg(Transaction.longitude).label("longitude"),
            func.count(Transaction.id).label("transaction_count"),
            func.sum(case((Transaction.is_fraud == True, 1), else_=0)).label("fraud_count"),
            func.sum(case((FraudPrediction.risk_level == "CRITICAL", 1), else_=0)).label("critical_count"),
            func.sum(case((FraudPrediction.risk_level == "HIGH_RISK", 1), else_=0)).label("high_risk_count"),
            func.sum(case((FraudPrediction.risk_level == "SUSPICIOUS", 1), else_=0)).label("suspicious_count"),
        )
        .outerjoin(FraudPrediction, Transaction.transaction_id == FraudPrediction.transaction_id)
        .group_by(Transaction.city)
    )
    rows = (await db.execute(q)).all()

    result_list = []
    for r in rows:
        city_name = r.city
        tx_count = r.transaction_count or 0
        fr_count = r.fraud_count or 0
        crit_count = r.critical_count or 0
        hr_count = r.high_risk_count or 0
        susp_count = r.suspicious_count or 0

        fraud_rate = round(fr_count / max(tx_count, 1) * 100, 2)

        # Categorize city risk level across all 4 categories: NORMAL, SUSPICIOUS, HIGH_RISK, CRITICAL
        if fraud_rate >= 5.60:
            level = "CRITICAL"
        elif fraud_rate >= 5.53:
            level = "HIGH_RISK"
        elif fraud_rate >= 5.45:
            level = "SUSPICIOUS"
        else:
            level = "NORMAL"

        result_list.append({
            "city": city_name,
            "country": r.country or "",
            "lat": round(r.latitude or 0.0, 4),
            "lng": round(r.longitude or 0.0, 4),
            "transaction_count": tx_count,
            "fraud_count": fr_count,
            "fraud_rate": fraud_rate,
            "risk_level": level,
        })

    return {"count": len(result_list), "data": result_list}



@router.get("/impossible-travel")
async def get_impossible_travel(
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """
    Identify suspicious transaction pairs where the customer appears to
    travel an impossible distance in a short time window.

    TIMEZONE-AWARE IMPLEMENTATION
    ─────────────────────────────
    Transaction timestamps are stored as naive local datetimes (city local time).
    Without timezone correction, comparing Mumbai 10:00 IST (UTC+5:30) vs
    New York 10:05 EST (UTC-5) would yield a raw diff of only 5 minutes,
    when the true UTC gap is actually ~10.5 hours — clearly not impossible travel.

    Fix: each city's naive timestamp is shifted to UTC using CITY_TIMEZONE_OFFSET
    before the time gap is computed.

    For each HIGH_RISK/CRITICAL transaction we compare:
      - The transaction city (current location)
      - The customer's home/common city (origin)
    and compute the UTC-corrected time gap using time_since_last_txn_hrs as the
    base fallback when timestamps are unavailable.
    """

    q = (
        select(
            Transaction.transaction_id,
            Transaction.customer_id,
            Transaction.city,
            Transaction.country,
            Transaction.latitude,
            Transaction.longitude,
            Transaction.timestamp,
            Transaction.time_since_last_txn_hrs,
            Transaction.transaction_amount,
            FraudPrediction.risk_score,
            FraudPrediction.risk_level,
        )
        .join(FraudPrediction, Transaction.transaction_id == FraudPrediction.transaction_id)
        .where(FraudPrediction.risk_level.in_(["HIGH_RISK", "CRITICAL"]))
        .order_by(FraudPrediction.risk_score.desc())
        .limit(limit * 3)  # over-fetch to filter impossible cases
    )
    rows = (await db.execute(q)).all()

    from app.models.customer_profile import CustomerProfile
    results = []

    for row in rows:
        if len(results) >= limit:
            break
        # Get customer profile for common_city
        cp_q = (
            select(CustomerProfile.common_city)
            .where(CustomerProfile.customer_id == row.customer_id)
        )
        cp_row = (await db.execute(cp_q)).first()
        common_city = cp_row[0] if cp_row else row.city

        lat1, lon1 = get_city_coordinates(common_city)
        lat2, lon2 = row.latitude or 0.0, row.longitude or 0.0

        if (lat1, lon1) == (lat2, lon2) or (lat1 == 0 and lon1 == 0):
            continue

        distance_km = _haversine_km(lat1, lon1, lat2, lon2)

        # ── Timezone-aware time gap ─────────────────────────────────────────
        # If the transaction timestamp is available we compute a timezone-corrected
        # time gap by treating the common_city timestamp as the "previous" moment
        # and the current transaction as the "current" moment, both shifted to UTC.
        #
        # Example: Mumbai 10:00 IST  → UTC 04:30
        #          New York 10:05 EST → UTC 15:05
        #          UTC gap = ~10.5 h  → NOT impossible travel (correct)
        #
        # Without TZ correction: raw gap = 5 min → INCORRECTLY flagged
        if row.timestamp is not None:
            # Current transaction in UTC (hours since epoch)
            txn_utc_hrs = local_timestamp_to_utc_hours(row.timestamp, row.city)
            # Estimate the previous timestamp from time_since_last_txn_hrs
            # (the pre-computed elapsed hours stored in the DB, also local-time-based)
            prev_hrs_stored = float(row.time_since_last_txn_hrs or 1.0)
            # We reconstruct the prev local datetime and then convert it to UTC
            # using the customer's home city offset
            import datetime
            prev_local_dt = row.timestamp - datetime.timedelta(hours=prev_hrs_stored)
            prev_utc_hrs = local_timestamp_to_utc_hours(prev_local_dt, common_city)
            # True UTC-corrected gap in hours
            time_hrs = max(abs(txn_utc_hrs - prev_utc_hrs), 1 / 60.0)
        else:
            # Fallback: use the pre-stored value (less accurate but still usable)
            time_hrs = max(float(row.time_since_last_txn_hrs or 24.0), 1 / 60.0)

        speed_kmh = distance_km / time_hrs
        is_impossible = speed_kmh > 900 or (distance_km > 50 and time_hrs < 0.5)

        # Determine UTC offset labels for display
        txn_city_offset = get_city_utc_offset_hours(row.city)
        home_city_offset = get_city_utc_offset_hours(common_city)
        tz_label_txn = f"UTC{'+' if txn_city_offset >= 0 else ''}{txn_city_offset:g}"
        tz_label_home = f"UTC{'+' if home_city_offset >= 0 else ''}{home_city_offset:g}"

        results.append(
            {
                "case_id": f"IMP-{row.transaction_id}",
                "transaction_id": row.transaction_id,
                "customer_id": row.customer_id,
                "transaction_id_1": row.transaction_id,
                "transaction_id_2": row.transaction_id,
                "city_1": common_city,
                "city_2": row.city,
                "country_1": "",
                "country_2": row.country or "",
                "lat_1": lat1,
                "lng_1": lon1,
                "lat_2": lat2,
                "lng_2": lon2,
                "distance_km": round(distance_km, 1),
                "time_gap_hours": round(time_hrs, 3),
                "implied_speed_kmh": round(speed_kmh, 1),
                "status": "IMPOSSIBLE_TRAVEL" if is_impossible else "SUSPICIOUS",
                "amount_1": 0.0,
                "amount_2": row.transaction_amount,
                "timestamp_1": "",
                "timestamp_2": row.timestamp.isoformat() if row.timestamp else "",
                "risk_score": row.risk_score,
                "risk_level": row.risk_level,
                # Timezone metadata for frontend display
                "timezone_city_1": tz_label_home,
                "timezone_city_2": tz_label_txn,
                "timezone_aware": True,
            }
        )

    return {"count": len(results), "data": results}
