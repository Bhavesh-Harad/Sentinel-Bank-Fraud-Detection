import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, ReferenceLine
} from 'recharts'
import { useAnomalyDistribution } from '../../hooks/useApi'

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl p-3 shadow-2xl">
      <p className="text-slate-400 text-xs mb-2">Error: {label}</p>
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

interface AnomalyHistogramProps {
  data?: Array<{ label: string; normal_count: number; anomaly_count: number }>
  threshold?: number
  height?: number
}

export default function AnomalyHistogram({ data: propData, threshold = 0.42, height = 240 }: AnomalyHistogramProps) {
  const { data: hookData, loading } = useAnomalyDistribution()
  const data = propData ?? hookData

  return (
    <div className="chart-container">
      <div className="mb-5">
        <h3 className="text-white font-semibold">Anomaly Score Distribution</h3>
        <p className="text-slate-400 text-xs mt-0.5">Autoencoder reconstruction error — normal vs anomalous transactions</p>
      </div>

      {loading && !propData ? (
        <div className="flex items-center justify-center" style={{ height }}>
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={height}>
          <BarChart data={data ?? []} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis
              dataKey="label"
              tick={{ fill: '#64748b', fontSize: 10 }}
              axisLine={{ stroke: '#1e293b' }}
              tickLine={false}
            />
            <YAxis
              tick={{ fill: '#64748b', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
            <Legend
              formatter={(value) => <span className="text-slate-400 text-xs">{value}</span>}
            />
            <ReferenceLine
              x={`${threshold}-${threshold + 0.1}`}
              stroke="#fbbf24"
              strokeDasharray="4 4"
              label={{ value: `Threshold: ${threshold}`, position: 'top', fill: '#fbbf24', fontSize: 10 }}
            />
            <Bar dataKey="normal_count" name="Normal" fill="#3b82f6" opacity={0.8} radius={[2, 2, 0, 0]} maxBarSize={28} />
            <Bar dataKey="anomaly_count" name="Anomalous" fill="#f87171" opacity={0.9} radius={[2, 2, 0, 0]} maxBarSize={28} />
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
