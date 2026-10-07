import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, Cell
} from 'recharts'
import { useFraudByCategory } from '../../hooks/useApi'

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  const d = payload[0]?.payload
  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl p-3 shadow-2xl">
      <p className="text-white text-sm font-semibold mb-1">{label}</p>
      <p className="text-red-400 text-xs">Fraud: {d?.fraud_count?.toLocaleString()}</p>
      <p className="text-slate-400 text-xs">Total: {d?.total_count?.toLocaleString()}</p>
      <p className="text-amber-400 text-xs">Rate: {d?.fraud_rate?.toFixed(1)}%</p>
    </div>
  )
}

const rateColor = (rate: number) => {
  if (rate >= 10) return '#f87171'
  if (rate >= 5) return '#fb923c'
  if (rate >= 2) return '#fbbf24'
  return '#34d399'
}

export default function FraudByCategoryChart() {
  const { data, loading } = useFraudByCategory()

  return (
    <div className="chart-container h-full">
      <div className="mb-5">
        <h3 className="text-white font-semibold">Fraud by Category</h3>
        <p className="text-slate-400 text-xs mt-0.5">Fraud count per merchant category</p>
      </div>

      {loading ? (
        <div className="h-64 flex items-center justify-center">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={260}>
          <BarChart
            data={data ?? []}
            layout="vertical"
            margin={{ top: 0, right: 30, left: 10, bottom: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
            <XAxis
              type="number"
              tick={{ fill: '#64748b', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              type="category"
              dataKey="category"
              tick={{ fill: '#94a3b8', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              width={110}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
            <Bar dataKey="fraud_count" name="Fraud Cases" radius={[0, 4, 4, 0]} maxBarSize={18}>
              {(data ?? []).map((entry, i) => (
                <Cell key={i} fill={rateColor(entry.fraud_rate)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
