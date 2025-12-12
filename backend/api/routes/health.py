"""
===========================================
API Routes - Health Check
===========================================
"""

from fastapi import APIRouter, Depends
from datetime import datetime
from loguru import logger

from schemas import HealthResponse
from database.connection import check_database_connection, check_postgis_extension
from services.graphhopper_service import GraphHopperService
from services.redis_service import RedisService

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Verificar estado de todos los servicios del sistema.
    
    Retorna el estado de:
    - Base de datos PostgreSQL/PostGIS
    - Redis
    - GraphHopper
    - Modelo RL cargado
    """
    db_status = await check_database_connection()
    
    # Verificar Redis
    try:
        redis_service = RedisService()
        redis_status = await redis_service.ping()
    except Exception as e:
        logger.warning(f"Redis no disponible: {e}")
        redis_status = False
    
    # Verificar GraphHopper
    try:
        gh_service = GraphHopperService()
        gh_status = await gh_service.health_check()
    except Exception as e:
        logger.warning(f"GraphHopper no disponible: {e}")
        gh_status = False
    
    # Verificar modelo RL
    try:
        from services.optimization_service import OptimizationService
        opt_service = OptimizationService()
        # Intentar cargar modelo si existe
        model_loaded = await opt_service.load_model()
    except Exception as e:
        logger.warning(f"Error verificando modelo RL: {e}")
        model_loaded = False
    
    # El sistema es healthy si la BD está disponible (crítico)
    # Redis y GraphHopper son opcionales pero mejoran funcionalidad
    if not db_status:
        overall_status = "unhealthy"
    elif not redis_status and not gh_status:
        overall_status = "degraded"  # Funcional pero con limitaciones
    else:
        overall_status = "healthy"  # BD disponible y al menos un servicio adicional
    
    return HealthResponse(
        status=overall_status,
        database=db_status,
        redis=redis_status,
        graphhopper=gh_status,
        model_loaded=model_loaded,
        timestamp=datetime.utcnow()
    )


@router.get("/health/database")
async def database_health():
    """Verificar conexión a la base de datos"""
    db_ok = await check_database_connection()
    postgis_ok = await check_postgis_extension()
    
    return {
        "database": db_ok,
        "postgis": postgis_ok,
        "timestamp": datetime.utcnow()
    }


@router.get("/health/graphhopper")
async def graphhopper_health():
    """Verificar conexión a GraphHopper"""
    try:
        gh_service = GraphHopperService()
        status = await gh_service.health_check()
        info = await gh_service.get_info()
        return {
            "status": "healthy" if status else "unhealthy",
            "info": info,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }
