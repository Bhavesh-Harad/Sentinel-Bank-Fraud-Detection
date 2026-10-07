import { DollarSign, AlertTriangle, Shield, TrendingUp, Activity, CreditCard } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import MetricCard from '../components/cards/MetricCard'
import AlertCard from '../components/cards/AlertCard'
import FraudTrendChart from '../components/charts/FraudTrendChart'
import RiskDonut from '../components/charts/RiskDonut'
import FraudByCategoryChart from '../components/charts/FraudByCategoryChart'
import AnomalyHistogram from '../components/charts/AnomalyHistogram'
import { useOverview, useAlerts } from '../hooks/useApi'
import { formatCurrency } from '../lib/utils'

export default function Dashboard() {
  const navigate = useNavigate()
  const { data: overview, loading: overviewLoading } = useOverview()
  const { data: alerts } = useAlerts()

  const metrics = overview ? [
    {
      title: 'Total Transactions',
      value: (overview.total_transactions / 1000).toFixed(1) + 'K',
      icon: CreditCard,
      change: overview.transactions_change,
      color: 'blue' as const,
      subtitle: 'Last 30 days',
    },
    {
      title: 'Transaction Volume',
      value: '$' + (overview.total_volume / 1000000).toFixed(2) + 'M',
      icon: DollarSign,
      change: overview.volume_change,
      color: 'emerald' as const,
      subtitle: 'Total processed',
    },
    {
      title: 'Fraud Alerts',
      value: overview.fraud_alerts.toLocaleString(),
      icon: AlertTriangle,
      change: overview.alerts_change,
      color: 'red' as const,
      subtitle: 'Flagged transactions',
    },
    {
      title: 'High Risk',
      value: overview.high_risk_count.toLocaleString(),
      icon: Shield,
      change: overview.high_risk_change,
      color: 'orange' as const,
      subtitle: 'Requires review',
    },
    {
      title: 'Detection Rate',
      value: overview.detection_rate.toFixed(1) + '%',
      icon: TrendingUp,
      change: overview.detection_change,
      color: 'purple' as const,
      subtitle: 'Model accuracy',
    },
    {
      title: 'Avg Risk Score',
      value: overview.avg_risk_score.toFixed(1),
      icon: Activity,
      change: overview.risk_score_change,
      color: 'slate' as const,
      subtitle: 'System average',
    },
  ] : []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <p className="text-slate-400 text-sm mt-1">Real-time fraud detection overview</p>
      </div>

      {/* KPI Cards */}
      {overviewLoading ? (
        <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="bg-slate-900 border border-slate-800 rounded-xl p-5 h-32 animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
          {metrics.map((m, i) => (
            <MetricCard key={m.title} {...m} index={i} />
          ))}
        </div>
      )}

      {/* Charts + Alert feed */}
      <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
        {/* Main charts area */}
        <div className="xl:col-span-3 space-y-6">
          <FraudTrendChart />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <RiskDonut />
            <FraudByCategoryChart />
          </div>

          <AnomalyHistogram />
        </div>

        {/* Live Alert Feed */}
        <div className="xl:col-span-1">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 h-full">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-white font-semibold text-sm">Live Alerts</h3>
              <button
                onClick={() => navigate('/alerts')}
                className="text-blue-400 hover:text-blue-300 text-xs font-medium transition-colors"
              >
                View all →
              </button>
            </div>

            <div className="space-y-2 overflow-y-auto max-h-[700px] pr-1">
              {(alerts ?? []).map(alert => (
                <AlertCard key={alert.alert_id} alert={alert} compact />
              ))}
              {(!alerts || alerts.length === 0) && (
                <div className="text-center py-8 text-slate-500 text-sm">No alerts</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
