"""
===========================================
API Routes - Routes (Rutas)
===========================================
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Optional
from uuid import UUID
from loguru import logger

from database.connection import get_db
from schemas import RouteResponse, RouteStatus

router = APIRouter()


@router.get("/")
async def list_routes(
    status: Optional[RouteStatus] = None,
    vehicle_id: Optional[UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """
    Listar rutas del sistema.
    
    - **status**: Filtrar por estado (planned, active, completed, cancelled)
    - **vehicle_id**: Filtrar por vehículo
    """
    where_clauses = ["1=1"]
    params = {"limit": limit, "skip": skip}
    
    if status:
        where_clauses.append("r.status = :status")
        params["status"] = status.value
    if vehicle_id:
        where_clauses.append("r.vehicle_id = :vehicle_id")
        params["vehicle_id"] = str(vehicle_id)
    
    query = text(f"""
        SELECT 
            r.id, r.vehicle_id, r.depot_id,
            r.optimization_method, r.status,
            r.total_distance_km, r.total_time_minutes, r.total_demand,
            r.sequence, r.metrics,
            r.created_at, r.started_at, r.completed_at,
            v.plate_number as vehicle_plate,
            d.name as depot_name
        FROM routes r
        LEFT JOIN vehicles v ON r.vehicle_id = v.id
        LEFT JOIN depots d ON r.depot_id = d.id
        WHERE {" AND ".join(where_clauses)}
        ORDER BY r.created_at DESC
        LIMIT :limit OFFSET :skip
    """)
    
    result = await db.execute(query, params)
    rows = result.fetchall()
    
    return [
        {
            "id": row.id,
            "vehicle_id": row.vehicle_id,
            "vehicle_plate": row.vehicle_plate,
            "depot_id": row.depot_id,
            "depot_name": row.depot_name,
            "optimization_method": row.optimization_method,
            "status": row.status,
            "total_distance_km": row.total_distance_km,
            "total_time_minutes": row.total_time_minutes,
            "total_demand": row.total_demand,
            "sequence": row.sequence,
            "metrics": row.metrics,
            "created_at": row.created_at,
            "started_at": row.started_at,
            "completed_at": row.completed_at
        }
        for row in rows
    ]


@router.get("/{route_id}")
async def get_route(
    route_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Obtener detalles de una ruta específica"""
    query = text("""
        SELECT 
            r.id, r.vehicle_id, r.depot_id,
            r.optimization_method, r.status,
            r.total_distance_km, r.total_time_minutes, r.total_demand,
            r.sequence, r.metrics,
            ST_AsGeoJSON(r.route_geometry::geometry) as geometry_geojson,
            r.created_at, r.started_at, r.completed_at,
            v.plate_number as vehicle_plate,
            v.driver_name,
            d.name as depot_name,
            ST_Y(d.location::geometry) as depot_lat,
            ST_X(d.location::geometry) as depot_lon
        FROM routes r
        LEFT JOIN vehicles v ON r.vehicle_id = v.id
        LEFT JOIN depots d ON r.depot_id = d.id
        WHERE r.id = :route_id
    """)
    
    result = await db.execute(query, {"route_id": str(route_id)})
    row = result.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Ruta no encontrada")
    
    # Obtener paradas de la ruta
    stops_query = text("""
        SELECT 
            rs.id, rs.stop_sequence, rs.status,
            rs.arrival_time_estimated, rs.arrival_time_actual,
            rs.distance_from_previous_km, rs.time_from_previous_minutes,
            c.name as customer_name, c.address,
            ST_Y(c.location::geometry) as lat,
            ST_X(c.location::geometry) as lon,
            c.demand
        FROM route_stops rs
        LEFT JOIN customers c ON rs.customer_id = c.id
        WHERE rs.route_id = :route_id
        ORDER BY rs.stop_sequence
    """)
    
    stops_result = await db.execute(stops_query, {"route_id": str(route_id)})
    stops = stops_result.fetchall()
    
    return {
        "id": row.id,
        "vehicle_id": row.vehicle_id,
        "vehicle_plate": row.vehicle_plate,
        "driver_name": row.driver_name,
        "depot_id": row.depot_id,
        "depot_name": row.depot_name,
        "depot_location": {"lat": row.depot_lat, "lon": row.depot_lon},
        "optimization_method": row.optimization_method,
        "status": row.status,
        "total_distance_km": row.total_distance_km,
        "total_time_minutes": row.total_time_minutes,
        "total_demand": row.total_demand,
        "sequence": row.sequence,
        "metrics": row.metrics,
        "geometry": row.geometry_geojson,
        "created_at": row.created_at,
        "started_at": row.started_at,
        "completed_at": row.completed_at,
        "stops": [
            {
                "id": stop.id,
                "sequence": stop.stop_sequence,
                "status": stop.status,
                "customer_name": stop.customer_name,
                "address": stop.address,
                "location": {"lat": stop.lat, "lon": stop.lon},
                "demand": stop.demand,
                "arrival_time_estimated": stop.arrival_time_estimated,
                "arrival_time_actual": stop.arrival_time_actual,
                "distance_from_previous_km": stop.distance_from_previous_km,
                "time_from_previous_minutes": stop.time_from_previous_minutes
            }
            for stop in stops
        ]
    }


