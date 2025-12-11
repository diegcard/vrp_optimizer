"""
===========================================
API Routes - Customers (Clientes)
===========================================
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, func
from typing import List, Optional
from uuid import UUID
from loguru import logger

from database.connection import get_db
from database.models import Customer
from schemas import CustomerCreate, CustomerUpdate, CustomerResponse, Coordinates

router = APIRouter()


def location_to_coordinates(location) -> Coordinates:
    """Convertir Geography a Coordinates"""
    if location is None:
        return None
    # Extraer lat/lon de WKB
    # Esto requiere procesamiento especial con PostGIS
    return Coordinates(lat=0, lon=0)  # Placeholder


@router.get("/", response_model=List[CustomerResponse])
async def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """
    Listar todos los clientes/puntos de entrega.
    
    - **skip**: Número de registros a saltar (paginación)
    - **limit**: Número máximo de registros a retornar
    """
    query = text("""
        SELECT 
            id, name, address, 
            ST_Y(location::geometry) as lat,
            ST_X(location::geometry) as lon,
            demand, priority, 
            time_window_start, time_window_end,
            service_time_minutes,
            created_at, updated_at
        FROM customers
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :skip
    """)
    
    result = await db.execute(query, {"limit": limit, "skip": skip})
    rows = result.fetchall()
    
    customers = []
    for row in rows:
        customers.append({
            "id": row.id,
            "name": row.name,
            "address": row.address,
            "location": {"lat": row.lat, "lon": row.lon},
            "demand": row.demand,
            "priority": row.priority,
            "time_window_start": row.time_window_start,
            "time_window_end": row.time_window_end,
            "service_time_minutes": row.service_time_minutes,
            "created_at": row.created_at,
            "updated_at": row.updated_at
        })
    
    return customers


@router.get("/{customer_id}")
async def get_customer(
    customer_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Obtener un cliente por ID"""
    query = text("""
        SELECT 
            id, name, address,
            ST_Y(location::geometry) as lat,
            ST_X(location::geometry) as lon,
            demand, priority,
            time_window_start, time_window_end,
            service_time_minutes,
            created_at, updated_at
        FROM customers
        WHERE id = :customer_id
    """)
    
    result = await db.execute(query, {"customer_id": str(customer_id)})
    row = result.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    return {
        "id": row.id,
        "name": row.name,
        "address": row.address,
        "location": {"lat": row.lat, "lon": row.lon},
        "demand": row.demand,
        "priority": row.priority,
        "time_window_start": row.time_window_start,
        "time_window_end": row.time_window_end,
        "service_time_minutes": row.service_time_minutes,
        "created_at": row.created_at,
        "updated_at": row.updated_at
    }


