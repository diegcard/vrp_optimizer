import { Outlet, Link, useLocation } from 'react-router-dom'

const navItems = [
  { path: '/', label: 'Dashboard', icon: '📊' },
  { path: '/customers', label: 'Clientes', icon: '📍' },
  { path: '/vehicles', label: 'Vehículos', icon: '🚗' },
  { path: '/optimization', label: 'Optimización', icon: '🛤️' },
  { path: '/training', label: 'Entrenamiento RL', icon: '🤖' },
]

export default function Layout() {
  const location = useLocation()

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-900 text-white">
        <div className="p-4 border-b border-gray-700">
          <h1 className="text-xl font-bold flex items-center gap-2">
            🗺️ VRP Optimizer
          </h1>
          <p className="text-xs text-gray-400 mt-1">
            Optimización de Rutas con RL
          </p>
        </div>
        
        <nav className="p-4">
          <ul className="space-y-2">
            {navItems.map((item) => (
              <li key={item.path}>
                <Link
                  to={item.path}
                  className={`flex items-center gap-3 px-4 py-2 rounded-lg transition-colors ${
                    location.pathname === item.path
                      ? 'bg-primary-600 text-white'
                      : 'text-gray-300 hover:bg-gray-800'
                  }`}
                >
                  <span>{item.icon}</span>
                  <span>{item.label}</span>
                </Link>
              </li>
            ))}
          </ul>
        </nav>
        
        {/* Status */}
        <div className="absolute bottom-0 left-0 w-64 p-4 border-t border-gray-700">
          <div className="flex items-center gap-2 text-sm">
            <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
            <span className="text-gray-400">Sistema activo</span>
          </div>
        </div>
      </aside>
      
      {/* Main content */}
      <main className="flex-1 bg-gray-100">
        <Outlet />
      </main>
    </div>
  )
}
