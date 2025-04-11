import asyncio
import os
import sys

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.engine import URL

from alembic import context
from src.repotracker.logging_config import LogSettings

# Project pathing setup
project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
src_dir = os.path.join(project_dir, "src")

# Make sure the root directory is in path, in order to find project modules.
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)


# Setting up logs
log_settings = LogSettings("alembic_env", "./logs/alembic_logs.log")
logger = log_settings.get_logger()

# Model Import
try:
    from db.models import Base

    target_metadata = Base.metadata
    logger.info("Successfully imported Base metadata from models.")
except ImportError as e:
    logger.error(f"Error importing Base from src.db.models: {e}")
    os._exit(os.EX_CONFIG)

# Database URL config

db_url_env = os.getenv("DATABASE_URL")

if not db_url_env:
    logger.error(
        "Failed to retrieve database URL from .env file. Does your .env file have a DATABASE_URL field?"
    )
    os._exit(os.EX_CONFIG)

if "asyncpg" not in db_url_env:
    logger.warning(
        "Warning: Alembic database URL might not be using the 'asyncpg' driver."
    )


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine, though
    engines are acceptable here as well. By skipping engine creation
    we don't even need a DBAPI to be avaliable.

    Calls to context.execute() here emit the given string to the script output.
    """

    url = db_url_env
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Create async engine using the URL from config
    connectable = create_async_engine(
        db_url_env,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        logger.info("Alembic connected to database.")
        # Run migrations within the async connection context
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()
    logger.info("Alembic disconnected from database.")


# Determine mode and run migrations
if context.is_offline_mode():
    logger.info("Running migrations in offline mode...")
    run_migrations_offline()
else:
    logger.info("Running migrations in online mode...")
    asyncio.run(run_migrations_online())

logger.info("Alembic env.py finished.")
