"""
Database Connection and Session Management
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator

from app.core.config import settings

# Build async URL
db_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Handle Neon's sslmode parameter
connect_args = {}
if "sslmode=" in db_url or "neon.tech" in db_url:
    # Remove only sslmode param, keep others
    if "?" in db_url:
        base, params = db_url.split("?", 1)
        filtered = "&".join(p for p in params.split("&") if not p.startswith("sslmode="))
        db_url = f"{base}?{filtered}" if filtered else base
    connect_args["ssl"] = "require"

# Create async engine
# pool_pre_ping: test connections before use (required for Neon which closes
# idle connections after a few minutes — without this, random 500s from
# "connection is closed" errors).
# pool_recycle: proactively recycle connections older than 5 min.
engine = create_async_engine(
    db_url,
    echo=settings.DEBUG_MODE,
    future=True,
    pool_size=5,
    max_overflow=2,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args=connect_args,
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Base class for models
Base = declarative_base()


# Dependency for getting database session
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
