import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as api from '../api/client'
import type { Customer, Vehicle, OptimizationRequest, TrainingConfig } from '../types'

// Query keys
export const queryKeys = {
  customers: ['customers'] as const,
  customer: (id: string) => ['customer', id] as const,
  vehicles: ['vehicles'] as const,
  vehicle: (id: string) => ['vehicle', id] as const,
  depots: ['depots'] as const,
  routes: ['routes'] as const,
  trainingStatus: ['training', 'status'] as const,
  trainingHistory: ['training', 'history'] as const,
  models: ['training', 'models'] as const,
  metrics: ['metrics'] as const,
  health: ['health'] as const,
}

// Health
export const useHealth = () => {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: api.checkHealth,
    refetchInterval: 30000,
  })
}

// Customers
export const useCustomers = () => {
  return useQuery({
    queryKey: queryKeys.customers,
    queryFn: api.getCustomers,
  })
}

export const useCustomer = (id: string) => {
  return useQuery({
    queryKey: queryKeys.customer(id),
    queryFn: () => api.getCustomer(id),
    enabled: !!id,
  })
}

export const useCreateCustomer = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (customer: Omit<Customer, 'id'>) => api.createCustomer(customer),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.customers })
    },
  })
}

export const useUpdateCustomer = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Customer> }) =>
      api.updateCustomer(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.customers })
      queryClient.invalidateQueries({ queryKey: queryKeys.customer(id) })
    },
  })
}

export const useDeleteCustomer = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: api.deleteCustomer,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.customers })
    },
  })
}

// Vehicles
export const useVehicles = () => {
  return useQuery({
    queryKey: queryKeys.vehicles,
    queryFn: api.getVehicles,
  })
}

export const useVehicle = (id: string) => {
  return useQuery({
    queryKey: queryKeys.vehicle(id),
    queryFn: () => api.getVehicle(id),
    enabled: !!id,
  })
}

export const useCreateVehicle = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (vehicle: Omit<Vehicle, 'id'>) => api.createVehicle(vehicle),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.vehicles })
    },
  })
}

export const useUpdateVehicle = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Vehicle> }) =>
      api.updateVehicle(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.vehicles })
      queryClient.invalidateQueries({ queryKey: queryKeys.vehicle(id) })
    },
  })
}

export const useDeleteVehicle = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: api.deleteVehicle,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.vehicles })
    },
  })
}

// Depots
export const useDepots = () => {
  return useQuery({
    queryKey: queryKeys.depots,
    queryFn: api.getDepots,
  })
}

// Optimization
export const useOptimizeRoutes = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (request: OptimizationRequest) => api.optimizeRoutes(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.routes })
    },
  })
}

export const useRoutes = () => {
  return useQuery({
    queryKey: queryKeys.routes,
    queryFn: api.getRoutes,
  })
}

// Training
export const useStartTraining = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (config: TrainingConfig) => api.startTraining(config),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.trainingStatus })
    },
  })
}

export const useTrainingStatus = (enabled: boolean = true) => {
  return useQuery({
    queryKey: queryKeys.trainingStatus,
    queryFn: api.getTrainingStatus,
    refetchInterval: (data) => (data?.status === 'running' ? 2000 : false),
    enabled,
  })
}

export const useStopTraining = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: api.stopTraining,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.trainingStatus })
    },
  })
}

export const useTrainingHistory = (limit?: number) => {
  return useQuery({
    queryKey: [...queryKeys.trainingHistory, limit],
    queryFn: () => api.getTrainingHistory(limit),
  })
}

export const useModels = () => {
  return useQuery({
    queryKey: queryKeys.models,
    queryFn: api.getModels,
  })
}

export const useLoadModel = () => {
  return useMutation({
    mutationFn: api.loadModel,
  })
}

export const useDeleteModel = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: api.deleteModel,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.models })
    },
  })
}

// Metrics
export const useSystemMetrics = () => {
  return useQuery({
    queryKey: queryKeys.metrics,
    queryFn: api.getSystemMetrics,
    refetchInterval: 10000,
  })
}
