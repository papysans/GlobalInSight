"""
Database configuration for the Stock News & Analysis Platform.

Uses SQLAlchemy 2.0+ async engine with SQLite + aiosqlite.
Schema design follows relational database conventions for easy migration to PostgreSQL/MySQL.

Usage:
- API endpoints: Use `Depends(get_db)` for request-scoped sessions
- Background tasks: Use `async_session_factory()` to create independent sessions
"""

import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

# Database URL from environment variable, defaults to SQLite
# For PostgreSQL migration, change to: postgresql+asyncpg://user:password@localhost:5432/platform_db
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/platform.db")

# Create async engine
# SQLite-specific: check_same_thread=False is required for async usage
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging during development
    connect_args=connect_args,
)

# Create async session factory (SQLAlchemy 2.0+ recommended pattern)
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Declarative base for ORM models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency injection: Request-scoped session.
    
    Session is automatically closed when the request ends.
    
    Usage in API endpoints:
        @app.get("/api/example")
        async def example(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Model))
            return result.scalars().all()
    """
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database tables.
    
    Creates all tables defined in ORM models if they don't exist.
    Should be called during application startup.
    
    Note: For production, use Alembic migrations instead.
    """
    async with engine.begin() as conn:
        # Import models to ensure they are registered with Base
        from app import models  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    Close database connections.
    
    Should be called during application shutdown.
    """
    await engine.dispose()
