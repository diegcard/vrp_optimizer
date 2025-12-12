import { useState } from 'react'
import { useCustomers, useVehicles, useDepots, useOptimizeRoutes } from '../hooks/useApi'
import { useAppStore } from '../store/appStore'
import MapView from '../components/MapView'
import toast from 'react-hot-toast'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Badge from '../components/ui/Badge'

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
          <h1 className="text-3xl font-bold text-gray-900">Optimización de Rutas</h1>
          <p className="text-gray-500 mt-1">VRP con Reinforcement Learning</p>
        </div>
        {!depot && (
          <Badge variant="danger" className="flex items-center gap-2">
            <span>⚠️</span>
            <span>No hay depósito configurado</span>
          </Badge>
        )}
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Config Panel */}
        <div className="space-y-6">
          {/* Method Selection */}
          <Card>
            <h2 className="text-lg font-semibold mb-4 text-gray-900">Método de Optimización</h2>
            
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
          </Card>
          
          {/* Selection Summary */}
          <Card>
            <h2 className="text-lg font-semibold mb-4 text-gray-900">Selección</h2>
            
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
            
            <Button
              onClick={handleOptimize}
              disabled={optimizeRoutes.isPending || selectedCustomers.length === 0 || selectedVehicles.length === 0 || !depot}
              isLoading={optimizeRoutes.isPending}
              className="w-full mt-4"
              size="lg"
            >
              🚀 Optimizar Rutas
            </Button>
          </Card>
          
          {/* Results */}
          {result && (
            <Card>
              <h2 className="text-lg font-semibold mb-4 text-gray-900">Resultados</h2>
              
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
            </Card>
          )}
        </div>
        
        {/* Map */}
        <Card className="lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Vista de Rutas</h2>
            {result && (
              <Badge variant="success">
                {result.metrics.vehicles_used} vehículo(s) usado(s)
              </Badge>
            )}
          </div>
          <div className="h-[600px] rounded-lg overflow-hidden">
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
            <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Leyenda de Rutas</h3>
              <div className="flex flex-wrap gap-4">
                {routes.map((route, index) => {
                  const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']
                  return (
                    <div key={route.vehicle_id} className="flex items-center gap-2 px-3 py-1.5 bg-white rounded-lg border border-gray-200">
                      <div 
                        className="w-4 h-1 rounded-full"
                        style={{ backgroundColor: colors[index % colors.length] }}
                      ></div>
                      <span className="text-sm font-medium text-gray-700">
                        Ruta {index + 1}: <span className="text-primary-600">{route.total_distance_km.toFixed(1)} km</span>, {route.points.length} paradas
                      </span>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}
