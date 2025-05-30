import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

try:
    from src.repotracker.config import settings
except ImportError as e:
    print(f"Error importing settings: {e}")
    print(
        "Ensure src/repotracker/config.py exists and PYTHONPATH is set correctly if needed."
    )
    os._exit(os.EX_CONFIG)

# --- SQLAlchemy Engine Setup ---
# Use the DATABASE_URL from settings
# Ensure the URL uses an async driver
# This is useful for users with wrong .env files.
DATABASE_URL = str(settings.database_url)
if "asyncpg" not in DATABASE_URL:
    print(
        f"DATABASE_URL does not seem to use an async driver (e.g., asyncpg): {DATABASE_URL}"
    )
    os._exit(os.EX_CONFIG)


# Create the async engine
try:
    async_engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
    print("Async SQLAlchemy engine created.")
except Exception as e:
    print(f"Failed to create async SQLAlchemy engine: {e}")
    os._exit(os.EX_DATAERR)


# Create an async session factory
AsyncSessionFactory = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
    class_=AsyncSession,
)
print("Async SQLAlchemy session factory created.")


# --- Session Dependency Provider ---
# This function provides a way to get a session and ensure it's closed
@asynccontextmanager
async def get_db_session() -> AsyncIterator[AsyncSession]:
    """
    Provides an asynchronous database session within a context manager.

    Ensures the session is closed and handles transaction rollback on exceptions.
    """
    session = AsyncSessionFactory()
    print(f"DB Session created: {session}")
    try:
        yield session

    except Exception as e:
        print(f"Exception occurred in DB session {session}, rolling back.")
        await session.rollback()
        # Re-raise the exception after rollback
        raise
    finally:
        await session.close()
        print(f"DB Session closed: {session}")


# Simple testing function
async def test_connection():
    print("Testing database connection...")
    try:
        async with get_db_session() as session:
            result = await session.execute(text("SELECT 1"))
            print(f"Database connection test successful. Result: {result.scalar()}")
    except Exception as e:
        print(f"Database connection test failed: {e}")


if __name__ == "__main__":
    import asyncio
    from sqlalchemy import text  # Import text for raw SQL execution

    # This is a duct-tape solution for now, it shouldn't be tested like this.
    asyncio.run(test_connection())
