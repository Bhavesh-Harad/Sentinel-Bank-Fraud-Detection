import { useEffect, useRef } from 'react'
import { motion, useMotionValue, useTransform, animate } from 'framer-motion'
import { getRiskGaugeColor, getRiskLevelFromScore } from '../../lib/utils'

interface RiskGaugeProps {
  score: number
  size?: 'sm' | 'md' | 'lg'
}

const sizeMap = {
  sm: { r: 70, cx: 90, cy: 90, viewBox: '0 0 180 100', stroke: 14, fontSize: '1.8rem', labelSize: '0.65rem' },
  md: { r: 90, cx: 115, cy: 115, viewBox: '0 0 230 130', stroke: 18, fontSize: '2.2rem', labelSize: '0.7rem' },
  lg: { r: 110, cx: 140, cy: 140, viewBox: '0 0 280 160', stroke: 22, fontSize: '2.8rem', labelSize: '0.8rem' },
}

export default function RiskGauge({ score, size = 'md' }: RiskGaugeProps) {
  const s = sizeMap[size]
  const circumference = Math.PI * s.r
  const clampedScore = Math.max(0, Math.min(100, score))
  const color = getRiskGaugeColor(clampedScore)
  const level = getRiskLevelFromScore(clampedScore)

  const motionScore = useMotionValue(0)
  const dashOffset = useTransform(
    motionScore,
    [0, 100],
    [circumference, 0]
  )

  const scoreRef = useRef<SVGTextElement>(null)

  useEffect(() => {
    const controls = animate(motionScore, clampedScore, {
      duration: 1.2,
      ease: 'easeOut',
      onUpdate: (v) => {
        if (scoreRef.current) {
          scoreRef.current.textContent = Math.round(v).toString()
        }
      }
    })
    return controls.stop
  }, [clampedScore, motionScore])

  // Color zones for the background arc
  const zones = [
    { start: 0, end: 30, color: '#34d399' },   // emerald
    { start: 30, end: 60, color: '#fbbf24' },  // amber
    { start: 60, end: 80, color: '#fb923c' },  // orange
    { start: 80, end: 100, color: '#f87171' }, // red
  ]

  const getArcPath = (startPct: number, endPct: number, r: number, cx: number, cy: number) => {
    const startAngle = Math.PI * startPct / 100
    const endAngle = Math.PI * endPct / 100
    const x1 = cx - r * Math.cos(startAngle)
    const y1 = cy - r * Math.sin(startAngle)
    const x2 = cx - r * Math.cos(endAngle)
    const y2 = cy - r * Math.sin(endAngle)
    return `M ${x1} ${y1} A ${r} ${r} 0 0 1 ${x2} ${y2}`
  }

  return (
    <div className="flex flex-col items-center">
      <svg viewBox={s.viewBox} className="w-full max-w-xs overflow-visible">
        {/* Background track */}
        <path
          d={`M ${s.cx - s.r} ${s.cy} A ${s.r} ${s.r} 0 0 1 ${s.cx + s.r} ${s.cy}`}
          fill="none"
          stroke="#1e293b"
          strokeWidth={s.stroke}
          strokeLinecap="round"
        />

        {/* Zone arcs */}
        {zones.map((zone, i) => (
          <path
            key={i}
            d={getArcPath(zone.start, zone.end, s.r, s.cx, s.cy)}
            fill="none"
            stroke={zone.color}
            strokeWidth={s.stroke - 4}
            strokeLinecap={i === 0 ? 'round' : i === zones.length - 1 ? 'round' : 'butt'}
            opacity={0.2}
          />
        ))}

        {/* Active fill arc */}
        <motion.path
          d={`M ${s.cx - s.r} ${s.cy} A ${s.r} ${s.r} 0 0 1 ${s.cx + s.r} ${s.cy}`}
          fill="none"
          stroke={color}
          strokeWidth={s.stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          style={{ strokeDashoffset: dashOffset }}
          filter={`drop-shadow(0 0 6px ${color}60)`}
        />

        {/* Score text */}
        <text
          ref={scoreRef}
          x={s.cx}
          y={s.cy - 8}
          textAnchor="middle"
          fill="white"
          style={{ fontSize: s.fontSize, fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}
        >
          0
        </text>

        {/* /100 */}
        <text
          x={s.cx}
          y={s.cy + 12}
          textAnchor="middle"
          fill="#64748b"
          style={{ fontSize: '0.7rem' }}
        >
          / 100
        </text>

        {/* Scale labels */}
        <text x={s.cx - s.r} y={s.cy + 18} textAnchor="middle" fill="#64748b" style={{ fontSize: '0.6rem' }}>0</text>
        <text x={s.cx + s.r} y={s.cy + 18} textAnchor="middle" fill="#64748b" style={{ fontSize: '0.6rem' }}>100</text>
      </svg>

      {/* Risk level label */}
      <motion.div
        initial={{ opacity: 0, y: 5 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8 }}
        className="mt-1 text-center"
      >
        <span
          className="text-xs font-bold tracking-widest uppercase px-3 py-1 rounded-full border"
          style={{ color, borderColor: `${color}40`, backgroundColor: `${color}15` }}
        >
          {level}
        </span>
      </motion.div>
    </div>
  )
}
