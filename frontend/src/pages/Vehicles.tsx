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
    plate_number: '',
    capacity: '100',
    vehicle_type: 'van',
    driver_name: '',
    driver_phone: '',
    fuel_efficiency: '',
  })
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      await createVehicle.mutateAsync({
        plate_number: formData.plate_number,
        capacity: parseInt(formData.capacity),
        vehicle_type: formData.vehicle_type,
        driver_name: formData.driver_name || undefined,
        driver_phone: formData.driver_phone || undefined,
        fuel_efficiency: formData.fuel_efficiency ? parseFloat(formData.fuel_efficiency) : undefined,
      })
      
      toast.success('Vehículo creado exitosamente')
      setShowModal(false)
      setFormData({ plate_number: '', capacity: '100', vehicle_type: 'van', driver_name: '', driver_phone: '', fuel_efficiency: '' })
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || 'Error al crear vehículo')
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
                  <h3 className="font-semibold text-gray-900">{vehicle.plate_number}</h3>
                  <div className="flex items-center gap-2 mt-1">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${getStatusColor(vehicle.status)}`}>
                      {getStatusLabel(vehicle.status)}
                    </span>
                    {vehicle.vehicle_type && (
                      <span className="text-xs text-gray-500">{vehicle.vehicle_type}</span>
                    )}
                  </div>
                </div>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  handleDelete(vehicle.id)
                }}
                className="text-gray-400 hover:text-red-500 p-2 hover:bg-red-50 rounded-lg transition-colors"
                title="Eliminar vehículo"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
            
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Capacidad</span>
                <span className="font-medium">{vehicle.capacity} unidades</span>
              </div>
              {vehicle.driver_name && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Conductor</span>
                  <span className="font-medium">{vehicle.driver_name}</span>
                </div>
              )}
              {vehicle.fuel_efficiency && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Eficiencia</span>
                  <span className="font-medium">{vehicle.fuel_efficiency} km/L</span>
                </div>
              )}
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
                  Placa del Vehículo *
                </label>
                <input
                  type="text"
                  value={formData.plate_number}
                  onChange={(e) => setFormData({ ...formData, plate_number: e.target.value.toUpperCase() })}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                  placeholder="Ej: ABC123"
                  required
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Capacidad (unidades) *
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
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Tipo de Vehículo
                  </label>
                  <select
                    value={formData.vehicle_type}
                    onChange={(e) => setFormData({ ...formData, vehicle_type: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="van">Van</option>
                    <option value="truck">Camión</option>
                    <option value="motorcycle">Motocicleta</option>
                    <option value="car">Carro</option>
                  </select>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Nombre del Conductor
                  </label>
                  <input
                    type="text"
                    value={formData.driver_name}
                    onChange={(e) => setFormData({ ...formData, driver_name: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                    placeholder="Opcional"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Teléfono del Conductor
                  </label>
                  <input
                    type="text"
                    value={formData.driver_phone}
                    onChange={(e) => setFormData({ ...formData, driver_phone: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                    placeholder="Opcional"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Eficiencia de Combustible (km/L)
                </label>
                <input
                  type="number"
                  min="0"
                  step="0.1"
                  value={formData.fuel_efficiency}
                  onChange={(e) => setFormData({ ...formData, fuel_efficiency: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                  placeholder="Opcional"
                />
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

