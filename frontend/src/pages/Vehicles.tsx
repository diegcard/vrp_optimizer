import { useState } from 'react'
import { useVehicles, useCreateVehicle, useDeleteVehicle } from '../hooks/useApi'
import { useAppStore } from '../store/appStore'
import toast from 'react-hot-toast'

export default function Vehicles() {
  const { data: vehicles = [], isLoading } = useVehicles()
  const createVehicle = useCreateVehicle()
  const deleteVehicle = useDeleteVehicle()
  
  const { selectedVehicles, toggleVehicleSelection, selectAllVehicles, clearVehicleSelection } = useAppStore()
  
  const [showModal, setShowModal] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    capacity: '100',
    speed_kmh: '30',
    cost_per_km: '500',
  })
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      await createVehicle.mutateAsync({
        name: formData.name,
        capacity: parseInt(formData.capacity),
        speed_kmh: parseFloat(formData.speed_kmh),
        cost_per_km: parseFloat(formData.cost_per_km),
        status: 'available',
      })
      
      toast.success('Vehículo creado exitosamente')
      setShowModal(false)
      setFormData({ name: '', capacity: '100', speed_kmh: '30', cost_per_km: '500' })
    } catch (error) {
      toast.error('Error al crear vehículo')
    }
  }
  
  const handleDelete = async (id: string) => {
    if (confirm('¿Está seguro de eliminar este vehículo?')) {
      try {
        await deleteVehicle.mutateAsync(id)
        toast.success('Vehículo eliminado')
      } catch (error) {
        toast.error('Error al eliminar vehículo')
      }
    }
  }
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'available': return 'bg-green-100 text-green-800'
      case 'in_route': return 'bg-blue-100 text-blue-800'
      case 'maintenance': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }
  
  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'available': return 'Disponible'
      case 'in_route': return 'En ruta'
      case 'maintenance': return 'Mantenimiento'
      default: return status
    }
  }
  
  if (isLoading) {
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
          <h1 className="text-2xl font-bold text-gray-900">Vehículos</h1>
          <p className="text-gray-500">Gestiona la flota de vehículos</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          + Nuevo Vehículo
        </button>
      </div>
      
      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center text-2xl">
              ✅
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">
                {vehicles.filter(v => v.status === 'available').length}
              </p>
              <p className="text-sm text-gray-500">Disponibles</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center text-2xl">
              🚗
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">
                {vehicles.filter(v => v.status === 'in_route').length}
              </p>
              <p className="text-sm text-gray-500">En ruta</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center text-2xl">
              📦
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">
                {vehicles.reduce((sum, v) => sum + v.capacity, 0)}
              </p>
              <p className="text-sm text-gray-500">Capacidad Total</p>
            </div>
          </div>
        </div>
      </div>
      
      {/* Selection controls */}
      <div className="flex gap-2">
        <button
          onClick={selectAllVehicles}
          className="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          Seleccionar todos
        </button>
        <button
          onClick={clearVehicleSelection}
          className="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          Limpiar selección
        </button>
        {selectedVehicles.length > 0 && (
          <span className="px-3 py-1 text-sm bg-primary-100 text-primary-700 rounded-lg">
            {selectedVehicles.length} seleccionado(s)
          </span>
        )}
      </div>
      
      {/* Vehicle Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {vehicles.map((vehicle) => (
          <div
            key={vehicle.id}
            className={`bg-white rounded-xl shadow-sm p-6 cursor-pointer transition-all ${
              selectedVehicles.includes(vehicle.id)
                ? 'ring-2 ring-primary-500'
                : 'hover:shadow-md'
            }`}
            onClick={() => toggleVehicleSelection(vehicle.id)}
          >
            <div className="flex justify-between items-start mb-4">
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={selectedVehicles.includes(vehicle.id)}
                  onChange={() => toggleVehicleSelection(vehicle.id)}
                  className="w-4 h-4 text-primary-600 rounded"
                  onClick={(e) => e.stopPropagation()}
                />
                <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center text-xl">
                  🚗
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">{vehicle.name}</h3>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${getStatusColor(vehicle.status)}`}>
                    {getStatusLabel(vehicle.status)}
                  </span>
                </div>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  handleDelete(vehicle.id)
                }}
                className="text-gray-400 hover:text-red-500"
              >
                🗑️
              </button>
            </div>
            
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Capacidad</span>
                <span className="font-medium">{vehicle.capacity} unidades</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Velocidad</span>
                <span className="font-medium">{vehicle.speed_kmh || 30} km/h</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Costo/km</span>
                <span className="font-medium">${vehicle.cost_per_km || 500}</span>
              </div>
            </div>
          </div>
        ))}
        
        {vehicles.length === 0 && (
          <div className="col-span-full text-center py-12 text-gray-500">
            No hay vehículos registrados
          </div>
        )}
      </div>
      
      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center" style={{ zIndex: 9999 }}>
          <div className="bg-white rounded-xl p-6 w-full max-w-md shadow-2xl" style={{ zIndex: 10000 }}>
            <h2 className="text-xl font-bold mb-4">Nuevo Vehículo</h2>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nombre / Identificador
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                  placeholder="Ej: Vehículo 1, Camioneta A"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Capacidad (unidades)
                </label>
                <input
                  type="number"
                  min="1"
                  value={formData.capacity}
                  onChange={(e) => setFormData({ ...formData, capacity: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                  required
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Velocidad (km/h)
                  </label>
                  <input
                    type="number"
                    min="1"
                    value={formData.speed_kmh}
                    onChange={(e) => setFormData({ ...formData, speed_kmh: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Costo por km ($)
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={formData.cost_per_km}
                    onChange={(e) => setFormData({ ...formData, cost_per_km: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                  />
                </div>
              </div>
              
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={createVehicle.isPending}
                  className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
                >
                  {createVehicle.isPending ? 'Guardando...' : 'Guardar'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
