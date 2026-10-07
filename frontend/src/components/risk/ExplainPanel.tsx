import { motion } from 'framer-motion'
import type { RiskFactor } from '../../types'

interface ExplainPanelProps {
  factors: RiskFactor[]
  explanation: string
}

const factorColors = (impact: number): { bar: string; text: string; bg: string } => {
  if (impact >= 0.8) return { bar: 'bg-red-500', text: 'text-red-400', bg: 'bg-red-400/10' }
  if (impact >= 0.6) return { bar: 'bg-orange-500', text: 'text-orange-400', bg: 'bg-orange-400/10' }
  if (impact >= 0.4) return { bar: 'bg-amber-500', text: 'text-amber-400', bg: 'bg-amber-400/10' }
  return { bar: 'bg-emerald-500', text: 'text-emerald-400', bg: 'bg-emerald-400/10' }
}

export default function ExplainPanel({ factors, explanation }: ExplainPanelProps) {
  const sorted = [...factors].sort((a, b) => b.impact - a.impact)

  return (
    <div className="space-y-4">
      <h3 className="text-white font-semibold text-sm flex items-center gap-2">
        <span>🔍</span> Why was this flagged?
      </h3>

      <div className="space-y-3">
        {sorted.map((factor, i) => {
          const pct = Math.round(factor.impact * 100)
          const colors = factorColors(factor.impact)
          return (
            <motion.div
              key={factor.name}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.08 }}
              className="space-y-1.5"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-base">{factor.icon ?? '📊'}</span>
                  <span className="text-slate-300 text-sm font-medium">{factor.name}</span>
                </div>
                <span className={`text-xs font-bold ${colors.text}`}>{pct}%</span>
              </div>

              {/* Progress bar */}
              <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${pct}%` }}
                  transition={{ duration: 0.8, delay: i * 0.08, ease: 'easeOut' }}
                  className={`h-full rounded-full ${colors.bar}`}
                />
              </div>

              {/* Description */}
              <p className="text-slate-500 text-xs leading-snug pl-7">{factor.description}</p>
            </motion.div>
          )
        })}
      </div>

      {/* Explanation paragraph */}
      {explanation && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="mt-4 p-4 bg-slate-800/60 rounded-xl border border-slate-700/50"
        >
          <p className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">AI Explanation</p>
          <p className="text-slate-300 text-sm leading-relaxed">{explanation}</p>
        </motion.div>
      )}
    </div>
  )
}
