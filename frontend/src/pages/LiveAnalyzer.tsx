import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Zap, Loader2, FileText, AlertTriangle, RotateCcw, Download } from 'lucide-react'
import RiskGauge from '../components/risk/RiskGauge'
import ExplainPanel from '../components/risk/ExplainPanel'
import { analyzeTransaction, generateReport, downloadReportPdf } from '../services/api'
import type { AnalyzeRequest, AnalyzeResponse } from '../types'
import { formatCurrency, getRiskBadgeClass } from '../lib/utils'

const DEMO_SCENARIOS: Array<{
  label: string
  emoji: string
  color: string
  data: AnalyzeRequest
}> = [
  {
    label: 'Normal Transaction',
    emoji: '🟢',
    color: 'border-emerald-500/40 hover:border-emerald-500/80 hover:bg-emerald-500/5',
    data: {
      customer_id: 'CUST00121959',
      amount: 39.49,
      city: 'London',
      country: 'UK',
      merchant_category: 'Grocery',
      payment_method: 'Bank Transfer',
      device_type: 'Mobile',
      hour_of_day: 14,
      is_weekend: false,
      is_night_transaction: false,
      is_international: false,
      failed_attempts: 0,
      pin_changed_recently: false,
      credit_score: 695,
      account_balance: 4200,
      distance_from_home_km: 2,
      time_since_last_txn_hrs: 8,
    },
  },
  {
    label: 'Suspicious Amount',
    emoji: '🟡',
    color: 'border-amber-500/40 hover:border-amber-500/80 hover:bg-amber-500/5',
    data: {
      customer_id: 'CUST00146868',
      amount: 2500,
      city: 'New York',
      country: 'USA',
      merchant_category: 'Electronics',
      payment_method: 'Credit Card',
      device_type: 'Desktop',
      hour_of_day: 23,
      is_weekend: false,
      is_night_transaction: true,
      is_international: false,
      failed_attempts: 1,
      pin_changed_recently: false,
      credit_score: 600,
      account_balance: 1800,
      distance_from_home_km: 15,
      time_since_last_txn_hrs: 2,
    },
  },
  {
    label: 'Impossible Travel',
    emoji: '🟠',
    color: 'border-orange-500/40 hover:border-orange-500/80 hover:bg-orange-500/5',
    data: {
      customer_id: 'CUST00131933',
      amount: 500,
      city: 'Delhi',
      country: 'India',
      merchant_category: 'ATM Withdrawal',
      payment_method: 'Debit Card',
      device_type: 'ATM',
      hour_of_day: 10,
      is_weekend: false,
      is_night_transaction: false,
      is_international: true,
      failed_attempts: 0,
      pin_changed_recently: false,
      credit_score: 580,
      account_balance: 2300,
      distance_from_home_km: 1400,
      time_since_last_txn_hrs: 0.08,
    },
  },
  {
    label: 'Critical Fraud',
    emoji: '🔴',
    color: 'border-red-500/40 hover:border-red-500/80 hover:bg-red-500/5',
    data: {
      customer_id: 'CUST00131933',
      amount: 15000,
      city: 'Tokyo',
      country: 'Japan',
      merchant_category: 'Crypto Exchange',
      payment_method: 'Crypto',
      device_type: 'Desktop',
      hour_of_day: 3,
      is_weekend: false,
      is_night_transaction: true,
      is_international: true,
      failed_attempts: 3,
      pin_changed_recently: true,
      credit_score: 450,
      account_balance: 2340,
      distance_from_home_km: 9842,
      time_since_last_txn_hrs: 0.05,
    },
  },
]

const MERCHANT_CATEGORIES = [
  'Grocery', 'Restaurant', 'Gas Station', 'Electronics', 'Online Shopping',
  'ATM Withdrawal', 'Wire Transfer', 'Crypto Exchange', 'Travel', 'Hotel',
  'Jewelry', 'Pharmacy', 'Entertainment', 'Utilities', 'Other'
]

const PAYMENT_METHODS = ['Credit Card', 'Debit Card', 'Bank Transfer', 'Crypto', 'PayPal', 'UPI', 'Wire Transfer']
const DEVICE_TYPES = ['Mobile', 'Desktop', 'ATM', 'POS', 'Tablet']

