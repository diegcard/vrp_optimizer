import { Outlet, Link, useLocation } from 'react-router-dom'
import { useHealth } from '../hooks/useApi'

const navItems = [
  { path: '/', label: 'Dashboard', icon: '📊' },
  { path: '/customers', label: 'Clientes', icon: '📍' },
  { path: '/vehicles', label: 'Vehículos', icon: '🚗' },
  { path: '/optimization', label: 'Optimización', icon: '🛤️' },
  { path: '/training', label: 'Entrenamiento RL', icon: '🤖' },
]

export default function Layout() {
  const location = useLocation()
  const { data: health } = useHealth()

  return (
    <div className="min-h-screen flex bg-gray-50">
      {/* Sidebar */}
      <aside className="w-64 bg-gradient-to-b from-gray-900 to-gray-800 text-white shadow-xl flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-gray-700/50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-600 rounded-lg flex items-center justify-center text-xl font-bold shadow-lg">
              🗺️
            </div>
            <div>
              <h1 className="text-lg font-bold">VRP Optimizer</h1>
              <p className="text-xs text-gray-400">Sistema de Optimización</p>
            </div>
          </div>
        </div>
        
        {/* Navigation */}
        <nav className="flex-1 p-4 overflow-y-auto">
          <ul className="space-y-1">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path
              return (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    className={`
                      flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200
                      ${isActive
                        ? 'bg-primary-600 text-white shadow-lg shadow-primary-500/30'
                        : 'text-gray-300 hover:bg-gray-800/50 hover:text-white'
                      }
                    `}
                  >
                    <span className="text-lg">{item.icon}</span>
                    <span className="font-medium">{item.label}</span>
                    {isActive && (
                      <span className="ml-auto w-2 h-2 bg-white rounded-full"></span>
                    )}
                  </Link>
                </li>
              )
            })}
          </ul>
        </nav>
        
        {/* Status Footer */}
        <div className="p-4 border-t border-gray-700/50">
          <div className="flex items-center gap-2 text-sm">
            <div className={`w-2 h-2 rounded-full ${
              health?.status === 'healthy' 
                ? 'bg-success-500 animate-pulse' 
                : 'bg-danger-500'
            }`}></div>
            <span className="text-gray-400">
              {health?.status === 'healthy' ? 'Sistema operativo' : 'Sistema con problemas'}
            </span>
          </div>
        </div>
      </aside>
      
      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}
