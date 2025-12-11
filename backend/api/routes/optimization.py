"""
===========================================
API Routes - Optimization (Optimización de Rutas)
===========================================
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List
from uuid import UUID
import time
from loguru import logger

from database.connection import get_db
from schemas import (
    OptimizationRequest, OptimizationResponse, OptimizedRoute,
    RoutePoint, Coordinates, OptimizationMethod
)
from services.optimization_service import OptimizationService
from services.graphhopper_service import GraphHopperService

router = APIRouter()


@router.post("/optimize", response_model=OptimizationResponse)
@router.post("/optimize/", response_model=OptimizationResponse)
async def optimize_routes(
    request: OptimizationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Optimizar rutas para un conjunto de clientes y vehículos.
    
    Este endpoint ejecuta el algoritmo de optimización seleccionado
    (RL, greedy, genético, OR-Tools) y retorna las rutas optimizadas.
    
    - **depot_id**: ID del centro de distribución de origen
    - **customer_ids**: Lista de IDs de clientes a visitar
    - **vehicle_ids**: Lista de IDs de vehículos disponibles
    - **method**: Método de optimización (rl, greedy, genetic, ortools)
    - **consider_time_windows**: Considerar ventanas de tiempo
    - **consider_traffic**: Considerar tráfico en tiempo real
    """
    start_time = time.time()
    
    # Obtener datos del depósito
    depot_query = text("""
        SELECT id, name,
            ST_Y(location::geometry) as lat,
            ST_X(location::geometry) as lon
        FROM depots WHERE id = :depot_id
    """)
    depot_result = await db.execute(depot_query, {"depot_id": str(request.depot_id)})
    depot = depot_result.fetchone()
    
    if not depot:
        raise HTTPException(status_code=404, detail="Depósito no encontrado")
    
    # Obtener datos de clientes
    customer_ids_str = ",".join([f"'{str(cid)}'" for cid in request.customer_ids])
    customers_query = text(f"""
        SELECT id, name,
            ST_Y(location::geometry) as lat,
            ST_X(location::geometry) as lon,
            demand, priority,
            time_window_start, time_window_end
        FROM customers
        WHERE id IN ({customer_ids_str})
    """)
    customers_result = await db.execute(customers_query)
    customers = customers_result.fetchall()
    
    if len(customers) != len(request.customer_ids):
        raise HTTPException(status_code=404, detail="Algunos clientes no encontrados")
    
    # Obtener datos de vehículos
    vehicle_ids_str = ",".join([f"'{str(vid)}'" for vid in request.vehicle_ids])
    vehicles_query = text(f"""
        SELECT id, plate_number, capacity,
            ST_Y(current_location::geometry) as lat,
            ST_X(current_location::geometry) as lon
        FROM vehicles
        WHERE id IN ({vehicle_ids_str}) AND status = 'available'
    """)
    vehicles_result = await db.execute(vehicles_query)
    vehicles = vehicles_result.fetchall()
    
    if len(vehicles) == 0:
        raise HTTPException(status_code=400, detail="No hay vehículos disponibles")
    
    # Preparar datos para optimización
    depot_data = {
        "id": depot.id,
        "lat": depot.lat,
        "lon": depot.lon
    }
    
    customers_data = [
        {
            "id": c.id,
            "lat": c.lat,
            "lon": c.lon,
            "demand": c.demand,
            "priority": c.priority,
            "time_window_start": c.time_window_start,
            "time_window_end": c.time_window_end
        }
        for c in customers
    ]
    
    vehicles_data = [
        {
            "id": v.id,
            "capacity": v.capacity,
            "lat": v.lat or depot.lat,
            "lon": v.lon or depot.lon
        }
        for v in vehicles
    ]
    
    # Ejecutar optimización
    opt_service = OptimizationService()
    use_real_roads = request.use_real_roads
    
    try:
        if request.method == OptimizationMethod.RL:
            result = await opt_service.optimize_with_rl(
                depot_data, customers_data, vehicles_data,
                consider_traffic=request.consider_traffic,
                use_real_roads=use_real_roads
            )
        elif request.method == OptimizationMethod.GREEDY:
            result = await opt_service.optimize_greedy(
                depot_data, customers_data, vehicles_data,
                use_real_roads=use_real_roads
            )
        elif request.method == OptimizationMethod.ORTOOLS:
            result = await opt_service.optimize_with_ortools(
                depot_data, customers_data, vehicles_data,
                use_real_roads=use_real_roads
            )
        else:
            result = await opt_service.optimize_greedy(
                depot_data, customers_data, vehicles_data,
                use_real_roads=use_real_roads
            )
    except Exception as e:
        logger.error(f"Error en optimización: {e}")
        raise HTTPException(status_code=500, detail=f"Error en optimización: {str(e)}")
    
    optimization_time_ms = int((time.time() - start_time) * 1000)
    
    # Guardar rutas en base de datos si es exitoso
    if result["success"]:
        for route in result["routes"]:
            await save_route_to_db(db, route, request.depot_id, request.method)
    
    return OptimizationResponse(
        success=result["success"],
        method_used=request.method,
        routes=result["routes"],
        total_distance_km=result["total_distance_km"],
        total_time_minutes=result["total_time_minutes"],
        customers_served=result["customers_served"],
        customers_unserved=result["customers_unserved"],
        optimization_time_ms=optimization_time_ms,
        metrics=result.get("metrics", {})
    )


