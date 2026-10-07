import { NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard, Zap, CreditCard, Users, AlertTriangle,
  TrendingUp, MapPin, Brain, FileText, Settings, Shield,
  ChevronLeft, ChevronRight, LogOut
} from 'lucide-react'
import { cn } from '../../lib/utils'
import { useAlerts } from '../../hooks/useApi'

interface SidebarProps {
  collapsed: boolean
  onToggle: () => void
}

const navItems = [
  { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/live-analyzer', icon: Zap, label: 'Live Analyzer', highlight: true },
  { path: '/transactions', icon: CreditCard, label: 'Transactions' },
  { path: '/customers', icon: Users, label: 'Customers' },
  { path: '/alerts', icon: AlertTriangle, label: 'Fraud Alerts', alertBadge: true },
  { path: '/behavior', icon: TrendingUp, label: 'Behavior Analytics' },
  { path: '/geospatial', icon: MapPin, label: 'Geospatial Analysis' },
  { path: '/model', icon: Brain, label: 'Model Monitoring' },
  { path: '/reports', icon: FileText, label: 'Reports' },
]

export default function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const location = useLocation()
  const { data: alerts } = useAlerts()
  const unreadCount = alerts?.filter(a => !a.is_read).length ?? 0

  const handleLogout = () => {
    localStorage.removeItem('sentinel_auth')
    window.location.href = '/login'
  }

  return (
    <aside
      className={cn(
        'fixed left-0 top-0 h-full z-50 flex flex-col bg-slate-900 border-r border-slate-800 transition-all duration-300',
        collapsed ? 'w-16' : 'w-64'
      )}
    >
      {/* Logo */}
      <div className={cn(
        'flex items-center gap-3 px-4 py-5 border-b border-slate-800',
        collapsed && 'justify-center px-0'
      )}>
        <div className="flex-shrink-0 w-9 h-9 bg-blue-600 rounded-lg flex items-center justify-center shadow-lg shadow-blue-600/30">
          <Shield className="w-5 h-5 text-white" />
        </div>
        {!collapsed && (
          <div>
            <div className="text-white font-bold text-lg leading-none tracking-tight">SENTINEL</div>
            <div className="text-slate-500 text-xs mt-0.5">Fraud Detection AI</div>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4 px-2 space-y-1">
        {navItems.map(({ path, icon: Icon, label, highlight, alertBadge }) => {
          const isActive = location.pathname === path || location.pathname.startsWith(path + '/')
          return (
            <NavLink
              key={path}
              to={path}
              className={cn(
                'flex items-center gap-3 rounded-lg transition-all duration-200 relative group',
                collapsed ? 'justify-center p-2.5' : 'px-3 py-2.5',
                isActive
                  ? highlight
                    ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                    : 'bg-slate-800 text-white border border-slate-700'
                  : highlight
                  ? 'text-blue-400 hover:bg-blue-600/10 hover:text-blue-300'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              )}
              title={collapsed ? label : undefined}
            >
              <Icon className={cn('flex-shrink-0', collapsed ? 'w-5 h-5' : 'w-4.5 h-4.5', highlight && 'drop-shadow-[0_0_6px_rgba(96,165,250,0.6)]')} size={18} />
              {!collapsed && (
                <span className="text-sm font-medium">{label}</span>
              )}
              {alertBadge && unreadCount > 0 && (
                <span className={cn(
                  'bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center',
                  collapsed ? 'absolute -top-1 -right-1 w-4 h-4 text-[9px]' : 'ml-auto w-5 h-5'
                )}>
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
              {collapsed && (
                <div className="absolute left-full ml-2 px-2 py-1 bg-slate-800 border border-slate-700 rounded text-white text-xs whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-50">
                  {label}
                </div>
              )}
            </NavLink>
          )
        })}
      </nav>

      {/* Bottom section */}
      <div className="border-t border-slate-800 p-2 space-y-1">
        <NavLink
          to="/settings"
          className={cn(
            'flex items-center gap-3 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-all duration-200',
            collapsed ? 'justify-center p-2.5' : 'px-3 py-2.5'
          )}
          title={collapsed ? 'Settings' : undefined}
        >
          <Settings size={18} />
          {!collapsed && <span className="text-sm font-medium">Settings</span>}
        </NavLink>

        {/* User section */}
        <div className={cn(
          'flex items-center gap-3 rounded-lg px-3 py-2.5',
          collapsed && 'justify-center px-2.5'
        )}>
          <div className="w-7 h-7 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0 text-white text-xs font-bold">
            A
          </div>
          {!collapsed && (
            <div className="flex-1 min-w-0">
              <div className="text-white text-xs font-semibold truncate">Admin User</div>
              <div className="text-slate-500 text-xs truncate">admin@sentinel.ai</div>
            </div>
          )}
          {!collapsed && (
            <button onClick={handleLogout} className="text-slate-500 hover:text-red-400 transition-colors" title="Logout">
              <LogOut size={15} />
            </button>
          )}
        </div>
      </div>

      {/* Collapse toggle */}
      <button
        onClick={onToggle}
        className="absolute -right-3 top-20 w-6 h-6 bg-slate-800 border border-slate-700 rounded-full flex items-center justify-center text-slate-400 hover:text-white hover:bg-slate-700 transition-all z-10"
      >
        {collapsed ? <ChevronRight size={12} /> : <ChevronLeft size={12} />}
      </button>
    </aside>
  )
}
