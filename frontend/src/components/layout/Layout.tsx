import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import TopBar from './TopBar'

export default function Layout() {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <div className="min-h-screen bg-slate-950">
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(c => !c)} />
      <TopBar sidebarCollapsed={collapsed} />
      <main
        className={`transition-all duration-300 pt-16 min-h-screen ${collapsed ? 'ml-16' : 'ml-64'}`}
      >
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
