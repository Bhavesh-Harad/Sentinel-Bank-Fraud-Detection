import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Bell, Search, ChevronDown, Wifi, WifiOff, RefreshCw } from 'lucide-react'
import { useAlerts } from '../../hooks/useApi'
import { getRiskBadgeClass, timeAgo } from '../../lib/utils'

interface TopBarProps {
  sidebarCollapsed: boolean
}

export default function TopBar({ sidebarCollapsed }: TopBarProps) {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [showNotifications, setShowNotifications] = useState(false)
  const [showUserMenu, setShowUserMenu] = useState(false)
  const [isOnline] = useState(true)
  const { data: alerts, refetch } = useAlerts()
  const unreadAlerts = alerts?.filter(a => !a.is_read) ?? []

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (search.trim()) {
      navigate(`/transactions?search=${encodeURIComponent(search)}`)
      setSearch('')
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('sentinel_auth')
    window.location.href = '/login'
  }

  return (
    <header className={`fixed top-0 right-0 z-40 h-16 bg-slate-900/95 backdrop-blur-sm border-b border-slate-800 flex items-center px-5 gap-4 transition-all duration-300 ${sidebarCollapsed ? 'left-16' : 'left-64'}`}>
      {/* Search */}
      <form onSubmit={handleSearch} className="flex-1 max-w-md">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search transactions, customers..."
            className="w-full bg-slate-800 border border-slate-700 text-white placeholder:text-slate-500 rounded-lg pl-9 pr-4 py-2 text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
          />
        </div>
      </form>

      <div className="flex items-center gap-3 ml-auto">
        {/* System status */}
        <div className="flex items-center gap-2 text-xs font-medium px-3 py-1.5 rounded-full bg-slate-800 border border-slate-700">
          {isOnline ? (
            <>
              <Wifi size={12} className="text-emerald-400" />
              <span className="text-emerald-400">System Online</span>
            </>
          ) : (
            <>
              <WifiOff size={12} className="text-red-400" />
              <span className="text-red-400">Offline Mode</span>
            </>
          )}
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
        </div>

        {/* Refresh */}
        <button
          onClick={refetch}
          className="w-9 h-9 flex items-center justify-center text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
          title="Refresh data"
        >
          <RefreshCw size={16} />
        </button>

        {/* Notifications */}
        <div className="relative">
          <button
            onClick={() => { setShowNotifications(!showNotifications); setShowUserMenu(false) }}
            className="w-9 h-9 flex items-center justify-center text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors relative"
          >
            <Bell size={18} />
            {unreadAlerts.length > 0 && (
              <span className="absolute top-1 right-1 w-4 h-4 bg-red-500 text-white text-[9px] font-bold rounded-full flex items-center justify-center">
                {unreadAlerts.length > 9 ? '9+' : unreadAlerts.length}
              </span>
            )}
          </button>

          {showNotifications && (
            <div className="absolute right-0 top-full mt-2 w-80 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl shadow-black/40 z-50 overflow-hidden">
              <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
                <span className="text-white font-semibold text-sm">Notifications</span>
                <span className="text-xs text-slate-400">{unreadAlerts.length} unread</span>
              </div>
              <div className="max-h-80 overflow-y-auto">
                {unreadAlerts.length === 0 ? (
                  <div className="p-4 text-center text-slate-500 text-sm">No unread notifications</div>
                ) : unreadAlerts.slice(0, 5).map(alert => (
                  <button
                    key={alert.alert_id}
                    onClick={() => { navigate(`/transactions/${alert.transaction_id}`); setShowNotifications(false) }}
                    className="w-full text-left px-4 py-3 hover:bg-slate-800 transition-colors border-b border-slate-800/50 last:border-0"
                  >
                    <div className="flex items-start gap-3">
                      <span className={getRiskBadgeClass(alert.risk_level)}>{(alert.risk_level ?? 'NORMAL').replace('_', ' ')}</span>
                      <div className="flex-1 min-w-0">
                        <p className="text-white text-xs font-medium truncate">{alert.message}</p>
                        <p className="text-slate-500 text-xs mt-0.5">{timeAgo(alert.timestamp)}</p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
              <button
                onClick={() => { navigate('/alerts'); setShowNotifications(false) }}
                className="w-full text-center text-blue-400 hover:text-blue-300 text-xs font-medium py-3 border-t border-slate-800 transition-colors"
              >
                View all alerts
              </button>
            </div>
          )}
        </div>

        {/* User menu */}
        <div className="relative">
          <button
            onClick={() => { setShowUserMenu(!showUserMenu); setShowNotifications(false) }}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-slate-800 transition-colors"
          >
            <div className="w-7 h-7 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white text-xs font-bold">
              A
            </div>
            <span className="text-white text-sm font-medium">Admin</span>
            <ChevronDown size={14} className="text-slate-400" />
          </button>

          {showUserMenu && (
            <div className="absolute right-0 top-full mt-2 w-44 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl shadow-black/40 z-50 overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-800">
                <div className="text-white text-sm font-medium">Admin User</div>
                <div className="text-slate-400 text-xs">admin@sentinel.ai</div>
              </div>
              <div className="p-1">
                <button className="w-full text-left px-3 py-2 text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg text-sm transition-colors">
                  Profile Settings
                </button>
                <button
                  onClick={handleLogout}
                  className="w-full text-left px-3 py-2 text-red-400 hover:text-red-300 hover:bg-red-400/10 rounded-lg text-sm transition-colors"
                >
                  Sign Out
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Overlay to close dropdowns */}
      {(showNotifications || showUserMenu) && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => { setShowNotifications(false); setShowUserMenu(false) }}
        />
      )}
    </header>
  )
}
