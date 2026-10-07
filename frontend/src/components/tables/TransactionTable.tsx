import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ChevronUp, ChevronDown, ChevronLeft, ChevronRight,
  Search, ExternalLink
} from 'lucide-react'
import { getRiskBadgeClass, formatCurrency, formatDate } from '../../lib/utils'
import type { Transaction } from '../../types'

interface Column {
  key: keyof Transaction | 'actions'
  label: string
  sortable?: boolean
}

const COLUMNS: Column[] = [
  { key: 'transaction_id', label: 'Transaction ID', sortable: true },
  { key: 'customer_id', label: 'Customer', sortable: true },
  { key: 'amount', label: 'Amount', sortable: true },
  { key: 'city', label: 'City', sortable: true },
  { key: 'merchant_category', label: 'Category', sortable: true },
  { key: 'timestamp', label: 'Time', sortable: true },
  { key: 'risk_score', label: 'Risk Score', sortable: true },
  { key: 'risk_level', label: 'Risk Level', sortable: true },
  { key: 'status', label: 'Status', sortable: false },
  { key: 'actions', label: '', sortable: false },
]

interface TransactionTableProps {
  transactions: Transaction[]
  total: number
  page: number
  totalPages: number
  loading?: boolean
  onPageChange: (page: number) => void
  onSearch?: (q: string) => void
  onRiskFilter?: (level: string) => void
  riskFilter?: string
}

export default function TransactionTable({
  transactions, total, page, totalPages, loading,
  onPageChange, onSearch, onRiskFilter, riskFilter = ''
}: TransactionTableProps) {
  const navigate = useNavigate()
  const [sortKey, setSortKey] = useState<keyof Transaction>('timestamp')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const [search, setSearch] = useState('')

  const handleSort = (key: keyof Transaction) => {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortKey(key); setSortDir('desc') }
  }

  const sorted = useMemo(() => {
    return [...transactions].sort((a, b) => {
      const av = a[sortKey]
      const bv = b[sortKey]
      if (av == null && bv == null) return 0
      if (av == null) return 1
      if (bv == null) return -1
      const cmp = av < bv ? -1 : av > bv ? 1 : 0
      return sortDir === 'asc' ? cmp : -cmp
    })
  }, [transactions, sortKey, sortDir])

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSearch?.(search)
  }

  const statusBadge = (status: string) => {
    const map: Record<string, string> = {
      COMPLETED: 'text-emerald-400 bg-emerald-400/10',
      FLAGGED: 'text-amber-400 bg-amber-400/10',
      BLOCKED: 'text-red-400 bg-red-400/10',
      REVIEW: 'text-orange-400 bg-orange-400/10',
    }
    return map[status] ?? 'text-slate-400 bg-slate-400/10'
  }

  const SortIcon = ({ colKey }: { colKey: keyof Transaction }) => {
    if (sortKey !== colKey) return <ChevronUp size={12} className="text-slate-600" />
    return sortDir === 'asc' ? <ChevronUp size={12} className="text-blue-400" /> : <ChevronDown size={12} className="text-blue-400" />
  }

  return (
    <div className="space-y-4">
      {/* Table controls */}
      <div className="flex items-center gap-3 flex-wrap">
        <form onSubmit={handleSearchSubmit} className="relative flex-1 min-w-48 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={14} />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search ID, customer, city..."
            className="input-field pl-9"
          />
        </form>
        <select
          value={riskFilter}
          onChange={e => onRiskFilter?.(e.target.value)}
          className="input-field w-44"
        >
          <option value="">All Risk Levels</option>
          <option value="NORMAL">Normal</option>
          <option value="SUSPICIOUS">Suspicious</option>
          <option value="HIGH_RISK">High Risk</option>
          <option value="CRITICAL">Critical</option>
        </select>
        <span className="text-slate-500 text-sm ml-auto">{total.toLocaleString()} transactions</span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-xl border border-slate-800">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-900 border-b border-slate-800">
              {COLUMNS.map(col => (
                <th
                  key={col.key}
                  className={`text-left px-4 py-3 text-slate-400 font-medium text-xs whitespace-nowrap ${col.sortable ? 'cursor-pointer select-none hover:text-white' : ''}`}
                  onClick={() => col.sortable && col.key !== 'actions' && handleSort(col.key as keyof Transaction)}
                >
                  <div className="flex items-center gap-1">
                    {col.label}
                    {col.sortable && col.key !== 'actions' && <SortIcon colKey={col.key as keyof Transaction} />}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              Array.from({ length: 8 }).map((_, i) => (
                <tr key={i} className="border-b border-slate-800/50">
                  {COLUMNS.map(col => (
                    <td key={col.key} className="px-4 py-3">
                      <div className="h-4 bg-slate-800 rounded animate-pulse" style={{ width: `${Math.random() * 40 + 60}%` }} />
                    </td>
                  ))}
                </tr>
              ))
            ) : sorted.length === 0 ? (
              <tr>
                <td colSpan={COLUMNS.length} className="text-center py-12 text-slate-500">
                  No transactions found
                </td>
              </tr>
            ) : (
              sorted.map(txn => (
                <tr
                  key={txn.transaction_id}
                  onClick={() => navigate(`/transactions/${txn.transaction_id}`)}
                  className="border-b border-slate-800/50 hover:bg-slate-800/40 cursor-pointer transition-colors group"
                >
                  <td className="px-4 py-3">
                    <span className="font-mono text-blue-400 text-xs group-hover:text-blue-300">
                      {txn.transaction_id}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-slate-300 font-mono text-xs">{txn.customer_id}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-white font-semibold tabular-nums">{formatCurrency(txn.amount)}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-slate-300">{txn.city}</span>
                    <span className="text-slate-600 text-xs ml-1">{txn.country}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-slate-400 text-xs">{txn.merchant_category}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-slate-400 text-xs whitespace-nowrap">{formatDate(txn.timestamp)}</span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-slate-800 rounded-full h-1.5 max-w-16">
                        <div
                          className="h-full rounded-full"
                          style={{
                            width: `${Math.min(100, Math.max(0, txn.risk_score))}%`,
                            backgroundColor: txn.risk_score > 80 ? '#f87171' : txn.risk_score > 60 ? '#fb923c' : txn.risk_score > 30 ? '#fbbf24' : '#34d399'
                          }}
                        />
                      </div>
                      <span className="text-xs font-semibold text-slate-300 tabular-nums min-w-[3rem]">
                        {typeof txn.risk_score === 'number' ? Number(txn.risk_score).toFixed(2) : txn.risk_score}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={getRiskBadgeClass(txn.risk_level)}>
                      {txn.risk_level.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${statusBadge(txn.status)}`}>
                      {txn.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <ExternalLink size={14} className="text-slate-600 group-hover:text-slate-400 transition-colors" />
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <span className="text-slate-500 text-sm">
          Page {page} of {totalPages}
        </span>
        <div className="flex items-center gap-2">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
            className="btn-secondary py-1.5 px-3 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <ChevronLeft size={14} />
          </button>
          {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
            const p = Math.max(1, Math.min(page - 2, totalPages - 4)) + i
            return p <= totalPages ? (
              <button
                key={p}
                onClick={() => onPageChange(p)}
                className={`w-8 h-8 rounded-lg text-sm font-medium transition-colors ${
                  p === page ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800'
                }`}
              >
                {p}
              </button>
            ) : null
          })}
          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages}
            className="btn-secondary py-1.5 px-3 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <ChevronRight size={14} />
          </button>
        </div>
      </div>
    </div>
  )
}
