import asyncio
import os
import sys
import logging

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.engine import URL

from alembic import context

# Project pathing setup
# Making sure the root directory is in path, in order to find project modules.
project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
src_dir = os.path.join(project_dir, "src")

if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# For CLI-run alembic sessions, this will rely on basicConfig
logger = logging.getLogger("repotracker.alembic")

# Model Import
try:
    from db.models import Base

    target_metadata = Base.metadata
    logger.info("Successfully imported Base metadata from models.")
except ImportError as e:
    logger.error(f"Error importing Base from src.db.models: {e}")
    os._exit(os.EX_CONFIG)

# Database URL config

try:
    from repotracker.config import settings

    # Ensure the URL is a string for create_async_engine
    db_url = str(settings.database_url)
    logger.info("Database URL loaded from settings.")
except ImportError:
    logger.error("Could not import settings from src.repotracker.config.")
    logger.error("Ensure .env file is present and PYTHONPATH includes src.")
    sys.exit(1)
except Exception as e:
    logger.error(f"Failed to retrieve database URL from settings: {e}")
    sys.exit(1)

if "asyncpg" not in db_url:
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

    url = db_url
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
        db_url,
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
