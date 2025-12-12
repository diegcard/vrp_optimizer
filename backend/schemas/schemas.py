"""
===========================================
Schemas Pydantic para VRP Optimizer
===========================================
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Any
from datetime import datetime, time
from uuid import UUID
from enum import Enum


# ===========================================
# Enums
# ===========================================

class VehicleStatus(str, Enum):
    AVAILABLE = "available"
    IN_ROUTE = "in_route"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"


class OrderStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RouteStatus(str, Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class OptimizationMethod(str, Enum):
    RL = "rl"
    GREEDY = "greedy"
    GENETIC = "genetic"
    ORTOOLS = "ortools"


# ===========================================
# Schemas de Coordenadas
# ===========================================

class Coordinates(BaseModel):
    """Coordenadas geográficas"""
    lat: float = Field(..., ge=-90, le=90, description="Latitud")
    lon: float = Field(..., ge=-180, le=180, description="Longitud")
    
    @validator('lat')
    def validate_bogota_lat(cls, v):
        # Validar que está en rango de Bogotá (aproximado)
        if not (4.4 <= v <= 4.85):
            pass  # Permitir cualquier coordenada, pero se podría restringir
        return v


# ===========================================
# Schemas de Cliente
# ===========================================

class CustomerBase(BaseModel):
    """Base de cliente"""
    name: str = Field(..., min_length=1, max_length=255)
    address: Optional[str] = None
    demand: int = Field(default=1, ge=1)
    priority: int = Field(default=1, ge=1, le=5)
    time_window_start: Optional[Any] = None
    time_window_end: Optional[Any] = None
    service_time_minutes: int = Field(default=5, ge=1)
    
    @validator('time_window_start', 'time_window_end', pre=True)
    def convert_time_to_string(cls, v):
        if v is None:
            return None
        if isinstance(v, time):
            return v.strftime("%H:%M")
        return str(v) if v else None


class CustomerCreate(CustomerBase):
    """Crear cliente"""
    location: Coordinates


class CustomerUpdate(BaseModel):
    """Actualizar cliente"""
    name: Optional[str] = None
    address: Optional[str] = None
    location: Optional[Coordinates] = None
    demand: Optional[int] = None
    priority: Optional[int] = None


class CustomerResponse(CustomerBase):
    """Respuesta de cliente"""
    id: UUID
    location: Coordinates
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ===========================================
# Schemas de Vehículo
# ===========================================

class VehicleBase(BaseModel):
    """Base de vehículo"""
    plate_number: str = Field(..., min_length=1, max_length=20)
    capacity: int = Field(default=100, ge=1)
    vehicle_type: str = Field(default="van")
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    fuel_efficiency: Optional[float] = None


class VehicleCreate(VehicleBase):
    """Crear vehículo"""
    current_location: Optional[Coordinates] = None


class VehicleUpdate(BaseModel):
    """Actualizar vehículo"""
    capacity: Optional[int] = None
    vehicle_type: Optional[str] = None
    current_location: Optional[Coordinates] = None
    status: Optional[VehicleStatus] = None
    driver_name: Optional[str] = None


class VehicleResponse(VehicleBase):
    """Respuesta de vehículo"""
    id: UUID
    current_location: Optional[Coordinates] = None
    status: VehicleStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ===========================================
# Schemas de Optimización
# ===========================================

class OptimizationRequest(BaseModel):
    """Solicitud de optimización de rutas"""
    depot_id: str
    customer_ids: List[str] = Field(..., min_length=1)
    vehicle_ids: List[str] = Field(..., min_length=1)
    method: OptimizationMethod = OptimizationMethod.RL
    max_time_minutes: Optional[int] = Field(default=480, ge=60)  # 8 horas default
    consider_time_windows: bool = True
    consider_traffic: bool = True
    use_real_roads: bool = False  # Si usar GraphHopper para rutas reales


class RoutePoint(BaseModel):
    """Punto en una ruta"""
    customer_id: Optional[UUID] = None
    location: Coordinates
    arrival_time: Optional[datetime] = None
    demand: int = 0
    sequence: int


class OptimizedRoute(BaseModel):
    """Ruta optimizada para un vehículo"""
    vehicle_id: UUID
    points: List[RoutePoint]
    total_distance_km: float
    total_time_minutes: int
    total_demand: int
    geometry: List[Coordinates]  # Polilínea para dibujar


class OptimizationResponse(BaseModel):
    """Respuesta de optimización"""
    success: bool
    method_used: OptimizationMethod
    routes: List[OptimizedRoute]
    total_distance_km: float
    total_time_minutes: int
    customers_served: int
    customers_unserved: int
    optimization_time_ms: int
    metrics: dict = {}


# ===========================================
# Schemas de Ruta
# ===========================================

class RouteResponse(BaseModel):
    """Respuesta de ruta guardada"""
    id: UUID
    vehicle_id: UUID
    depot_id: UUID
    optimization_method: str
    status: RouteStatus
    total_distance_km: Optional[float]
    total_time_minutes: Optional[int]
    total_demand: Optional[int]
    sequence: Optional[List[dict]]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ===========================================
# Schemas de Depot
# ===========================================

class DepotBase(BaseModel):
    """Base de depósito"""
    name: str = Field(..., min_length=1, max_length=255)
    address: Optional[str] = None
    opening_time: Optional[str] = "06:00:00"
    closing_time: Optional[str] = "22:00:00"


class DepotCreate(DepotBase):
    """Crear depósito"""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class DepotResponse(DepotBase):
    """Respuesta de depósito"""
    id: str
    latitude: float
    longitude: float
    
    class Config:
        from_attributes = True


# ===========================================
# Schemas de Entrenamiento RL
# ===========================================

class TrainingConfig(BaseModel):
    """Configuración de entrenamiento"""
    model_name: str = Field(default="vrp_dqn_v1")
    episodes: int = Field(default=1000, ge=1)
    learning_rate: float = Field(default=0.001, gt=0)
    gamma: float = Field(default=0.99, ge=0, le=1)
    epsilon_start: float = Field(default=1.0, ge=0, le=1)
    epsilon_end: float = Field(default=0.01, ge=0, le=1)
    epsilon_decay: float = Field(default=0.995, ge=0, le=1)
    batch_size: int = Field(default=64, ge=1)
    memory_size: int = Field(default=100000, ge=1000)
    num_customers: int = Field(default=20, ge=5, le=100)
    num_vehicles: int = Field(default=3, ge=1, le=20)
    vehicle_capacity: int = Field(default=100, ge=1)


class TrainingStatus(BaseModel):
    """Estado del entrenamiento"""
    is_training: bool
    current_episode: int
    total_episodes: int
    current_reward: Optional[float] = None
    best_reward: Optional[float] = None
    avg_reward_last_100: Optional[float] = None
    epsilon: float = 1.0
    elapsed_time_seconds: float = 0.0
    estimated_remaining_seconds: Optional[float] = None


class TrainingResult(BaseModel):
    """Resultado del entrenamiento"""
    model_name: str
    episodes_trained: int
    final_avg_reward: float
    best_reward: float
    training_time_seconds: float
    model_path: str


class ModelInfo(BaseModel):
    """Información de un modelo"""
    id: UUID
    name: str
    version: Optional[str]
    model_type: str
    is_active: bool
    metrics: Optional[dict]
    trained_episodes: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ===========================================
# Schemas de GraphHopper
# ===========================================

class GraphHopperRouteRequest(BaseModel):
    """Solicitud de ruta a GraphHopper"""
    points: List[Coordinates]
    profile: str = "car"
    locale: str = "es"
    instructions: bool = True
    points_encoded: bool = False


class GraphHopperRouteResponse(BaseModel):
    """Respuesta de GraphHopper"""
    distance_meters: float
    time_ms: int
    points: List[Coordinates]
    instructions: Optional[List[dict]] = None


# ===========================================
# Schemas Generales
# ===========================================

class HealthResponse(BaseModel):
    """Respuesta de health check"""
    status: str
    database: bool
    redis: bool
    graphhopper: bool
    model_loaded: bool
    timestamp: datetime


class ErrorResponse(BaseModel):
    """Respuesta de error"""
    detail: str
    code: Optional[str] = None


class PaginatedResponse(BaseModel):
    """Respuesta paginada"""
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int
