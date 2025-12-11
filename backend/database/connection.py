"""
===========================================
Conexión a Base de Datos PostgreSQL/PostGIS
===========================================
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from config.settings import settings
from loguru import logger

# Convertir URL sync a async
DATABASE_URL = settings.DATABASE_URL.replace(
    "postgresql://", "postgresql+asyncpg://"
)

# Crear engine async
engine = create_async_engine(
    DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=settings.DEBUG
)

# Crear session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base para modelos
Base = declarative_base()


async def get_db():
    """Dependency para obtener sesión de BD"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def check_database_connection():
    """Verificar conexión a la base de datos"""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            logger.info("✅ Conexión a PostgreSQL exitosa")
            return True
    except Exception as e:
        logger.error(f"❌ Error de conexión a PostgreSQL: {e}")
        return False


async def check_postgis_extension():
    """Verificar que PostGIS está habilitado"""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text("SELECT PostGIS_Version()")
            )
            version = result.scalar()
            logger.info(f"✅ PostGIS versión: {version}")
            return True
    except Exception as e:
        logger.error(f"❌ PostGIS no disponible: {e}")
        return False
