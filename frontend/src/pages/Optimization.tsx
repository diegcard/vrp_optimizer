import { useState } from 'react'
import { useCustomers, useVehicles, useDepots, useOptimizeRoutes } from '../hooks/useApi'
import { useAppStore } from '../store/appStore'
import MapView from '../components/MapView'
import toast from 'react-hot-toast'

type OptimizationMethod = 'rl' | 'greedy' | 'ortools'

export default function Optimization() {
  const { data: customers = [] } = useCustomers()
  const { data: vehicles = [] } = useVehicles()
  const { data: depots = [] } = useDepots()
  const optimizeRoutes = useOptimizeRoutes()
  
  const { 
    selectedCustomers, 
    selectedVehicles, 
    routes, 
    setRoutes,
    selectAllCustomers,
    selectAllVehicles,
    clearCustomerSelection,
    clearVehicleSelection,
  } = useAppStore()
  
  const [method, setMethod] = useState<OptimizationMethod>('rl')
  const [useRealRoads, setUseRealRoads] = useState(true)
  const [result, setResult] = useState<any>(null)
  
  const handleOptimize = async () => {
    if (selectedCustomers.length === 0) {
      toast.error('Seleccione al menos un cliente')
      return
    }
    
    if (selectedVehicles.length === 0) {
      toast.error('Seleccione al menos un vehículo')
      return
    }
    
    const depot = depots[0]
    if (!depot) {
      toast.error('No hay depósito configurado')
      return
    }
    
    try {
      const response = await optimizeRoutes.mutateAsync({
        customer_ids: selectedCustomers,
        vehicle_ids: selectedVehicles,
        depot_id: depot.id,
        method,
        use_real_roads: useRealRoads,
      })
      
      setRoutes(response.routes)
      setResult(response)
      toast.success(`Optimización completada en ${response.computation_time_ms}ms`)
    } catch (error) {
      toast.error('Error durante la optimización')
    }
  }
  
  const depot = depots[0]
  const displayCustomers = customers.filter(c => selectedCustomers.includes(c.id))
  
  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Optimización de Rutas</h1>
          <p className="text-gray-500">VRP con Reinforcement Learning</p>
        </div>
        {!depot && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-2 rounded-lg flex items-center gap-2">
            <span>⚠️</span>
            <span>No hay depósito configurado</span>
          </div>
        )}
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Config Panel */}
        <div className="space-y-6">
          {/* Method Selection */}
          <div className="bg-white rounded-xl shadow-sm p-4">
            <h2 className="text-lg font-semibold mb-4">Método de Optimización</h2>
            
            <div className="space-y-3">
              <label
                className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                  method === 'rl' ? 'border-primary-500 bg-primary-50' : 'border-gray-200'
                }`}
              >
                <input
                  type="radio"
                  name="method"
                  value="rl"
                  checked={method === 'rl'}
                  onChange={() => setMethod('rl')}
                  className="text-primary-600"
                />
                <div>
                  <p className="font-medium">🤖 Reinforcement Learning (DQN)</p>
                  <p className="text-sm text-gray-500">Optimización mediante aprendizaje por refuerzo</p>
                </div>
              </label>
              
              <label
                className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                  method === 'greedy' ? 'border-primary-500 bg-primary-50' : 'border-gray-200'
                }`}
              >
                <input
                  type="radio"
                  name="method"
                  value="greedy"
                  checked={method === 'greedy'}
                  onChange={() => setMethod('greedy')}
                  className="text-primary-600"
                />
                <div>
                  <p className="font-medium">🔄 Greedy (Vecino más cercano)</p>
                  <p className="text-sm text-gray-500">Heurística rápida y simple</p>
                </div>
              </label>
              
              <label
                className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                  method === 'ortools' ? 'border-primary-500 bg-primary-50' : 'border-gray-200'
                }`}
              >
                <input
                  type="radio"
                  name="method"
                  value="ortools"
                  checked={method === 'ortools'}
                  onChange={() => setMethod('ortools')}
                  className="text-primary-600"
                />
                <div>
                  <p className="font-medium">🔧 OR-Tools (Google)</p>
                  <p className="text-sm text-gray-500">Solver de programación lineal</p>
                </div>
              </label>
            </div>
            
            <div className="mt-4 pt-4 border-t">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={useRealRoads}
                  onChange={(e) => setUseRealRoads(e.target.checked)}
                  className="w-4 h-4 text-primary-600 rounded"
                />
                <div>
                  <span className="text-sm font-medium">🛣️ Rutas por calles reales</span>
                  <p className="text-xs text-gray-500">Usa OSRM para seguir calles en lugar de líneas rectas</p>
                </div>
              </label>
            </div>
          </div>
          
          {/* Selection Summary */}
          <div className="bg-white rounded-xl shadow-sm p-4">
            <h2 className="text-lg font-semibold mb-4">Selección</h2>
            
            <div className="space-y-4">
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-gray-600">Clientes</span>
                  <span className="font-semibold">{selectedCustomers.length} / {customers.length}</span>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={selectAllCustomers}
                    className="text-xs px-2 py-1 bg-gray-100 rounded hover:bg-gray-200"
                  >
                    Todos
                  </button>
                  <button
                    onClick={clearCustomerSelection}
                    className="text-xs px-2 py-1 bg-gray-100 rounded hover:bg-gray-200"
                  >
                    Limpiar
                  </button>
                </div>
              </div>
              
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-gray-600">Vehículos</span>
                  <span className="font-semibold">{selectedVehicles.length} / {vehicles.length}</span>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={selectAllVehicles}
                    className="text-xs px-2 py-1 bg-gray-100 rounded hover:bg-gray-200"
                  >
                    Todos
                  </button>
                  <button
                    onClick={clearVehicleSelection}
                    className="text-xs px-2 py-1 bg-gray-100 rounded hover:bg-gray-200"
                  >
                    Limpiar
                  </button>
                </div>
              </div>
            </div>
            
            <button
              onClick={handleOptimize}
              disabled={optimizeRoutes.isPending || selectedCustomers.length === 0 || selectedVehicles.length === 0}
              className="w-full mt-4 px-4 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {optimizeRoutes.isPending ? (
                <>
                  <div className="animate-spin w-5 h-5 border-2 border-white border-t-transparent rounded-full"></div>
                  Optimizando...
                </>
              ) : (
                <>
                  🚀 Optimizar Rutas
                </>
              )}
            </button>
          </div>
          
          {/* Results */}
          {result && (
            <div className="bg-white rounded-xl shadow-sm p-4">
              <h2 className="text-lg font-semibold mb-4">Resultados</h2>
              
              <div className="space-y-3">
                <div className="flex justify-between items-center p-2 bg-green-50 rounded-lg">
                  <span className="text-gray-600">Distancia Total</span>
                  <span className="font-bold text-green-700">{result.total_distance_km.toFixed(2)} km</span>
                </div>
                
                <div className="flex justify-between items-center p-2 bg-blue-50 rounded-lg">
                  <span className="text-gray-600">Tiempo Total</span>
                  <span className="font-bold text-blue-700">{result.total_time_minutes.toFixed(0)} min</span>
                </div>
                
                <div className="flex justify-between items-center p-2 bg-purple-50 rounded-lg">
                  <span className="text-gray-600">Vehículos Usados</span>
                  <span className="font-bold text-purple-700">{result.metrics.vehicles_used}</span>
                </div>
                
                <div className="flex justify-between items-center p-2 bg-gray-50 rounded-lg">
                  <span className="text-gray-600">Tiempo de Cómputo</span>
                  <span className="font-semibold">{result.computation_time_ms} ms</span>
                </div>
                
                <div className="text-xs text-gray-500 mt-2">
                  Método: {result.method_used.toUpperCase()}
                </div>
              </div>
            </div>
          )}
        </div>
        
        {/* Map */}
        <div className="lg:col-span-2 bg-white rounded-xl shadow-sm p-4">
          <h2 className="text-lg font-semibold mb-4">Vista de Rutas</h2>
          <div className="h-[600px]">
            <MapView
              customers={displayCustomers.length > 0 ? displayCustomers.map(c => ({
                ...c,
                location: { lat: c.location?.lat || 4.65, lon: c.location?.lon || -74.05 }
              })) : customers.map(c => ({
                ...c,
                location: { lat: c.location?.lat || 4.65, lon: c.location?.lon || -74.05 }
              }))}
              depot={depot ? { lat: depot.latitude || 4.6577, lon: depot.longitude || -74.0553 } : { lat: 4.6577, lon: -74.0553 }}
              routes={routes}
            />
          </div>
          
          {/* Route Legend */}
          {routes.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-4">
              {routes.map((route, index) => {
                const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']
                return (
                  <div key={route.vehicle_id} className="flex items-center gap-2">
                    <div 
                      className="w-4 h-1 rounded"
                      style={{ backgroundColor: colors[index % colors.length] }}
                    ></div>
                    <span className="text-sm text-gray-600">
                      Ruta {index + 1}: {route.total_distance_km.toFixed(1)}km, {route.points.length} paradas
                    </span>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
