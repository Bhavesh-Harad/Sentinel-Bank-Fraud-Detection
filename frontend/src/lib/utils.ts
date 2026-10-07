import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount)
}

export function formatDate(dateStr: string): string {
  try {
    const date = new Date(dateStr)
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    }).format(date)
  } catch {
    return dateStr
  }
}

export function formatDateShort(dateStr: string): string {
  try {
    const date = new Date(dateStr)
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    }).format(date)
  } catch {
    return dateStr
  }
}

export function timeAgo(dateStr: string): string {
  if (!dateStr) return 'recently'
  try {
    const date = new Date(dateStr)
    if (isNaN(date.getTime())) return 'recently'
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffSecs = Math.floor(diffMs / 1000)
    const diffMins = Math.floor(diffSecs / 60)
    const diffHours = Math.floor(diffMins / 60)
    const diffDays = Math.floor(diffHours / 24)

    if (diffSecs < 60) return `${Math.max(0, diffSecs)}s ago`
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    return `${diffDays}d ago`
  } catch {
    return 'recently'
  }
}

export function getRiskColor(level: string): string {
  const normalized = level?.toLowerCase().replace(/[_\s]/g, '') ?? 'normal'
  switch (normalized) {
    case 'normal': return 'text-emerald-400'
    case 'suspicious': return 'text-amber-400'
    case 'highrisk':
    case 'high': return 'text-orange-400'
    case 'critical': return 'text-red-400'
    default: return 'text-slate-400'
  }
}

export function getRiskBgColor(level: string): string {
  const normalized = level?.toLowerCase().replace(/[_\s]/g, '') ?? 'normal'
  switch (normalized) {
    case 'normal': return 'bg-emerald-500'
    case 'suspicious': return 'bg-amber-500'
    case 'highrisk':
    case 'high': return 'bg-orange-500'
    case 'critical': return 'bg-red-500'
    default: return 'bg-slate-500'
  }
}

export function getRiskBadgeClass(level: string): string {
  const normalized = level?.toLowerCase().replace(/[_\s]/g, '') ?? 'normal'
  switch (normalized) {
    case 'normal': return 'risk-badge-normal'
    case 'suspicious': return 'risk-badge-suspicious'
    case 'highrisk':
    case 'high': return 'risk-badge-high'
    case 'critical': return 'risk-badge-critical'
    default: return 'risk-badge-normal'
  }
}

export function getRiskIcon(level: string): string {
  const normalized = level?.toLowerCase().replace(/[_\s]/g, '') ?? 'normal'
  switch (normalized) {
    case 'normal': return '🟢'
    case 'suspicious': return '🟡'
    case 'highrisk':
    case 'high': return '🟠'
    case 'critical': return '🔴'
    default: return '⚪'
  }
}

export function getRiskGaugeColor(score: number): string {
  if (score <= 30) return '#34d399' // emerald
  if (score <= 60) return '#fbbf24' // amber
  if (score <= 80) return '#fb923c' // orange
  return '#f87171' // red
}

export function getRiskLevelFromScore(score: number): string {
  if (score <= 30) return 'NORMAL'
  if (score <= 60) return 'SUSPICIOUS'
  if (score <= 80) return 'HIGH RISK'
  return 'CRITICAL'
}

export function truncate(str: string, maxLen: number): string {
  if (str.length <= maxLen) return str
  return str.slice(0, maxLen) + '…'
}
