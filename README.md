# 🛡️ SENTINEL — AI-Powered Transaction Fraud & Risk Detection Platform

> **Detect anomalies. Understand behavior. Prevent fraud.**

SENTINEL is a production-grade, end-to-end **fintech fraud monitoring platform** built for bank transaction analysis. It combines Deep Learning Autoencoders, behavioral profiling, geospatial impossible travel detection, and a 10-component explainable risk engine — all wrapped in a modern dark-themed React dashboard.

---

## 📸 Platform Overview

| Module | Description |
|---|---|
| **Dashboard** | Real-time KPIs, fraud trend charts, risk distribution, live alert feed |
| **Live Analyzer** | Enter any transaction → instant AI risk score + explainability panel |
| **Transactions** | Browse and filter all 1M transactions with risk scoring |
| **Customers** | 198,662 behavioral profiles with spending patterns |
| **Fraud Alerts** | Real-time alert feed for HIGH_RISK and CRITICAL transactions |
| **Behavior Analytics** | Aggregate patterns — hourly, daily, payment methods, devices |
| **Geospatial Analysis** | World fraud map with impossible travel detection |
| **Model Monitoring** | Autoencoder architecture, training history, performance metrics |
| **Reports** | PDF investigation report generation per transaction |

---

## 📊 Dataset

| Property | Value |
|---|---|
| Source | `bank_fraud.csv` |
| Total Records | **1,000,000** transactions |
| Fraud Rate | ~5.5% (labeled) |
| Customers | **198,662** unique customer profiles |
| Features | 26 columns including amount, city, merchant category, device, credit score, etc. |
| Date Range | 2020 – 2024 |

---

## 🧠 AI Architecture

### Deep Learning Autoencoder
```
Input (22 features)
  → Dense(128) + BatchNorm + ReLU + Dropout(0.2)
  → Dense(64)  + BatchNorm + ReLU + Dropout(0.2)
  → Dense(32)  + BatchNorm + ReLU
  → Latent(16)   ← Compressed transaction "fingerprint"
  → Dense(32)  + ReLU
  → Dense(64)  + ReLU
  → Dense(128) + ReLU
  → Output(22 features)  ← Reconstructed transaction
```

**Principle:** The autoencoder is trained ONLY on normal transactions. When it encounters fraud, it cannot reconstruct the pattern well → high reconstruction error → anomaly detected.

### 10-Component Hybrid Risk Engine

| Component | Weight | Description |
|---|---|---|
| Autoencoder Anomaly Score | **35%** | Neural network reconstruction error |
| Amount Deviation | **15%** | Deviation from customer's normal spending |
| Geographic Risk | **15%** | Impossible travel detection (speed > 900 km/h) |
| Velocity Risk | **10%** | Too many transactions in short time window |
| Time Anomaly | **10%** | Late-night or unusual-hour transactions |
| Behavioral Deviation | **8%** | Differs from customer's historical patterns |
| International Flag | **3%** | Cross-border transaction risk |
| Failed Attempts | **2%** | Multiple authentication failures |
| PIN Change | **1%** | PIN changed recently |
| Credit Factor | **1%** | Low credit score multiplier |

### Risk Levels
| Score | Level | Color |
|---|---|---|
| 0 – 30 | NORMAL | 🟢 Green |
| 31 – 60 | SUSPICIOUS | 🟡 Amber |
| 61 – 80 | HIGH_RISK | 🟠 Orange |
| 81 – 100 | CRITICAL | 🔴 Red |

---

## 🗂️ Project Structure

```
fraud-detection-platform/
│
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI route handlers
│   │   │   ├── analyze.py    # POST /api/analyze
│   │   │   ├── transactions.py
│   │   │   ├── customers.py
│   │   │   ├── alerts.py
│   │   │   ├── analytics.py
│   │   │   ├── geospatial.py
│   │   │   ├── model.py
│   │   │   └── reports.py
│   │   ├── ml/               # Machine Learning core
│   │   │   ├── autoencoder.py    # PyTorch model definition
│   │   │   ├── preprocessing.py  # Feature engineering & scaling
│   │   │   ├── training.py       # Training pipeline
│   │   │   ├── inference.py      # Singleton inference engine
│   │   │   └── risk_engine.py    # 10-component risk scoring
│   │   ├── models/           # SQLAlchemy ORM models
│   │   │   ├── transaction.py
│   │   │   ├── customer_profile.py
│   │   │   ├── fraud_prediction.py
│   │   │   ├── risk_factor.py
│   │   │   └── alert.py
│   │   ├── services/         # Business logic layer
│   │   │   ├── transaction_service.py
│   │   │   ├── customer_service.py
│   │   │   ├── analytics_service.py
│   │   │   ├── alert_service.py
│   │   │   └── report_service.py
│   │   ├── config.py         # Pydantic settings
│   │   ├── database.py       # SQLite async/sync engines
│   │   └── main.py           # FastAPI app entry point
│   ├── scripts/
│   │   ├── train_model.py    # Run to train the autoencoder
│   │   └── ingest_data.py    # Run to populate database
│   ├── models/               # Saved model artifacts (after training)
│   │   ├── autoencoder.pt
│   │   ├── preprocessor.pkl
│   │   ├── metrics.json
│   │   └── training_history.json
│   ├── sentinel.db           # SQLite database (auto-created)
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── pages/            # 11 page components
│   │   ├── components/       # Reusable UI components
│   │   │   ├── cards/        # MetricCard, AlertCard
│   │   │   ├── charts/       # FraudTrendChart, RiskDonut, etc.
│   │   │   ├── maps/         # FraudMap (Leaflet)
│   │   │   ├── risk/         # RiskGauge, ExplainPanel
│   │   │   ├── tables/       # TransactionTable
│   │   │   └── layout/       # Sidebar, TopBar, Layout
│   │   ├── hooks/            # useApi custom hooks
│   │   ├── services/         # api.ts (Axios calls + mock fallback)
│   │   ├── types/            # TypeScript interfaces
│   │   └── lib/              # Utility functions
│   └── package.json
│
└── data/
    └── raw/
        └── bank_fraud.csv    # Source dataset
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Git

### Step 1 — Clone & Setup
```bash
git clone <repo-url>
cd fraud-detection-platform
```

### Step 2 — Backend Setup
```bash
cd backend
pip install -r requirements.txt
```

### Step 3 — Configure Environment
Create `backend/.env` (copy from `.env.example`):
```env
DATABASE_URL=sqlite+aiosqlite:///./sentinel.db
SYNC_DATABASE_URL=sqlite:///./sentinel.db
SECRET_KEY=your-secret-key-change-in-production
MODEL_PATH=../models
DATA_PATH=../data/raw/bank_fraud.csv
```

### Step 4 — Train the AI Model
```bash
cd backend
python scripts/train_model.py
```
> ⏱️ Takes 5–15 minutes. Trains on 800K normal transactions for 50 epochs.

### Step 5 — Ingest Dataset into Database
```bash
python scripts/ingest_data.py
```
> ⏱️ Takes 20–45 minutes for 1M rows. Press `Ctrl+C` after 5–10 chunks (50K–100K rows) to test the app early.

### Step 6 — Start Backend Server
```bash
python -m uvicorn app.main:app --reload --port 8000
```
> API available at `http://localhost:8000` | Docs at `http://localhost:8000/docs`

