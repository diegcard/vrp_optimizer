import { useState } from 'react'
import { useCustomers, useCreateCustomer, useDeleteCustomer } from '../hooks/useApi'
import { useAppStore } from '../store/appStore'
import MapView from '../components/MapView'
import toast from 'react-hot-toast'
import type { Customer } from '../types'

export default function Customers() {
  const { data: customers = [], isLoading } = useCustomers()
  const createCustomer = useCreateCustomer()
  const deleteCustomer = useDeleteCustomer()
  
  const { selectedCustomers, toggleCustomerSelection, selectAllCustomers, clearCustomerSelection } = useAppStore()
  
  const [showModal, setShowModal] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    address: '',
    lat: '',
    lon: '',
    demand: '1',
    priority: '1',
  })
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      await createCustomer.mutateAsync({
        name: formData.name,
        address: formData.address,
        location: {
          lat: parseFloat(formData.lat),
          lon: parseFloat(formData.lon),
        },
        demand: parseInt(formData.demand),
        priority: parseInt(formData.priority),
      })
      
      toast.success('Cliente creado exitosamente')
      setShowModal(false)
      setFormData({ name: '', address: '', lat: '', lon: '', demand: '1', priority: '1' })
    } catch (error) {
      toast.error('Error al crear cliente')
    }
  }
  
  const handleDelete = async (id: string) => {
    if (confirm('¿Está seguro de eliminar este cliente?')) {
      try {
        await deleteCustomer.mutateAsync(id)
        toast.success('Cliente eliminado')
      } catch (error) {
        toast.error('Error al eliminar cliente')
      }
    }
  }
  
  const handleMapClick = (latlng: { lat: number; lng: number }) => {
    setFormData((prev) => ({
      ...prev,
      lat: latlng.lat.toFixed(6),
      lon: latlng.lng.toFixed(6),
    }))
    setShowModal(true)
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
          <h1 className="text-2xl font-bold text-gray-900">Clientes</h1>
          <p className="text-gray-500">Gestiona los puntos de entrega</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          + Nuevo Cliente
        </button>
      </div>
      
      {/* Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Map */}
        <div className="bg-white rounded-xl shadow-sm p-4">
          <h2 className="text-lg font-semibold mb-4">Mapa - Click para agregar cliente</h2>
          <div className="h-96">
            <MapView
              customers={customers.map(c => ({
                ...c,
                location: { lat: c.location?.lat || 4.65, lon: c.location?.lon || -74.05 }
              }))}
              depot={{ lat: 4.6577, lon: -74.0553 }}
              onMapClick={handleMapClick}
              onCustomerClick={(customer) => toggleCustomerSelection(customer.id)}
            />
          </div>
        </div>
        
        {/* Customer List */}
        <div className="bg-white rounded-xl shadow-sm p-4">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold">Lista de Clientes ({customers.length})</h2>
            <div className="flex gap-2">
              <button
                onClick={selectAllCustomers}
                className="text-sm text-primary-600 hover:text-primary-700"
              >
                Seleccionar todos
              </button>
              <button
                onClick={clearCustomerSelection}
                className="text-sm text-gray-500 hover:text-gray-600"
              >
                Limpiar
              </button>
            </div>
          </div>
          
          <div className="space-y-2 max-h-80 overflow-y-auto">
            {customers.map((customer) => (
              <div
                key={customer.id}
                className={`flex items-center justify-between p-3 rounded-lg border transition-colors cursor-pointer ${
                  selectedCustomers.includes(customer.id)
                    ? 'border-primary-500 bg-primary-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => toggleCustomerSelection(customer.id)}
              >
                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={selectedCustomers.includes(customer.id)}
                    onChange={() => toggleCustomerSelection(customer.id)}
                    className="w-4 h-4 text-primary-600 rounded"
                  />
                  <div>
                    <p className="font-medium text-gray-900">{customer.name}</p>
                    <p className="text-sm text-gray-500">{customer.address || 'Sin dirección'}</p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right text-sm">
                    <p className="text-gray-600">Demanda: {customer.demand}</p>
                    <p className="text-gray-500">Prioridad: {customer.priority}</p>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDelete(customer.id)
                    }}
                    className="text-red-500 hover:text-red-600"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            ))}
            
            {customers.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                No hay clientes registrados. Haz click en el mapa para agregar.
              </div>
            )}
          </div>
          
          {selectedCustomers.length > 0 && (
            <div className="mt-4 p-3 bg-primary-50 rounded-lg">
              <p className="text-sm text-primary-700">
                {selectedCustomers.length} cliente(s) seleccionado(s) para optimización
              </p>
            </div>
          )}
        </div>
      </div>
      
      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center" style={{ zIndex: 9999 }}>
          <div className="bg-white rounded-xl p-6 w-full max-w-md shadow-2xl" style={{ zIndex: 10000 }}>
            <h2 className="text-xl font-bold mb-4">Nuevo Cliente</h2>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nombre
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Dirección
                </label>
                <input
                  type="text"
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Latitud
                  </label>
                  <input
                    type="number"
                    step="any"
                    value={formData.lat}
                    onChange={(e) => setFormData({ ...formData, lat: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Longitud
                  </label>
                  <input
                    type="number"
                    step="any"
                    value={formData.lon}
                    onChange={(e) => setFormData({ ...formData, lon: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                    required
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Demanda
                  </label>
                  <input
                    type="number"
                    min="1"
                    value={formData.demand}
                    onChange={(e) => setFormData({ ...formData, demand: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Prioridad (1-5)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="5"
                    value={formData.priority}
                    onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
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
                  disabled={createCustomer.isPending}
                  className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
                >
                  {createCustomer.isPending ? 'Guardando...' : 'Guardar'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
