import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend } from 'recharts'
import { useRiskDistribution } from '../../hooks/useApi'

const COLORS = {
  Normal: '#34d399',
  Suspicious: '#fbbf24',
  'High Risk': '#fb923c',
  Critical: '#f87171',
}

const CustomTooltip = ({ active, payload }: any) => {
  if (!active || !payload?.length || !payload[0]) return null
  const item = payload[0]
  const pct = item?.payload?.pct ?? '0'
  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl p-3 shadow-2xl">
      <p className="text-white text-sm font-semibold">{item.name}</p>
      <p className="text-slate-300 text-xs">{item.value?.toLocaleString() ?? 0} transactions</p>
      <p className="text-slate-400 text-xs">{pct}%</p>
    </div>
  )
}

const CustomLabel = ({ cx, cy, total }: any) => (
  <>
    <text x={cx} y={cy - 8} textAnchor="middle" fill="white" style={{ fontSize: '1.6rem', fontWeight: 700 }}>
      {total?.toLocaleString() ?? '—'}
    </text>
    <text x={cx} y={cy + 14} textAnchor="middle" fill="#64748b" style={{ fontSize: '0.7rem' }}>
      Total
    </text>
  </>
)

export default function RiskDonut() {
  const { data, loading } = useRiskDistribution()

  const total = data?.total || 1
  const chartData = data ? [
    { name: 'Normal', value: data.normal ?? 0, pct: (((data.normal ?? 0) / total) * 100).toFixed(1) },
    { name: 'Suspicious', value: data.suspicious ?? 0, pct: (((data.suspicious ?? 0) / total) * 100).toFixed(1) },
    { name: 'High Risk', value: data.high_risk ?? 0, pct: (((data.high_risk ?? 0) / total) * 100).toFixed(1) },
    { name: 'Critical', value: data.critical ?? 0, pct: (((data.critical ?? 0) / total) * 100).toFixed(1) },
  ] : []

  return (
    <div className="chart-container h-full">
      <div className="mb-5">
        <h3 className="text-white font-semibold">Risk Distribution</h3>
        <p className="text-slate-400 text-xs mt-0.5">Breakdown by risk level</p>
      </div>

      {loading ? (
        <div className="h-52 flex items-center justify-center">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={85}
                paddingAngle={3}
                dataKey="value"
              >
                {chartData.map((entry) => (
                  <Cell key={entry.name} fill={COLORS[entry.name as keyof typeof COLORS]} stroke="transparent" />
                ))}
                <CustomLabel cx="50%" cy="50%" total={data?.total} />
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>

          <div className="grid grid-cols-2 gap-2 mt-2">
            {chartData.map(item => (
              <div key={item.name} className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: COLORS[item.name as keyof typeof COLORS] }} />
                <div className="min-w-0">
                  <span className="text-slate-400 text-xs">{item.name}</span>
                  <span className="text-white text-xs font-semibold ml-2">{item.pct}%</span>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
