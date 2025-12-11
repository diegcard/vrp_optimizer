"""
===========================================
API Routes - Vehicles (Vehículos)
===========================================
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Optional
from uuid import UUID
from loguru import logger

from database.connection import get_db
from schemas import VehicleCreate, VehicleUpdate, VehicleResponse, VehicleStatus

router = APIRouter()


@router.get("/")
async def list_vehicles(
    status: Optional[VehicleStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """
    Listar todos los vehículos de la flota.
    
    - **status**: Filtrar por estado (available, in_route, maintenance, offline)
    - **skip**: Paginación - registros a saltar
    - **limit**: Máximo de registros
    """
    where_clause = "WHERE 1=1"
    params = {"limit": limit, "skip": skip}
    
    if status:
        where_clause += " AND status = :status"
        params["status"] = status.value
    
    query = text(f"""
        SELECT 
            id, plate_number, capacity, vehicle_type,
            ST_Y(current_location::geometry) as lat,
            ST_X(current_location::geometry) as lon,
            status, driver_name, driver_phone, fuel_efficiency,
            created_at, updated_at
        FROM vehicles
        {where_clause}
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :skip
    """)
    
    result = await db.execute(query, params)
    rows = result.fetchall()
    
    vehicles = []
    for row in rows:
        vehicle = {
            "id": row.id,
            "plate_number": row.plate_number,
            "capacity": row.capacity,
            "vehicle_type": row.vehicle_type,
            "current_location": {"lat": row.lat, "lon": row.lon} if row.lat else None,
            "status": row.status,
            "driver_name": row.driver_name,
            "driver_phone": row.driver_phone,
            "fuel_efficiency": row.fuel_efficiency,
            "created_at": row.created_at,
            "updated_at": row.updated_at
        }
        vehicles.append(vehicle)
    
    return vehicles


@router.get("/{vehicle_id}")
async def get_vehicle(
    vehicle_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Obtener un vehículo por ID"""
    query = text("""
        SELECT 
            id, plate_number, capacity, vehicle_type,
            ST_Y(current_location::geometry) as lat,
            ST_X(current_location::geometry) as lon,
            status, driver_name, driver_phone, fuel_efficiency,
            created_at, updated_at
        FROM vehicles
        WHERE id = :vehicle_id
    """)
    
    result = await db.execute(query, {"vehicle_id": str(vehicle_id)})
    row = result.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    
    return {
        "id": row.id,
        "plate_number": row.plate_number,
        "capacity": row.capacity,
        "vehicle_type": row.vehicle_type,
        "current_location": {"lat": row.lat, "lon": row.lon} if row.lat else None,
        "status": row.status,
        "driver_name": row.driver_name,
        "driver_phone": row.driver_phone,
        "fuel_efficiency": row.fuel_efficiency,
        "created_at": row.created_at,
        "updated_at": row.updated_at
    }


