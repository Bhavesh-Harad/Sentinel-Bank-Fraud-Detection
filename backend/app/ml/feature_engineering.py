"""
SENTINEL — Feature engineering for real-time risk scoring.

FeatureEngineer computes behavioural deviation metrics from a transaction
dict + optional CustomerProfile, producing intermediate scores consumed by
the RiskEngine.
"""

from __future__ import annotations

import math
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Compute derived risk signals from raw transaction data and customer history.

    All score methods return values in [0, 1] where 1 = maximum risk.
    """

    # ── Amount anomaly ────────────────────────────────────────────────────────
    @staticmethod
    def compute_amount_anomaly(
        amount: float,
        avg: float,
        std: float,
    ) -> dict[str, float]:
        """
        Compute z-score deviation and normalised score.

        Returns:
            z_score         : signed standard-deviation distance
            normalised_score: clamped to [0, 1]
        """
        if std <= 0:
            std = max(avg * 0.1, 1.0)
        z = (amount - avg) / std
        # Normalise to [0, 1] using sigmoid-like mapping
        normalised = min(1.0, max(0.0, (abs(z) - 1.0) / 4.0))
        return {"z_score": z, "normalised_score": normalised}

    # ── Time anomaly ──────────────────────────────────────────────────────────
    @staticmethod
    def compute_time_anomaly(
        hour: int,
        customer_avg_hour: float = 12.0,
    ) -> float:
        """
        Circular distance between transaction hour and customer's average hour.

        Returns a score in [0, 1] where 1 = 12 hours apart (maximum).
        """
        diff = abs(hour - customer_avg_hour)
        circular_diff = min(diff, 24.0 - diff)  # max possible = 12
        return min(1.0, circular_diff / 12.0)

    # ── Velocity risk ─────────────────────────────────────────────────────────
    @staticmethod
    def compute_velocity_risk(
        time_since_last_hrs: float,
        freq_monthly: int = 10,
    ) -> float:
        """
        High velocity (transactions very close together) increases risk.

        time_since_last_hrs: hours since the previous transaction.
        freq_monthly       : how many transactions per month the customer does.

        Returns score in [0, 1].
        """
        # Expected gap in hours between transactions
        if freq_monthly <= 0:
            freq_monthly = 1
        expected_gap_hrs = (30 * 24) / freq_monthly  # average gap

        if time_since_last_hrs <= 0:
            return 1.0  # simultaneous — maximum risk
        ratio = expected_gap_hrs / max(time_since_last_hrs, 0.0167)  # min 1 min
        # ratio > 1 → transaction faster than usual
        score = min(1.0, max(0.0, (ratio - 1.0) / 9.0))
        return score

    # ── Behavioural deviation ─────────────────────────────────────────────────
    @staticmethod
    def compute_behavioral_deviation(
        transaction: dict[str, Any],
        customer_profile: Optional[dict[str, Any]],
    ) -> float:
        """
        Aggregate deviation score across multiple behavioural dimensions:
        - Amount vs customer average
        - City departure from usual
        - Merchant category departure
        - Payment method departure
        - Device type departure

        Returns score in [0, 1].
        """
        if customer_profile is None:
            return 0.3  # moderate risk when no profile available

        deviations: list[float] = []

        # Amount deviation
        avg = float(customer_profile.get("avg_amount", 0) or 0)
        std = float(customer_profile.get("std_amount", 0) or 0)
        amount = float(transaction.get("amount", transaction.get("transaction_amount", 0)))
        amt_info = FeatureEngineer.compute_amount_anomaly(amount, avg, std)
        deviations.append(amt_info["normalised_score"])

        # City deviation (binary)
        common_city = customer_profile.get("common_city", "")
        txn_city = transaction.get("city", "")
        deviations.append(0.0 if txn_city == common_city else 0.4)

        # Merchant category deviation (binary)
        common_cat = customer_profile.get("common_merchant_category", "")
        txn_cat = transaction.get("merchant_category", "")
        deviations.append(0.0 if txn_cat == common_cat else 0.2)

        # Payment method deviation (binary)
        common_pay = customer_profile.get("common_payment_method", "")
        txn_pay = transaction.get("payment_method", "")
        deviations.append(0.0 if txn_pay == common_pay else 0.25)

        # Device type deviation (binary)
        common_dev = customer_profile.get("common_device_type", "")
        txn_dev = transaction.get("device_type", "")
        deviations.append(0.0 if txn_dev == common_dev else 0.15)

        if not deviations:
            return 0.0
        return min(1.0, sum(deviations) / len(deviations))

    # ── Combined feature computation ──────────────────────────────────────────
    def compute_features(
        self,
        transaction: dict[str, Any],
        customer_profile: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Run all feature computations and return a feature dictionary.

        Parameters
        ----------
        transaction     : dict with raw transaction fields
        customer_profile: optional dict with CustomerProfile fields

        Returns
        -------
        dict containing all computed feature scores
        """
        amount = float(transaction.get("amount", transaction.get("transaction_amount", 0)))
        hour = int(transaction.get("hour_of_day", 12))
        time_since_last = float(transaction.get("time_since_last_txn_hrs", 24.0))
        freq_monthly = int(transaction.get("transaction_freq_monthly", 10))
        is_international = bool(transaction.get("is_international", False))
        failed_attempts = int(transaction.get("failed_attempts", 0))
        pin_changed = bool(transaction.get("pin_changed_recently", False))
        credit_score = int(transaction.get("credit_score", 700))
        is_night = bool(transaction.get("is_night_transaction", False))

        if customer_profile:
            avg_amount = float(customer_profile.get("avg_amount", amount))
            std_amount = float(customer_profile.get("std_amount", amount * 0.2))
            avg_hour = float(customer_profile.get("avg_hour", 12.0))
        else:
            avg_amount = amount
            std_amount = amount * 0.2
            avg_hour = 12.0

        amount_info = self.compute_amount_anomaly(amount, avg_amount, std_amount)
        time_anomaly = self.compute_time_anomaly(hour, avg_hour)
        velocity = self.compute_velocity_risk(time_since_last, freq_monthly)
        behavioral = self.compute_behavioral_deviation(transaction, customer_profile)

        # Night/off-hours risk
        night_risk = 1.0 if is_night else (0.4 if hour < 6 or hour > 22 else 0.0)

        # International risk
        intl_risk = 0.6 if is_international else 0.0

        # Failed attempts risk
        failed_risk = min(1.0, failed_attempts / 3.0)

        # PIN change risk (recent PIN change = elevated)
        pin_risk = 0.8 if pin_changed else 0.0

        # Credit score risk (lower score → higher risk)
        credit_risk = max(0.0, (750 - credit_score) / 450.0)
        credit_risk = min(1.0, credit_risk)

        return {
            "amount": amount,
            "avg_amount": avg_amount,
            "std_amount": std_amount,
            "amount_z_score": amount_info["z_score"],
            "amount_risk_score": amount_info["normalised_score"],
            "time_anomaly_score": time_anomaly,
            "velocity_score": velocity,
            "behavioral_deviation_score": behavioral,
            "night_risk_score": night_risk,
            "international_risk_score": intl_risk,
            "failed_attempts_score": failed_risk,
            "pin_change_score": pin_risk,
            "credit_risk_score": credit_risk,
            "is_night": is_night,
            "is_international": is_international,
            "failed_attempts": failed_attempts,
            "pin_changed": pin_changed,
            "credit_score": credit_score,
            "hour_of_day": hour,
        }
