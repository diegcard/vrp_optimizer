"""
===========================================
Configuración del Sistema VRP Optimizer
===========================================
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # Ambiente
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Base de datos
    DATABASE_URL: str = "postgresql://vrp_user:vrp_password_123@localhost:5432/vrp_routes"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # GraphHopper
    GRAPHHOPPER_URL: str = "http://localhost:8989"
    GRAPHHOPPER_TIMEOUT: int = 30
    
    # Modelo RL
    MODEL_PATH: str = "./models"
    DEFAULT_MODEL_NAME: str = "vrp_dqn_v1"
    
    # Entrenamiento RL
    RL_LEARNING_RATE: float = 0.001
    RL_GAMMA: float = 0.99
    RL_EPSILON_START: float = 1.0
    RL_EPSILON_END: float = 0.01
    RL_EPSILON_DECAY: float = 0.995
    RL_BATCH_SIZE: int = 64
    RL_MEMORY_SIZE: int = 100000
    RL_TARGET_UPDATE: int = 10
    
    # VRP Parameters
    MAX_VEHICLES: int = 50
    DEFAULT_VEHICLE_CAPACITY: int = 100
    MAX_CUSTOMERS_PER_ROUTE: int = 30
    TIME_HORIZON_HOURS: int = 12
    
    # API
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # JWT
    SECRET_KEY: str = "vrp-optimizer-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Bogotá bounds (para validación)
    BOGOTA_LAT_MIN: float = 4.4
    BOGOTA_LAT_MAX: float = 4.85
    BOGOTA_LON_MIN: float = -74.25
    BOGOTA_LON_MAX: float = -73.95
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
