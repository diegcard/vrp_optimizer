import { useEffect, useRef } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Legend } from 'recharts'
import { useSystemMetrics, useCustomers, useVehicles, useRoutes, useHealth } from '../hooks/useApi'
import MapView from '../components/MapView'
import { useAppStore } from '../store/appStore'
import Card from '../components/ui/Card'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import Badge from '../components/ui/Badge'

export default function Dashboard() {
  const { data: health, isLoading: healthLoading } = useHealth()
  const { data: customers = [], isLoading: customersLoading } = useCustomers()
  const { data: vehicles = [], isLoading: vehiclesLoading } = useVehicles()
  const { data: routes = [] } = useRoutes()
  const { data: metrics } = useSystemMetrics()
  
  const { mapCenter, mapZoom, setCustomers, setVehicles, setRoutes } = useAppStore()
  
  // Usar refs para evitar bucle infinito
  const customersRef = useRef(customers)
  const vehiclesRef = useRef(vehicles)
  const routesRef = useRef(routes)
  
  useEffect(() => {
    // Solo actualizar si los datos realmente cambiaron
    if (customers.length > 0 && JSON.stringify(customers) !== JSON.stringify(customersRef.current)) {
      customersRef.current = customers
      setCustomers(customers)
    }
  }, [customers, setCustomers])
  
  useEffect(() => {
    if (vehicles.length > 0 && JSON.stringify(vehicles) !== JSON.stringify(vehiclesRef.current)) {
      vehiclesRef.current = vehicles
      setVehicles(vehicles)
    }
  }, [vehicles, setVehicles])
  
  useEffect(() => {
    if (routes.length > 0 && JSON.stringify(routes) !== JSON.stringify(routesRef.current)) {
      routesRef.current = routes
      setRoutes(routes)
    }
  }, [routes, setRoutes])
  
  const stats = [
    { 
      label: 'Clientes', 
      value: customers.length, 
      icon: '📍', 
      color: 'bg-primary-500',
      bgColor: 'bg-primary-100'
    },
    { 
      label: 'Vehículos', 
      value: vehicles.length, 
      icon: '🚗', 
      color: 'bg-success-500',
      bgColor: 'bg-success-100'
    },
    { 
      label: 'Rutas Activas', 
      value: routes.length, 
      icon: '🛤️', 
      color: 'bg-warning-500',
      bgColor: 'bg-warning-100'
    },
    { 
      label: 'Entregas Hoy', 
      value: metrics?.total_deliveries_today || 0, 
      icon: '📦', 
      color: 'bg-purple-500',
      bgColor: 'bg-purple-100'
    },
  ]
  
  // Datos de ejemplo para gráficos
  const performanceData = [
    { name: '00:00', latencia: 45, optimizaciones: 12 },
    { name: '04:00', latencia: 38, optimizaciones: 8 },
    { name: '08:00', latencia: 120, optimizaciones: 45 },
    { name: '12:00', latencia: 89, optimizaciones: 67 },
    { name: '16:00', latencia: 95, optimizaciones: 54 },
    { name: '20:00', latencia: 55, optimizaciones: 23 },
  ]
  
  const routeStats = [
    { name: 'Lunes', distancia: 156 },
    { name: 'Martes', distancia: 189 },
    { name: 'Miércoles', distancia: 145 },
    { name: 'Jueves', distancia: 178 },
    { name: 'Viernes', distancia: 210 },
    { name: 'Sábado', distancia: 95 },
    { name: 'Domingo', distancia: 45 },
  ]
  
  if (healthLoading || customersLoading || vehiclesLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <LoadingSpinner size="lg" />
      </div>
    )
  }
  
  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500 mt-1">Sistema de Optimización de Rutas VRP</p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant={health?.status === 'healthy' ? 'success' : 'danger'}>
            {health?.status === 'healthy' ? '✓ Operativo' : '✗ Con problemas'}
          </Badge>
        </div>
      </div>
      
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <Card key={stat.label} hover>
            <div className="flex items-center gap-4">
              <div className={`${stat.bgColor} w-14 h-14 rounded-xl flex items-center justify-center text-2xl shadow-sm`}>
                {stat.icon}
              </div>
              <div>
                <p className="text-3xl font-bold text-gray-900">{stat.value}</p>
                <p className="text-sm text-gray-500 font-medium">{stat.label}</p>
              </div>
            </div>
          </Card>
        ))}
      </div>
      
      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Map */}
        <Card className="lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Mapa de Rutas - Bogotá</h2>
            {routes.length > 0 && (
              <Badge variant="primary">{routes.length} ruta(s) activa(s)</Badge>
            )}
          </div>
          <div className="h-96 rounded-lg overflow-hidden">
            <MapView
              customers={customers.map(c => ({
                ...c,
                location: { lat: c.location?.lat || 4.65, lon: c.location?.lon || -74.05 }
              }))}
              depot={{ lat: 4.6577, lon: -74.0553 }}
              routes={routes}
              center={mapCenter}
              zoom={mapZoom}
            />
          </div>
        </Card>
        
        {/* System Status */}
        <Card>
          <h2 className="text-lg font-semibold mb-4 text-gray-900">Estado del Sistema</h2>
          <div className="space-y-4">
            <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-600">Latencia API</span>
                <span className="text-lg font-bold text-gray-900">{metrics?.api_latency_ms || 0} ms</span>
              </div>
              <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                <div 
                  className={`h-full rounded-full transition-all ${
                    (metrics?.api_latency_ms || 0) < 100 ? 'bg-success-500' :
                    (metrics?.api_latency_ms || 0) < 300 ? 'bg-warning-500' : 'bg-danger-500'
                  }`}
                  style={{ width: `${Math.min((metrics?.api_latency_ms || 0) / 5, 100)}%` }}
                ></div>
              </div>
            </div>
            
            <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-600">CPU</span>
                <span className="text-lg font-bold text-gray-900">{metrics?.cpu_usage || 0}%</span>
              </div>
              <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                <div 
                  className={`h-full rounded-full transition-all ${
                    (metrics?.cpu_usage || 0) < 50 ? 'bg-success-500' :
                    (metrics?.cpu_usage || 0) < 80 ? 'bg-warning-500' : 'bg-danger-500'
                  }`}
                  style={{ width: `${metrics?.cpu_usage || 0}%` }}
                ></div>
              </div>
            </div>
            
            <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-600">Memoria</span>
                <span className="text-lg font-bold text-gray-900">{metrics?.memory_usage || 0}%</span>
              </div>
              <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                <div 
                  className={`h-full rounded-full transition-all ${
                    (metrics?.memory_usage || 0) < 70 ? 'bg-success-500' :
                    (metrics?.memory_usage || 0) < 90 ? 'bg-warning-500' : 'bg-danger-500'
                  }`}
                  style={{ width: `${metrics?.memory_usage || 0}%` }}
                ></div>
              </div>
            </div>
            
            <div className="p-4 bg-primary-50 rounded-lg border border-primary-200">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium text-primary-700">Distancia Total Hoy</span>
                <span className="text-xl font-bold text-primary-900">{metrics?.total_distance_today || 0} km</span>
              </div>
            </div>
          </div>
        </Card>
      </div>
      
      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Performance Chart */}
        <Card>
          <h2 className="text-lg font-semibold mb-4 text-gray-900">Rendimiento del Sistema</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="name" stroke="#6b7280" />
                <YAxis stroke="#6b7280" />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'white', 
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                  }}
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="latencia" 
                  stroke="#3b82f6" 
                  strokeWidth={2}
                  name="Latencia (ms)"
                  dot={false}
                />
                <Line 
                  type="monotone" 
                  dataKey="optimizaciones" 
                  stroke="#10b981" 
                  strokeWidth={2}
                  name="Optimizaciones"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>
        
        {/* Route Stats Chart */}
        <Card>
          <h2 className="text-lg font-semibold mb-4 text-gray-900">Distancia por Día (km)</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={routeStats}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="name" stroke="#6b7280" />
                <YAxis stroke="#6b7280" />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'white', 
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                  }}
                />
                <Bar 
                  dataKey="distancia" 
                  fill="#8b5cf6" 
                  name="Distancia (km)"
                  radius={[8, 8, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>
    </div>
  )
}
