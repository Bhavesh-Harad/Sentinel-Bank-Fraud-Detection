import { useEffect, useRef } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup, Polyline, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import type { GeoPoint, ImpossibleTravel } from '../../types'
import { formatCurrency } from '../../lib/utils'

// Fix leaflet icon issue
import L from 'leaflet'
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

const riskColor = (level: string) => {
  switch (level?.toUpperCase()) {
    case 'NORMAL': return '#34d399'
    case 'SUSPICIOUS': return '#fbbf24'
    case 'HIGH_RISK': return '#fb923c'
    case 'CRITICAL': return '#f87171'
    default: return '#94a3b8'
  }
}

function FitBounds({ points, impossibleTravel }: { points: GeoPoint[]; impossibleTravel: ImpossibleTravel[] }) {
  const map = useMap()
  useEffect(() => {
    const coords: [number, number][] = []
    points.forEach(p => coords.push([p.lat, p.lng]))
    impossibleTravel.forEach(it => {
      coords.push([it.lat_1, it.lng_1])
      coords.push([it.lat_2, it.lng_2])
    })
    if (coords.length > 0) {
      const bounds = L.latLngBounds(coords)
      map.fitBounds(bounds, { padding: [40, 40] })
    }
  }, [map, points, impossibleTravel])
  return null
}

interface FraudMapProps {
  geoPoints?: GeoPoint[]
  impossibleTravel: ImpossibleTravel[]
  height?: string
}

export default function FraudMap({ geoPoints = [], impossibleTravel = [], height = '530px' }: FraudMapProps) {
  const center: [number, number] = [20, 0]

  return (
    <div style={{ height }} className="rounded-xl overflow-hidden border border-slate-700 shadow-2xl relative">
      <MapContainer
        center={center}
        zoom={2}
        style={{ height: '100%', width: '100%', background: '#1e293b' }}
        zoomControl={true}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          subdomains="abcd"
          maxZoom={20}
        />

        <FitBounds points={geoPoints} impossibleTravel={impossibleTravel} />

        {/* Global Fraud Monitored Cities & Transaction Clusters */}
        {geoPoints.map((point, i) => (
          <CircleMarker
            key={`city-${i}`}
            center={[point.lat, point.lng]}
            radius={Math.max(7, Math.min(22, point.transaction_count / 700))}
            pathOptions={{
              color: riskColor(point.risk_level),
              fillColor: riskColor(point.risk_level),
              fillOpacity: 0.8,
              weight: 2.5,
            }}
          >
            <Popup className="dark-popup">
              <div className="bg-slate-900 text-white p-3 rounded-lg min-w-52 -m-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-bold text-sm">{point.city}, {point.country}</span>
                  <span
                    className="text-[10px] font-bold px-2 py-0.5 rounded-full"
                    style={{
                      color: riskColor(point.risk_level),
                      backgroundColor: `${riskColor(point.risk_level)}20`,
                      border: `1px solid ${riskColor(point.risk_level)}40`,
                    }}
                  >
                    {point.risk_level.replace('_', ' ')}
                  </span>
                </div>
                <div className="space-y-1.5 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Total Transactions:</span>
                    <span className="font-semibold">{point.transaction_count.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Detected Fraud:</span>
                    <span className="text-red-400 font-bold">{point.fraud_count.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Fraud Rate:</span>
                    <span className="text-amber-400 font-semibold">{point.fraud_rate.toFixed(2)}%</span>
                  </div>
                </div>
              </div>
            </Popup>
          </CircleMarker>
        ))}

        {/* Impossible Travel Transaction Routes */}
        {impossibleTravel.map((imp, i) => (
          <Polyline
            key={`route-${i}`}
            positions={[[imp.lat_1, imp.lng_1], [imp.lat_2, imp.lng_2]]}
            pathOptions={{
              color: imp.status === 'IMPOSSIBLE_TRAVEL' ? '#ef4444' : '#f59e0b',
              weight: 3,
              opacity: 0.85,
              dashArray: '8 5',
            }}
          >
            <Popup>
              <div className="bg-slate-900 text-white p-3 rounded-lg min-w-56 -m-3">
                <div className="font-bold text-sm mb-1 text-red-400 flex items-center gap-1.5">
                  <span>{imp.status === 'IMPOSSIBLE_TRAVEL' ? '⚡ IMPOSSIBLE TRAVEL' : '⚠️ Suspicious Route'}</span>
                </div>
                <div className="text-xs text-slate-300 font-semibold mb-2">
                  {imp.city_1} ➔ {imp.city_2}
                </div>
                <div className="space-y-1.5 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Customer ID:</span>
                    <span className="font-mono text-blue-400">{imp.customer_id}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Distance:</span>
                    <span className="font-semibold">{imp.distance_km.toLocaleString()} km</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Time Gap:</span>
                    <span className="font-semibold">{(imp.time_gap_hours * 60).toFixed(0)} min</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Implied Speed:</span>
                    <span className="text-red-400 font-bold">{imp.implied_speed_kmh.toLocaleString()} km/h</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Flagged Amount:</span>
                    <span className="font-semibold text-emerald-400">{formatCurrency(imp.amount_2)}</span>
                  </div>
                </div>
              </div>
            </Popup>
          </Polyline>
        ))}
      </MapContainer>
    </div>
  )
}
