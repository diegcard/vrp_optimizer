import { useEffect, useCallback, useRef } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'
import { useSystemMetrics, useCustomers, useVehicles, useRoutes, useHealth } from '../hooks/useApi'
import MapView from '../components/MapView'
import { useAppStore } from '../store/appStore'

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
      color: 'bg-blue-500' 
    },
    { 
      label: 'Vehículos', 
      value: vehicles.length, 
      icon: '🚗', 
      color: 'bg-green-500' 
    },
    { 
      label: 'Rutas Activas', 
      value: routes.length, 
      icon: '🛤️', 
      color: 'bg-yellow-500' 
    },
    { 
      label: 'Entregas Hoy', 
      value: metrics?.total_deliveries_today || 0, 
      icon: '📦', 
      color: 'bg-purple-500' 
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
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }
  
  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500">Sistema de Optimización de Rutas VRP</p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`w-3 h-3 rounded-full ${health?.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'}`}></span>
          <span className="text-sm text-gray-600">
            {health?.status === 'healthy' ? 'Sistema operativo' : 'Sistema con problemas'}
          </span>
        </div>
      </div>
      
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <div 
            key={stat.label}
            className="bg-white rounded-xl shadow-sm p-6 flex items-center gap-4"
          >
            <div className={`${stat.color} w-12 h-12 rounded-lg flex items-center justify-center text-2xl`}>
              {stat.icon}
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
              <p className="text-sm text-gray-500">{stat.label}</p>
            </div>
          </div>
        ))}
      </div>
      
      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Map */}
        <div className="lg:col-span-2 bg-white rounded-xl shadow-sm p-4">
          <h2 className="text-lg font-semibold mb-4">Mapa de Rutas - Bogotá</h2>
          <div className="h-96">
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
        </div>
        
        {/* System Status */}
        <div className="bg-white rounded-xl shadow-sm p-4">
          <h2 className="text-lg font-semibold mb-4">Estado del Sistema</h2>
          <div className="space-y-4">
            <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
              <span className="text-gray-600">Latencia API</span>
              <span className="font-semibold">{metrics?.api_latency_ms || 0} ms</span>
            </div>
            <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
              <span className="text-gray-600">CPU</span>
              <div className="flex items-center gap-2">
                <div className="w-24 h-2 bg-gray-200 rounded-full">
                  <div 
                    className="h-2 bg-primary-500 rounded-full" 
                    style={{ width: `${metrics?.cpu_usage || 0}%` }}
                  ></div>
                </div>
                <span className="font-semibold">{metrics?.cpu_usage || 0}%</span>
              </div>
            </div>
            <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
              <span className="text-gray-600">Memoria</span>
              <div className="flex items-center gap-2">
                <div className="w-24 h-2 bg-gray-200 rounded-full">
                  <div 
                    className="h-2 bg-green-500 rounded-full" 
                    style={{ width: `${metrics?.memory_usage || 0}%` }}
                  ></div>
                </div>
                <span className="font-semibold">{metrics?.memory_usage || 0}%</span>
              </div>
            </div>
            <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
              <span className="text-gray-600">Distancia Total Hoy</span>
              <span className="font-semibold">{metrics?.total_distance_today || 0} km</span>
            </div>
          </div>
        </div>
      </div>
      
      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Performance Chart */}
        <div className="bg-white rounded-xl shadow-sm p-4">
          <h2 className="text-lg font-semibold mb-4">Rendimiento del Sistema</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="latencia" stroke="#3b82f6" name="Latencia (ms)" />
                <Line type="monotone" dataKey="optimizaciones" stroke="#10b981" name="Optimizaciones" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
        
        {/* Route Stats Chart */}
        <div className="bg-white rounded-xl shadow-sm p-4">
          <h2 className="text-lg font-semibold mb-4">Distancia por Día (km)</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={routeStats}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="distancia" fill="#8b5cf6" name="Distancia (km)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  )
}
