import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Users, Search, TrendingUp } from 'lucide-react'
import { useCustomers } from '../hooks/useApi'
import { getRiskBadgeClass, formatCurrency } from '../lib/utils'

export default function Customers() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)

  const { data, loading } = useCustomers({ page, limit: 50, search: search || undefined })

  const filtered = (data?.customers ?? []).filter(c =>
    !search || c.customer_id.toLowerCase().includes(search.toLowerCase()) || c.common_city.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 bg-blue-600/10 border border-blue-500/20 rounded-lg flex items-center justify-center">
          <Users className="text-blue-400" size={18} />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">Customers</h1>
          <p className="text-slate-400 text-sm">Customer risk profiles and behavioral analysis</p>
        </div>
      </div>

      {/* Search */}
      <div className="flex gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={14} />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search by customer ID or city..."
            className="input-field pl-9"
          />
        </div>
        <span className="text-slate-500 text-sm self-center">{filtered.length} customers</span>
      </div>

      {/* Customer Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="bg-slate-900 border border-slate-800 rounded-xl p-5 h-48 animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map(customer => (
            <button
              key={customer.customer_id}
              onClick={() => navigate(`/customers/${customer.customer_id}`)}
              className="text-left bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-xl p-5 transition-all duration-200 hover:shadow-xl hover:shadow-black/20 group"
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <div className="text-blue-400 font-mono text-sm font-semibold group-hover:text-blue-300 transition-colors">
                    {customer.customer_id}
                  </div>
                  <div className="text-slate-500 text-xs mt-0.5">{customer.common_city}</div>
                </div>
                <span className={getRiskBadgeClass(customer.risk_profile)}>
                  {(customer.risk_profile ?? 'NORMAL').replace('_', ' ')}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <div className="text-slate-500 mb-0.5">Total Txns</div>
                  <div className="text-white font-semibold">{customer.total_transactions.toLocaleString()}</div>
                </div>
                <div>
                  <div className="text-slate-500 mb-0.5">Avg Amount</div>
                  <div className="text-white font-semibold">{formatCurrency(customer.avg_transaction_amount)}</div>
                </div>
                <div>
                  <div className="text-slate-500 mb-0.5">Fraud Count</div>
                  <div className={customer.fraud_count > 0 ? 'text-red-400 font-bold' : 'text-emerald-400 font-semibold'}>
                    {customer.fraud_count} {customer.fraud_count > 0 ? '⚠️' : '✓'}
                  </div>
                </div>
                <div>
                  <div className="text-slate-500 mb-0.5">Credit Score</div>
                  <div className={customer.credit_score >= 700 ? 'text-emerald-400' : customer.credit_score >= 600 ? 'text-amber-400' : 'text-red-400'}>
                    {customer.credit_score}
                  </div>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-800">
                <div className="flex items-center gap-2 text-xs text-slate-500">
                  <TrendingUp size={10} />
                  <span>{customer.common_category} · {customer.common_payment_method}</span>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
