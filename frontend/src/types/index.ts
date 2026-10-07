// ─── Transaction Types ────────────────────────────────────────────────────────

export interface Transaction {
  transaction_id: string
  customer_id: string
  amount: number
  city: string
  country: string
  merchant_category: string
  payment_method: string
  device_type: string
  timestamp: string
  risk_score: number
  risk_level: string
  is_fraud: boolean
  is_flagged: boolean
  status: string
}

export interface RiskFactor {
  name: string
  value: number
  impact: number
  description: string
  icon?: string
}

export interface TransactionDetail extends Transaction {
  hour_of_day: number
  is_weekend: boolean
  is_night_transaction: boolean
  is_international: boolean
  failed_attempts: number
  pin_changed_recently: boolean
  credit_score: number
  account_balance: number
  distance_from_home_km: number
  time_since_last_txn_hrs: number
  autoencoder_score: number
  reconstruction_error: number
  risk_factors: RiskFactor[]
  explanation: string
  previous_transaction?: Transaction | null
  next_transaction?: Transaction | null
  impossible_travel?: ImpossibleTravel | null
  customer_profile?: CustomerSummary | null
}

export interface TransactionListResponse {
  transactions: Transaction[]
  total: number
  page: number
  limit: number
  total_pages: number
}

// ─── Customer Types ───────────────────────────────────────────────────────────

export interface CustomerSummary {
  customer_id: string
  avg_transaction_amount: number
  std_transaction_amount: number
  total_transactions: number
  fraud_count: number
  fraud_rate: number
  common_city: string
  common_category: string
  common_payment_method: string
  typical_hours: string
  avg_daily_transactions: number
  account_age_days: number
  credit_score: number
  risk_profile: string
}

export interface CustomerProfile extends CustomerSummary {
  transactions: Transaction[]
  spending_over_time: SpendingPoint[]
  hourly_distribution: HourlyPoint[]
  category_distribution: CategoryPoint[]
  location_history: LocationPoint[]
}

export interface SpendingPoint {
  date: string
  amount: number
  count: number
}

export interface HourlyPoint {
  hour: number
  count: number
  avg_amount: number
}

export interface CategoryPoint {
  category: string
  count: number
  total_amount: number
  fraud_count: number
}

export interface LocationPoint {
  city: string
  country: string
  count: number
  lat?: number
  lng?: number
}

export interface CustomerListResponse {
  customers: CustomerSummary[]
  total: number
  page: number
  limit: number
  total_pages: number
}

// ─── Alert Types ──────────────────────────────────────────────────────────────

export interface Alert {
  alert_id: string
  transaction_id: string
  customer_id: string
  amount: number
  city: string
  risk_level: string
  risk_score: number
  message: string
  timestamp: string
  is_read: boolean
  alert_type: string
}

// ─── Analytics Types ──────────────────────────────────────────────────────────

export interface OverviewStats {
  total_transactions: number
  total_volume: number
  fraud_alerts: number
  high_risk_count: number
  detection_rate: number
  avg_risk_score: number
  transactions_change: number
  volume_change: number
  alerts_change: number
  high_risk_change: number
  detection_change: number
  risk_score_change: number
}

export interface FraudTrendPoint {
  timestamp: string
  total_transactions: number
  fraud_alerts: number
  high_risk: number
  normal: number
}

export interface RiskDistribution {
  normal: number
  suspicious: number
  high_risk: number
  critical: number
  total: number
}

export interface CategoryFraud {
  category: string
  fraud_count: number
  total_count: number
  fraud_rate: number
}

export interface AnomalyBin {
  bin_start: number
  bin_end: number
  label: string
  normal_count: number
  anomaly_count: number
}

export interface BehaviorData {
  hourly_distribution: HourlyPoint[]
  daily_distribution: DailyPoint[]
  amount_distribution: AmountBin[]
  payment_method_dist: PaymentMethodPoint[]
}

export interface DailyPoint {
  day: string
  count: number
  fraud_count: number
}

export interface AmountBin {
  range: string
  count: number
  fraud_count: number
}

export interface PaymentMethodPoint {
  method: string
  count: number
  fraud_count: number
}

// ─── Model Types ──────────────────────────────────────────────────────────────

export interface ModelInfo {
  name: string
  version: string
  architecture: string
  input_features: number
  latent_dim: number
  threshold: number
  last_trained: string
  training_samples: number
  validation_samples: number
}

export interface ModelMetrics {
  precision: number
  recall: number
  f1_score: number
  roc_auc: number
  pr_auc: number
  accuracy: number
  false_positive_rate: number
  false_negative_rate: number
  confusion_matrix: number[][]
  labeled_samples: number
}

export interface TrainingEpoch {
  epoch: number
  train_loss: number
  val_loss: number
}

// ─── Geospatial Types ─────────────────────────────────────────────────────────

export interface GeoPoint {
  city: string
  country: string
  lat: number
  lng: number
  transaction_count: number
  fraud_count: number
  fraud_rate: number
  risk_level: string
}

export interface ImpossibleTravel {
  case_id: string
  customer_id: string
  transaction_id_1: string
  transaction_id_2: string
  city_1: string
  city_2: string
  country_1: string
  country_2: string
  lat_1: number
  lng_1: number
  lat_2: number
  lng_2: number
  distance_km: number
  time_gap_hours: number
  implied_speed_kmh: number
  timestamp_1: string
  timestamp_2: string
  amount_1: number
  amount_2: number
  status: string
}

// ─── Analysis Types ───────────────────────────────────────────────────────────

export interface AnalyzeRequest {
  customer_id?: string
  amount: number
  city?: string
  country?: string
  merchant_category?: string
  payment_method?: string
  device_type?: string
  hour_of_day?: number
  is_weekend?: boolean
  is_night_transaction?: boolean
  is_international?: boolean
  failed_attempts?: number
  pin_changed_recently?: boolean
  credit_score?: number
  account_balance?: number
  distance_from_home_km?: number
  time_since_last_txn_hrs?: number
}

export interface AnalyzeResponse {
  transaction_id: string
  risk_score: number
  risk_level: string
  is_fraud: boolean
  prediction_label: string
  autoencoder_score: number
  reconstruction_error: number
  risk_factors: RiskFactor[]
  explanation: string
  impossible_travel?: ImpossibleTravel | null
  timestamp: string
}

// ─── Report Types ─────────────────────────────────────────────────────────────

export interface ReportRequest {
  transaction_id: string
  include_customer_context?: boolean
  include_risk_factors?: boolean
}

export interface Report {
  report_id: string
  transaction_id: string
  generated_at: string
  risk_score: number
  risk_level: string
  summary: string
  recommendation: string
  full_content: string
}
