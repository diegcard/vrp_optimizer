// Tipos principales de la aplicación

export interface Coordinates {
  lat: number
  lon: number
}

export interface Customer {
  id: string
  name: string
  location: Coordinates
  address?: string
  demand: number
  priority: number
  time_window_start?: string
  time_window_end?: string
  service_time?: number
}

export interface Vehicle {
  id: string
  plate_number: string
  capacity: number
  vehicle_type?: string
  current_location?: Coordinates
  status: 'available' | 'in_route' | 'maintenance' | 'offline'
  driver_name?: string
  driver_phone?: string
  fuel_efficiency?: number
  created_at?: string
  updated_at?: string
}

export interface Depot {
  id: string
  name: string
  latitude: number
  longitude: number
  address?: string
  opening_time?: string
  closing_time?: string
}

export interface RoutePoint {
  customer_id: string
  arrival_time: string
  departure_time: string
  sequence: number
}

export interface Route {
  vehicle_id: string
  points: RoutePoint[]
  geometry: Coordinates[]
  total_distance_km: number
  total_time_minutes: number
  total_load: number
}

export interface OptimizationRequest {
  customer_ids: string[]
  vehicle_ids: string[]
  depot_id: string
  method: 'rl' | 'greedy' | 'ortools'
  use_real_roads?: boolean
}

export interface OptimizationResponse {
  routes: Route[]
  total_distance_km: number
  total_time_minutes: number
  computation_time_ms: number
  method_used: string
  metrics: {
    vehicles_used: number
    total_stops: number
    avg_route_distance: number
    avg_route_time: number
  }
}

export interface TrainingConfig {
  num_episodes: number
  learning_rate: number
  gamma: number
  epsilon_start: number
  epsilon_end: number
  epsilon_decay: number
  batch_size: number
  buffer_size: number
}

export interface TrainingStatus {
  is_training: boolean
  current_episode: number
  total_episodes: number
  current_reward?: number
  best_reward?: number
  avg_reward_last_100?: number
  epsilon: number
  elapsed_time_seconds: number
  estimated_remaining_seconds?: number
}

export interface TrainingHistory {
  episode: number
  reward: number
  epsilon: number
  loss: number
  steps: number
  timestamp: string
}

export interface ModelInfo {
  id: string
  name: string
  created_at: string
  num_episodes: number
  final_reward: number
  file_path: string
  config: TrainingConfig
}

export interface SystemMetrics {
  api_latency_ms: number
  optimization_time_ms: number
  active_routes: number
  total_distance_today: number
  total_deliveries_today: number
  cpu_usage: number
  memory_usage: number
}

export interface ApiError {
  detail: string
  status_code: number
}
