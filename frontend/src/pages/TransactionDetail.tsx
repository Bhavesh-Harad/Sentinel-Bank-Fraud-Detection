import { useParams, useNavigate, Link } from 'react-router-dom'
import { ChevronRight, MapPin, CreditCard, Clock, Globe, AlertTriangle, User, ArrowLeft } from 'lucide-react'
import RiskGauge from '../components/risk/RiskGauge'
import ExplainPanel from '../components/risk/ExplainPanel'
import { useTransaction } from '../hooks/useApi'
import { formatCurrency, formatDate, getRiskBadgeClass, getRiskBgColor } from '../lib/utils'

export default function TransactionDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: txn, loading, error } = useTransaction(id ?? '')

  if (loading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="bg-slate-900 border border-slate-800 rounded-xl p-6 animate-pulse h-40" />
        ))}
      </div>
    )
  }

  if (error || !txn) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <AlertTriangle className="text-red-400 mb-3" size={40} />
        <h2 className="text-white font-semibold text-lg">Transaction not found</h2>
        <p className="text-slate-400 text-sm mb-4">{id}</p>
        <button onClick={() => navigate('/transactions')} className="btn-primary">
          Back to Transactions
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-slate-400">
        <Link to="/dashboard" className="hover:text-white transition-colors">Dashboard</Link>
        <ChevronRight size={14} />
        <Link to="/transactions" className="hover:text-white transition-colors">Transactions</Link>
        <ChevronRight size={14} />
        <span className="text-white font-mono">{txn.transaction_id}</span>
      </div>

      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/transactions')} className="btn-secondary py-1.5 px-3">
          <ArrowLeft size={14} />
        </button>
        <h1 className="text-xl font-bold text-white font-mono">{txn.transaction_id}</h1>
        <span className={getRiskBadgeClass(txn.risk_level)}>{(txn.risk_level ?? 'NORMAL').replace('_', ' ')}</span>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Left column */}
        <div className="xl:col-span-2 space-y-6">
          {/* Transaction Info */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <h2 className="text-white font-semibold mb-5 flex items-center gap-2">
              <CreditCard size={16} className="text-blue-400" /> Transaction Details
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-5">
              <div>
                <p className="text-slate-500 text-xs mb-1">Amount</p>
                <p className="text-white text-2xl font-bold tabular-nums">{formatCurrency(txn.amount)}</p>
              </div>
              <div>
                <p className="text-slate-500 text-xs mb-1">Customer</p>
                <Link to={`/customers/${txn.customer_id}`} className="text-blue-400 hover:text-blue-300 font-mono text-sm transition-colors">
                  {txn.customer_id}
                </Link>
              </div>
              <div>
                <p className="text-slate-500 text-xs mb-1">Timestamp</p>
                <p className="text-slate-300 text-sm flex items-center gap-1">
                  <Clock size={12} /> {formatDate(txn.timestamp)}
                </p>
              </div>
              <div>
                <p className="text-slate-500 text-xs mb-1">Merchant Category</p>
                <p className="text-slate-300 text-sm">{txn.merchant_category}</p>
              </div>
              <div>
                <p className="text-slate-500 text-xs mb-1">Payment Method</p>
                <p className="text-slate-300 text-sm">{txn.payment_method}</p>
              </div>
              <div>
                <p className="text-slate-500 text-xs mb-1">Device Type</p>
                <p className="text-slate-300 text-sm">{txn.device_type}</p>
              </div>
              <div>
                <p className="text-slate-500 text-xs mb-1">Location</p>
                <p className="text-slate-300 text-sm flex items-center gap-1">
                  <MapPin size={12} /> {txn.city}, {txn.country}
                </p>
              </div>
              <div>
                <p className="text-slate-500 text-xs mb-1">Status</p>
                <p className="text-slate-300 text-sm">{txn.status}</p>
              </div>
              {txn.is_international && (
                <div>
                  <p className="text-slate-500 text-xs mb-1">International</p>
                  <span className="flex items-center gap-1 text-amber-400 text-sm">
                    <Globe size={12} /> Yes
                  </span>
                </div>
              )}
            </div>

            {/* Feature flags */}
            <div className="mt-5 pt-5 border-t border-slate-800 flex flex-wrap gap-2">
              {txn.is_night_transaction && <span className="bg-slate-800 text-slate-300 text-xs px-2.5 py-1 rounded-full border border-slate-700">🌙 Night Transaction</span>}
              {txn.is_weekend && <span className="bg-slate-800 text-slate-300 text-xs px-2.5 py-1 rounded-full border border-slate-700">📅 Weekend</span>}
              {txn.pin_changed_recently && <span className="bg-amber-400/10 text-amber-400 text-xs px-2.5 py-1 rounded-full border border-amber-400/30">⚠️ PIN Changed</span>}
              {txn.failed_attempts > 0 && <span className="bg-red-400/10 text-red-400 text-xs px-2.5 py-1 rounded-full border border-red-400/30">🔐 {txn.failed_attempts} Failed Attempts</span>}
              {txn.is_international && <span className="bg-orange-400/10 text-orange-400 text-xs px-2.5 py-1 rounded-full border border-orange-400/30">🌍 International</span>}
            </div>
          </div>

          {/* AI Analysis */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <h2 className="text-white font-semibold mb-5 flex items-center gap-2">
              🧠 AI Analysis
            </h2>

            {/* Autoencoder score bar */}
            <div className="mb-5">
              <div className="flex justify-between text-xs mb-1.5">
                <span className="text-slate-400">Autoencoder Anomaly Score</span>
                <span className="text-white font-bold">{(txn.autoencoder_score * 100).toFixed(1)}%</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-2">
                <div
                  className="h-full rounded-full transition-all"
                  style={{
                    width: `${txn.autoencoder_score * 100}%`,
                    backgroundColor: txn.autoencoder_score > 0.8 ? '#f87171' : txn.autoencoder_score > 0.6 ? '#fb923c' : '#3b82f6',
                  }}
                />
              </div>
              <div className="flex justify-between text-xs mt-1 text-slate-600">
                <span>Normal</span>
                <span>Threshold: 42%</span>
                <span>Anomalous</span>
              </div>
            </div>

            <ExplainPanel
              factors={txn.risk_factors ?? []}
              explanation={txn.explanation ?? ''}
            />
          </div>

          {/* Impossible Travel */}
          {txn.impossible_travel && (
            <div className="bg-red-500/5 border border-red-500/30 rounded-xl p-6">
              <h2 className="text-red-400 font-semibold mb-4 flex items-center gap-2">
                <AlertTriangle size={16} /> Impossible Travel Detected
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-slate-900/60 rounded-lg p-3 text-center">
                  <div className="text-slate-400 text-xs mb-1">From</div>
                  <div className="text-white font-semibold">{txn.impossible_travel.city_1}</div>
                  <div className="text-slate-500 text-xs">{txn.impossible_travel.country_1}</div>
                </div>
                <div className="bg-slate-900/60 rounded-lg p-3 text-center">
                  <div className="text-slate-400 text-xs mb-1">To</div>
                  <div className="text-white font-semibold">{txn.impossible_travel.city_2}</div>
                  <div className="text-slate-500 text-xs">{txn.impossible_travel.country_2}</div>
                </div>
                <div className="bg-slate-900/60 rounded-lg p-3 text-center">
                  <div className="text-slate-400 text-xs mb-1">Distance</div>
                  <div className="text-white font-bold">{txn.impossible_travel.distance_km.toLocaleString()} km</div>
                </div>
                <div className="bg-slate-900/60 rounded-lg p-3 text-center">
                  <div className="text-slate-400 text-xs mb-1">Time Gap</div>
                  <div className="text-white font-bold">{(txn.impossible_travel.time_gap_hours * 60).toFixed(0)} min</div>
                </div>
              </div>
              <div className="mt-3 text-center">
                <span className="text-red-400 text-sm font-semibold">
                  Implied Speed: {txn.impossible_travel.implied_speed_kmh.toLocaleString(undefined, { maximumFractionDigits: 0 })} km/h
                </span>
                <span className="text-slate-500 text-xs ml-2">(Max human speed: ~1,200 km/h on commercial aircraft)</span>
              </div>
            </div>
          )}

          {/* Transaction Timeline */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <h2 className="text-white font-semibold mb-5">Transaction Timeline</h2>
            <div className="space-y-3">
              {txn.previous_transaction && (
                <div className="flex gap-4 items-start opacity-60 hover:opacity-100 transition-opacity cursor-pointer" onClick={() => navigate(`/transactions/${txn.previous_transaction!.transaction_id}`)}>
                  <div className="flex flex-col items-center gap-1">
                    <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-xs text-slate-400">
                      ↑
                    </div>
                    <div className="w-0.5 h-8 bg-slate-800" />
                  </div>
                  <div className="flex-1 bg-slate-800/50 rounded-lg p-3">
                    <div className="flex justify-between text-xs text-slate-400 mb-1">
                      <span>Previous Transaction</span>
                      <span>{formatDate(txn.previous_transaction.timestamp)}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-white font-semibold">{formatCurrency(txn.previous_transaction.amount)}</span>
                      <span className="text-slate-400 text-xs">· {txn.previous_transaction.city}</span>
                      <span className={`${getRiskBadgeClass(txn.previous_transaction.risk_level)} ml-auto`}>{(txn.previous_transaction.risk_level ?? 'NORMAL').replace('_', ' ')}</span>
                    </div>
                  </div>
                </div>
              )}

              <div className="flex gap-4 items-start">
                <div className="flex flex-col items-center gap-1">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-xs ${getRiskBgColor(txn.risk_level)}`}>
                    ★
                  </div>
                </div>
                <div className="flex-1 bg-slate-800 border border-slate-700 rounded-lg p-3">
                  <div className="flex justify-between text-xs text-slate-400 mb-1">
                    <span className="text-white font-medium">Current Transaction</span>
                    <span>{formatDate(txn.timestamp)}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-white font-bold text-lg">{formatCurrency(txn.amount)}</span>
                    <span className="text-slate-400 text-xs">· {txn.city}</span>
                    <span className={`${getRiskBadgeClass(txn.risk_level)} ml-auto`}>{(txn.risk_level ?? 'NORMAL').replace('_', ' ')}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right column */}
        <div className="space-y-6">
          {/* Risk Assessment */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <h2 className="text-white font-semibold mb-4">Risk Assessment</h2>
            <RiskGauge score={txn.risk_score} size="md" />
            <div className="mt-4 grid grid-cols-2 gap-3">
              <div className="bg-slate-800 rounded-lg p-3 text-center">
                <div className="text-slate-400 text-xs mb-0.5">Risk Score</div>
                <div className="text-white font-bold text-xl tabular-nums">
                  {typeof txn.risk_score === 'number' ? Number(txn.risk_score).toFixed(2) : txn.risk_score}
                </div>
              </div>
              <div className="bg-slate-800 rounded-lg p-3 text-center">
                <div className="text-slate-400 text-xs mb-0.5">Prediction</div>
                <div className={`font-semibold text-sm ${txn.is_fraud ? 'text-red-400' : 'text-emerald-400'}`}>
                  {txn.is_fraud ? 'FRAUD' : 'LEGIT'}
                </div>
              </div>
            </div>
          </div>

          {/* Customer Context */}
          {txn.customer_profile && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <h2 className="text-white font-semibold mb-4 flex items-center gap-2">
                <User size={16} className="text-blue-400" /> Customer Context
              </h2>
              <Link to={`/customers/${txn.customer_id}`} className="text-blue-400 hover:text-blue-300 text-sm font-mono transition-colors block mb-4">
                {txn.customer_id} →
              </Link>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-400">Avg Transaction</span>
                  <span className="text-white">{formatCurrency(txn.customer_profile.avg_transaction_amount)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Total Transactions</span>
                  <span className="text-white">{txn.customer_profile.total_transactions.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Common City</span>
                  <span className="text-white">{txn.customer_profile.common_city}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Typical Hours</span>
                  <span className="text-white">{txn.customer_profile.typical_hours}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Credit Score</span>
                  <span className={txn.customer_profile.credit_score >= 700 ? 'text-emerald-400' : txn.customer_profile.credit_score >= 600 ? 'text-amber-400' : 'text-red-400'}>
                    {txn.customer_profile.credit_score}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Fraud History</span>
                  <span className={txn.customer_profile.fraud_count > 0 ? 'text-red-400 font-semibold' : 'text-emerald-400'}>
                    {txn.customer_profile.fraud_count} incidents
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">This Amount vs Avg</span>
                  <span className={txn.amount > txn.customer_profile.avg_transaction_amount * 3 ? 'text-red-400 font-bold' : 'text-slate-300'}>
                    {(txn.amount / txn.customer_profile.avg_transaction_amount).toFixed(1)}×
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
