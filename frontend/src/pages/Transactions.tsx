import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { CreditCard } from 'lucide-react'
import TransactionTable from '../components/tables/TransactionTable'
import { useTransactions } from '../hooks/useApi'

export default function Transactions() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState(searchParams.get('search') ?? '')
  const [riskFilter, setRiskFilter] = useState(searchParams.get('risk_level') ?? '')

  useEffect(() => {
    const sq = searchParams.get('search')
    if (sq) setSearch(sq)
  }, [searchParams])

  const { data, loading } = useTransactions({
    page,
    limit: 50,
    risk_level: riskFilter || undefined,
    search: search || undefined,
  })

  const handleSearch = (q: string) => {
    setSearch(q)
    setPage(1)
    setSearchParams(q ? { search: q } : {})
  }

  const handleRiskFilter = (level: string) => {
    setRiskFilter(level)
    setPage(1)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 bg-blue-600/10 border border-blue-500/20 rounded-lg flex items-center justify-center">
          <CreditCard className="text-blue-400" size={18} />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">Transactions</h1>
          <p className="text-slate-400 text-sm">Browse and filter all processed transactions</p>
        </div>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <TransactionTable
          transactions={data?.transactions ?? []}
          total={data?.total ?? 0}
          page={page}
          totalPages={data?.total_pages ?? 1}
          loading={loading}
          onPageChange={setPage}
          onSearch={handleSearch}
          onRiskFilter={handleRiskFilter}
          riskFilter={riskFilter}
        />
      </div>
    </div>
  )
}
