import { useState, useEffect } from 'react'
import { FileText, Download, Loader2, CheckCircle, Clock } from 'lucide-react'
import { generateReport, downloadReportPdf, fetchTransactions } from '../services/api'
import type { Report } from '../types'
import { formatDate } from '../lib/utils'

interface TxnOption {
  id: string
  label: string
}

const DEFAULT_OPTIONS: TxnOption[] = [
  { id: 'TXN0000360089', label: 'TXN0000360089 — $4.03 — Suspicious (34.42) — Mexico City' },
  { id: 'TXN0000211066', label: 'TXN0000211066 — $15.62 — High Risk (80.00) — Melbourne' },
  { id: 'TXN0000042122', label: 'TXN0000042122 — $103.14 — Normal (22.32) — Munich' },
  { id: 'TXN0000408846', label: 'TXN0000408846 — $81.45 — High Risk (80.00) — Toronto' },
  { id: 'TXN0000473328', label: 'TXN0000473328 — $11.11 — Suspicious (31.96) — Tokyo' },
  { id: 'TXN0000119019', label: 'TXN0000119019 — $68.19 — Normal (27.12) — London' },
]

const recentReports: Report[] = [
  {
    report_id: 'SEC-360089',
    transaction_id: 'TXN0000360089',
    generated_at: new Date(Date.now() - 1800000).toISOString(),
    risk_score: 34.42,
    risk_level: 'SUSPICIOUS',
    summary: 'SENTINEL Security Investigation Dossier — TXN0000360089',
    recommendation: 'RECOMMENDED: Secondary authentication & velocity review.',
    full_content: '',
  },
  {
    report_id: 'SEC-211066',
    transaction_id: 'TXN0000211066',
    generated_at: new Date(Date.now() - 7200000).toISOString(),
    risk_score: 80.0,
    risk_level: 'HIGH_RISK',
    summary: 'SENTINEL Security Investigation Dossier — TXN0000211066',
    recommendation: 'ACTION REQUIRED: High fraud probability detected. Immediate account freeze.',
    full_content: '',
  },
  {
    report_id: 'SEC-042122',
    transaction_id: 'TXN0000042122',
    generated_at: new Date(Date.now() - 14400000).toISOString(),
    risk_score: 22.32,
    risk_level: 'NORMAL',
    summary: 'SENTINEL Security Investigation Dossier — TXN0000042122',
    recommendation: 'APPROVED: Transaction cleared through SENTINEL behavioral & ML models.',
    full_content: '',
  },
]