@router.post("/", status_code=201)
async def create_vehicle(
    vehicle: VehicleCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Registrar un nuevo vehículo en la flota.
    
    - **plate_number**: Placa del vehículo (única)
    - **capacity**: Capacidad de carga
    - **vehicle_type**: Tipo (van, truck, motorcycle)
    - **current_location**: Ubicación actual (opcional)
    """
    location_sql = "NULL"
    params = {
        "plate_number": vehicle.plate_number,
        "capacity": vehicle.capacity,
        "vehicle_type": vehicle.vehicle_type,
        "driver_name": vehicle.driver_name,
        "driver_phone": vehicle.driver_phone,
        "fuel_efficiency": vehicle.fuel_efficiency
    }
    
    if vehicle.current_location:
        location_sql = "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)"
        params["lat"] = vehicle.current_location.lat
        params["lon"] = vehicle.current_location.lon
    
    query = text(f"""
        INSERT INTO vehicles (
            plate_number, capacity, vehicle_type,
            current_location, driver_name, driver_phone, fuel_efficiency
        ) VALUES (
            :plate_number, :capacity, :vehicle_type,
            {location_sql}, :driver_name, :driver_phone, :fuel_efficiency
        )
        RETURNING id, plate_number, capacity, vehicle_type,
            ST_Y(current_location::geometry) as lat,
            ST_X(current_location::geometry) as lon,
            status, driver_name, driver_phone, fuel_efficiency,
            created_at, updated_at
    """)
    
    try:
        result = await db.execute(query, params)
        await db.commit()
        row = result.fetchone()
        logger.info(f"Vehículo creado: {row.id} - {row.plate_number}")
        
        return {
            "id": row.id,
            "plate_number": row.plate_number,
            "capacity": row.capacity,
            "vehicle_type": row.vehicle_type,
            "current_location": {"lat": row.lat, "lon": row.lon} if row.lat else None,
            "status": row.status,
            "driver_name": row.driver_name,
            "driver_phone": row.driver_phone,
            "fuel_efficiency": row.fuel_efficiency,
            "created_at": row.created_at,
            "updated_at": row.updated_at
        }
    except Exception as e:
        await db.rollback()
        if "unique" in str(e).lower():
            raise HTTPException(status_code=400, detail="La placa ya existe")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{vehicle_id}")
async def update_vehicle(
    vehicle_id: UUID,
    vehicle: VehicleUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Actualizar un vehículo"""
    updates = []
    params = {"vehicle_id": str(vehicle_id)}
    
    if vehicle.capacity is not None:
        updates.append("capacity = :capacity")
        params["capacity"] = vehicle.capacity
    if vehicle.vehicle_type is not None:
        updates.append("vehicle_type = :vehicle_type")
        params["vehicle_type"] = vehicle.vehicle_type
    if vehicle.current_location is not None:
        updates.append("current_location = ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)")
        params["lat"] = vehicle.current_location.lat
        params["lon"] = vehicle.current_location.lon
    if vehicle.status is not None:
        updates.append("status = :status")
        params["status"] = vehicle.status.value
    if vehicle.driver_name is not None:
        updates.append("driver_name = :driver_name")
        params["driver_name"] = vehicle.driver_name
    
    if not updates:
        raise HTTPException(status_code=400, detail="No hay campos para actualizar")
    
    query = text(f"""
        UPDATE vehicles
        SET {", ".join(updates)}, updated_at = CURRENT_TIMESTAMP
        WHERE id = :vehicle_id
        RETURNING id, plate_number, capacity, vehicle_type,
            ST_Y(current_location::geometry) as lat,
            ST_X(current_location::geometry) as lon,
            status, driver_name, driver_phone, fuel_efficiency,
            created_at, updated_at
    """)
    
    result = await db.execute(query, params)
    await db.commit()
    
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    
    return {
        "id": row.id,
        "plate_number": row.plate_number,
        "capacity": row.capacity,
        "vehicle_type": row.vehicle_type,
        "current_location": {"lat": row.lat, "lon": row.lon} if row.lat else None,
        "status": row.status,
        "driver_name": row.driver_name,
        "driver_phone": row.driver_phone,
        "fuel_efficiency": row.fuel_efficiency,
        "created_at": row.created_at,
        "updated_at": row.updated_at
    }


@router.patch("/{vehicle_id}/location")
async def update_vehicle_location(
    vehicle_id: UUID,
    lat: float,
    lon: float,
    db: AsyncSession = Depends(get_db)
):
    """Actualizar solo la ubicación de un vehículo (para tracking GPS)"""
    query = text("""
        UPDATE vehicles
        SET current_location = ST_SetSRID(ST_MakePoint(:lon, :lat), 4326),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = :vehicle_id
        RETURNING id, plate_number
    """)
    
    result = await db.execute(query, {
        "vehicle_id": str(vehicle_id),
        "lat": lat,
        "lon": lon
    })
    await db.commit()
    
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    
    return {"message": "Ubicación actualizada", "vehicle_id": row.id}


@router.delete("/{vehicle_id}", status_code=204)
async def delete_vehicle(
    vehicle_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Eliminar un vehículo"""
    query = text("DELETE FROM vehicles WHERE id = :vehicle_id RETURNING id")
    result = await db.execute(query, {"vehicle_id": str(vehicle_id)})
    await db.commit()
    
    if result.fetchone() is None:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    
    logger.info(f"Vehículo eliminado: {vehicle_id}")


@router.get("/available/count")
async def get_available_vehicles_count(
    db: AsyncSession = Depends(get_db)
):
    """Obtener conteo de vehículos disponibles por tipo"""
    query = text("""
        SELECT vehicle_type, COUNT(*) as count
        FROM vehicles
        WHERE status = 'available'
        GROUP BY vehicle_type
    """)
    
    result = await db.execute(query)
    rows = result.fetchall()
    
    return {
        "total_available": sum(row.count for row in rows),
        "by_type": {row.vehicle_type: row.count for row in rows}
    }
