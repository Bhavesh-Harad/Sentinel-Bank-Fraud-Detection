import { useNavigate } from 'react-router-dom'
import { MapPin, DollarSign, Clock } from 'lucide-react'
import { getRiskBadgeClass, getRiskBgColor, formatCurrency, timeAgo } from '../../lib/utils'
import type { Alert } from '../../types'

interface AlertCardProps {
  alert: Alert
  compact?: boolean
}

export default function AlertCard({ alert, compact = false }: AlertCardProps) {
  const navigate = useNavigate()

  return (
    <button
      onClick={() => navigate(`/transactions/${alert.transaction_id}`)}
      className="w-full text-left flex gap-3 p-3 rounded-xl bg-slate-800/50 hover:bg-slate-800 border border-slate-700/50 hover:border-slate-700 transition-all duration-200 group"
    >
      {/* Risk level indicator bar */}
      <div className={`w-1 flex-shrink-0 rounded-full ${getRiskBgColor(alert.risk_level)}`} />

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1.5">
          <span className={getRiskBadgeClass(alert.risk_level)}>
            {(alert.risk_level ?? 'NORMAL').replace('_', ' ')}
          </span>
          <span className="text-slate-500 text-xs font-mono">{alert.transaction_id}</span>
        </div>

        <p className={`text-slate-300 leading-snug ${compact ? 'text-xs line-clamp-1' : 'text-sm line-clamp-2'} group-hover:text-white transition-colors`}>
          {alert.message}
        </p>

        <div className={`flex items-center gap-3 mt-1.5 text-slate-500 ${compact ? 'text-[10px]' : 'text-xs'}`}>
          <span className="flex items-center gap-1">
            <DollarSign size={10} />
            {formatCurrency(alert.amount)}
          </span>
          <span className="flex items-center gap-1">
            <MapPin size={10} />
            {alert.city}
          </span>
          <span className="flex items-center gap-1 ml-auto">
            <Clock size={10} />
            {timeAgo(alert.timestamp)}
          </span>
        </div>
      </div>
    </button>
  )
}