@router.patch("/{route_id}/status")
async def update_route_status(
    route_id: UUID,
    status: RouteStatus,
    db: AsyncSession = Depends(get_db)
):
    """Actualizar el estado de una ruta"""
    update_fields = ["status = :status"]
    params = {"route_id": str(route_id), "status": status.value}
    
    if status == RouteStatus.ACTIVE:
        update_fields.append("started_at = CURRENT_TIMESTAMP")
    elif status == RouteStatus.COMPLETED:
        update_fields.append("completed_at = CURRENT_TIMESTAMP")
    
    query = text(f"""
        UPDATE routes
        SET {", ".join(update_fields)}
        WHERE id = :route_id
        RETURNING id, status
    """)
    
    result = await db.execute(query, params)
    await db.commit()
    
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Ruta no encontrada")
    
    logger.info(f"Ruta {route_id} actualizada a estado: {status}")
    return {"message": "Estado actualizado", "route_id": row.id, "status": row.status}


@router.patch("/{route_id}/stops/{stop_sequence}/complete")
async def complete_stop(
    route_id: UUID,
    stop_sequence: int,
    db: AsyncSession = Depends(get_db)
):
    """Marcar una parada como completada"""
    query = text("""
        UPDATE route_stops
        SET status = 'completed',
            arrival_time_actual = CURRENT_TIMESTAMP
        WHERE route_id = :route_id AND stop_sequence = :stop_sequence
        RETURNING id
    """)
    
    result = await db.execute(query, {
        "route_id": str(route_id),
        "stop_sequence": stop_sequence
    })
    await db.commit()
    
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Parada no encontrada")
    
    return {"message": "Parada completada", "stop_id": row.id}


@router.delete("/{route_id}", status_code=204)
async def delete_route(
    route_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Eliminar una ruta"""
    query = text("DELETE FROM routes WHERE id = :route_id RETURNING id")
    result = await db.execute(query, {"route_id": str(route_id)})
    await db.commit()
    
    if result.fetchone() is None:
        raise HTTPException(status_code=404, detail="Ruta no encontrada")
    
    logger.info(f"Ruta eliminada: {route_id}")


@router.get("/active/summary")
async def get_active_routes_summary(
    db: AsyncSession = Depends(get_db)
):
    """Obtener resumen de rutas activas"""
    query = text("""
        SELECT 
            COUNT(*) as total_routes,
            SUM(total_distance_km) as total_distance,
            SUM(total_demand) as total_demand,
            COUNT(DISTINCT vehicle_id) as vehicles_in_use
        FROM routes
        WHERE status IN ('planned', 'active')
    """)
    
    result = await db.execute(query)
    row = result.fetchone()
    
    return {
        "total_active_routes": row.total_routes,
        "total_distance_km": row.total_distance or 0,
        "total_demand": row.total_demand or 0,
        "vehicles_in_use": row.vehicles_in_use
    }
