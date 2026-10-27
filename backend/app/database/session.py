"""
Async database engine and session management.

Per ARCHITECTURE.md §7 (BACKEND): "The backend must be asynchronous where
useful." We use SQLAlchemy's async engine with the asyncpg driver.

PostgreSQL is the single authoritative source of truth (§8) — this module
is the one place the rest of the application should go through to reach it.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

settings = get_settings()

# NullPool: every checkout opens a fresh asyncpg connection rather than
# reusing one from a pool. Two reasons:
#   1. Each FastAPI request already opens/closes its own AsyncSession via
#      get_db() below, so cross-request pooling buys little at this scale.
#   2. Pooled asyncpg connections are bound to the event loop they were
#      created on. Test suites that use a new event loop per test (the
#      pytest-asyncio default) would otherwise hit
#      "Future attached to a different loop" errors when a connection
#      created in one test's loop is reused in another's. NullPool sidesteps
#      this entirely instead of requiring test-only engine configuration.
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    poolclass=NullPool,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a database session per-request."""
    async with AsyncSessionLocal() as session:
        yield session


async def check_database_connection() -> bool:
    """
    Attempt a trivial round-trip query against the database.

    Used by the /health endpoint to confirm PostgreSQL connectivity per
    ARCHITECTURE.md §102 Phase 1 definition of done ("PostgreSQL connects").
    """
    from sqlalchemy import text

    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return True
