"""
Alembic migration environment configuration.

Supports both sync and async database engines.
For SQLite + aiosqlite, uses synchronous mode for migrations.
For PostgreSQL + asyncpg, can use async mode.
"""

import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy import create_engine

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import models to register them with Base.metadata
# This is required for autogenerate to detect model changes
from app.database import Base
from app import models  # noqa: F401 - imports models to register with Base

target_metadata = Base.metadata

# Get database URL from environment variable or alembic.ini
def get_url() -> str:
    """Get database URL from environment or config."""
    return os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Render as batch operations for SQLite ALTER TABLE support
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with the given connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # Render as batch operations for SQLite ALTER TABLE support
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    For SQLite, we use synchronous mode since aiosqlite doesn't support
    all operations needed for migrations.
    
    For PostgreSQL with asyncpg, async mode can be used.
    """
    url = get_url()
    
    # For SQLite, use synchronous engine
    # Convert aiosqlite URL to sqlite URL for sync operations
    if url.startswith("sqlite+aiosqlite"):
        sync_url = url.replace("sqlite+aiosqlite", "sqlite")
        connectable = create_engine(
            sync_url,
            poolclass=pool.NullPool,
        )
        
        with connectable.connect() as connection:
            do_run_migrations(connection)
    
    # For PostgreSQL with asyncpg, use async engine
    elif url.startswith("postgresql+asyncpg"):
        asyncio.run(run_async_migrations())
    
    # For other databases, use standard sync approach
    else:
        connectable = create_engine(
            url,
            poolclass=pool.NullPool,
        )
        
        with connectable.connect() as connection:
            do_run_migrations(connection)


async def run_async_migrations() -> None:
    """Run migrations in async mode for PostgreSQL."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()
    
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
