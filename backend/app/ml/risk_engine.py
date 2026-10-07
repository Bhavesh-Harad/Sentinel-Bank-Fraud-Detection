"""
SENTINEL — 10-Component Hybrid Risk Engine.

WEIGHT_CONFIG defines how each component contributes to the final 0–100 risk score.
RiskEngine.compute_final_risk() is the main entry point.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any, Optional

from app.ml.preprocessing import CITY_COORDINATES, get_city_coordinates

logger = logging.getLogger(__name__)

# ── Weight configuration ──────────────────────────────────────────────────────
WEIGHT_CONFIG: dict[str, float] = {
    "autoencoder": 0.35,
    "amount_deviation": 0.15,
    "geographic_risk": 0.15,
    "velocity_risk": 0.10,
    "time_anomaly": 0.10,
    "behavioral_deviation": 0.08,
    "international_flag": 0.03,
    "failed_attempts": 0.02,
    "pin_change": 0.01,
    "credit_factor": 0.01,
}

assert abs(sum(WEIGHT_CONFIG.values()) - 1.0) < 1e-9, "Weights must sum to 1.0"


@dataclass
class RiskFactorResult:
    name: str
    score: float          # 0–1
    weight: float         # from WEIGHT_CONFIG
    contribution: float   # score × weight × 100
    explanation: str


@dataclass
class RiskResult:
    risk_score: float                          # 0–100
    risk_level: str                            # NORMAL / SUSPICIOUS / HIGH_RISK / CRITICAL
    prediction: str                            # NORMAL / POTENTIAL_FRAUD
    factors: list[RiskFactorResult] = field(default_factory=list)
    explanation: str = ""
    is_impossible_travel: bool = False
    distance_km: float = 0.0
    travel_speed_kmh: float = 0.0


# ── Haversine distance ─────────────────────────────────────────────────────────
def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


# ── Risk Engine ────────────────────────────────────────────────────────────────
class RiskEngine:
    """
    Computes a weighted risk score from 10 independent components.
    All component methods return a value in [0, 1].
    """

    IMPOSSIBLE_TRAVEL_DISTANCE_KM: float = 50.0
    IMPOSSIBLE_TRAVEL_TIME_HOURS: float = 0.5
    IMPOSSIBLE_TRAVEL_SPEED_KMPH: float = 900.0  # faster than commercial jet

    # ── Component 1: Autoencoder anomaly score ─────────────────────────────
    @staticmethod
    def compute_autoencoder_risk(anomaly_score: float) -> tuple[float, str]:
        score = float(min(1.0, max(0.0, anomaly_score)))
        if score >= 0.8:
            explanation = (
                f"Transaction pattern is highly abnormal (autoencoder anomaly score: {score:.2f}). "
                "The deep learning model found this transaction very different from normal behaviour."
            )
        elif score >= 0.5:
            explanation = (
                f"Transaction shows moderate anomaly characteristics (score: {score:.2f}). "
                "Several features deviate from the customer's typical pattern."
            )
        else:
            explanation = (
                f"Transaction pattern appears relatively normal (autoencoder score: {score:.2f})."
            )
        return score, explanation

    # ── Component 2: Amount deviation ─────────────────────────────────────
    @staticmethod
    def compute_amount_risk(
        amount: float,
        avg_amount: float,
        std_amount: float,
    ) -> tuple[float, str]:
        if std_amount <= 0:
            std_amount = max(avg_amount * 0.1, 1.0)
        z = (amount - avg_amount) / std_amount
        # Score rises steeply beyond 2σ
        score = min(1.0, max(0.0, (abs(z) - 1.0) / 5.0))
        direction = "above" if z > 0 else "below"
        explanation = (
            f"Transaction amount ${amount:,.2f} is {abs(z):.1f}σ {direction} "
            f"customer's average ${avg_amount:,.2f} (σ=${std_amount:,.2f})."
        )
        return score, explanation

    # ── Component 3: Geographic risk ───────────────────────────────────────
    @staticmethod
    def compute_geographic_risk(
        city: str,
        prev_city: str,
        time_diff_hours: float,
        distance_from_home_km: Optional[float] = None,
    ) -> tuple[float, float, float, bool, str]:
        """
        Returns (score, distance_km, speed_kmh, is_impossible_travel, explanation).
        """
        # If the transaction is explicitly close to home (< 50 km) or in the same city, no geo risk
        if city and prev_city and city.strip().lower() == prev_city.strip().lower():
            return 0.0, 0.0, 0.0, False, f"Transaction in expected city ({city}). No geographic risk."

        if distance_from_home_km is not None and distance_from_home_km <= 50.0:
            return (
                0.0,
                float(distance_from_home_km),
                0.0,
                False,
                f"Transaction is within customer's local area ({distance_from_home_km:.1f} km from home). No geographic risk.",
            )

        lat1, lon1 = get_city_coordinates(prev_city)
        lat2, lon2 = get_city_coordinates(city)

        # Both cities unknown / same coords
        if (lat1, lon1) == (0.0, 0.0) and (lat2, lon2) == (0.0, 0.0):
            return 0.05, 0.0, 0.0, False, "City coordinates unavailable; minimal geographic risk assumed."

        distance_km = _haversine_km(lat1, lon1, lat2, lon2)
        speed_kmh = distance_km / max(time_diff_hours, 1 / 60.0)  # avoid div/0

        # Impossible travel requires both significant distance (>50km) and physically impossible speed
        is_impossible = (
            distance_km > RiskEngine.IMPOSSIBLE_TRAVEL_DISTANCE_KM
            and (
                (time_diff_hours < RiskEngine.IMPOSSIBLE_TRAVEL_TIME_HOURS)
                or (speed_kmh > RiskEngine.IMPOSSIBLE_TRAVEL_SPEED_KMPH and time_diff_hours < 4.0)
            )
        )

        if is_impossible:
            score = 1.0
            explanation = (
                f"⚠ IMPOSSIBLE TRAVEL DETECTED: {distance_km:.0f} km from {prev_city} to {city} "
                f"in {time_diff_hours * 60:.1f} minutes (implied speed: {speed_kmh:.0f} km/h). "
                "Physical travel is impossible at this speed."
            )
        elif distance_km > 500:
            score = 0.5 if time_diff_hours > 6.0 else 0.8
            explanation = (
                f"Long-distance transaction: {distance_km:.0f} km from {prev_city} to {city} "
                f"({time_diff_hours:.1f} hours since last transaction)."
            )
        elif distance_km > 100:
            score = min(0.4, distance_km / 1000.0)
            explanation = (
                f"Transaction in {city} is {distance_km:.0f} km from previous location "
                f"({prev_city}), {time_diff_hours:.1f} hours apart."
            )
        elif city != prev_city:
            score = 0.1
            explanation = (
                f"Transaction in {city} — different city from last transaction in {prev_city} "
                f"({distance_km:.0f} km, {time_diff_hours:.1f} h apart)."
            )
        else:
            score = 0.0
            explanation = f"Transaction in expected city ({city}). No geographic risk."

        return score, distance_km, speed_kmh, is_impossible, explanation

    # ── Component 4: Velocity risk ─────────────────────────────────────────
    @staticmethod
    def compute_velocity_risk(
        time_since_last_hrs: float,
        freq_monthly: int,
    ) -> tuple[float, str]:
        if freq_monthly <= 0:
            freq_monthly = 1

        if time_since_last_hrs <= 0:
            score = 1.0
            explanation = "Transaction occurred simultaneously with (or before) the previous one — extreme velocity risk."
        elif time_since_last_hrs < (5.0 / 60.0):  # under 5 minutes
            score = 0.9
            explanation = f"Very rapid successive transaction: only {time_since_last_hrs * 60:.1f} minutes since last transaction."
        elif time_since_last_hrs < (15.0 / 60.0):  # 5 - 15 minutes
            score = 0.6
            explanation = f"High velocity transaction: {time_since_last_hrs * 60:.0f} minutes since last transaction."
        elif time_since_last_hrs < 0.5:  # 15 - 30 minutes
            score = 0.3
            explanation = f"Successive transaction within {time_since_last_hrs * 60:.0f} minutes."
        elif time_since_last_hrs < 1.0:  # 30 - 60 minutes
            score = 0.1
            explanation = f"Transaction {time_since_last_hrs * 60:.0f} minutes after previous one."
        else:
            score = 0.0
            explanation = f"Transaction {time_since_last_hrs:.1f} h after last — within normal velocity range."

        return score, explanation

    # ── Component 5: Time anomaly ──────────────────────────────────────────
    @staticmethod
    def compute_time_anomaly(
        hour_of_day: int,
        is_night: bool,
    ) -> tuple[float, str]:
        # Night hours 00:00–05:59 and 22:00–23:59
        if is_night or hour_of_day < 6 or hour_of_day >= 22:
            score = 0.7 if is_night else 0.4
            explanation = (
                f"Transaction at {hour_of_day:02d}:00 — unusual off-hours activity "
                f"({'night transaction flag set' if is_night else 'late-night/early-morning hour'})."
            )
        elif 6 <= hour_of_day < 9 or 18 <= hour_of_day < 22:
            score = 0.2
            explanation = f"Transaction at {hour_of_day:02d}:00 — slightly off peak hours."
        else:
            score = 0.0
            explanation = f"Transaction at {hour_of_day:02d}:00 — normal business hours."
        return score, explanation

    # ── Component 6: Behavioural deviation ────────────────────────────────
    @staticmethod
    def compute_behavioral_deviation(
        transaction: dict[str, Any],
        customer_profile: Optional[dict[str, Any]],
    ) -> tuple[float, str]:
        if customer_profile is None:
            return 0.2, "No customer profile available; baseline behavioural risk applied."

        deviations: list[float] = []
        notes: list[str] = []

        # Amount deviation
        avg = float(customer_profile.get("avg_amount", 0) or 0)
        std = float(customer_profile.get("std_amount", 1) or 1)
        amount = float(transaction.get("amount", transaction.get("transaction_amount", 0)))
        if std > 0 and avg > 0:
            z = abs((amount - avg) / std)
            amt_score = min(1.0, (z - 1.0) / 5.0) if z > 1 else 0.0
            deviations.append(max(0.0, amt_score))
            if amt_score > 0.3:
                notes.append(f"amount ${amount:,.0f} vs avg ${avg:,.0f}")

        # City
        if transaction.get("city", "") != customer_profile.get("common_city", ""):
            deviations.append(0.35)
            notes.append(f"unusual city {transaction.get('city')!r}")

        # Merchant category
        if transaction.get("merchant_category", "") != customer_profile.get("common_merchant_category", ""):
            deviations.append(0.2)
            notes.append(f"unusual category {transaction.get('merchant_category')!r}")

        # Payment method
        if transaction.get("payment_method", "") != customer_profile.get("common_payment_method", ""):
            deviations.append(0.25)
            notes.append(f"unusual payment method {transaction.get('payment_method')!r}")

        # Device type
        if transaction.get("device_type", "") != customer_profile.get("common_device_type", ""):
            deviations.append(0.15)
            notes.append(f"unusual device {transaction.get('device_type')!r}")

        score = min(1.0, sum(deviations) / max(len(deviations), 1))
        if notes:
            explanation = (
                f"Behavioural deviations detected: {', '.join(notes)}. "
                f"Customer normally uses {customer_profile.get('common_payment_method')} "
                f"in {customer_profile.get('common_city')} "
                f"at avg ${customer_profile.get('avg_amount', 0):,.0f}."
            )
        else:
            explanation = "Transaction matches customer's typical behavioural profile."

        return score, explanation

    # ── Component 7: International flag ───────────────────────────────────
    @staticmethod
    def compute_international_risk(is_international: bool) -> tuple[float, str]:
        if is_international:
            return 0.8, "Transaction flagged as international — elevated cross-border risk."
        return 0.0, "Domestic transaction — no international risk."

    # ── Component 8: Failed attempts ──────────────────────────────────────
    @staticmethod
    def compute_failed_attempts_risk(failed_attempts: int) -> tuple[float, str]:
        score = min(1.0, failed_attempts / 3.0)
        if failed_attempts == 0:
            explanation = "No prior failed attempts on this transaction."
        elif failed_attempts == 1:
            explanation = "1 prior failed attempt detected — slightly elevated risk."
        elif failed_attempts == 2:
            explanation = f"{failed_attempts} prior failed attempts — moderate credential-stuffing risk."
        else:
            explanation = (
                f"⚠ {failed_attempts} prior failed attempts — high risk of brute-force or credential attack."
            )
        return score, explanation

    # ── Component 9: PIN change risk ──────────────────────────────────────
    @staticmethod
    def compute_pin_change_risk(pin_changed_recently: bool) -> tuple[float, str]:
        if pin_changed_recently:
            return 0.8, (
                "PIN changed recently before this transaction — may indicate "
                "account takeover or coercion."
            )
        return 0.0, "No recent PIN change."

    # ── Component 10: Credit score factor ─────────────────────────────────
    @staticmethod
    def compute_credit_risk(credit_score: int) -> tuple[float, str]:
        score = max(0.0, min(1.0, (750 - credit_score) / 450.0))
        if credit_score >= 750:
            explanation = f"Excellent credit score ({credit_score}) — minimal credit risk."
        elif credit_score >= 650:
            explanation = f"Good credit score ({credit_score}) — low credit risk."
        elif credit_score >= 550:
            explanation = f"Fair credit score ({credit_score}) — moderate credit risk."
        else:
            explanation = f"Poor credit score ({credit_score}) — elevated credit risk."
        return score, explanation

    # ── Master risk computation ────────────────────────────────────────────
    def compute_final_risk(
        self,
        transaction: dict[str, Any],
        customer_profile: Optional[dict[str, Any]],
        anomaly_score: float,
        reconstruction_error: float = 0.0,
    ) -> RiskResult:
        """
        Compute all 10 risk components, apply weights, produce final score.

        Parameters
        ----------
        transaction        : raw transaction dict
        customer_profile   : dict from CustomerProfile (may be None)
        anomaly_score      : autoencoder anomaly score [0,1]
        reconstruction_error: raw MSE from autoencoder

        Returns
        -------
        RiskResult with full breakdown
        """
        from app.config import settings

        amount = float(transaction.get("amount", transaction.get("transaction_amount", 0)))
        hour = int(transaction.get("hour_of_day", 12))
        is_night = bool(transaction.get("is_night_transaction", False))
        is_intl = bool(transaction.get("is_international", False))
        failed = int(transaction.get("failed_attempts", 0))
        pin_changed = bool(transaction.get("pin_changed_recently", False))
        credit = int(transaction.get("credit_score", 700))
        city = str(transaction.get("city", "Unknown"))
        time_since_last = float(transaction.get("time_since_last_txn_hrs", 24.0))
        freq_monthly = int(transaction.get("transaction_freq_monthly", 10))

        if customer_profile:
            avg_amount = float(customer_profile.get("avg_amount", amount))
            std_amount = float(customer_profile.get("std_amount", amount * 0.2))
            prev_city = str(customer_profile.get("common_city", city))
        else:
            avg_amount = amount
            std_amount = amount * 0.2
            prev_city = city

        factors: list[RiskFactorResult] = []
        is_impossible = False
        distance_km = 0.0
        speed_kmh = 0.0

        # 1. Autoencoder
        s, e = self.compute_autoencoder_risk(anomaly_score)
        factors.append(RiskFactorResult("autoencoder", s, WEIGHT_CONFIG["autoencoder"], s * WEIGHT_CONFIG["autoencoder"] * 100, e))

        # 2. Amount deviation
        s, e = self.compute_amount_risk(amount, avg_amount, std_amount)
        factors.append(RiskFactorResult("amount_deviation", s, WEIGHT_CONFIG["amount_deviation"], s * WEIGHT_CONFIG["amount_deviation"] * 100, e))

        # 3. Geographic risk
        dist_home = float(transaction.get("distance_from_home_km", 0.0)) if "distance_from_home_km" in transaction else None
        s, dist, spd, imp, e = self.compute_geographic_risk(city, prev_city, time_since_last, distance_from_home_km=dist_home)
        is_impossible = imp
        distance_km = dist
        speed_kmh = spd
        factors.append(RiskFactorResult("geographic_risk", s, WEIGHT_CONFIG["geographic_risk"], s * WEIGHT_CONFIG["geographic_risk"] * 100, e))

        # 4. Velocity risk
        s, e = self.compute_velocity_risk(time_since_last, freq_monthly)
        factors.append(RiskFactorResult("velocity_risk", s, WEIGHT_CONFIG["velocity_risk"], s * WEIGHT_CONFIG["velocity_risk"] * 100, e))

        # 5. Time anomaly
        s, e = self.compute_time_anomaly(hour, is_night)
        factors.append(RiskFactorResult("time_anomaly", s, WEIGHT_CONFIG["time_anomaly"], s * WEIGHT_CONFIG["time_anomaly"] * 100, e))

        # 6. Behavioural deviation
        s, e = self.compute_behavioral_deviation(transaction, customer_profile)
        factors.append(RiskFactorResult("behavioral_deviation", s, WEIGHT_CONFIG["behavioral_deviation"], s * WEIGHT_CONFIG["behavioral_deviation"] * 100, e))

        # 7. International flag
        s, e = self.compute_international_risk(is_intl)
        factors.append(RiskFactorResult("international_flag", s, WEIGHT_CONFIG["international_flag"], s * WEIGHT_CONFIG["international_flag"] * 100, e))

        # 8. Failed attempts
        s, e = self.compute_failed_attempts_risk(failed)
        factors.append(RiskFactorResult("failed_attempts", s, WEIGHT_CONFIG["failed_attempts"], s * WEIGHT_CONFIG["failed_attempts"] * 100, e))

        # 9. PIN change
        s, e = self.compute_pin_change_risk(pin_changed)
        factors.append(RiskFactorResult("pin_change", s, WEIGHT_CONFIG["pin_change"], s * WEIGHT_CONFIG["pin_change"] * 100, e))

        # 10. Credit factor
        s, e = self.compute_credit_risk(credit)
        factors.append(RiskFactorResult("credit_factor", s, WEIGHT_CONFIG["credit_factor"], s * WEIGHT_CONFIG["credit_factor"] * 100, e))

        # ── Final score ────────────────────────────────────────────────────
        raw_score = sum(f.contribution for f in factors)
        risk_score = min(100.0, max(0.0, raw_score))

        # Impossible travel → minimum HIGH_RISK
        if is_impossible and risk_score < settings.HIGH_RISK_THRESHOLD:
            risk_score = max(risk_score, settings.HIGH_RISK_THRESHOLD)

        # ── Risk level ─────────────────────────────────────────────────────
        if risk_score <= settings.NORMAL_THRESHOLD:
            risk_level = "NORMAL"
        elif risk_score <= settings.SUSPICIOUS_THRESHOLD:
            risk_level = "SUSPICIOUS"
        elif risk_score <= settings.HIGH_RISK_THRESHOLD:
            risk_level = "HIGH_RISK"
        else:
            risk_level = "CRITICAL"

        prediction = "POTENTIAL_FRAUD" if risk_score > settings.SUSPICIOUS_THRESHOLD else "NORMAL"

        explanation = self.generate_explanation(factors, transaction, customer_profile, is_impossible)

        return RiskResult(
            risk_score=risk_score,
            risk_level=risk_level,
            prediction=prediction,
            factors=factors,
            explanation=explanation,
            is_impossible_travel=is_impossible,
            distance_km=distance_km,
            travel_speed_kmh=speed_kmh,
        )

    # ── Explanation generator ──────────────────────────────────────────────
    @staticmethod
    def generate_explanation(
        risk_factors: list[RiskFactorResult],
        transaction: dict[str, Any],
        customer_profile: Optional[dict[str, Any]],
        is_impossible_travel: bool = False,
    ) -> str:
        """
        Build a human-readable paragraph explaining the risk decision.
        """
        lines: list[str] = []
        amount = float(transaction.get("amount", transaction.get("transaction_amount", 0)))
        city = transaction.get("city", "Unknown")
        hour = int(transaction.get("hour_of_day", 12))

        if is_impossible_travel:
            lines.append(
                "⚠ CRITICAL: Impossible travel detected — the customer cannot have "
                "physically moved between locations in the time available."
            )

        # Top contributing factors
        sorted_factors = sorted(risk_factors, key=lambda f: f.contribution, reverse=True)
        high_factors = [f for f in sorted_factors if f.score > 0.4][:3]

        if customer_profile:
            avg = customer_profile.get("avg_amount", 0)
            common_city = customer_profile.get("common_city", "Unknown")
            lines.append(
                f"Customer typically spends ${avg:,.0f} in {common_city} during daytime hours. "
                f"This transaction is ${amount:,.0f} at {hour:02d}:00 in {city}."
            )

        if high_factors:
            lines.append("Main risk drivers:")
            for f in high_factors:
                lines.append(f"  • {f.name.replace('_', ' ').title()}: {f.explanation}")

        low_risk_count = sum(1 for f in risk_factors if f.score < 0.2)
        if low_risk_count >= 5:
            lines.append(
                f"{low_risk_count} of 10 risk factors show low or zero risk."
            )

        return " ".join(lines) if lines else "Risk assessment based on 10-component hybrid model."
