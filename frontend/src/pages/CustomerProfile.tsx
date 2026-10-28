import { useParams, useNavigate, Link } from 'react-router-dom'
import { ArrowLeft, ChevronRight, TrendingUp, Clock, Tag, User } from 'lucide-react'
import {
  ResponsiveContainer, LineChart, Line, BarChart, Bar,
  PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip
} from 'recharts'
import { useCustomer } from '../hooks/useApi'
import { formatCurrency, formatDate, getRiskBadgeClass } from '../lib/utils'

const PIE_COLORS = ['#3b82f6', '#34d399', '#fbbf24', '#f87171', '#a78bfa', '#fb923c']

function EmptyChart({ label }: { label: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-[220px] text-slate-500 text-sm">
      <span className="text-2xl mb-2">📊</span>
      <span>No {label} data available</span>
    </div>
  )
}

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
        <p className="text-slate-400 text-sm mb-4">{error}</p>
        <button onClick={() => navigate('/customers')} className="btn-primary">Back to Customers</button>
      </div>
    )
  }

  // Determine the date range label from real historical data
  const dateRangeLabel = customer.date_range
    ? `All Transactions (${customer.date_range})`
    : 'All Transactions (Historical Dataset 2020–2024)'

  // For the X-axis: if many data points, sample every Nth for readability
  const spendingData = customer.spending_over_time ?? []
  const hasSpendingData = spendingData.length > 0
  const hourlyData = customer.hourly_distribution ?? []
  const hasHourlyData = hourlyData.some(h => h.count > 0)
  const categoryData = customer.category_distribution ?? []
  const hasCategoryData = categoryData.length > 0

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
          { label: 'Active Days', value: customer.account_age_days + 'd' },
        ].map(stat => (
          <div key={stat.label} className="bg-slate-900 border border-slate-800 rounded-xl p-4">
            <div className="text-slate-400 text-xs mb-1">{stat.label}</div>
            <div className={`text-lg font-bold ${stat.red ? 'text-red-400' : 'text-white'}`}>{stat.value}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Spending over time — from real historical dataset */}
        <div className="chart-container">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp size={16} className="text-blue-400" />
            <h3 className="section-title mb-0">Spending Over Time</h3>
          </div>
          <p className="text-xs text-slate-500 mb-3">{dateRangeLabel}</p>
          {hasSpendingData ? (
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={spendingData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis
                  dataKey="date"
                  tick={{ fill: '#64748b', fontSize: 10 }}
                  tickFormatter={v => v.slice(0, 7)} /* Show YYYY-MM */
                  interval={Math.max(1, Math.floor(spendingData.length / 8))}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  tick={{ fill: '#64748b', fontSize: 10 }}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={v => `$${v}`}
                />
                <Tooltip
                  contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 8 }}
                  labelStyle={{ color: '#94a3b8' }}
                  formatter={(v: any) => [`$${Number(v).toFixed(2)}`, 'Daily Total']}
                />
                <Line type="monotone" dataKey="amount" stroke="#3b82f6" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <EmptyChart label="spending" />
          )}
        </div>

        {/* Hourly distribution */}
        <div className="chart-container">
          <div className="flex items-center gap-2 mb-3">
            <Clock size={16} className="text-indigo-400" />
            <h3 className="section-title mb-0">Transactions by Hour of Day</h3>
          </div>
          <p className="text-xs text-slate-500 mb-3">Aggregated across all historical transactions</p>
          {hasHourlyData ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={hourlyData} margin={{ left: -20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="hour" tick={{ fill: '#64748b', fontSize: 10 }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fill: '#64748b', fontSize: 10 }} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 8 }}
                  labelStyle={{ color: '#94a3b8' }}
                  formatter={(v: any, name: string) => [v, name === 'count' ? 'Transactions' : 'Avg Amount']}
                />
                <Bar dataKey="count" fill="#6366f1" radius={[2, 2, 0, 0]} maxBarSize={20} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <EmptyChart label="hourly" />
          )}
        </div>

        {/* Category distribution */}
        <div className="chart-container">
          <div className="flex items-center gap-2 mb-3">
            <Tag size={16} className="text-amber-400" />
            <h3 className="section-title mb-0">Merchant Category Distribution</h3>
          </div>
          <p className="text-xs text-slate-500 mb-3">Aggregated across all historical transactions</p>
          {hasCategoryData ? (
            <div className="flex items-center gap-4">
              <ResponsiveContainer width="50%" height={180}>
                <PieChart>
                  <Pie data={categoryData} dataKey="count" cx="50%" cy="50%" outerRadius={70} paddingAngle={3}>
                    {categoryData.map((_, i) => (
                      <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 8 }} />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex-1 space-y-2">
                {categoryData.slice(0, 6).map((cat, i) => (
                  <div key={cat.category} className="flex items-center gap-2 text-xs">
                    <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: PIE_COLORS[i % PIE_COLORS.length] }} />
                    <span className="text-slate-400 flex-1 truncate">{cat.category}</span>
                    <span className="text-white font-semibold">{cat.count.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <EmptyChart label="category" />
          )}
        </div>

        {/* Profile info */}
        <div className="chart-container">
          <div className="flex items-center gap-2 mb-3">
            <User size={16} className="text-green-400" />
            <h3 className="section-title mb-0">Behavioral Profile</h3>
          </div>
          <p className="text-xs text-slate-500 mb-3">Derived from complete transaction history</p>
          <div className="space-y-3 text-sm">
            {[
              { label: 'Common City', value: customer.common_city },
              { label: 'Common Category', value: customer.common_category },
              { label: 'Common Payment', value: customer.common_payment_method },
              { label: 'Typical Hour', value: customer.typical_hours },
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
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-white font-semibold">Recent Transactions</h3>
          <span className="text-slate-500 text-xs">Last 20 (most recent first)</span>
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
              {(customer.transactions ?? []).length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-10 text-slate-500">No recent transactions found</td>
                </tr>
              ) : (
                customer.transactions.slice(0, 20).map(txn => (
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
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
