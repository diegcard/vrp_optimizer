"""
===========================================
VRP Optimizer - FastAPI Backend Principal
Sistema de Optimización de Rutas con Reinforcement Learning
===========================================
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
from loguru import logger

from config.settings import settings
from api.routes import customers, vehicles, routes, optimization, training, health, metrics, depots
from database.connection import engine, get_db
from services.graphhopper_service import GraphHopperService
from services.optimization_service import OptimizationService

# Configurar logging
logger.add(
    "logs/vrp_optimizer.log",
    rotation="500 MB",
    retention="10 days",
    level="INFO"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida de la aplicación"""
    logger.info("🚀 Iniciando VRP Optimizer Backend...")
    
    # Inicializar servicios
    try:
        # Verificar conexión a GraphHopper
        gh_service = GraphHopperService()
        await gh_service.health_check()
        logger.info("✅ GraphHopper conectado")
    except Exception as e:
        logger.warning(f"⚠️ GraphHopper no disponible: {e}")
    
    # Cargar modelo RL si existe (no crítico para inicio)
    try:
        opt_service = OptimizationService()
        model_loaded = await opt_service.load_model()
        if model_loaded:
            logger.info("✅ Modelo RL cargado")
        else:
            logger.info("ℹ️ Modelo RL no encontrado (se puede entrenar uno nuevo)")
    except Exception as e:
        logger.warning(f"⚠️ Error verificando modelo RL: {e}")
    
    logger.info("✅ VRP Optimizer Backend listo")
    
    yield
    
    # Cleanup
    logger.info("🛑 Cerrando VRP Optimizer Backend...")


# Crear aplicación FastAPI
# redirect_slashes=False evita redirects 307 que causan problemas con Docker
app = FastAPI(
    title="VRP Optimizer API",
    description="""
    ## Sistema de Optimización de Rutas de Última Milla
    
    Esta API proporciona endpoints para:
    
    * 🗺️ **Gestión de Clientes**: CRUD de puntos de entrega
    * 🚗 **Gestión de Flota**: Control de vehículos
    * 🛤️ **Optimización de Rutas**: Algoritmos RL y heurísticos
    * 🤖 **Entrenamiento RL**: Entrenar y evaluar modelos
    * 📊 **Métricas**: Monitoreo del sistema
    
    ### Tecnologías:
    - FastAPI + PostgreSQL/PostGIS
    - PyTorch + Stable-Baselines3 para RL
    - GraphHopper para motor de rutas
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    redirect_slashes=False
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(metrics.router, prefix="/api/v1", tags=["Metrics"])
app.include_router(customers.router, prefix="/api/v1/customers", tags=["Customers"])
app.include_router(vehicles.router, prefix="/api/v1/vehicles", tags=["Vehicles"])
app.include_router(depots.router, prefix="/api/v1/depots", tags=["Depots"])
app.include_router(routes.router, prefix="/api/v1/routes", tags=["Routes"])
app.include_router(optimization.router, prefix="/api/v1/optimization", tags=["Optimization"])
app.include_router(training.router, prefix="/api/v1/training", tags=["RL Training"])


@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "VRP Optimizer API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Manejador global de excepciones"""
    logger.error(f"Error no manejado: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor"}
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
