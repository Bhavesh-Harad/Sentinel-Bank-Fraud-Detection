"""
SENTINEL — Preprocessing pipeline.

Provides:
- CITY_COORDINATES   : city name → (lat, lon) lookup dict
- load_and_preprocess: loads CSV, augments with coordinates
- FraudPreprocessor  : sklearn-compatible transformer (fit/transform/save/load)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import RobustScaler, OrdinalEncoder
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)

# ── City → (latitude, longitude) lookup ──────────────────────────────────────
CITY_COORDINATES: dict[str, tuple[float, float]] = {
    # UK
    "London": (51.5074, -0.1278),
    "Manchester": (53.4808, -2.2426),
    "Birmingham": (52.4862, -1.8904),
    "Leeds": (53.8008, -1.5491),
    "Glasgow": (55.8642, -4.2518),
    "Edinburgh": (55.9533, -3.1883),
    "Bristol": (51.4545, -2.5879),
    "Liverpool": (53.4084, -2.9916),
    "Sheffield": (53.3811, -1.4701),
    "Cardiff": (51.4816, -3.1791),
    # USA
    "New York": (40.7128, -74.0060),
    "NewYork": (40.7128, -74.0060),
    "Los Angeles": (34.0522, -118.2437),
    "LosAngeles": (34.0522, -118.2437),
    "Chicago": (41.8781, -87.6298),
    "Houston": (29.7604, -95.3698),
    "Phoenix": (33.4484, -112.0740),
    "Philadelphia": (39.9526, -75.1652),
    "San Antonio": (29.4241, -98.4936),
    "San Diego": (32.7157, -117.1611),
    "Dallas": (32.7767, -96.7970),
    "San Francisco": (37.7749, -122.4194),
    "Miami": (25.7617, -80.1918),
    "Seattle": (47.6062, -122.3321),
    "Boston": (42.3601, -71.0589),
    "Atlanta": (33.7490, -84.3880),
    "Denver": (39.7392, -104.9903),
    "Portland": (45.5051, -122.6750),
    "Las Vegas": (36.1699, -115.1398),
    "Detroit": (42.3314, -83.0458),
    # India
    "Delhi": (28.6139, 77.2090),
    "Mumbai": (19.0760, 72.8777),
    "Bangalore": (12.9716, 77.5946),
    "Chennai": (13.0827, 80.2707),
    "Kolkata": (22.5726, 88.3639),
    "Hyderabad": (17.3850, 78.4867),
    "Pune": (18.5204, 73.8567),
    "Ahmedabad": (23.0225, 72.5714),
    "Jaipur": (26.9124, 75.7873),
    "Surat": (21.1702, 72.8311),
    # Japan
    "Tokyo": (35.6762, 139.6503),
    "Osaka": (34.6937, 135.5023),
    "Yokohama": (35.4437, 139.6380),
    "Nagoya": (35.1815, 136.9066),
    "Sapporo": (43.0618, 141.3545),
    "Kyoto": (35.0116, 135.7681),
    "Kobe": (34.6901, 135.1956),
    "Fukuoka": (33.5904, 130.4017),
    # Australia
    "Sydney": (-33.8688, 151.2093),
    "Melbourne": (-37.8136, 144.9631),
    "Brisbane": (-27.4698, 153.0251),
    "Perth": (-31.9505, 115.8605),
    "Adelaide": (-34.9285, 138.6007),
    # Canada
    "Toronto": (43.6532, -79.3832),
    "Vancouver": (49.2827, -123.1207),
    "Montreal": (45.5017, -73.5673),
    "Calgary": (51.0447, -114.0719),
    "Ottawa": (45.4215, -75.6972),
    # Germany
    "Berlin": (52.5200, 13.4050),
    "Munich": (48.1351, 11.5820),
    "Hamburg": (53.5753, 10.0153),
    "Frankfurt": (50.1109, 8.6821),
    "Cologne": (50.9333, 6.9500),
    "Stuttgart": (48.7758, 9.1829),
    "Dusseldorf": (51.2217, 6.7762),
    # France
    "Paris": (48.8566, 2.3522),
    "Lyon": (45.7640, 4.8357),
    "Marseille": (43.2965, 5.3698),
    "Toulouse": (43.6047, 1.4442),
    "Nice": (43.7102, 7.2620),
    "Bordeaux": (44.8378, -0.5792),
    "Strasbourg": (48.5734, 7.7521),
    # Mexico
    "Mexico City": (19.4326, -99.1332),
    "MexicoCity": (19.4326, -99.1332),
    "Guadalajara": (20.6597, -103.3496),
    "Monterrey": (25.6866, -100.3161),
    "Puebla": (19.0414, -98.2063),
    "Tijuana": (32.5149, -117.0382),
    # Brazil
    "Sao Paulo": (-23.5505, -46.6333),
    "SaoPaulo": (-23.5505, -46.6333),
    "Rio de Janeiro": (-22.9068, -43.1729),
    "Rio": (-22.9068, -43.1729),
    "Salvador": (-12.9714, -38.5014),
    "Brasilia": (-15.8267, -47.9218),
    "Fortaleza": (-3.7319, -38.5267),
    "Curitiba": (-25.4284, -49.2733),
    # South Korea
    "Seoul": (37.5665, 126.9780),
    "Busan": (35.1796, 129.0756),
    "Incheon": (37.4563, 126.7052),
    "Daegu": (35.8714, 128.6014),
    # China
    "Beijing": (39.9042, 116.4074),
    "Shanghai": (31.2304, 121.4737),
    "Guangzhou": (23.1291, 113.2644),
    "Shenzhen": (22.5431, 114.0579),
    "Chengdu": (30.5728, 104.0668),
    "Wuhan": (30.5928, 114.3055),
    # Singapore / SE Asia
    "Singapore": (1.3521, 103.8198),
    "Bangkok": (13.7563, 100.5018),
    "Kuala Lumpur": (3.1390, 101.6869),
    "Jakarta": (-6.2088, 106.8456),
    "Manila": (14.5995, 120.9842),
    "Ho Chi Minh City": (10.8231, 106.6297),
    # Middle East / Africa
    "Dubai": (25.2048, 55.2708),
    "Abu Dhabi": (24.4539, 54.3773),
    "Cairo": (30.0444, 31.2357),
    "Lagos": (6.5244, 3.3792),
    "Nairobi": (-1.2921, 36.8219),
    "Johannesburg": (-26.2041, 28.0473),
    "Cape Town": (-33.9249, 18.4241),
    "Riyadh": (24.7136, 46.6753),
    "Istanbul": (41.0082, 28.9784),
    "Tel Aviv": (32.0853, 34.7818),
    # South America (others)
    "Buenos Aires": (-34.6037, -58.3816),
    "Lima": (-12.0464, -77.0428),
    "Bogota": (4.7110, -74.0721),
    "Santiago": (-33.4489, -70.6693),
    "Caracas": (10.4806, -66.9036),
    # Europe (others)
    "Madrid": (40.4168, -3.7038),
    "Barcelona": (41.3851, 2.1734),
    "Rome": (41.9028, 12.4964),
    "Milan": (45.4642, 9.1900),
    "Amsterdam": (52.3676, 4.9041),
    "Brussels": (50.8503, 4.3517),
    "Vienna": (48.2082, 16.3738),
    "Zurich": (47.3769, 8.5417),
    "Stockholm": (59.3293, 18.0686),
    "Oslo": (59.9139, 10.7522),
    "Copenhagen": (55.6761, 12.5683),
    "Helsinki": (60.1699, 24.9384),
    "Warsaw": (52.2297, 21.0122),
    "Prague": (50.0755, 14.4378),
    "Budapest": (47.4979, 19.0402),
    "Lisbon": (38.7169, -9.1395),
    "Athens": (37.9838, 23.7275),
    # Default fallback
    "Unknown": (0.0, 0.0),
}

# ── City → UTC offset (hours) lookup ─────────────────────────────────────────
# These are standard/winter offsets (non-DST). For fraud detection purposes
# this is sufficient: the key is avoiding cross-timezone comparison errors.
CITY_TIMEZONE_OFFSET: dict[str, float] = {
    # UK / Ireland (UTC+0 / UTC+1 BST — use standard)
    "London": 0.0, "Manchester": 0.0, "Birmingham": 0.0, "Leeds": 0.0,
    "Glasgow": 0.0, "Edinburgh": 0.0, "Bristol": 0.0, "Liverpool": 0.0,
    "Sheffield": 0.0, "Cardiff": 0.0,
    # USA Eastern (UTC-5)
    "New York": -5.0, "NewYork": -5.0, "Philadelphia": -5.0, "Boston": -5.0,
    "Miami": -5.0, "Atlanta": -5.0, "Detroit": -5.0,
    # USA Central (UTC-6)
    "Chicago": -6.0, "Houston": -6.0, "Dallas": -6.0, "San Antonio": -6.0,
    # USA Mountain (UTC-7)
    "Denver": -7.0, "Phoenix": -7.0,
    # USA Pacific (UTC-8)
    "Los Angeles": -8.0, "LosAngeles": -8.0, "San Francisco": -8.0,
    "Seattle": -8.0, "Portland": -8.0,
    # USA Hawaii (UTC-10)
    "Las Vegas": -8.0,  # same tz as Pacific
    # India (UTC+5:30)
    "Delhi": 5.5, "Mumbai": 5.5, "Bangalore": 5.5, "Chennai": 5.5,
    "Kolkata": 5.5, "Hyderabad": 5.5, "Pune": 5.5, "Ahmedabad": 5.5,
    "Jaipur": 5.5, "Surat": 5.5,
    # Japan (UTC+9)
    "Tokyo": 9.0, "Osaka": 9.0, "Yokohama": 9.0, "Nagoya": 9.0,
    "Sapporo": 9.0, "Kyoto": 9.0, "Kobe": 9.0, "Fukuoka": 9.0,
    # Australia
    "Sydney": 10.0, "Melbourne": 10.0, "Brisbane": 10.0,
    "Adelaide": 9.5, "Perth": 8.0,
    # Canada
    "Toronto": -5.0, "Ottawa": -5.0, "Montreal": -5.0,
    "Vancouver": -8.0, "Calgary": -7.0,
    # Germany / Central Europe (UTC+1)
    "Berlin": 1.0, "Munich": 1.0, "Hamburg": 1.0, "Frankfurt": 1.0,
    "Cologne": 1.0, "Stuttgart": 1.0, "Dusseldorf": 1.0,
    # France (UTC+1)
    "Paris": 1.0, "Lyon": 1.0, "Marseille": 1.0, "Toulouse": 1.0,
    "Nice": 1.0, "Bordeaux": 1.0, "Strasbourg": 1.0,
    # Mexico (UTC-6)
    "Mexico City": -6.0, "MexicoCity": -6.0, "Guadalajara": -6.0,
    "Monterrey": -6.0, "Puebla": -6.0, "Tijuana": -8.0,
    # Brazil (UTC-3)
    "Sao Paulo": -3.0, "SaoPaulo": -3.0, "Rio de Janeiro": -3.0, "Rio": -3.0,
    "Salvador": -3.0, "Brasilia": -3.0, "Fortaleza": -3.0, "Curitiba": -3.0,
    # South Korea (UTC+9)
    "Seoul": 9.0, "Busan": 9.0, "Incheon": 9.0, "Daegu": 9.0,
    # China (UTC+8)
    "Beijing": 8.0, "Shanghai": 8.0, "Guangzhou": 8.0, "Shenzhen": 8.0,
    "Chengdu": 8.0, "Wuhan": 8.0,
    # Singapore / SE Asia
    "Singapore": 8.0, "Bangkok": 7.0, "Kuala Lumpur": 8.0,
    "Jakarta": 7.0, "Manila": 8.0, "Ho Chi Minh City": 7.0,
    # Middle East / Africa
    "Dubai": 4.0, "Abu Dhabi": 4.0, "Riyadh": 3.0, "Istanbul": 3.0,
    "Tel Aviv": 2.0, "Cairo": 2.0,
    "Lagos": 1.0, "Nairobi": 3.0,
    "Johannesburg": 2.0, "Cape Town": 2.0,
    # South America (others)
    "Buenos Aires": -3.0, "Lima": -5.0, "Bogota": -5.0,
    "Santiago": -3.0, "Caracas": -4.0,
    # Europe (others)
    "Madrid": 1.0, "Barcelona": 1.0, "Rome": 1.0, "Milan": 1.0,
    "Amsterdam": 1.0, "Brussels": 1.0, "Vienna": 1.0, "Zurich": 1.0,
    "Stockholm": 1.0, "Oslo": 1.0, "Copenhagen": 1.0, "Helsinki": 2.0,
    "Warsaw": 1.0, "Prague": 1.0, "Budapest": 1.0, "Lisbon": 0.0,
    "Athens": 2.0,
    # Default fallback (UTC)
    "Unknown": 0.0,
}

# ── Feature lists ──────────────────────────────────────────────────────────────
NUMERIC_FEATURES: list[str] = [
    "transaction_amount",
    "log_amount",
    "hour_of_day",
    "is_weekend",
    "is_night_transaction",
    "credit_score",
    "account_age_years",
    "account_balance",
    "num_prev_transactions",
    "transaction_freq_monthly",
    "distance_from_home_km",
    "time_since_last_txn_hrs",
    "is_international",
    "failed_attempts",
    "pin_changed_recently",
    "sin_hour",
    "cos_hour",
    "customer_age",
]

CATEGORICAL_FEATURES: list[str] = [
    "merchant_category",
    "payment_method",
    "device_type",
    "country",
]

ALL_FEATURES: list[str] = NUMERIC_FEATURES + CATEGORICAL_FEATURES


# ── City coordinate helper ────────────────────────────────────────────────────
def get_city_coordinates(city: str) -> tuple[float, float]:
    """Return (lat, lon) for a city name, falling back to (0, 0) if unknown."""
    if city in CITY_COORDINATES:
        return CITY_COORDINATES[city]
    # Try normalised (strip whitespace, title-case)
    normalised = city.strip().title()
    return CITY_COORDINATES.get(normalised, (0.0, 0.0))


# ── City timezone helper ───────────────────────────────────────────────────────
def get_city_utc_offset_hours(city: str) -> float:
    """
    Return the UTC offset in hours for a given city name.

    Uses a static lookup (standard/winter offsets, no DST adjustment).
    For fraud-detection purposes the ±1h DST variance is negligible compared
    to the hours-wide gaps that constitute impossible travel.

    Falls back to 0.0 (UTC) for unknown cities.
    """
    if city in CITY_TIMEZONE_OFFSET:
        return CITY_TIMEZONE_OFFSET[city]
    normalised = city.strip().title()
    return CITY_TIMEZONE_OFFSET.get(normalised, 0.0)


def local_timestamp_to_utc_hours(timestamp_naive, city: str) -> float:
    """
    Convert a naive local datetime (stored without tzinfo) for the given city
    to a comparable UTC timestamp in seconds-since-epoch, then return as hours.

    This is used to compute accurate time gaps between transactions
    in different time zones (e.g. Mumbai IST vs New York EST).

    Args:
        timestamp_naive: datetime object without timezone info (local city time)
        city: city name used to look up UTC offset

    Returns:
        float: UTC time expressed in fractional hours (for relative comparisons)
    """
    import datetime
    if timestamp_naive is None:
        return 0.0
    utc_offset_hours = get_city_utc_offset_hours(city)
    # Shift the naive local time to UTC
    utc_dt = timestamp_naive - datetime.timedelta(hours=utc_offset_hours)
    # Return as total hours since epoch (for diff computation)
    epoch = datetime.datetime(1970, 1, 1)
    return (utc_dt - epoch).total_seconds() / 3600.0


# ── CSV loader ────────────────────────────────────────────────────────────────
def load_and_preprocess(csv_path: str | Path) -> pd.DataFrame:
    """
    Load bank_fraud.csv and apply initial transformations:
    - Build `timestamp` column from transaction_date + transaction_time
    - Map `city` to `latitude` / `longitude`
    - Add `log_amount`, `sin_hour`, `cos_hour` cyclical features
    - Cast boolean columns consistently
    - Fill NaN values
    """
    logger.info(f"Loading dataset from {csv_path}")
    df = pd.read_csv(csv_path, low_memory=False)
    logger.info(f"Loaded {len(df):,} rows, {df.shape[1]} columns")

    # ── Timestamp ──────────────────────────────────────────────────────────────
    if "transaction_date" in df.columns and "transaction_time" in df.columns:
        try:
            df["timestamp"] = pd.to_datetime(
                df["transaction_date"].astype(str) + " " + df["transaction_time"].astype(str),
                errors="coerce",
            )
        except Exception:
            df["timestamp"] = pd.NaT
    else:
        df["timestamp"] = pd.NaT

    # ── City coordinates ──────────────────────────────────────────────────────
    if "city" in df.columns:
        coords = df["city"].apply(get_city_coordinates)
        df["latitude"] = coords.apply(lambda c: c[0])
        df["longitude"] = coords.apply(lambda c: c[1])
    else:
        df["latitude"] = 0.0
        df["longitude"] = 0.0

    # ── Derived numeric features ───────────────────────────────────────────────
    df["log_amount"] = np.log1p(df["transaction_amount"].clip(lower=0))
    df["sin_hour"] = np.sin(2 * np.pi * df["hour_of_day"] / 24)
    df["cos_hour"] = np.cos(2 * np.pi * df["hour_of_day"] / 24)

    # ── Boolean columns ───────────────────────────────────────────────────────
    bool_cols = [
        "is_weekend", "is_night_transaction", "is_international",
        "pin_changed_recently",
    ]
    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].astype(bool).astype(int)

    # ── Fill NaN ──────────────────────────────────────────────────────────────
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
    cat_cols = df.select_dtypes(include=["object"]).columns
    df[cat_cols] = df[cat_cols].fillna("Unknown")

    logger.info("Preprocessing complete")
    return df


# ── FraudPreprocessor ─────────────────────────────────────────────────────────
class FraudPreprocessor:
    """
    Fit/transform pipeline for the fraud detection autoencoder.

    Numeric features  → RobustScaler
    Categorical features → OrdinalEncoder → float (for concatenation)
    """

    def __init__(self) -> None:
        self.numeric_scaler = RobustScaler()
        self.categorical_encoder = OrdinalEncoder(
            handle_unknown="use_encoded_value",
            unknown_value=-1,
            dtype=np.float32,
        )
        self.numeric_features: list[str] = NUMERIC_FEATURES
        self.categorical_features: list[str] = CATEGORICAL_FEATURES
        self.feature_names: list[str] = ALL_FEATURES
        self._is_fitted: bool = False

    # ── Internal helpers ──────────────────────────────────────────────────────
    def _ensure_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add missing derived features (log_amount, sin/cos hour)."""
        df = df.copy()
        if "log_amount" not in df.columns:
            df["log_amount"] = np.log1p(df.get("transaction_amount", 0).clip(lower=0))
        if "sin_hour" not in df.columns:
            df["sin_hour"] = np.sin(2 * np.pi * df.get("hour_of_day", 0) / 24)
        if "cos_hour" not in df.columns:
            df["cos_hour"] = np.cos(2 * np.pi * df.get("hour_of_day", 0) / 24)
        # Cast boolean cols
        for col in ["is_weekend", "is_night_transaction", "is_international", "pin_changed_recently"]:
            if col in df.columns:
                df[col] = df[col].astype(float)
        # Fill missing
        for col in self.numeric_features:
            if col not in df.columns:
                df[col] = 0.0
        for col in self.categorical_features:
            if col not in df.columns:
                df[col] = "Unknown"
        return df

    # ── Public API ────────────────────────────────────────────────────────────
    def fit(self, df: pd.DataFrame) -> "FraudPreprocessor":
        """Fit scaler and encoder on the provided DataFrame."""
        df = self._ensure_features(df)
        self.numeric_scaler.fit(df[self.numeric_features])
        self.categorical_encoder.fit(df[self.categorical_features])
        self._is_fitted = True
        logger.info(
            f"FraudPreprocessor fitted on {len(df):,} samples. "
            f"Features: {len(self.feature_names)}"
        )
        return self

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        """Transform DataFrame → float32 numpy array ready for the model."""
        if not self._is_fitted:
            raise RuntimeError("FraudPreprocessor must be fitted before transform().")
        df = self._ensure_features(df)
        num_scaled = self.numeric_scaler.transform(df[self.numeric_features])
        cat_encoded = self.categorical_encoder.transform(df[self.categorical_features])
        combined = np.concatenate([num_scaled, cat_encoded], axis=1).astype(np.float32)
        return combined

    def fit_transform(self, df: pd.DataFrame) -> np.ndarray:
        """Convenience: fit then transform."""
        return self.fit(df).transform(df)

    def transform_single(self, record: dict) -> np.ndarray:
        """Transform a single transaction dict → (1, n_features) array."""
        row = pd.DataFrame([record])
        return self.transform(row)

    def save(self, path: str | Path) -> None:
        """Persist the fitted preprocessor to disk."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)
        logger.info(f"Preprocessor saved to {path}")

    @classmethod
    def load(cls, path: str | Path) -> "FraudPreprocessor":
        """Load a previously saved preprocessor."""
        obj = joblib.load(path)
        if not isinstance(obj, cls):
            raise TypeError(f"Expected FraudPreprocessor, got {type(obj)}")
        logger.info(f"Preprocessor loaded from {path}")
        return obj
