import { motion } from 'framer-motion'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { cn } from '../../lib/utils'

interface MetricCardProps {
  title: string
  value: string | number
  icon: LucideIcon
  change?: number
  changeLabel?: string
  color?: 'blue' | 'emerald' | 'red' | 'orange' | 'purple' | 'slate'
  index?: number
  subtitle?: string
}

const colorMap = {
  blue: {
    icon: 'text-blue-400 bg-blue-400/10',
    bar: 'bg-blue-500',
    glow: 'shadow-blue-500/10',
    change_pos: 'text-blue-400',
  },
  emerald: {
    icon: 'text-emerald-400 bg-emerald-400/10',
    bar: 'bg-emerald-500',
    glow: 'shadow-emerald-500/10',
    change_pos: 'text-emerald-400',
  },
  red: {
    icon: 'text-red-400 bg-red-400/10',
    bar: 'bg-red-500',
    glow: 'shadow-red-500/10',
    change_pos: 'text-red-400',
  },
  orange: {
    icon: 'text-orange-400 bg-orange-400/10',
    bar: 'bg-orange-500',
    glow: 'shadow-orange-500/10',
    change_pos: 'text-orange-400',
  },
  purple: {
    icon: 'text-purple-400 bg-purple-400/10',
    bar: 'bg-purple-500',
    glow: 'shadow-purple-500/10',
    change_pos: 'text-purple-400',
  },
  slate: {
    icon: 'text-slate-400 bg-slate-400/10',
    bar: 'bg-slate-500',
    glow: 'shadow-slate-500/10',
    change_pos: 'text-slate-400',
  },
}

export default function MetricCard({
  title, value, icon: Icon, change, changeLabel, color = 'blue', index = 0, subtitle
}: MetricCardProps) {
  const colors = colorMap[color]
  const isPositive = (change ?? 0) >= 0
  const isZero = change === 0 || change === undefined

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.08 }}
      className={cn('relative bg-slate-900 border border-slate-800 rounded-xl p-5 overflow-hidden shadow-xl', colors.glow)}
    >
      {/* Background glow */}
      <div className={cn('absolute top-0 right-0 w-32 h-32 rounded-full blur-3xl opacity-5', colors.bar)} />

      <div className="relative">
        <div className="flex items-start justify-between mb-4">
          <div className={cn('w-10 h-10 rounded-lg flex items-center justify-center', colors.icon)}>
            <Icon size={20} />
          </div>
          {!isZero && (
            <div className={cn(
              'flex items-center gap-1 text-xs font-semibold px-2 py-1 rounded-full',
              isPositive ? 'bg-emerald-400/10 text-emerald-400' : 'bg-red-400/10 text-red-400'
            )}>
              {isPositive ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
              {isPositive ? '+' : ''}{change?.toFixed(1)}%
            </div>
          )}
          {isZero && (
            <div className="flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-full bg-slate-700 text-slate-400">
              <Minus size={10} />
              0.0%
            </div>
          )}
        </div>

        <div className="text-3xl font-bold text-white mb-1 tabular-nums">{value}</div>
        <div className="text-slate-400 text-sm font-medium">{title}</div>
        {subtitle && <div className="text-slate-500 text-xs mt-0.5">{subtitle}</div>}
        {changeLabel && (
          <div className="text-slate-500 text-xs mt-1">{changeLabel}</div>
        )}
      </div>

      {/* Bottom accent bar */}
      <div className={cn('absolute bottom-0 left-0 right-0 h-0.5', colors.bar)} />
    </motion.div>
  )
}
