
import re

path = 'd:/DL_Fraud_Detection/fraud-detection-platform/frontend/src/services/api.ts'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# 1. fetchFraudTrend -> data.data
c = re.sub(r'(export async function fetchFraudTrend.*?return) data(\n  \} catch \{)', r'\1 data.data || []\2', c, flags=re.DOTALL)

# 2. fetchFraudByCategory -> data.data
c = re.sub(r'(export async function fetchFraudByCategory.*?return) data(\n  \} catch \{)', r'\1 data.data || []\2', c, flags=re.DOTALL)

# 3. fetchAnomalyDistribution -> data.data
c = re.sub(r'(export async function fetchAnomalyDistribution.*?return) data(\n  \} catch \{)', r'\1 data.data || []\2', c, flags=re.DOTALL)

# 4. fetchGeospatialData -> data.data
c = re.sub(r'(export async function fetchGeospatialData.*?return) data(\n  \} catch \{)', r'\1 data.data || []\2', c, flags=re.DOTALL)

# 5. fetchImpossibleTravel -> data.data
c = re.sub(r'(export async function fetchImpossibleTravel.*?return) data(\n  \} catch \{)', r'\1 data.data || []\2', c, flags=re.DOTALL)

# 6. fetchRiskDistribution -> map to object
new_risk = '''export async function fetchRiskDistribution(): Promise<RiskDistribution> {
  try {
    const { data } = await api.get('/analytics/risk-distribution')
    const arr = data.data || []
    return {
      normal: arr.find((x: any) => x.level === 'NORMAL')?.count || 0,
      suspicious: arr.find((x: any) => x.level === 'SUSPICIOUS')?.count || 0,
      high_risk: arr.find((x: any) => x.level === 'HIGH_RISK')?.count || 0,
      critical: arr.find((x: any) => x.level === 'CRITICAL')?.count || 0,
      total: arr.reduce((acc: number, x: any) => acc + (x.count || 0), 0)
    }
  } catch {
    return { normal: 132481, suspicious: 9847, high_risk: 4723, critical: 1341, total: 148392 }
  }
}'''
c = re.sub(r'export async function fetchRiskDistribution.*?catch \{\n.*?\}\n\}', new_risk, c, flags=re.DOTALL)

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)
print('api.ts fixed')

