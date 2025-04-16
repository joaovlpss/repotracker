import asyncio
import os

from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)

from src.db.models import Base
from src.repotracker.config import settings

# Import the testing database URL and check the variable's existence
TEST_DB_URL = str(settings.test_database_url)

if not TEST_DB_URL:
    pytest.fail("TEST_DATABASE_URL environment variable not set.")


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    Create an instance of the default event loop for the test session.
    Necessary for session-scoped async fixtures.
    """

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_db_engine() -> AsyncGenerator[AsyncEngine, None]:
    """
    Yeld an async SQLAlchemy engine connected to the test DB.
    Scoped to the entire test section.
    """

    engine = create_async_engine(TEST_DB_URL, echo=False)
    print(f"\n Creating test database schema on {TEST_DB_URL}")

    # We create all the tables here, as Alembic migrations won't
    # be run against the test DB automatically.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Provide the engine to the dependent fixtures
    yield engine

    # Teardown: We drop all tables after session.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    print("\n Test session finished, engine closing and tearing down.")
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """
    Yield an async SQLAlchemy session connected via the test_db_engine.
    Scoped to a single test function. Manages transactions.
    """

    session_factory = async_sessionmaker(
        bind=test_db_engine, expire_on_commit=False, class_=AsyncSession
    )

    async with session_factory as session:
        # Begin a transaction
        await session.begin()
        print(f"\n DB session {id(session)} created, transaction started.")

        try:
            # Provite the session to the test function
            yield session
        finally:
            # Rollback the transaction after the test finishes.
            await session.rollback()
            print(f"\n DB session {id(session)} transaction rolled back.")
            await session.close()

