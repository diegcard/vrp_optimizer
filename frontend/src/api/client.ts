import axios, { AxiosError } from 'axios'
import type {
  Customer,
  Vehicle,
  Depot,
  OptimizationRequest,
  OptimizationResponse,
  TrainingConfig,
  TrainingStatus,
  TrainingHistory,
  ModelInfo,
  SystemMetrics,
} from '../types'

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Interceptor para asegurar trailing slash y evitar redirects 307
api.interceptors.request.use((config) => {
  // Si la URL no termina en / y no tiene query params, agregar /
  if (config.url && !config.url.endsWith('/') && !config.url.includes('?')) {
    config.url = config.url + '/'
  }
  return config
})

// Error handler
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    const message = (error.response?.data as any)?.detail || error.message
    console.error('API Error:', message)
    return Promise.reject(error)
  }
)

// Health check
export const checkHealth = async () => {
  const response = await api.get('/health')
  return response.data
}

// Customers
export const getCustomers = async (): Promise<Customer[]> => {
  const response = await api.get('/customers')
  return response.data
}

export const getCustomer = async (id: string): Promise<Customer> => {
  const response = await api.get(`/customers/${id}`)
  return response.data
}

export const createCustomer = async (customer: Omit<Customer, 'id'>): Promise<Customer> => {
  const response = await api.post('/customers', customer)
  return response.data
}

export const updateCustomer = async (id: string, customer: Partial<Customer>): Promise<Customer> => {
  const response = await api.put(`/customers/${id}`, customer)
  return response.data
}

export const deleteCustomer = async (id: string): Promise<void> => {
  await api.delete(`/customers/${id}`)
}

// Vehicles
export const getVehicles = async (): Promise<Vehicle[]> => {
  const response = await api.get('/vehicles')
  return response.data
}

export const getVehicle = async (id: string): Promise<Vehicle> => {
  const response = await api.get(`/vehicles/${id}`)
  return response.data
}

export const createVehicle = async (vehicle: Omit<Vehicle, 'id'>): Promise<Vehicle> => {
  const response = await api.post('/vehicles', vehicle)
  return response.data
}

export const updateVehicle = async (id: string, vehicle: Partial<Vehicle>): Promise<Vehicle> => {
  const response = await api.put(`/vehicles/${id}`, vehicle)
  return response.data
}

export const deleteVehicle = async (id: string): Promise<void> => {
  await api.delete(`/vehicles/${id}`)
}

// Depots
export const getDepots = async (): Promise<Depot[]> => {
  const response = await api.get('/depots')
  return response.data
}

export const getDepot = async (id: string): Promise<Depot> => {
  const response = await api.get(`/depots/${id}`)
  return response.data
}

// Optimization
export const optimizeRoutes = async (request: OptimizationRequest): Promise<OptimizationResponse> => {
  const response = await api.post('/optimization/optimize', request)
  return response.data
}

export const getRoutes = async (): Promise<OptimizationResponse['routes']> => {
  const response = await api.get('/routes')
  return response.data
}

// Training
export const startTraining = async (config: TrainingConfig): Promise<{ session_id: string }> => {
  const response = await api.post('/training/start', config)
  return response.data
}

export const getTrainingStatus = async (): Promise<TrainingStatus> => {
  const response = await api.get('/training/status')
  return response.data
}

export const stopTraining = async (): Promise<void> => {
  await api.post('/training/stop')
}

export const getTrainingHistory = async (limit?: number): Promise<TrainingHistory[]> => {
  const response = await api.get('/training/history', {
    params: { limit },
  })
  return response.data
}

export const getModels = async (): Promise<ModelInfo[]> => {
  const response = await api.get('/training/models')
  return response.data
}

export const loadModel = async (modelId: string): Promise<void> => {
  await api.post(`/training/models/${modelId}/load`)
}

export const deleteModel = async (modelId: string): Promise<void> => {
  await api.delete(`/training/models/${modelId}`)
}

// Metrics
export const getSystemMetrics = async (): Promise<SystemMetrics> => {
  const response = await api.get('/metrics')
  return response.data
}

export default api