export default function Reports() {
  const [selectedTxn, setSelectedTxn] = useState(DEFAULT_OPTIONS[0].id)
  const [txnOptions, setTxnOptions] = useState<TxnOption[]>(DEFAULT_OPTIONS)
  const [loading, setLoading] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [report, setReport] = useState<Report | null>(null)
  const [reports, setReports] = useState<Report[]>(recentReports)

  useEffect(() => {
    fetchTransactions({ limit: 25 })
      .then(res => {
        if (res.transactions && res.transactions.length > 0) {
          const opts: TxnOption[] = res.transactions.map(t => ({
            id: t.transaction_id,
            label: `${t.transaction_id} — $${Number(t.amount || 0).toFixed(2)} — ${t.risk_level?.replace('_', ' ')} (${Number(t.risk_score || 0).toFixed(2)}) — ${t.city}`,
          }))
          setTxnOptions(opts)
          if (!selectedTxn) setSelectedTxn(opts[0].id)
        }
      })
      .catch(() => {})
  }, [])

  const handleGenerate = async () => {
    if (!selectedTxn) return
    setLoading(true)
    try {
      const r = await generateReport(selectedTxn)
      setReport(r)
      setReports(prev => [r, ...prev.filter(item => item.transaction_id !== r.transaction_id)])
    } finally {
      setLoading(false)
    }
  }

  const handleDownloadPdf = async (transactionId: string) => {
    setDownloading(true)
    try {
      const blob = await downloadReportPdf(transactionId)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `SENTINEL_Investigation_Report_${transactionId}.pdf`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch {
      if (report) {
        const textBlob = new Blob([report.full_content], { type: 'text/plain' })
        const url = URL.createObjectURL(textBlob)
        const a = document.createElement('a')
        a.href = url
        a.download = `SENTINEL-Report-${transactionId}.txt`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
      }
    } finally {
      setDownloading(false)
    }
  }

  const riskLevelStyle = (level: string) => {
    if (level === 'CRITICAL') return 'text-red-400'
    if (level === 'HIGH_RISK') return 'text-orange-400'
    if (level === 'SUSPICIOUS') return 'text-amber-400'
    return 'text-emerald-400'
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 bg-blue-600/10 border border-blue-500/20 rounded-lg flex items-center justify-center">
          <FileText className="text-blue-400" size={18} />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">Investigation Reports</h1>
          <p className="text-slate-400 text-sm">Generate publication-quality PDF audit reports and security dossiers</p>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Generate Report Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-5">
          <h2 className="text-white font-semibold flex items-center justify-between">
            <span>Generate New Report</span>
            <span className="text-xs font-normal text-slate-400">PDF Publication Format</span>
          </h2>

          <div>
            <label className="text-slate-400 text-xs font-medium mb-1.5 block">Select Evaluated Transaction</label>
            <select
              value={selectedTxn}
              onChange={e => setSelectedTxn(e.target.value)}
              className="input-field w-full"
            >
              {txnOptions.map(t => (
                <option key={t.id} value={t.id}>{t.label}</option>
              ))}
            </select>
          </div>

          <div className="flex gap-3">
            <button
              onClick={handleGenerate}
              disabled={!selectedTxn || loading}
              className="btn-primary flex-1 justify-center py-2.5 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <><Loader2 size={16} className="animate-spin" /> Compiling Dossier...</>
              ) : (
                <><FileText size={16} /> View Investigation Summary</>
              )}
            </button>
            <button
              onClick={() => handleDownloadPdf(selectedTxn)}
              disabled={!selectedTxn || downloading}
              className="btn-secondary py-2.5 px-4 flex items-center gap-2 border-blue-500/30 hover:border-blue-500/60 text-blue-400 hover:text-blue-300"
              title="Download publication-ready PDF report directly"
            >
              {downloading ? (
                <Loader2 size={16} className="animate-spin" />
              ) : (
                <Download size={16} />
              )}
              <span>Export PDF</span>
            </button>
          </div>

          {/* Report Preview */}
          {report && (
            <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-emerald-400 text-sm font-medium">
                  <CheckCircle size={14} /> Report Generated Successfully
                </div>
                <button
                  onClick={() => handleDownloadPdf(report.transaction_id)}
                  disabled={downloading}
                  className="btn-secondary text-xs py-1.5 px-3 flex items-center gap-1.5 border-emerald-500/30 text-emerald-400 hover:text-emerald-300"
                >
                  {downloading ? <Loader2 size={12} className="animate-spin" /> : <Download size={12} />}
                  Download Official PDF
                </button>
              </div>
              <div>
                <div className="text-white font-semibold text-sm">{report.summary}</div>
                <div className="text-slate-500 text-xs mt-0.5">{formatDate(report.generated_at)}</div>
              </div>
              <div className="flex items-center gap-3 text-xs">
                <span className={`font-bold ${riskLevelStyle(report.risk_level)}`}>
                  {report.risk_level.replace('_', ' ')} — Score: {Number(report.risk_score).toFixed(2)}/100
                </span>
              </div>
              <div className="bg-slate-900 rounded-lg p-3 border border-slate-800">
                <div className="text-slate-400 text-xs font-medium mb-1">Executive Recommendation</div>
                <div className="text-white text-sm font-medium">{report.recommendation}</div>
              </div>
              <div className="bg-slate-950 rounded-lg p-3 max-h-56 overflow-y-auto border border-slate-800/80">
                <pre className="text-slate-300 text-xs whitespace-pre-wrap font-mono leading-relaxed">
                  {report.full_content}
                </pre>
              </div>
            </div>
          )}
        </div>

        {/* Recent Reports List */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h2 className="text-white font-semibold mb-5 flex items-center justify-between">
            <span>Recent Audit Dossiers</span>
            <span className="text-xs text-slate-500">Live Security Records</span>
          </h2>
          <div className="space-y-3">
            {reports.map(r => (
              <div
                key={r.report_id}
                className="flex items-center justify-between p-3.5 bg-slate-800/50 rounded-xl border border-slate-700/50 hover:border-slate-600 transition-colors cursor-pointer group"
                onClick={() => setReport(r)}
              >
                <div className="flex gap-3 items-center min-w-0">
                  <div className="w-10 h-10 bg-slate-800 border border-slate-700 rounded-lg flex items-center justify-center flex-shrink-0 group-hover:border-blue-500/40">
                    <FileText size={16} className="text-blue-400" />
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-white text-sm font-medium font-mono">{r.transaction_id}</span>
                      <span className={`text-xs font-semibold ${riskLevelStyle(r.risk_level)}`}>
                        Score: {Number(r.risk_score).toFixed(2)}
                      </span>
                    </div>
                    <div className="text-slate-400 text-xs mt-0.5 truncate max-w-xs">{r.recommendation}</div>
                    <div className="text-slate-500 text-xs flex items-center gap-1 mt-1">
                      <Clock size={10} /> {formatDate(r.generated_at)}
                    </div>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={e => {
                    e.stopPropagation()
                    handleDownloadPdf(r.transaction_id)
                  }}
                  className="p-2 text-slate-400 hover:text-white hover:bg-slate-700/60 rounded-lg transition-colors flex-shrink-0 ml-3"
                  title="Download PDF Dossier"
                >
                  <Download size={15} />
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
