import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, PieChart, Pie, Cell, ReferenceLine,
  AreaChart, Area, Legend
} from 'recharts'
import { TrendingUp } from 'lucide-react'
import { useBehaviorAnalytics } from '../hooks/useApi'

const METHOD_COLORS: Record<string, string> = {
  'Credit Card': '#3b82f6',
  'Debit Card': '#34d399',
  'Bank Transfer': '#a78bfa',
  'Crypto': '#f87171',
  'PayPal': '#fbbf24',
  'UPI': '#fb923c',
}

export default function BehaviorAnalytics() {
  const { data, loading } = useBehaviorAnalytics()

  const Spinner = () => (
    <div className="h-48 flex items-center justify-center">
      <div className="w-7 h-7 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
    </div>
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 bg-purple-600/10 border border-purple-500/20 rounded-lg flex items-center justify-center">
          <TrendingUp className="text-purple-400" size={18} />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">Behavior Analytics</h1>
          <p className="text-slate-400 text-sm">Spending patterns, distributions and anomaly analysis</p>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Hourly distribution */}
        <div className="chart-container">
          <h3 className="section-title">Hourly Transaction Volume</h3>
          {loading ? <Spinner /> : (
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={data?.hourly_distribution ?? []}>
                <defs>
                  <linearGradient id="blueGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="hour" tick={{ fill: '#64748b', fontSize: 10 }} tickLine={false} axisLine={false} tickFormatter={h => `${h}:00`} />
                <YAxis tick={{ fill: '#64748b', fontSize: 10 }} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 8 }} labelStyle={{ color: '#94a3b8' }} />
                <ReferenceLine x={9} stroke="#64748b" strokeDasharray="3 3" />
                <ReferenceLine x={18} stroke="#64748b" strokeDasharray="3 3" />
                <Area type="monotone" dataKey="count" stroke="#3b82f6" strokeWidth={2} fill="url(#blueGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Day of week */}
        <div className="chart-container">
          <h3 className="section-title">Day of Week Distribution</h3>
          {loading ? <Spinner /> : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={data?.daily_distribution ?? []} margin={{ left: -20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="day" tick={{ fill: '#64748b', fontSize: 10 }} tickFormatter={d => d.slice(0, 3)} tickLine={false} axisLine={false} />
                <YAxis tick={{ fill: '#64748b', fontSize: 10 }} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 8 }} />
                <Legend formatter={(v) => <span className="text-slate-400 text-xs">{v}</span>} />
                <Bar dataKey="count" name="Transactions" fill="#6366f1" radius={[3, 3, 0, 0]} maxBarSize={36} />
                <Bar dataKey="fraud_count" name="Fraud" fill="#f87171" radius={[3, 3, 0, 0]} maxBarSize={36} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Amount distribution */}
        <div className="chart-container">
          <h3 className="section-title">Amount Distribution vs Fraud</h3>
          {loading ? <Spinner /> : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={data?.amount_distribution ?? []} margin={{ left: -20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="range" tick={{ fill: '#64748b', fontSize: 10 }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fill: '#64748b', fontSize: 10 }} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 8 }} />
                <Legend formatter={(v) => <span className="text-slate-400 text-xs">{v}</span>} />
                <Bar dataKey="count" name="Total" fill="#3b82f6" radius={[3, 3, 0, 0]} maxBarSize={36} />
                <Bar dataKey="fraud_count" name="Fraud" fill="#f87171" radius={[3, 3, 0, 0]} maxBarSize={36} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Payment method distribution */}
        <div className="chart-container">
          <h3 className="section-title">Payment Method Distribution</h3>
          {loading ? <Spinner /> : (
            <div className="flex items-center gap-4">
              <ResponsiveContainer width="55%" height={200}>
                <PieChart>
                  <Pie data={data?.payment_method_dist ?? []} dataKey="count" cx="50%" cy="50%" outerRadius={75} paddingAngle={3}>
                    {(data?.payment_method_dist ?? []).map((entry, i) => (
                      <Cell key={i} fill={METHOD_COLORS[entry.method] ?? '#64748b'} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 8 }} />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex-1 space-y-2">
                {(data?.payment_method_dist ?? []).map(pm => (
                  <div key={pm.method} className="flex items-center gap-2 text-xs">
                    <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: METHOD_COLORS[pm.method] ?? '#64748b' }} />
                    <span className="text-slate-400 flex-1 truncate">{pm.method}</span>
                    <span className="text-white font-semibold">{pm.count.toLocaleString()}</span>
                    <span className="text-red-400 text-[10px]">{pm.fraud_count}⚠</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
