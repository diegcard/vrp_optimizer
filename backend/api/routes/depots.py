"""
===========================================
API Routes - Depots (Depósitos/Centros)
===========================================
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List
from uuid import UUID
from loguru import logger

from database.connection import get_db
from schemas import DepotResponse, DepotCreate

router = APIRouter()


@router.get("", response_model=List[DepotResponse])
@router.get("/", response_model=List[DepotResponse])
async def get_depots(db: AsyncSession = Depends(get_db)):
    """
    Obtener todos los depósitos/centros de distribución.
    """
    query = text("""
        SELECT 
            id, name, address,
            ST_X(location::geometry) as longitude,
            ST_Y(location::geometry) as latitude,
            operating_hours_start, operating_hours_end
        FROM depots
        ORDER BY name
    """)
    
    result = await db.execute(query)
    rows = result.fetchall()
    
    return [
        DepotResponse(
            id=str(row.id),
            name=row.name,
            address=row.address or "",
            latitude=row.latitude,
            longitude=row.longitude,
            opening_time=str(row.operating_hours_start) if row.operating_hours_start else "06:00:00",
            closing_time=str(row.operating_hours_end) if row.operating_hours_end else "22:00:00"
        )
        for row in rows
    ]


@router.get("/{depot_id}", response_model=DepotResponse)
async def get_depot(depot_id: str, db: AsyncSession = Depends(get_db)):
    """Obtener un depósito por ID"""
    query = text("""
        SELECT 
            id, name, address,
            ST_X(location::geometry) as longitude,
            ST_Y(location::geometry) as latitude,
            operating_hours_start, operating_hours_end
        FROM depots
        WHERE id = :id
    """)
    
    result = await db.execute(query, {"id": depot_id})
    row = result.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Depósito no encontrado")
    
    return DepotResponse(
        id=str(row.id),
        name=row.name,
        address=row.address or "",
        latitude=row.latitude,
        longitude=row.longitude,
        opening_time=str(row.operating_hours_start) if row.operating_hours_start else "06:00:00",
        closing_time=str(row.operating_hours_end) if row.operating_hours_end else "22:00:00"
    )


@router.post("", response_model=DepotResponse)
@router.post("/", response_model=DepotResponse)
async def create_depot(depot: DepotCreate, db: AsyncSession = Depends(get_db)):
    """Crear un nuevo depósito"""
    query = text("""
        INSERT INTO depots (name, address, location)
        VALUES (
            :name, :address, 
            ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326)
        )
        RETURNING id, name, address,
            ST_X(location::geometry) as longitude,
            ST_Y(location::geometry) as latitude
    """)
    
    result = await db.execute(query, {
        "name": depot.name,
        "address": depot.address,
        "latitude": depot.latitude,
        "longitude": depot.longitude
    })
    await db.commit()
    
    row = result.fetchone()
    
    return DepotResponse(
        id=str(row.id),
        name=row.name,
        address=row.address or "",
        latitude=row.latitude,
        longitude=row.longitude,
        opening_time="06:00:00",
        closing_time="22:00:00"
    )