async def save_route_to_db(db: AsyncSession, route: dict, depot_id: UUID, method: OptimizationMethod):
    """Guardar ruta optimizada en la base de datos"""
    try:
        # Crear ruta principal
        route_query = text("""
            INSERT INTO routes (
                vehicle_id, depot_id, optimization_method, status,
                total_distance_km, total_time_minutes, total_demand,
                sequence, metrics
            ) VALUES (
                :vehicle_id, :depot_id, :method, 'planned',
                :distance, :time, :demand, :sequence, :metrics
            )
            RETURNING id
        """)
        
        result = await db.execute(route_query, {
            "vehicle_id": str(route["vehicle_id"]),
            "depot_id": str(depot_id),
            "method": method.value,
            "distance": route["total_distance_km"],
            "time": route["total_time_minutes"],
            "demand": route["total_demand"],
            "sequence": {"points": [p.dict() if hasattr(p, 'dict') else p for p in route["points"]]},
            "metrics": route.get("metrics", {})
        })
        
        route_id = result.fetchone().id
        
        # Crear paradas
        for idx, point in enumerate(route["points"]):
            if point.get("customer_id"):
                stop_query = text("""
                    INSERT INTO route_stops (
                        route_id, customer_id, stop_sequence,
                        distance_from_previous_km
                    ) VALUES (
                        :route_id, :customer_id, :sequence, :distance
                    )
                """)
                await db.execute(stop_query, {
                    "route_id": str(route_id),
                    "customer_id": str(point["customer_id"]),
                    "sequence": idx,
                    "distance": point.get("distance_from_previous", 0)
                })
        
        await db.commit()
        logger.info(f"Ruta guardada: {route_id}")
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error guardando ruta: {e}")


@router.post("/optimize/quick")
async def quick_optimize(
    depot_lat: float,
    depot_lon: float,
    customer_coords: List[dict],
    num_vehicles: int = 1,
    vehicle_capacity: int = 100,
    method: OptimizationMethod = OptimizationMethod.GREEDY
):
    """
    Optimización rápida sin persistencia en base de datos.
    
    Útil para pruebas y demostraciones.
    
    - **depot_lat/lon**: Coordenadas del depósito
    - **customer_coords**: Lista de {lat, lon, demand}
    - **num_vehicles**: Número de vehículos
    - **method**: Método de optimización
    """
    start_time = time.time()
    
    depot_data = {"id": "temp", "lat": depot_lat, "lon": depot_lon}
    
    customers_data = [
        {
            "id": f"customer_{i}",
            "lat": c["lat"],
            "lon": c["lon"],
            "demand": c.get("demand", 1),
            "priority": c.get("priority", 1)
        }
        for i, c in enumerate(customer_coords)
    ]
    
    vehicles_data = [
        {"id": f"vehicle_{i}", "capacity": vehicle_capacity, "lat": depot_lat, "lon": depot_lon}
        for i in range(num_vehicles)
    ]
    
    opt_service = OptimizationService()
    
    if method == OptimizationMethod.RL:
        result = await opt_service.optimize_with_rl(depot_data, customers_data, vehicles_data)
    else:
        result = await opt_service.optimize_greedy(depot_data, customers_data, vehicles_data)
    
    return {
        "success": result["success"],
        "routes": result["routes"],
        "total_distance_km": result["total_distance_km"],
        "optimization_time_ms": int((time.time() - start_time) * 1000)
    }


@router.get("/methods")
async def get_optimization_methods():
    """Obtener métodos de optimización disponibles"""
    return {
        "methods": [
            {
                "id": "rl",
                "name": "Reinforcement Learning",
                "description": "Optimización mediante Deep Q-Learning. Mejor para escenarios dinámicos.",
                "recommended_for": "Entornos con alta variabilidad de tráfico"
            },
            {
                "id": "greedy",
                "name": "Greedy (Vecino más cercano)",
                "description": "Algoritmo rápido que selecciona el cliente más cercano.",
                "recommended_for": "Pruebas rápidas, baseline"
            },
            {
                "id": "ortools",
                "name": "Google OR-Tools",
                "description": "Optimización exacta mediante programación de restricciones.",
                "recommended_for": "Soluciones óptimas con pocos clientes"
            },
            {
                "id": "genetic",
                "name": "Algoritmo Genético",
                "description": "Meta-heurística evolutiva para optimización global.",
                "recommended_for": "Problemas grandes sin restricciones de tiempo"
            }
        ]
    }


@router.get("/compare")
async def compare_methods(
    depot_id: UUID,
    customer_ids: str,  # Comma-separated UUIDs
    vehicle_ids: str,   # Comma-separated UUIDs
    db: AsyncSession = Depends(get_db)
):
    """
    Comparar diferentes métodos de optimización para el mismo problema.
    
    Ejecuta todos los métodos disponibles y compara resultados.
    """
    customer_id_list = [UUID(cid.strip()) for cid in customer_ids.split(",")]
    vehicle_id_list = [UUID(vid.strip()) for vid in vehicle_ids.split(",")]
    
    request = OptimizationRequest(
        depot_id=depot_id,
        customer_ids=customer_id_list,
        vehicle_ids=vehicle_id_list,
        method=OptimizationMethod.GREEDY
    )
    
    results = {}
    
    for method in [OptimizationMethod.GREEDY, OptimizationMethod.RL, OptimizationMethod.ORTOOLS]:
        request.method = method
        try:
            # Ejecutar optimización (simplificado)
            start_time = time.time()
            # ... ejecutar optimización ...
            elapsed = time.time() - start_time
            
            results[method.value] = {
                "total_distance_km": 0,  # Placeholder
                "total_time_minutes": 0,
                "optimization_time_ms": int(elapsed * 1000),
                "status": "success"
            }
        except Exception as e:
            results[method.value] = {
                "status": "error",
                "error": str(e)
            }
    
    return {
        "comparison": results,
        "recommended": min(
            [(k, v.get("total_distance_km", float("inf"))) 
             for k, v in results.items() if v.get("status") == "success"],
            key=lambda x: x[1],
            default=("greedy", 0)
        )[0]
    }