@router.post("/", status_code=201)
async def create_customer(
    customer: CustomerCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Crear un nuevo cliente/punto de entrega.
    
    - **name**: Nombre del cliente
    - **address**: Dirección (opcional)
    - **location**: Coordenadas (lat, lon)
    - **demand**: Demanda/carga requerida
    - **priority**: Prioridad 1-5 (5 = más alta)
    """
    query = text("""
        INSERT INTO customers (
            name, address, location, demand, priority,
            time_window_start, time_window_end, service_time_minutes
        ) VALUES (
            :name, :address, 
            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326),
            :demand, :priority,
            :time_window_start, :time_window_end, :service_time_minutes
        )
        RETURNING id, name, address,
            ST_Y(location::geometry) as lat,
            ST_X(location::geometry) as lon,
            demand, priority, time_window_start, time_window_end,
            service_time_minutes, created_at, updated_at
    """)
    
    result = await db.execute(query, {
        "name": customer.name,
        "address": customer.address,
        "lat": customer.location.lat,
        "lon": customer.location.lon,
        "demand": customer.demand,
        "priority": customer.priority,
        "time_window_start": customer.time_window_start,
        "time_window_end": customer.time_window_end,
        "service_time_minutes": customer.service_time_minutes
    })
    await db.commit()
    
    row = result.fetchone()
    logger.info(f"Cliente creado: {row.id} - {row.name}")
    
    return {
        "id": row.id,
        "name": row.name,
        "address": row.address,
        "location": {"lat": row.lat, "lon": row.lon},
        "demand": row.demand,
        "priority": row.priority,
        "time_window_start": row.time_window_start,
        "time_window_end": row.time_window_end,
        "service_time_minutes": row.service_time_minutes,
        "created_at": row.created_at,
        "updated_at": row.updated_at
    }


@router.put("/{customer_id}")
async def update_customer(
    customer_id: UUID,
    customer: CustomerUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Actualizar un cliente existente"""
    # Construir query dinámicamente basado en campos proporcionados
    updates = []
    params = {"customer_id": str(customer_id)}
    
    if customer.name is not None:
        updates.append("name = :name")
        params["name"] = customer.name
    if customer.address is not None:
        updates.append("address = :address")
        params["address"] = customer.address
    if customer.location is not None:
        updates.append("location = ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)")
        params["lat"] = customer.location.lat
        params["lon"] = customer.location.lon
    if customer.demand is not None:
        updates.append("demand = :demand")
        params["demand"] = customer.demand
    if customer.priority is not None:
        updates.append("priority = :priority")
        params["priority"] = customer.priority
    
    if not updates:
        raise HTTPException(status_code=400, detail="No hay campos para actualizar")
    
    query = text(f"""
        UPDATE customers
        SET {", ".join(updates)}, updated_at = CURRENT_TIMESTAMP
        WHERE id = :customer_id
        RETURNING id, name, address,
            ST_Y(location::geometry) as lat,
            ST_X(location::geometry) as lon,
            demand, priority, time_window_start, time_window_end,
            service_time_minutes, created_at, updated_at
    """)
    
    result = await db.execute(query, params)
    await db.commit()
    
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    return {
        "id": row.id,
        "name": row.name,
        "address": row.address,
        "location": {"lat": row.lat, "lon": row.lon},
        "demand": row.demand,
        "priority": row.priority,
        "time_window_start": row.time_window_start,
        "time_window_end": row.time_window_end,
        "service_time_minutes": row.service_time_minutes,
        "created_at": row.created_at,
        "updated_at": row.updated_at
    }


@router.delete("/{customer_id}", status_code=204)
async def delete_customer(
    customer_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Eliminar un cliente"""
    query = text("DELETE FROM customers WHERE id = :customer_id RETURNING id")
    result = await db.execute(query, {"customer_id": str(customer_id)})
    await db.commit()
    
    if result.fetchone() is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    logger.info(f"Cliente eliminado: {customer_id}")


@router.get("/nearby/{lat}/{lon}")
async def get_nearby_customers(
    lat: float,
    lon: float,
    radius_km: float = Query(5.0, ge=0.1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtener clientes cercanos a una ubicación.
    
    - **lat**: Latitud del punto central
    - **lon**: Longitud del punto central
    - **radius_km**: Radio de búsqueda en kilómetros
    """
    query = text("""
        SELECT 
            id, name, address,
            ST_Y(location::geometry) as lat,
            ST_X(location::geometry) as lon,
            demand, priority,
            ST_Distance(
                location,
                ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography
            ) / 1000 as distance_km
        FROM customers
        WHERE ST_DWithin(
            location,
            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
            :radius_meters
        )
        ORDER BY distance_km
    """)
    
    result = await db.execute(query, {
        "lat": lat,
        "lon": lon,
        "radius_meters": radius_km * 1000
    })
    
    rows = result.fetchall()
    
    return [
        {
            "id": row.id,
            "name": row.name,
            "address": row.address,
            "location": {"lat": row.lat, "lon": row.lon},
            "demand": row.demand,
            "priority": row.priority,
            "distance_km": round(row.distance_km, 2)
        }
        for row in rows
    ]
