import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import type { Customer, Vehicle, Route, TrainingStatus, SystemMetrics } from '../types'

interface AppState {
  // Customers
  customers: Customer[]
  selectedCustomers: string[]
  setCustomers: (customers: Customer[]) => void
  addCustomer: (customer: Customer) => void
  removeCustomer: (id: string) => void
  toggleCustomerSelection: (id: string) => void
  selectAllCustomers: () => void
  clearCustomerSelection: () => void
  
  // Vehicles
  vehicles: Vehicle[]
  selectedVehicles: string[]
  setVehicles: (vehicles: Vehicle[]) => void
  addVehicle: (vehicle: Vehicle) => void
  removeVehicle: (id: string) => void
  toggleVehicleSelection: (id: string) => void
  selectAllVehicles: () => void
  clearVehicleSelection: () => void
  
  // Routes
  routes: Route[]
  setRoutes: (routes: Route[]) => void
  clearRoutes: () => void
  
  // Map settings
  mapCenter: [number, number]
  mapZoom: number
  setMapCenter: (center: [number, number]) => void
  setMapZoom: (zoom: number) => void
  
  // Training
  trainingStatus: TrainingStatus | null
  setTrainingStatus: (status: TrainingStatus | null) => void
  
  // Metrics
  systemMetrics: SystemMetrics | null
  setSystemMetrics: (metrics: SystemMetrics | null) => void
  
  // UI State
  sidebarOpen: boolean
  toggleSidebar: () => void
}

export const useAppStore = create<AppState>()(
  devtools(
    persist(
      (set, get) => ({
        // Customers
        customers: [],
        selectedCustomers: [],
        setCustomers: (customers) => set({ customers }),
        addCustomer: (customer) => set((state) => ({
          customers: [...state.customers, customer],
        })),
        removeCustomer: (id) => set((state) => ({
          customers: state.customers.filter((c) => c.id !== id),
          selectedCustomers: state.selectedCustomers.filter((cid) => cid !== id),
        })),
        toggleCustomerSelection: (id) => set((state) => ({
          selectedCustomers: state.selectedCustomers.includes(id)
            ? state.selectedCustomers.filter((cid) => cid !== id)
            : [...state.selectedCustomers, id],
        })),
        selectAllCustomers: () => set((state) => ({
          selectedCustomers: state.customers.map((c) => c.id),
        })),
        clearCustomerSelection: () => set({ selectedCustomers: [] }),
        
        // Vehicles
        vehicles: [],
        selectedVehicles: [],
        setVehicles: (vehicles) => set({ vehicles }),
        addVehicle: (vehicle) => set((state) => ({
          vehicles: [...state.vehicles, vehicle],
        })),
        removeVehicle: (id) => set((state) => ({
          vehicles: state.vehicles.filter((v) => v.id !== id),
          selectedVehicles: state.selectedVehicles.filter((vid) => vid !== id),
        })),
        toggleVehicleSelection: (id) => set((state) => ({
          selectedVehicles: state.selectedVehicles.includes(id)
            ? state.selectedVehicles.filter((vid) => vid !== id)
            : [...state.selectedVehicles, id],
        })),
        selectAllVehicles: () => set((state) => ({
          selectedVehicles: state.vehicles.map((v) => v.id),
        })),
        clearVehicleSelection: () => set({ selectedVehicles: [] }),
        
        // Routes
        routes: [],
        setRoutes: (routes) => set({ routes }),
        clearRoutes: () => set({ routes: [] }),
        
        // Map settings
        mapCenter: [4.6577, -74.0553], // Bogotá
        mapZoom: 12,
        setMapCenter: (center) => set({ mapCenter: center }),
        setMapZoom: (zoom) => set({ mapZoom: zoom }),
        
        // Training
        trainingStatus: null,
        setTrainingStatus: (status) => set({ trainingStatus: status }),
        
        // Metrics
        systemMetrics: null,
        setSystemMetrics: (metrics) => set({ systemMetrics: metrics }),
        
        // UI State
        sidebarOpen: true,
        toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      }),
      {
        name: 'vrp-optimizer-storage',
        partialize: (state) => ({
          mapCenter: state.mapCenter,
          mapZoom: state.mapZoom,
          sidebarOpen: state.sidebarOpen,
        }),
      }
    )
  )
)
