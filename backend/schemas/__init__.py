"""Schemas module"""
from .schemas import (
    Coordinates,
    CustomerCreate, CustomerUpdate, CustomerResponse,
    VehicleCreate, VehicleUpdate, VehicleResponse, VehicleStatus,
    OptimizationRequest, OptimizationResponse, OptimizedRoute, RoutePoint,
    RouteResponse, RouteStatus,
    DepotBase, DepotCreate, DepotResponse,
    TrainingConfig, TrainingStatus, TrainingResult, ModelInfo,
    GraphHopperRouteRequest, GraphHopperRouteResponse,
    HealthResponse, ErrorResponse, PaginatedResponse,
    OptimizationMethod, OrderStatus
)
