import { useParams, useNavigate, Link } from 'react-router-dom'
import { ArrowLeft, ChevronRight } from 'lucide-react'
import {
  ResponsiveContainer, LineChart, Line, BarChart, Bar,
  PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip
} from 'recharts'
import { useCustomer } from '../hooks/useApi'
import { formatCurrency, formatDate, getRiskBadgeClass } from '../lib/utils'

const PIE_COLORS = ['#3b82f6', '#34d399', '#fbbf24', '#f87171', '#a78bfa', '#fb923c']

export default function CustomerProfile() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: customer, loading, error } = useCustomer(id ?? '')

  if (loading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="bg-slate-900 border border-slate-800 rounded-xl p-6 animate-pulse h-40" />
        ))}
      </div>
    )
  }

  if (error || !customer) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <p className="text-white mb-3">Customer not found: {id}</p>
        <button onClick={() => navigate('/customers')} className="btn-primary">Back</button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-slate-400">
        <Link to="/customers" className="hover:text-white transition-colors">Customers</Link>
        <ChevronRight size={14} />
        <span className="text-white font-mono">{customer.customer_id}</span>
      </div>

      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/customers')} className="btn-secondary py-1.5 px-3">
          <ArrowLeft size={14} />
        </button>
        <h1 className="text-xl font-bold text-white font-mono">{customer.customer_id}</h1>
        <span className={getRiskBadgeClass(customer.risk_profile)}>{(customer.risk_profile ?? 'NORMAL').replace('_', ' ')}</span>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-6 gap-4">
        {[
          { label: 'Total Transactions', value: customer.total_transactions.toLocaleString() },
          { label: 'Avg Amount', value: formatCurrency(customer.avg_transaction_amount) },
          { label: 'Fraud Count', value: customer.fraud_count.toString(), red: customer.fraud_count > 0 },
          { label: 'Fraud Rate', value: customer.fraud_rate.toFixed(2) + '%', red: customer.fraud_rate > 0.5 },
          { label: 'Credit Score', value: customer.credit_score.toString() },
          { label: 'Account Age', value: customer.account_age_days + 'd' },
        ].map(stat => (
          <div key={stat.label} className="bg-slate-900 border border-slate-800 rounded-xl p-4">
            <div className="text-slate-400 text-xs mb-1">{stat.label}</div>
            <div className={`text-lg font-bold ${stat.red ? 'text-red-400' : 'text-white'}`}>{stat.value}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Spending over time */}
        <div className="chart-container">
          <h3 className="section-title">Spending Over Time (30 Days)</h3>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={customer.spending_over_time}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 10 }} tickFormatter={v => v.slice(5)} tickLine={false} axisLine={false} />
              <YAxis tick={{ fill: '#64748b', fontSize: 10 }} tickLine={false} axisLine={false} tickFormatter={v => `$${v}`} />
              <Tooltip
                contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 8 }}
                labelStyle={{ color: '#94a3b8' }}
                formatter={(v: any) => [`$${v.toFixed(2)}`, 'Amount']}
              />
              <Line type="monotone" dataKey="amount" stroke="#3b82f6" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Hourly distribution */}
        <div className="chart-container">
          <h3 className="section-title">Transactions by Hour</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={customer.hourly_distribution} margin={{ left: -20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="hour" tick={{ fill: '#64748b', fontSize: 10 }} tickLine={false} axisLine={false} />
              <YAxis tick={{ fill: '#64748b', fontSize: 10 }} tickLine={false} axisLine={false} />
              <Tooltip
                contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 8 }}
                labelStyle={{ color: '#94a3b8' }}
              />
              <Bar dataKey="count" fill="#6366f1" radius={[2, 2, 0, 0]} maxBarSize={20} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Category distribution */}
        <div className="chart-container">
          <h3 className="section-title">Merchant Category Distribution</h3>
          <div className="flex items-center gap-4">
            <ResponsiveContainer width="50%" height={180}>
              <PieChart>
                <Pie data={customer.category_distribution} dataKey="count" cx="50%" cy="50%" outerRadius={70} paddingAngle={3}>
                  {customer.category_distribution.map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 8 }} />
              </PieChart>
            </ResponsiveContainer>
            <div className="flex-1 space-y-2">
              {customer.category_distribution.slice(0, 5).map((cat, i) => (
                <div key={cat.category} className="flex items-center gap-2 text-xs">
                  <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: PIE_COLORS[i % PIE_COLORS.length] }} />
                  <span className="text-slate-400 flex-1 truncate">{cat.category}</span>
                  <span className="text-white font-semibold">{cat.count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Profile info */}
        <div className="chart-container">
          <h3 className="section-title">Behavioral Profile</h3>
          <div className="space-y-3 text-sm">
            {[
              { label: 'Common City', value: customer.common_city },
              { label: 'Common Category', value: customer.common_category },
              { label: 'Common Payment', value: customer.common_payment_method },
              { label: 'Typical Hours', value: customer.typical_hours },
              { label: 'Daily Avg Transactions', value: customer.avg_daily_transactions.toFixed(1) },
              { label: 'Std Dev Amount', value: formatCurrency(customer.std_transaction_amount) },
            ].map(item => (
              <div key={item.label} className="flex justify-between">
                <span className="text-slate-400">{item.label}</span>
                <span className="text-white font-medium">{item.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Transactions */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-800">
          <h3 className="text-white font-semibold">Recent Transactions</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-900">
                {['Transaction ID', 'Amount', 'City', 'Category', 'Time', 'Risk'].map(h => (
                  <th key={h} className="text-left px-4 py-3 text-slate-400 font-medium text-xs">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {customer.transactions.slice(0, 20).map(txn => (
                <tr
                  key={txn.transaction_id}
                  onClick={() => navigate(`/transactions/${txn.transaction_id}`)}
                  className="border-b border-slate-800/50 hover:bg-slate-800/40 cursor-pointer transition-colors"
                >
                  <td className="px-4 py-3 font-mono text-blue-400 text-xs">{txn.transaction_id}</td>
                  <td className="px-4 py-3 text-white font-semibold">{formatCurrency(txn.amount)}</td>
                  <td className="px-4 py-3 text-slate-300">{txn.city}</td>
                  <td className="px-4 py-3 text-slate-400 text-xs">{txn.merchant_category}</td>
                  <td className="px-4 py-3 text-slate-400 text-xs">{formatDate(txn.timestamp)}</td>
                  <td className="px-4 py-3"><span className={getRiskBadgeClass(txn.risk_level)}>{(txn.risk_level ?? 'NORMAL').replace('_', ' ')}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
