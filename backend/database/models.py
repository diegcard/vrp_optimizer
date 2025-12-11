"""
===========================================
Modelos SQLAlchemy para VRP Optimizer
===========================================
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography
from datetime import datetime
import uuid

from database.connection import Base


class Customer(Base):
    """Modelo de Cliente/Punto de Entrega"""
    __tablename__ = "customers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    address = Column(String(500))
    location = Column(Geography(geometry_type='POINT', srid=4326), nullable=False)
    demand = Column(Integer, default=1)
    priority = Column(Integer, default=1)
    time_window_start = Column(String(8))  # HH:MM:SS
    time_window_end = Column(String(8))
    service_time_minutes = Column(Integer, default=5)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    orders = relationship("Order", back_populates="customer")


class Vehicle(Base):
    """Modelo de Vehículo"""
    __tablename__ = "vehicles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plate_number = Column(String(20), unique=True, nullable=False)
    capacity = Column(Integer, nullable=False, default=100)
    vehicle_type = Column(String(50), default='van')
    current_location = Column(Geography(geometry_type='POINT', srid=4326))
    status = Column(String(20), default='available')
    driver_name = Column(String(255))
    driver_phone = Column(String(20))
    fuel_efficiency = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    routes = relationship("Route", back_populates="vehicle")


class Depot(Base):
    """Modelo de Centro de Distribución"""
    __tablename__ = "depots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    address = Column(String(500))
    location = Column(Geography(geometry_type='POINT', srid=4326), nullable=False)
    capacity = Column(Integer)
    operating_hours_start = Column(String(8), default='06:00:00')
    operating_hours_end = Column(String(8), default='22:00:00')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    routes = relationship("Route", back_populates="depot")
    orders = relationship("Order", back_populates="depot")


class Order(Base):
    """Modelo de Pedido/Orden de Entrega"""
    __tablename__ = "orders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey('customers.id'))
    depot_id = Column(UUID(as_uuid=True), ForeignKey('depots.id'))
    status = Column(String(30), default='pending')
    demand = Column(Integer, default=1)
    priority = Column(Integer, default=1)
    required_delivery_date = Column(DateTime)
    time_window_start = Column(String(8))
    time_window_end = Column(String(8))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    customer = relationship("Customer", back_populates="orders")
    depot = relationship("Depot", back_populates="orders")


class Route(Base):
    """Modelo de Ruta Optimizada"""
    __tablename__ = "routes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey('vehicles.id'))
    depot_id = Column(UUID(as_uuid=True), ForeignKey('depots.id'))
    optimization_method = Column(String(50), nullable=False)
    status = Column(String(20), default='planned')
    total_distance_km = Column(Float)
    total_time_minutes = Column(Integer)
    total_demand = Column(Integer)
    route_geometry = Column(Geography(geometry_type='LINESTRING', srid=4326))
    sequence = Column(JSONB)  # Array ordenado de paradas
    metrics = Column(JSONB)  # Métricas adicionales
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Relaciones
    vehicle = relationship("Vehicle", back_populates="routes")
    depot = relationship("Depot", back_populates="routes")
    stops = relationship("RouteStop", back_populates="route", cascade="all, delete-orphan")


class RouteStop(Base):
    """Modelo de Parada en Ruta"""
    __tablename__ = "route_stops"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_id = Column(UUID(as_uuid=True), ForeignKey('routes.id'))
    order_id = Column(UUID(as_uuid=True), ForeignKey('orders.id'))
    customer_id = Column(UUID(as_uuid=True), ForeignKey('customers.id'))
    stop_sequence = Column(Integer, nullable=False)
    arrival_time_estimated = Column(DateTime)
    arrival_time_actual = Column(DateTime)
    departure_time_actual = Column(DateTime)
    distance_from_previous_km = Column(Float)
    time_from_previous_minutes = Column(Integer)
    status = Column(String(20), default='pending')
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    route = relationship("Route", back_populates="stops")


class RLTrainingHistory(Base):
    """Historial de Entrenamiento RL"""
    __tablename__ = "rl_training_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name = Column(String(100), nullable=False)
    episode = Column(Integer, nullable=False)
    total_reward = Column(Float)
    avg_distance = Column(Float)
    avg_deliveries = Column(Integer)
    epsilon = Column(Float)
    loss = Column(Float)
    training_time_seconds = Column(Float)
    hyperparameters = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)


class RLModel(Base):
    """Modelos RL Guardados"""
    __tablename__ = "rl_models"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    version = Column(String(20))
    model_type = Column(String(50))
    file_path = Column(String(500))
    is_active = Column(Boolean, default=False)
    metrics = Column(JSONB)
    hyperparameters = Column(JSONB)
    trained_episodes = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SystemMetric(Base):
    """Métricas del Sistema"""
    __tablename__ = "system_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float)
    metric_type = Column(String(50))
    tags = Column(JSONB)
    recorded_at = Column(DateTime, default=datetime.utcnow)
