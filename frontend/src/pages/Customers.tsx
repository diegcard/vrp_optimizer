import { useState } from 'react'
import { useCustomers, useCreateCustomer, useDeleteCustomer } from '../hooks/useApi'
import { useAppStore } from '../store/appStore'
import MapView from '../components/MapView'
import toast from 'react-hot-toast'
import type { Customer } from '../types'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Modal from '../components/ui/Modal'
import Input from '../components/ui/Input'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import Badge from '../components/ui/Badge'

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
  const [formErrors, setFormErrors] = useState<Record<string, string>>({})
  
  const validateForm = () => {
    const errors: Record<string, string> = {}
    
    if (!formData.name.trim()) {
      errors.name = 'El nombre es requerido'
    }
    
    if (!formData.lat || isNaN(parseFloat(formData.lat))) {
      errors.lat = 'Latitud inválida'
    } else {
      const lat = parseFloat(formData.lat)
      if (lat < -90 || lat > 90) {
        errors.lat = 'Latitud debe estar entre -90 y 90'
      }
    }
    
    if (!formData.lon || isNaN(parseFloat(formData.lon))) {
      errors.lon = 'Longitud inválida'
    } else {
      const lon = parseFloat(formData.lon)
      if (lon < -180 || lon > 180) {
        errors.lon = 'Longitud debe estar entre -180 y 180'
      }
    }
    
    const demand = parseInt(formData.demand)
    if (isNaN(demand) || demand < 1) {
      errors.demand = 'La demanda debe ser mayor a 0'
    }
    
    const priority = parseInt(formData.priority)
    if (isNaN(priority) || priority < 1 || priority > 5) {
      errors.priority = 'La prioridad debe estar entre 1 y 5'
    }
    
    setFormErrors(errors)
    return Object.keys(errors).length === 0
  }
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) {
      toast.error('Por favor corrija los errores en el formulario')
      return
    }
    
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
      setFormErrors({})
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || 'Error al crear cliente')
    }
  }
  
  const handleDelete = async (id: string) => {
    if (window.confirm('¿Está seguro de eliminar este cliente?')) {
      try {
        await deleteCustomer.mutateAsync(id)
        toast.success('Cliente eliminado')
      } catch (error: any) {
        toast.error(error?.response?.data?.detail || 'Error al eliminar cliente')
      }
    }
  }
  
  const handleMapClick = (latlng: { lat: number; lng: number }) => {
    setFormData((prev) => ({
      ...prev,
      lat: latlng.lat.toFixed(6),
      lon: latlng.lng.toFixed(6),
    }))
    setFormErrors((prev) => ({ ...prev, lat: '', lon: '' }))
    setShowModal(true)
  }
  
  if (isLoading) {
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
          <h1 className="text-3xl font-bold text-gray-900">Clientes</h1>
          <p className="text-gray-500 mt-1">Gestiona los puntos de entrega</p>
        </div>
        <Button onClick={() => setShowModal(true)}>
          + Nuevo Cliente
        </Button>
      </div>
      
      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center text-2xl">
              📍
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{customers.length}</p>
              <p className="text-sm text-gray-500">Total Clientes</p>
            </div>
          </div>
        </Card>
        
        <Card>
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-success-100 rounded-lg flex items-center justify-center text-2xl">
              ✅
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{selectedCustomers.length}</p>
              <p className="text-sm text-gray-500">Seleccionados</p>
            </div>
          </div>
        </Card>
        
        <Card>
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-warning-100 rounded-lg flex items-center justify-center text-2xl">
              📦
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">
                {customers.reduce((sum, c) => sum + c.demand, 0)}
              </p>
              <p className="text-sm text-gray-500">Demanda Total</p>
            </div>
          </div>
        </Card>
      </div>
      
      {/* Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Map */}
        <Card>
          <h2 className="text-lg font-semibold mb-4 text-gray-900">
            Mapa - Click para agregar cliente
          </h2>
          <div className="h-96 rounded-lg overflow-hidden">
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
        </Card>
        
        {/* Customer List */}
        <Card>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              Lista de Clientes ({customers.length})
            </h2>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={selectAllCustomers}
                disabled={customers.length === 0}
              >
                Todos
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={clearCustomerSelection}
                disabled={selectedCustomers.length === 0}
              >
                Limpiar
              </Button>
            </div>
          </div>
          
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {customers.map((customer) => (
              <div
                key={customer.id}
                className={`
                  flex items-center justify-between p-4 rounded-lg border transition-all cursor-pointer
                  ${selectedCustomers.includes(customer.id)
                    ? 'border-primary-500 bg-primary-50 shadow-sm'
                    : 'border-gray-200 hover:border-primary-300 hover:bg-gray-50'
                  }
                `}
                onClick={() => toggleCustomerSelection(customer.id)}
              >
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <input
                    type="checkbox"
                    checked={selectedCustomers.includes(customer.id)}
                    onChange={() => toggleCustomerSelection(customer.id)}
                    className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                    onClick={(e) => e.stopPropagation()}
                  />
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-gray-900 truncate">{customer.name}</p>
                    <p className="text-sm text-gray-500 truncate">{customer.address || 'Sin dirección'}</p>
                    <div className="flex gap-2 mt-1">
                      <Badge variant="gray" size="sm">Demanda: {customer.demand}</Badge>
                      <Badge variant="primary" size="sm">Prioridad: {customer.priority}</Badge>
                    </div>
                  </div>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    handleDelete(customer.id)
                  }}
                  className="ml-4 p-2 text-gray-400 hover:text-danger-500 hover:bg-danger-50 rounded-lg transition-colors"
                  title="Eliminar cliente"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            ))}
            
            {customers.length === 0 && (
              <div className="text-center py-12 text-gray-500">
                <div className="text-4xl mb-4">📍</div>
                <p className="font-medium">No hay clientes registrados</p>
                <p className="text-sm mt-1">Haz click en el mapa para agregar un cliente</p>
              </div>
            )}
          </div>
          
          {selectedCustomers.length > 0 && (
            <div className="mt-4 p-4 bg-primary-50 border border-primary-200 rounded-lg">
              <p className="text-sm font-medium text-primary-700">
                {selectedCustomers.length} cliente(s) seleccionado(s) para optimización
              </p>
            </div>
          )}
        </Card>
      </div>
      
      {/* Modal */}
      <Modal
        isOpen={showModal}
        onClose={() => {
          setShowModal(false)
          setFormErrors({})
        }}
        title="Nuevo Cliente"
        size="md"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Nombre"
            value={formData.name}
            onChange={(e) => {
              setFormData({ ...formData, name: e.target.value })
              setFormErrors((prev) => ({ ...prev, name: '' }))
            }}
            error={formErrors.name}
            required
            placeholder="Ej: Cliente ABC"
          />
          
          <Input
            label="Dirección"
            value={formData.address}
            onChange={(e) => setFormData({ ...formData, address: e.target.value })}
            placeholder="Ej: Calle 123 #45-67"
          />
          
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Latitud"
              type="number"
              step="any"
              value={formData.lat}
              onChange={(e) => {
                setFormData({ ...formData, lat: e.target.value })
                setFormErrors((prev) => ({ ...prev, lat: '' }))
              }}
              error={formErrors.lat}
              required
              helperText="Coordenada del mapa"
            />
            <Input
              label="Longitud"
              type="number"
              step="any"
              value={formData.lon}
              onChange={(e) => {
                setFormData({ ...formData, lon: e.target.value })
                setFormErrors((prev) => ({ ...prev, lon: '' }))
              }}
              error={formErrors.lon}
              required
              helperText="Coordenada del mapa"
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Demanda"
              type="number"
              min="1"
              value={formData.demand}
              onChange={(e) => {
                setFormData({ ...formData, demand: e.target.value })
                setFormErrors((prev) => ({ ...prev, demand: '' }))
              }}
              error={formErrors.demand}
              helperText="Unidades a entregar"
            />
            <Input
              label="Prioridad"
              type="number"
              min="1"
              max="5"
              value={formData.priority}
              onChange={(e) => {
                setFormData({ ...formData, priority: e.target.value })
                setFormErrors((prev) => ({ ...prev, priority: '' }))
              }}
              error={formErrors.priority}
              helperText="1 (baja) a 5 (alta)"
            />
          </div>
          
          <div className="flex gap-3 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setShowModal(false)
                setFormErrors({})
              }}
              className="flex-1"
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              isLoading={createCustomer.isPending}
              className="flex-1"
            >
              Guardar Cliente
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
