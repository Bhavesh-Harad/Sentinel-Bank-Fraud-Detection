import { useState } from 'react'
import { AlertTriangle, CheckCheck, Filter } from 'lucide-react'
import AlertCard from '../components/cards/AlertCard'
import { useAlerts } from '../hooks/useApi'
import { markAlertRead } from '../services/api'

export default function FraudAlerts() {
  const { data: alerts, refetch } = useAlerts()
  const [riskFilter, setRiskFilter] = useState('')
  const [readFilter, setReadFilter] = useState<'all' | 'unread' | 'read'>('all')

  const unread = alerts?.filter(a => !a.is_read).length ?? 0
  const bySeverity = {
    CRITICAL: alerts?.filter(a => a.risk_level === 'CRITICAL').length ?? 0,
    HIGH_RISK: alerts?.filter(a => a.risk_level === 'HIGH_RISK').length ?? 0,
    SUSPICIOUS: alerts?.filter(a => a.risk_level === 'SUSPICIOUS').length ?? 0,
    NORMAL: alerts?.filter(a => a.risk_level === 'NORMAL').length ?? 0,
  }

  const filtered = (alerts ?? []).filter(a => {
    if (riskFilter && a.risk_level !== riskFilter) return false
    if (readFilter === 'unread' && a.is_read) return false
    if (readFilter === 'read' && !a.is_read) return false
    return true
  })

  const handleMarkAllRead = async () => {
    const unreadAlerts = (alerts ?? []).filter(a => !a.is_read)
    for (const a of unreadAlerts) {
      await markAlertRead(a.alert_id)
    }
    refetch()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-red-600/10 border border-red-500/20 rounded-lg flex items-center justify-center">
            <AlertTriangle className="text-red-400" size={18} />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Fraud Alerts</h1>
            <p className="text-slate-400 text-sm">{unread} unread alerts</p>
          </div>
        </div>
        {unread > 0 && (
          <button onClick={handleMarkAllRead} className="btn-secondary text-sm">
            <CheckCheck size={14} /> Mark all read
          </button>
        )}
      </div>

      {/* Severity stats */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: 'Critical', count: bySeverity.CRITICAL, color: 'text-red-400 border-red-400/30 bg-red-400/10' },
          { label: 'High Risk', count: bySeverity.HIGH_RISK, color: 'text-orange-400 border-orange-400/30 bg-orange-400/10' },
          { label: 'Suspicious', count: bySeverity.SUSPICIOUS, color: 'text-amber-400 border-amber-400/30 bg-amber-400/10' },
          { label: 'Normal', count: bySeverity.NORMAL, color: 'text-emerald-400 border-emerald-400/30 bg-emerald-400/10' },
        ].map(s => (
          <div key={s.label} className={`rounded-xl p-4 border ${s.color}`}>
            <div className="text-2xl font-bold">{s.count}</div>
            <div className="text-xs font-medium mt-0.5 opacity-80">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <Filter size={14} className="text-slate-400" />
        <select value={riskFilter} onChange={e => setRiskFilter(e.target.value)} className="input-field w-44">
          <option value="">All Levels</option>
          <option value="CRITICAL">Critical</option>
          <option value="HIGH_RISK">High Risk</option>
          <option value="SUSPICIOUS">Suspicious</option>
          <option value="NORMAL">Normal</option>
        </select>
        <div className="flex bg-slate-800 rounded-lg p-1 gap-1">
          {(['all', 'unread', 'read'] as const).map(f => (
            <button
              key={f}
              onClick={() => setReadFilter(f)}
              className={`px-3 py-1 rounded-md text-xs font-medium transition-all capitalize ${readFilter === f ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'}`}
            >
              {f}
            </button>
          ))}
        </div>
        <span className="text-slate-500 text-sm">{filtered.length} alerts</span>
      </div>

      {/* Alert list */}
      <div className="space-y-2">
        {filtered.length === 0 ? (
          <div className="text-center py-12 text-slate-500">No alerts match your filters</div>
        ) : (
          filtered.map(alert => (
            <div key={alert.alert_id} className={alert.is_read ? 'opacity-60' : ''}>
              <AlertCard alert={alert} />
            </div>
          ))
        )}
      </div>
    </div>
  )
}