### Step 7 — Start Frontend
Open a new terminal:
```bash
cd frontend
npm install
npm run preview
```
> App available at `http://localhost:5173`

### Step 8 — Login
- **URL:** http://localhost:5173
- **Username:** `admin`
- **Password:** `sentinel123`

---

## 🔌 API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Server health check |
| GET | `/api/analytics/overview` | Dashboard KPI cards |
| GET | `/api/analytics/fraud-trend?period=24h` | Fraud trend (24h/7d/30d) |
| GET | `/api/analytics/risk-distribution` | Risk level breakdown |
| GET | `/api/analytics/fraud-by-category` | Fraud by merchant category |
| GET | `/api/analytics/anomaly-distribution` | Anomaly score histogram |
| GET | `/api/analytics/behavior` | Behavioral analytics |
| GET | `/api/transactions?page=1&limit=50` | Paginated transactions |
| GET | `/api/transactions/{id}` | Single transaction detail |
| POST | `/api/analyze` | Real-time transaction analysis |
| GET | `/api/customers?page=1` | Customer profiles |
| GET | `/api/customers/{id}` | Customer detail + history |
| GET | `/api/alerts?limit=50` | Alert feed |
| PATCH | `/api/alerts/{id}/read` | Mark alert as read |
| GET | `/api/geospatial/suspicious` | Geo fraud markers |
| GET | `/api/geospatial/impossible-travel` | Impossible travel cases |
| GET | `/api/model/info` | Model metadata |
| GET | `/api/model/metrics` | Model performance metrics |
| GET | `/api/model/training-history` | Training loss per epoch |
| POST | `/api/reports/generate` | Generate PDF report |

### Sample POST /api/analyze Request
```json
{
  "customer_id": "CUST00131933",
  "amount": 15000.0,
  "city": "Tokyo",
  "country": "Japan",
  "merchant_category": "Crypto Exchange",
  "payment_method": "Crypto",
  "device_type": "Mobile",
  "hour_of_day": 3,
  "is_weekend": false,
  "is_night_transaction": true,
  "is_international": true,
  "failed_attempts": 3,
  "pin_changed_recently": true,
  "credit_score": 450,
  "account_balance": 1200.0,
  "distance_from_home_km": 5800.0,
  "time_since_last_txn_hrs": 0.08
}
```

---

## 🛠️ Technology Stack

### Backend
| Technology | Version | Purpose |
|---|---|---|
| Python | 3.10 | Core language |
| FastAPI | 0.140 | REST API framework |
| SQLAlchemy | 2.0 | ORM (async + sync) |
| SQLite + aiosqlite | — | Database |
| PyTorch | 2.14 (CPU) | Deep Learning Autoencoder |
| scikit-learn | 1.7 | Preprocessing (RobustScaler, OrdinalEncoder) |
| pandas | 2.3 | Data processing |
| numpy | 1.26 | Numerical operations |
| haversine | 2.9 | Geospatial distance calculation |
| reportlab | 5.0 | PDF report generation |
| Uvicorn | 0.29+ | ASGI server |

### Frontend
| Technology | Version | Purpose |
|---|---|---|
| React | 19 | UI framework |
| TypeScript | 6.0 | Type safety |
| Vite | 8.3 | Build tool |
| Tailwind CSS | 4.3 | Styling (dark mode) |
| Recharts | 3.10 | All charts (line, bar, pie, histogram) |
| React Leaflet | 5.0 | Interactive fraud world map |
| Framer Motion | 13 | Animations (gauge, cards) |
| Axios | 1.20 | HTTP client |
| React Router | 7.18 | Client-side routing |
| Lucide React | 1.47 | Icons |

---

## 📄 License

This project is built for academic and demonstration purposes.

---

## 👤 Author

**Bhavesh Harad**  
📧 Email: [haradb275@gmail.com](mailto:haradb275@gmail.com)  
🔗 GitHub: [Bhavesh-Harad](https://github.com/Bhavesh-Harad)  

---

*SENTINEL — AI-Powered Transaction Fraud & Risk Detection Platform*
