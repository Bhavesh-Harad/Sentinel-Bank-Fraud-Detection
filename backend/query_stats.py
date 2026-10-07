import sqlite3, json
db = sqlite3.connect('sentinel.db')
db.row_factory = sqlite3.Row
cur = db.cursor()

cur.execute('SELECT COUNT(*) as total, ROUND(SUM(transaction_amount),2) as vol FROM transactions')
t = dict(cur.fetchone())
print('TRANSACTIONS:', json.dumps(t))

cur.execute('SELECT COUNT(*) as total FROM customer_profiles')
print('CUSTOMERS:', cur.fetchone()[0])

cur.execute('SELECT COUNT(*) as total FROM fraud_predictions')
print('PREDICTIONS:', cur.fetchone()[0])

cur.execute('SELECT COUNT(*) as total FROM alerts')
print('ALERTS:', cur.fetchone()[0])

cur.execute('SELECT risk_level, COUNT(*) as cnt FROM fraud_predictions GROUP BY risk_level')
print('RISK_DIST:', json.dumps([dict(r) for r in cur.fetchall()]))

cur.execute('SELECT merchant_category, COUNT(*) as cnt, SUM(CASE WHEN is_fraud=1 THEN 1 ELSE 0 END) as fraud FROM transactions GROUP BY merchant_category ORDER BY fraud DESC LIMIT 6')
print('TOP_FRAUD_CAT:', json.dumps([dict(r) for r in cur.fetchall()]))

cur.execute('SELECT transaction_id, customer_id, city, country, transaction_amount, fraud_type FROM transactions WHERE is_fraud=1 LIMIT 5')
print('FRAUD_SAMPLES:', json.dumps([dict(r) for r in cur.fetchall()]))

cur.execute('SELECT t.transaction_id, t.customer_id, t.city, t.transaction_amount, fp.risk_score, fp.risk_level FROM transactions t JOIN fraud_predictions fp ON t.transaction_id=fp.transaction_id WHERE fp.risk_level="CRITICAL" ORDER BY fp.risk_score DESC LIMIT 5')
print('CRITICAL_TXN:', json.dumps([dict(r) for r in cur.fetchall()]))

cur.execute('SELECT customer_id, total_transactions, ROUND(avg_amount,2) as avg_amount, fraud_count, common_city FROM customer_profiles ORDER BY fraud_count DESC LIMIT 5')
print('TOP_FRAUD_CUSTS:', json.dumps([dict(r) for r in cur.fetchall()]))

cur.execute('SELECT transaction_id, customer_id, risk_level, ROUND(risk_score,1) as risk_score, message, city, ROUND(amount,2) as amount FROM alerts WHERE risk_level="CRITICAL" LIMIT 3')
print('CRITICAL_ALERTS:', json.dumps([dict(r) for r in cur.fetchall()]))

cur.execute('SELECT city, country, latitude, longitude, COUNT(*) as cnt, SUM(CASE WHEN is_fraud=1 THEN 1 ELSE 0 END) as fraud FROM transactions WHERE latitude IS NOT NULL GROUP BY city ORDER BY fraud DESC LIMIT 8')
print('TOP_CITIES:', json.dumps([dict(r) for r in cur.fetchall()]))

cur.execute('SELECT AVG(risk_score) as avg_risk, AVG(anomaly_score) as avg_anomaly FROM fraud_predictions')
print('MODEL_STATS:', json.dumps(dict(cur.fetchone())))

cur.execute('SELECT hour_of_day, COUNT(*) as cnt FROM transactions GROUP BY hour_of_day ORDER BY cnt DESC LIMIT 3')
print('PEAK_HOURS:', json.dumps([dict(r) for r in cur.fetchall()]))

cur.execute('SELECT payment_method, COUNT(*) as cnt FROM transactions GROUP BY payment_method ORDER BY cnt DESC')
print('PAYMENT_METHODS:', json.dumps([dict(r) for r in cur.fetchall()]))

cur.execute('SELECT device_type, COUNT(*) as cnt FROM transactions GROUP BY device_type ORDER BY cnt DESC')
print('DEVICES:', json.dumps([dict(r) for r in cur.fetchall()]))

cur.execute('SELECT country, COUNT(*) as cnt FROM transactions GROUP BY country ORDER BY cnt DESC LIMIT 5')
print('TOP_COUNTRIES:', json.dumps([dict(r) for r in cur.fetchall()]))

cur.execute('SELECT t.customer_id, t.city, t.transaction_amount, t.time_since_last_txn_hrs, t.distance_from_home_km, fp.risk_score FROM transactions t JOIN fraud_predictions fp ON t.transaction_id=fp.transaction_id WHERE t.distance_from_home_km > 1000 AND t.time_since_last_txn_hrs < 1 ORDER BY fp.risk_score DESC LIMIT 3')
print('IMPOSSIBLE_TRAVEL:', json.dumps([dict(r) for r in cur.fetchall()]))
