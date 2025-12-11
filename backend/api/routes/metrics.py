"""
===========================================
API Routes - System Metrics
===========================================
"""

from fastapi import APIRouter, Depends
from datetime import datetime
from loguru import logger
import psutil
import random

router = APIRouter()


@router.get("/metrics")
async def get_system_metrics():
    """
    Obtener métricas del sistema.
    
    Retorna:
    - Uso de CPU
    - Uso de memoria
    - Entregas del día
    - Rutas optimizadas
    - Tiempo promedio de respuesta
    """
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        return {
            "cpu_usage": cpu_percent,
            "memory_usage": memory.percent,
            "memory_total": memory.total,
            "memory_available": memory.available,
            "total_deliveries_today": random.randint(50, 200),  # TODO: Obtener de BD
            "routes_optimized_today": random.randint(10, 50),
            "average_response_time_ms": random.uniform(50, 150),
            "active_vehicles": random.randint(2, 10),
            "pending_deliveries": random.randint(20, 100),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error obteniendo métricas: {e}")
        return {
            "cpu_usage": 0,
            "memory_usage": 0,
            "total_deliveries_today": 0,
            "routes_optimized_today": 0,
            "average_response_time_ms": 0,
            "active_vehicles": 0,
            "pending_deliveries": 0,
            "timestamp": datetime.now().isoformat()
        }
