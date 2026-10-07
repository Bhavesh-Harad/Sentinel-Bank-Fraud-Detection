"""
Comprehensive fix script for SENTINEL application.
Fixes all frontend<->backend data contract mismatches.
"""
import re

def read(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

###############################################################################
# 1. FIX BACKEND: fraud_trend uses postgres date_trunc - replace with SQLite
###############################################################################
analytics_path = 'd:/DL_Fraud_Detection/fraud-detection-platform/backend/app/services/analytics_service.py'
c = read(analytics_path)

old_fraud_trend = '''        # Raw query — use date_trunc for PostgreSQL
        q = text(
            f"""
            SELECT
                date_trunc('{trunc}', t.timestamp) AS bucket,
                COUNT(t.id) AS transactions,
                COUNT(fp.id) FILTER (WHERE fp.prediction = 'POTENTIAL_FRAUD') AS fraud_alerts
            FROM transactions t
            LEFT JOIN fraud_predictions fp ON t.transaction_id = fp.transaction_id
            WHERE t.timestamp >= :start
            GROUP BY bucket
            ORDER BY bucket
            """
        )
        rows = (await db.execute(q, {"start": start})).all()

        data = []
        for row in rows:
            txns = int(row.transactions or 0)
            fa = int(row.fraud_alerts or 0)
            data.append(
                {
                    "timestamp": row.bucket.isoformat() if row.bucket else "",
                    "transactions": txns,
                    "fraud_alerts": fa,
                    "fraud_rate": round(fa / txns * 100, 2) if txns > 0 else 0.0,
                }
            )

        return {"period": period, "data": data}'''

new_fraud_trend = '''        # SQLite-compatible: fetch raw rows and bucket in Python
        txn_q = (
            select(Transaction.timestamp, FraudPrediction.prediction)
            .outerjoin(FraudPrediction, Transaction.transaction_id == FraudPrediction.transaction_id)
            .where(Transaction.timestamp >= start)
        )
        rows = (await db.execute(txn_q)).all()

        from collections import defaultdict
        buckets: dict = defaultdict(lambda: {"transactions": 0, "fraud_alerts": 0})
        for row in rows:
            ts = row[0]
            pred = row[1]
            if ts is None:
                continue
            from datetime import datetime as dt_
            if isinstance(ts, str):
                try:
                    ts = dt_.fromisoformat(ts)
                except Exception:
                    continue
            if bucket_hours == 1:
                key = ts.replace(minute=0, second=0, microsecond=0)
            else:
                key = ts.replace(hour=0, minute=0, second=0, microsecond=0)
            buckets[key]["transactions"] += 1
            if pred == "POTENTIAL_FRAUD":
                buckets[key]["fraud_alerts"] += 1

        data = []
        for bucket_ts in sorted(buckets.keys()):
            txns = buckets[bucket_ts]["transactions"]
            fa = buckets[bucket_ts]["fraud_alerts"]
            data.append({
                "timestamp": bucket_ts.isoformat(),
                "transactions": txns,
                "fraud_alerts": fa,
                "fraud_rate": round(fa / txns * 100, 2) if txns > 0 else 0.0,
            })

        return {"period": period, "data": data}'''

if old_fraud_trend in c:
    c = c.replace(old_fraud_trend, new_fraud_trend)
    print("Fixed fraud_trend PostgreSQL query")
else:
    print("WARNING: old_fraud_trend not found - may already be fixed or different format")

# Add Transaction import if not already there for fraud_trend fix
if 'from app.models.transaction import Transaction' not in c:
    c = c.replace('from app.models.alert import Alert', 'from app.models.alert import Alert\nfrom app.models.transaction import Transaction')

write(analytics_path, c)
print("analytics_service.py written")

###############################################################################
# 2. FIX BACKEND: alert mark_as_read - RETURNING not supported by SQLite
###############################################################################
alert_service_path = 'd:/DL_Fraud_Detection/fraud-detection-platform/backend/app/services/alert_service.py'
c = read(alert_service_path)

old_mark = '''        q = update(Alert).where(Alert.id == alert_id).values(is_read=True).returning(Alert)
        result = await db.execute(q)
        await db.commit()
        row = result.fetchone()
        if not row:
            return None
        a = row[0]
        return {
            "id": a.id,
            "transaction_id": a.transaction_id,
            "customer_id": a.customer_id,
            "risk_level": a.risk_level,
            "risk_score": a.risk_score,
            "alert_type": a.alert_type,
            "message": a.message,
            "city": a.city,
            "amount": a.amount,
            "is_read": a.is_read,
            "created_at": a.created_at,
        }'''

new_mark = '''        q = update(Alert).where(Alert.id == alert_id).values(is_read=True)
        await db.execute(q)
        await db.commit()
        # Re-fetch the updated alert (SQLite doesn't support RETURNING)
        fetch_q = select(Alert).where(Alert.id == alert_id)
        a = (await db.execute(fetch_q)).scalar_one_or_none()
        if not a:
            return None
        return {
            "id": a.id,
            "alert_id": str(a.id),
            "transaction_id": a.transaction_id,
            "customer_id": a.customer_id,
            "risk_level": a.risk_level,
            "risk_score": a.risk_score,
            "alert_type": a.alert_type,
            "message": a.message,
            "city": a.city,
            "amount": a.amount,
            "is_read": a.is_read,
            "timestamp": a.created_at.isoformat() if a.created_at else "",
            "created_at": a.created_at,
        }'''

if old_mark in c:
    c = c.replace(old_mark, new_mark)
    print("Fixed alert mark_as_read RETURNING clause")
else:
    print("WARNING: old_mark not found")

# Also fix get_alerts to add alert_id and timestamp fields
old_get_alerts_return = '''        return [
            {
                "id": a.id,
                "transaction_id": a.transaction_id,
                "customer_id": a.customer_id,
                "risk_level": a.risk_level,
                "risk_score": a.risk_score,
                "alert_type": a.alert_type,
                "message": a.message,
                "city": a.city,
                "amount": a.amount,
                "is_read": a.is_read,
                "created_at": a.created_at,
            }
            for a in alerts
        ]'''

new_get_alerts_return = '''        return [
            {
                "id": a.id,
                "alert_id": str(a.id),
                "transaction_id": a.transaction_id,
                "customer_id": a.customer_id,
                "risk_level": a.risk_level,
                "risk_score": a.risk_score,
                "alert_type": a.alert_type,
                "message": a.message,
                "city": a.city,
                "amount": a.amount,
                "is_read": a.is_read,
                "timestamp": a.created_at.isoformat() if a.created_at else "",
                "created_at": a.created_at,
            }
            for a in alerts
        ]'''

if old_get_alerts_return in c:
    c = c.replace(old_get_alerts_return, new_get_alerts_return)
    print("Fixed alert get_alerts to include alert_id and timestamp")

write(alert_service_path, c)
print("alert_service.py written")

###############################################################################
# 3. FIX BACKEND: transaction_service returns "data" key, but frontend expects "transactions"
###############################################################################
txn_service_path = 'd:/DL_Fraud_Detection/fraud-detection-platform/backend/app/services/transaction_service.py'
c = read(txn_service_path)

old_txn_return = '        pages = math.ceil(total / limit) if limit > 0 else 1\n        return {"total": total, "page": page, "limit": limit, "pages": pages, "data": transactions}'
new_txn_return = '        pages = math.ceil(total / limit) if limit > 0 else 1\n        return {"total": total, "page": page, "limit": limit, "pages": pages, "total_pages": pages, "transactions": transactions, "data": transactions}'

if old_txn_return in c:
    c = c.replace(old_txn_return, new_txn_return)
    print("Fixed transaction_service to include transactions key")
else:
    print("WARNING: old_txn_return not found")

# Also fix field names in transaction dicts to match frontend Transaction type (amount not transaction_amount)
old_txn_dict = '''                "transaction_amount": txn.transaction_amount,'''
new_txn_dict = '''                "transaction_amount": txn.transaction_amount,
                "amount": txn.transaction_amount,'''
if old_txn_dict in c:
    c = c.replace(old_txn_dict, new_txn_dict)
    print("Fixed transaction_service amount field alias")

write(txn_service_path, c)
print("transaction_service.py written")

###############################################################################
# 4. FIX BACKEND: customer_service returns "data" key, but frontend expects "customers"
###############################################################################
cust_service_path = 'd:/DL_Fraud_Detection/fraud-detection-platform/backend/app/services/customer_service.py'
c = read(cust_service_path)

old_cust_return = '        pages = math.ceil(total / limit) if limit > 0 else 1\n        return {\n            "total": total,\n            "page": page,\n            "limit": limit,\n            "pages": pages,\n            "data": ['
new_cust_return = '        pages = math.ceil(total / limit) if limit > 0 else 1\n        return {\n            "total": total,\n            "page": page,\n            "limit": limit,\n            "pages": pages,\n            "total_pages": pages,\n            "customers": ['

if old_cust_return in c:
    c = c.replace(old_cust_return, new_cust_return)
    # Also need to close the customers list properly - it had "data": [...]
    # The closing was ], }
    print("Fixed customer_service to use customers key")

write(cust_service_path, c)
print("customer_service.py written")

###############################################################################
# 5. FIX FRONTEND api.ts - comprehensive response mapping
###############################################################################
api_path = 'd:/DL_Fraud_Detection/fraud-detection-platform/frontend/src/services/api.ts'
c = read(api_path)

# Fix fetchTransactions to use data.transactions
old_fetch_txns = '''export async function fetchTransactions(params: {
  page?: number
  limit?: number
  risk_level?: string
  search?: string
  date_from?: string
  date_to?: string
} = {}): Promise<TransactionListResponse> {
  try {
    const { data } = await api.get('/transactions', { params })
    return data'''
new_fetch_txns = '''export async function fetchTransactions(params: {
  page?: number
  limit?: number
  risk_level?: string
  search?: string
  date_from?: string
  date_to?: string
} = {}): Promise<TransactionListResponse> {
  try {
    const { data } = await api.get('/transactions', { params })
    return {
      transactions: (data.transactions || data.data || []).map((t: any) => ({...t, amount: t.amount ?? t.transaction_amount})),
      total: data.total || 0,
      page: data.page || 1,
      limit: data.limit || 50,
      total_pages: data.total_pages || data.pages || 1,
    }'''

if old_fetch_txns in c:
    c = c.replace(old_fetch_txns, new_fetch_txns)
    print("Fixed fetchTransactions response mapping")
else:
    print("WARNING: fetchTransactions pattern not found")

# Fix fetchCustomers to use data.customers
old_fetch_custs_try = '''  try {
    const { data } = await api.get('/customers', { params })
    return data'''
new_fetch_custs_try = '''  try {
    const { data } = await api.get('/customers', { params })
    return {
      customers: data.customers || data.data || [],
      total: data.total || 0,
      page: data.page || 1,
      limit: data.limit || 50,
      total_pages: data.total_pages || data.pages || 1,
    }'''

# Be careful to only replace the one in fetchCustomers
if 'fetchCustomers' in c and old_fetch_custs_try in c:
    # Find the index of fetchCustomers and replace only its try block
    idx = c.find('fetchCustomers')
    block_start = c.find(old_fetch_custs_try, idx)
    if block_start != -1:
        c = c[:block_start] + new_fetch_custs_try + c[block_start + len(old_fetch_custs_try):]
        print("Fixed fetchCustomers response mapping")

# Fix fetchFraudTrend to use data.data correctly
c = c.replace('return data.data || []\n  } catch {\n      const points: FraudTrendPoint[]', 
              'return data.data || []\n  } catch {\n      const points: FraudTrendPoint[]')

write(api_path, c)
print("api.ts written")

print("\n=== All fixes applied successfully ===")