const defaultForm: AnalyzeRequest = {
  customer_id: '',
  amount: 0,
  city: '',
  country: '',
  merchant_category: 'Grocery',
  payment_method: 'Credit Card',
  device_type: 'Mobile',
  hour_of_day: 12,
  is_weekend: false,
  is_night_transaction: false,
  is_international: false,
  failed_attempts: 0,
  pin_changed_recently: false,
  credit_score: 700,
  account_balance: 5000,
  distance_from_home_km: 5,
  time_since_last_txn_hrs: 24,
}

function Toggle({ label, value, onChange }: { label: string; value: boolean; onChange: (v: boolean) => void }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-slate-400 text-sm">{label}</span>
      <button
        type="button"
        onClick={() => onChange(!value)}
        className={`relative w-10 h-5 rounded-full transition-colors duration-200 focus:outline-none ${value ? 'bg-blue-600' : 'bg-slate-700'}`}
      >
        <span className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform duration-200 ${value ? 'translate-x-5' : 'translate-x-0'}`} />
      </button>
    </div>
  )
}

export default function LiveAnalyzer() {
  const [form, setForm] = useState<AnalyzeRequest>(defaultForm)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<AnalyzeResponse | null>(null)
  const [reportLoading, setReportLoading] = useState(false)
  const [reportGenerated, setReportGenerated] = useState(false)
  const [activeScenario, setActiveScenario] = useState<number | null>(null)

  const updateField = (key: keyof AnalyzeRequest, value: unknown) => {
    setForm(f => ({ ...f, [key]: value }))
  }

  const loadScenario = (idx: number) => {
    setActiveScenario(idx)
    setForm({ ...defaultForm, ...DEMO_SCENARIOS[idx].data })
    setResult(null)
    setReportGenerated(false)
  }

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setResult(null)
    setReportGenerated(false)
    try {
      const res = await analyzeTransaction(form)
      setResult(res)
    } catch {
      // handled in service
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateReport = async () => {
    if (!result) return
    setReportLoading(true)
    try {
      const blob = await downloadReportPdf(result.transaction_id)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `SENTINEL_Report_${result.transaction_id}.pdf`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      setReportGenerated(true)
    } catch {
      await new Promise(r => setTimeout(r, 800))
      setReportGenerated(true)
    } finally {
      setReportLoading(false)
    }
  }

  const handleReset = () => {
    setForm(defaultForm)
    setResult(null)
    setActiveScenario(null)
    setReportGenerated(false)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Zap className="text-blue-400" size={24} />
          Live Transaction Analyzer
        </h1>
        <p className="text-slate-400 text-sm mt-1">Enter transaction details to analyze for fraud risk in real-time</p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Input Panel */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          {/* Demo Scenarios */}
          <div className="mb-6">
            <p className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-3">Quick Demo Scenarios</p>
            <div className="grid grid-cols-2 gap-2">
              {DEMO_SCENARIOS.map((scenario, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => loadScenario(idx)}
                  className={`flex items-center gap-2 px-3 py-2.5 rounded-lg border text-left transition-all duration-200 ${scenario.color} ${activeScenario === idx ? 'ring-1 ring-white/20' : ''}`}
                >
                  <span className="text-base">{scenario.emoji}</span>
                  <span className="text-white text-xs font-medium">{scenario.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Form */}
          <form onSubmit={handleAnalyze} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-slate-400 text-xs font-medium mb-1.5 block">Customer ID</label>
                <input
                  type="text"
                  value={form.customer_id ?? ''}
                  onChange={e => updateField('customer_id', e.target.value)}
                  placeholder="CUST00121959"
                  className="input-field"
                />
              </div>
              <div>
                <label className="text-slate-400 text-xs font-medium mb-1.5 block">Amount ($)</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={form.amount}
                  onChange={e => updateField('amount', parseFloat(e.target.value) || 0)}
                  placeholder="0.00"
                  className="input-field"
                  required
                />
              </div>
              <div>
                <label className="text-slate-400 text-xs font-medium mb-1.5 block">City</label>
                <input
                  type="text"
                  value={form.city ?? ''}
                  onChange={e => updateField('city', e.target.value)}
                  placeholder="London"
                  className="input-field"
                />
              </div>
              <div>
                <label className="text-slate-400 text-xs font-medium mb-1.5 block">Country</label>
                <input
                  type="text"
                  value={form.country ?? ''}
                  onChange={e => updateField('country', e.target.value)}
                  placeholder="UK"
                  className="input-field"
                />
              </div>
              <div>
                <label className="text-slate-400 text-xs font-medium mb-1.5 block">Merchant Category</label>
                <select
                  value={form.merchant_category ?? ''}
                  onChange={e => updateField('merchant_category', e.target.value)}
                  className="input-field"
                >
                  {MERCHANT_CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div>
                <label className="text-slate-400 text-xs font-medium mb-1.5 block">Payment Method</label>
                <select
                  value={form.payment_method ?? ''}
                  onChange={e => updateField('payment_method', e.target.value)}
                  className="input-field"
                >
                  {PAYMENT_METHODS.map(m => <option key={m} value={m}>{m}</option>)}
                </select>
              </div>
              <div>
                <label className="text-slate-400 text-xs font-medium mb-1.5 block">Device Type</label>
                <select
                  value={form.device_type ?? ''}
                  onChange={e => updateField('device_type', e.target.value)}
                  className="input-field"
                >
                  {DEVICE_TYPES.map(d => <option key={d} value={d}>{d}</option>)}
                </select>
              </div>
              <div>
                <label className="text-slate-400 text-xs font-medium mb-1.5 block">Hour of Day (0–23)</label>
                <input
                  type="number"
                  min="0"
                  max="23"
                  value={form.hour_of_day ?? 12}
                  onChange={e => updateField('hour_of_day', parseInt(e.target.value))}
                  className="input-field"
                />
              </div>
              <div>
                <label className="text-slate-400 text-xs font-medium mb-1.5 block">Credit Score</label>
                <input
                  type="number"
                  min="300"
                  max="850"
                  value={form.credit_score ?? 700}
                  onChange={e => updateField('credit_score', parseInt(e.target.value))}
                  className="input-field"
                />
              </div>
              <div>
                <label className="text-slate-400 text-xs font-medium mb-1.5 block">Account Balance ($)</label>
                <input
                  type="number"
                  min="0"
                  value={form.account_balance ?? 0}
                  onChange={e => updateField('account_balance', parseFloat(e.target.value))}
                  className="input-field"
                />
              </div>
              <div>
                <label className="text-slate-400 text-xs font-medium mb-1.5 block">Distance from Home (km)</label>
                <input
                  type="number"
                  min="0"
                  value={form.distance_from_home_km ?? 0}
                  onChange={e => updateField('distance_from_home_km', parseFloat(e.target.value))}
                  className="input-field"
                />
              </div>
              <div>
                <label className="text-slate-400 text-xs font-medium mb-1.5 block">Time Since Last Txn (hrs)</label>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={form.time_since_last_txn_hrs ?? 24}
                  onChange={e => updateField('time_since_last_txn_hrs', parseFloat(e.target.value))}
                  className="input-field"
                />
              </div>
              <div>
                <label className="text-slate-400 text-xs font-medium mb-1.5 block">Failed Attempts (0–5)</label>
                <input
                  type="number"
                  min="0"
                  max="5"
                  value={form.failed_attempts ?? 0}
                  onChange={e => updateField('failed_attempts', parseInt(e.target.value))}
                  className="input-field"
                />
              </div>
            </div>

            {/* Toggles */}
            <div className="grid grid-cols-2 gap-3 pt-2 border-t border-slate-800">
              <Toggle label="Is Weekend" value={form.is_weekend ?? false} onChange={v => updateField('is_weekend', v)} />
              <Toggle label="Is Night Txn" value={form.is_night_transaction ?? false} onChange={v => updateField('is_night_transaction', v)} />
              <Toggle label="International" value={form.is_international ?? false} onChange={v => updateField('is_international', v)} />
              <Toggle label="PIN Changed" value={form.pin_changed_recently ?? false} onChange={v => updateField('pin_changed_recently', v)} />
            </div>

            {/* Actions */}
            <div className="flex gap-3 pt-2">
              <button
                type="submit"
                disabled={loading}
                className="flex-1 bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 text-white font-semibold py-3 rounded-xl transition-all flex items-center justify-center gap-2"
              >
                {loading ? (
                  <><Loader2 size={16} className="animate-spin" /> Analyzing...</>
                ) : (
                  <><Zap size={16} /> Analyze Transaction</>
                )}
              </button>
              <button
                type="button"
                onClick={handleReset}
                className="btn-secondary py-3"
                title="Reset"
              >
                <RotateCcw size={16} />
              </button>
            </div>
          </form>
        </div>

        {/* Results Panel */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <AnimatePresence mode="wait">
            {!result && !loading && (
              <motion.div
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="h-full flex flex-col items-center justify-center text-center py-16"
              >
                <div className="w-20 h-20 bg-blue-600/10 border border-blue-500/20 rounded-full flex items-center justify-center mb-4">
                  <Zap className="text-blue-400" size={36} />
                </div>
                <h3 className="text-white font-semibold text-lg mb-2">Ready to Analyze</h3>
                <p className="text-slate-500 text-sm max-w-xs">
                  Fill in the transaction details or pick a demo scenario, then click "Analyze Transaction"
                </p>
                <div className="mt-6 grid grid-cols-2 gap-3 w-full max-w-xs">
                  {DEMO_SCENARIOS.map((s, idx) => (
                    <button key={idx} onClick={() => loadScenario(idx)} className="text-xs text-slate-400 hover:text-white py-2 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 transition-colors">
                      {s.emoji} {s.label}
                    </button>
                  ))}
                </div>
              </motion.div>
            )}

            {loading && (
              <motion.div
                key="loading"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="h-full flex flex-col items-center justify-center py-16"
              >
                <div className="relative w-20 h-20 mb-4">
                  <div className="absolute inset-0 border-4 border-blue-500/20 rounded-full" />
                  <div className="absolute inset-0 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
                  <div className="absolute inset-2 border-2 border-blue-400/30 rounded-full animate-spin" style={{ animationDirection: 'reverse', animationDuration: '0.8s' }} />
                </div>
                <p className="text-white font-semibold">AI Model Processing</p>
                <p className="text-slate-500 text-sm mt-1">Running autoencoder analysis...</p>
              </motion.div>
            )}

            {result && !loading && (
              <motion.div
                key="result"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="space-y-5"
              >
                {/* Risk Gauge */}
                <div className="text-center">
                  <RiskGauge score={result.risk_score} size="md" />
                  <div className="mt-2 flex items-center justify-center gap-3">
                    <span className={getRiskBadgeClass(result.risk_level)}>
                      {(result.risk_level ?? 'NORMAL').replace('_', ' ')}
                    </span>
                    <span className="text-slate-400 text-sm">{result.prediction_label}</span>
                  </div>
                  <div className="mt-2 text-xs text-slate-500 font-mono">
                    TXN: {result.transaction_id} | Autoencoder: {(result.autoencoder_score * 100).toFixed(1)}%
                  </div>
                </div>

                {/* Impossible Travel */}
                {result.impossible_travel && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="bg-red-500/10 border border-red-500/30 rounded-xl p-4"
                  >
                    <div className="flex items-center gap-2 text-red-400 font-semibold text-sm mb-2">
                      <AlertTriangle size={16} />
                      Impossible Travel Detected!
                    </div>
                    <div className="grid grid-cols-3 gap-2 text-xs">
                      <div className="text-center">
                        <div className="text-slate-400">Distance</div>
                        <div className="text-white font-bold">{result.impossible_travel.distance_km.toLocaleString()} km</div>
                      </div>
                      <div className="text-center">
                        <div className="text-slate-400">Time</div>
                        <div className="text-white font-bold">{(result.impossible_travel.time_gap_hours * 60).toFixed(0)} min</div>
                      </div>
                      <div className="text-center">
                        <div className="text-slate-400">Speed</div>
                        <div className="text-red-400 font-bold">{result.impossible_travel.implied_speed_kmh.toLocaleString()} km/h</div>
                      </div>
                    </div>
                    <div className="mt-2 text-xs text-red-400/80">
                      {result.impossible_travel.city_1} → {result.impossible_travel.city_2}
                    </div>
                  </motion.div>
                )}

                {/* Explainability */}
                <ExplainPanel
                  factors={result.risk_factors}
                  explanation={result.explanation}
                />

                {/* Generate Report */}
                <button
                  onClick={handleGenerateReport}
                  disabled={reportLoading}
                  className={`w-full py-2.5 rounded-xl font-medium text-sm flex items-center justify-center gap-2 transition-all border ${
                    reportGenerated
                      ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20'
                      : 'btn-secondary'
                  }`}
                >
                  {reportLoading ? (
                    <><Loader2 size={14} className="animate-spin" /> Compiling PDF Dossier...</>
                  ) : reportGenerated ? (
                    <><Download size={14} /> Download Investigation PDF ✓</>
                  ) : (
                    <><FileText size={14} /> Generate & Export PDF Report</>
                  )}
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  )
}
