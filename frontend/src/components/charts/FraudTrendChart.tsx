import { useState } from 'react'
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend
} from 'recharts'
import { useFraudTrend } from '../../hooks/useApi'
import { format } from 'date-fns'

const periods = [
  { label: '24H', value: '24h' },
  { label: '7D', value: '7d' },
  { label: '30D', value: '30d' },
]

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl p-3 shadow-2xl">
      <p className="text-slate-400 text-xs mb-2">{label}</p>
      {payload.map((entry: any) => (
        <div key={entry.name} className="flex items-center gap-2 text-xs">
          <span className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
          <span className="text-slate-300">{entry.name}:</span>
          <span className="text-white font-semibold">{entry.value?.toLocaleString()}</span>
        </div>
      ))}
    </div>
  )
}

export default function FraudTrendChart() {
  const [period, setPeriod] = useState('24h')
  const { data, loading } = useFraudTrend(period)

  const formatted = (data ?? []).map(d => {
    let label = ''
    try {
      if (d?.timestamp) {
        const dateObj = new Date(d.timestamp)
        if (!isNaN(dateObj.getTime())) {
          label = period === '24h'
            ? format(dateObj, 'HH:mm')
            : format(dateObj, 'MMM dd')
        }
      }
    } catch {
      label = ''
    }
    return {
      ...d,
      total_transactions: d.total_transactions ?? d.transactions ?? 0,
      label,
    }
  })

  return (
    <div className="chart-container">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h3 className="text-white font-semibold">Fraud Trend</h3>
          <p className="text-slate-400 text-xs mt-0.5">Transaction volume vs fraud alerts over time</p>
        </div>
        <div className="flex bg-slate-800 rounded-lg p-1 gap-1">
          {periods.map(p => (
            <button
              key={p.value}
              onClick={() => setPeriod(p.value)}
              className={`px-3 py-1 rounded-md text-xs font-semibold transition-all ${
                period === p.value
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="h-64 flex items-center justify-center">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={formatted} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis
              dataKey="label"
              tick={{ fill: '#64748b', fontSize: 11 }}
              axisLine={{ stroke: '#1e293b' }}
              tickLine={false}
              interval="preserveStartEnd"
            />
            <YAxis
              tick={{ fill: '#64748b', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              formatter={(value) => <span className="text-slate-400 text-xs">{value}</span>}
            />
            <Line
              type="monotone"
              dataKey="total_transactions"
              name="Total Transactions"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={{ r: 3, fill: '#3b82f6' }}
              activeDot={{ r: 5, fill: '#3b82f6' }}
            />
            <Line
              type="monotone"
              dataKey="fraud_alerts"
              name="Fraud Alerts"
              stroke="#f87171"
              strokeWidth={2}
              dot={{ r: 3, fill: '#f87171' }}
              activeDot={{ r: 5, fill: '#f87171' }}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
