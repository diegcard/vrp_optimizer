"""
===========================================
API Routes - Training (Entrenamiento RL)
===========================================
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Optional
from uuid import UUID
from loguru import logger
import asyncio

from database.connection import get_db
from schemas import TrainingConfig, TrainingStatus, TrainingResult, ModelInfo
from services.training_service import TrainingService

router = APIRouter()

# Estado global del entrenamiento (en producción usar Redis)
training_state = {
    "is_training": False,
    "current_episode": 0,
    "total_episodes": 0,
    "current_reward": None,
    "avg_reward": None,
    "epsilon": 1.0,
    "start_time": None
}


@router.post("/start", response_model=dict)
@router.post("/start/", response_model=dict)
async def start_training(
    config: TrainingConfig,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Iniciar entrenamiento del modelo de Reinforcement Learning.
    
    El entrenamiento se ejecuta en segundo plano. Usar /status para monitorear.
    
    - **model_name**: Nombre para identificar el modelo
    - **episodes**: Número de episodios de entrenamiento
    - **learning_rate**: Tasa de aprendizaje (default: 0.001)
    - **gamma**: Factor de descuento (default: 0.99)
    - **epsilon_start/end/decay**: Parámetros de exploración
    - **num_customers**: Clientes por episodio de entrenamiento
    - **num_vehicles**: Vehículos por episodio
    """
    global training_state
    
    if training_state["is_training"]:
        raise HTTPException(
            status_code=409,
            detail="Ya hay un entrenamiento en progreso"
        )
    
    # Iniciar entrenamiento en background
    training_service = TrainingService(config)
    background_tasks.add_task(run_training, training_service, config, db)
    
    training_state["is_training"] = True
    training_state["total_episodes"] = config.episodes
    training_state["current_episode"] = 0
    
    logger.info(f"Entrenamiento iniciado: {config.model_name}")
    
    return {
        "message": "Entrenamiento iniciado",
        "model_name": config.model_name,
        "episodes": config.episodes,
        "status_endpoint": "/api/v1/training/status"
    }


async def run_training(service: TrainingService, config: TrainingConfig, db: AsyncSession):
    """Ejecutar entrenamiento en background"""
    global training_state
    
    try:
        import time
        start_time = time.time()
        training_state["start_time"] = start_time
        service.start_time = start_time  # Para calcular tiempo en historial
        
        # Callback para actualizar estado
        def update_callback(episode, reward, epsilon, avg_reward):
            training_state["current_episode"] = episode
            training_state["current_reward"] = reward
            training_state["epsilon"] = epsilon
            training_state["avg_reward"] = avg_reward
            training_state["best_reward"] = max(
                training_state.get("best_reward", reward),
                reward
            )
        
        # Ejecutar entrenamiento
        result = await service.train(
            callback=update_callback,
            db_session=db
        )
        
        # Guardar resultado en BD
        await save_training_result(db, config, result)
        
        # Actualizar estado final
        training_state["current_episode"] = config.episodes
        training_state["is_training"] = False
        
        logger.info(f"Entrenamiento completado: {config.model_name}")
        
    except Exception as e:
        logger.error(f"Error en entrenamiento: {e}", exc_info=True)
        training_state["is_training"] = False
        training_state["error"] = str(e)
    finally:
        training_state["is_training"] = False


async def save_training_result(db: AsyncSession, config: TrainingConfig, result: dict):
    """Guardar resultado del entrenamiento"""
    try:
        # Guardar modelo en BD
        query = text("""
            INSERT INTO rl_models (
                name, version, model_type, file_path,
                is_active, metrics, hyperparameters, trained_episodes
            ) VALUES (
                :name, :version, :model_type, :file_path,
                false, :metrics, :hyperparameters, :episodes
            )
            ON CONFLICT (name) DO UPDATE SET
                version = EXCLUDED.version,
                file_path = EXCLUDED.file_path,
                metrics = EXCLUDED.metrics,
                trained_episodes = EXCLUDED.trained_episodes,
                updated_at = CURRENT_TIMESTAMP
        """)
        
        await db.execute(query, {
            "name": config.model_name,
            "version": "1.0",
            "model_type": "dqn",
            "file_path": result.get("model_path", ""),
            "metrics": result.get("metrics", {}),
            "hyperparameters": config.dict(),
            "episodes": config.episodes
        })
        await db.commit()
        
    except Exception as e:
        logger.error(f"Error guardando resultado: {e}")


@router.get("/status", response_model=TrainingStatus)
@router.get("/status/", response_model=TrainingStatus)
async def get_training_status():
    """
    Obtener estado actual del entrenamiento.
    
    Retorna:
    - is_training: Si hay entrenamiento activo
    - current_episode: Episodio actual
    - current_reward: Recompensa del último episodio
    - epsilon: Valor actual de exploración
    """
    import time
    
    elapsed = 0
    estimated_remaining = None
    best_reward = training_state.get("best_reward", training_state.get("current_reward"))
    
    if training_state.get("start_time"):
        elapsed = time.time() - training_state["start_time"]
        if training_state["current_episode"] > 0 and training_state["total_episodes"] > 0:
            avg_time_per_episode = elapsed / training_state["current_episode"]
            remaining_episodes = training_state["total_episodes"] - training_state["current_episode"]
            estimated_remaining = max(0, avg_time_per_episode * remaining_episodes)
    
    return TrainingStatus(
        is_training=training_state["is_training"],
        current_episode=training_state["current_episode"],
        total_episodes=training_state["total_episodes"],
        current_reward=training_state.get("current_reward"),
        best_reward=best_reward,
        avg_reward_last_100=training_state.get("avg_reward"),
        epsilon=training_state.get("epsilon", 1.0),
        elapsed_time_seconds=elapsed,
        estimated_remaining_seconds=estimated_remaining
    )


