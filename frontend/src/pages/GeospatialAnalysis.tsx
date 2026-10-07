import { MapPin, AlertTriangle, Zap } from 'lucide-react'
import FraudMap from '../components/maps/FraudMap'
import { useGeospatialData, useImpossibleTravel } from '../hooks/useApi'
import { formatCurrency } from '../lib/utils'

const statusBadge = (status: string) => status === 'IMPOSSIBLE_TRAVEL'
  ? 'text-red-400 bg-red-400/10 border border-red-400/30 text-xs font-semibold px-2.5 py-1 rounded-full'
  : 'text-amber-400 bg-amber-400/10 border border-amber-400/30 text-xs font-semibold px-2.5 py-1 rounded-full'

export default function GeospatialAnalysis() {
  const { data: geoPoints, loading: geoLoading } = useGeospatialData()
  const { data: impossibleTravel, loading: itLoading } = useImpossibleTravel()

  const impCount = impossibleTravel?.filter(i => i.status === 'IMPOSSIBLE_TRAVEL').length ?? 0
  const suspCount = impossibleTravel?.filter(i => i.status === 'SUSPICIOUS').length ?? 0

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 bg-emerald-600/10 border border-emerald-500/20 rounded-lg flex items-center justify-center">
          <MapPin className="text-emerald-400" size={18} />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">Geospatial Analysis</h1>
          <p className="text-slate-400 text-sm">Transaction geography, hotspots and impossible travel detection</p>
        </div>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="text-slate-400 text-xs mb-1">Monitored Cities</div>
          <div className="text-white text-2xl font-bold">{geoPoints?.length ?? 0}</div>
        </div>
        <div className="bg-slate-900 border border-red-800/30 rounded-xl p-4">
          <div className="text-red-400 text-xs mb-1">Impossible Travel</div>
          <div className="text-red-400 text-2xl font-bold">{impCount}</div>
        </div>
        <div className="bg-slate-900 border border-amber-800/30 rounded-xl p-4">
          <div className="text-amber-400 text-xs mb-1">Suspicious Routes</div>
          <div className="text-amber-400 text-2xl font-bold">{suspCount}</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="text-slate-400 text-xs mb-1">Critical Cities</div>
          <div className="text-white text-2xl font-bold">{geoPoints?.filter(g => g.risk_level === 'CRITICAL').length ?? 0}</div>
        </div>
      </div>

      {/* Map */}
      {geoLoading || itLoading ? (
        <div className="h-96 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-center">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <FraudMap
          geoPoints={geoPoints ?? []}
          impossibleTravel={impossibleTravel ?? []}
          height="520px"
        />
      )}

      {/* Map legend */}
      <div className="flex flex-wrap items-center gap-5 text-xs bg-slate-900 border border-slate-800 rounded-xl px-4 py-3">
        {[
          { color: '#34d399', label: 'Normal Risk City' },
          { color: '#fbbf24', label: 'Suspicious City' },
          { color: '#fb923c', label: 'High Risk City' },
          { color: '#f87171', label: 'Critical Risk Hotspot' },
        ].map(l => (
          <div key={l.label} className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full" style={{ backgroundColor: l.color }} />
            <span className="text-slate-300">{l.label}</span>
          </div>
        ))}
        <div className="flex items-center gap-1.5">
          <div className="w-7 h-0.5 border-b-2 border-dashed border-red-500" />
          <span className="text-slate-300 font-medium">⚡ Impossible Travel (&gt;900 km/h)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-7 h-0.5 border-b-2 border-dashed border-amber-400" />
          <span className="text-slate-300">⚠️ Suspicious Route</span>
        </div>
      </div>

      {/* Impossible Travel Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-800 flex items-center gap-2">
          <AlertTriangle size={16} className="text-red-400" />
          <h3 className="text-white font-semibold">Impossible Travel Cases</h3>
          <span className="ml-auto text-slate-500 text-sm">{impossibleTravel?.length ?? 0} cases</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-900">
                {['Customer', 'From', 'To', 'Distance', 'Time Gap', 'Implied Speed', 'Amount', 'Status'].map(h => (
                  <th key={h} className="text-left px-4 py-3 text-slate-400 text-xs font-medium whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {(impossibleTravel ?? []).map(imp => (
                <tr key={imp.case_id} className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors">
                  <td className="px-4 py-3 font-mono text-blue-400 text-xs">{imp.customer_id}</td>
                  <td className="px-4 py-3">
                    <div className="text-white text-xs font-medium">{imp.city_1}</div>
                    <div className="text-slate-500 text-xs">{imp.country_1}</div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-white text-xs font-medium">{imp.city_2}</div>
                    <div className="text-slate-500 text-xs">{imp.country_2}</div>
                  </td>
                  <td className="px-4 py-3 text-slate-300 text-xs">{imp.distance_km.toLocaleString()} km</td>
                  <td className="px-4 py-3 text-slate-300 text-xs">{(imp.time_gap_hours * 60).toFixed(0)} min</td>
                  <td className="px-4 py-3">
                    <span className="text-red-400 font-bold text-xs flex items-center gap-1">
                      <Zap size={10} />
                      {imp.implied_speed_kmh.toLocaleString(undefined, { maximumFractionDigits: 0 })} km/h
                    </span>
                  </td>
                  <td className="px-4 py-3 text-white text-xs font-semibold">{formatCurrency(imp.amount_2)}</td>
                  <td className="px-4 py-3">
                    <span className={statusBadge(imp.status)}>{(imp.status ?? 'SUSPICIOUS').replace('_', ' ')}</span>
                  </td>
                </tr>
              ))}
              {(!impossibleTravel || impossibleTravel.length === 0) && (
                <tr>
                  <td colSpan={8} className="text-center py-8 text-slate-500 text-sm">No impossible travel cases detected</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