@router.post("/stop")
@router.post("/stop/")
async def stop_training():
    """Detener el entrenamiento actual"""
    global training_state
    
    if not training_state["is_training"]:
        raise HTTPException(status_code=400, detail="No hay entrenamiento activo")
    
    # TODO: Implementar señal de parada al training service
    training_state["is_training"] = False
    
    return {"message": "Señal de parada enviada"}


@router.get("/models", response_model=List[ModelInfo])
@router.get("/models/", response_model=List[ModelInfo])
async def list_models(
    db: AsyncSession = Depends(get_db)
):
    """Listar todos los modelos entrenados"""
    try:
        query = text("""
            SELECT 
                id, name, version, model_type, file_path,
                is_active, metrics, hyperparameters, trained_episodes,
                created_at, updated_at
            FROM rl_models
            ORDER BY created_at DESC
        """)
        
        result = await db.execute(query)
        rows = result.fetchall()
        
        return [
            {
                "id": row.id,
                "name": row.name,
                "version": row.version,
                "model_type": row.model_type,
                "is_active": row.is_active,
                "metrics": row.metrics,
                "trained_episodes": row.trained_episodes,
                "created_at": row.created_at
            }
            for row in rows
        ]
    except Exception as e:
        logger.warning(f"Error listando modelos: {e}")
        return []


@router.get("/history")
@router.get("/history/")
async def get_all_training_history(
    limit: int = 500,
    db: AsyncSession = Depends(get_db)
):
    """Obtener historial de todos los entrenamientos"""
    try:
        query = text("""
            SELECT 
                id, model_name, episode, total_reward, avg_distance,
                epsilon, loss, created_at
            FROM rl_training_history
            ORDER BY created_at DESC
            LIMIT :limit
        """)
        
        result = await db.execute(query, {"limit": limit})
        rows = result.fetchall()
        
        return [
            {
                "id": str(row.id),
                "model_name": row.model_name,
                "episode": row.episode,
                "total_reward": row.total_reward,
                "avg_distance": row.avg_distance,
                "epsilon": row.epsilon,
                "loss": row.loss,
                "created_at": row.created_at
            }
            for row in rows
        ]
    except Exception as e:
        logger.warning(f"Error obteniendo historial: {e}")
        return []


@router.post("/models/{model_name}/activate")
async def activate_model(
    model_name: str,
    db: AsyncSession = Depends(get_db)
):
    """Activar un modelo para uso en producción"""
    # Desactivar todos los modelos
    await db.execute(text("UPDATE rl_models SET is_active = false"))
    
    # Activar el modelo seleccionado
    result = await db.execute(
        text("UPDATE rl_models SET is_active = true WHERE name = :name RETURNING id"),
        {"name": model_name}
    )
    await db.commit()
    
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Modelo no encontrado")
    
    # Recargar modelo en servicio de optimización
    # TODO: Implementar recarga de modelo
    
    logger.info(f"Modelo activado: {model_name}")
    return {"message": f"Modelo {model_name} activado"}


@router.delete("/models/{model_name}")
async def delete_model(
    model_name: str,
    db: AsyncSession = Depends(get_db)
):
    """Eliminar un modelo"""
    result = await db.execute(
        text("DELETE FROM rl_models WHERE name = :name RETURNING id, file_path"),
        {"name": model_name}
    )
    await db.commit()
    
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Modelo no encontrado")
    
    # TODO: Eliminar archivo del modelo
    
    return {"message": f"Modelo {model_name} eliminado"}


@router.get("/history/{model_name}")
async def get_training_history(
    model_name: str,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Obtener historial de entrenamiento de un modelo"""
    query = text("""
        SELECT 
            episode, total_reward, avg_distance, avg_deliveries,
            epsilon, loss, training_time_seconds, created_at
        FROM rl_training_history
        WHERE model_name = :model_name
        ORDER BY episode DESC
        LIMIT :limit
    """)
    
    result = await db.execute(query, {"model_name": model_name, "limit": limit})
    rows = result.fetchall()
    
    return {
        "model_name": model_name,
        "history": [
            {
                "episode": row.episode,
                "total_reward": row.total_reward,
                "avg_distance": row.avg_distance,
                "epsilon": row.epsilon,
                "loss": row.loss,
                "created_at": row.created_at
            }
            for row in rows
        ]
    }


@router.post("/evaluate/{model_name}")
async def evaluate_model(
    model_name: str,
    num_scenarios: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """
    Evaluar rendimiento de un modelo en escenarios aleatorios.
    
    Compara contra baseline greedy.
    """
    # TODO: Implementar evaluación completa
    
    return {
        "model_name": model_name,
        "num_scenarios": num_scenarios,
        "results": {
            "avg_distance_rl": 0,
            "avg_distance_greedy": 0,
            "improvement_pct": 0,
            "avg_time_rl_ms": 0,
            "avg_time_greedy_ms": 0
        }
    }
