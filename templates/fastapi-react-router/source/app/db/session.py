from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

engine_kwargs: Any = {
    "echo": settings.APP_ENV == "development",
    "pool_pre_ping": True,
}

# SQLite's async engine setup differs from Postgres and rejects queue-pool
# options like max_overflow that are valid for asyncpg-backed deployments.
if not settings.DATABASE_URL.startswith("sqlite"):
    engine_kwargs["pool_recycle"] = 3600
    engine_kwargs["max_overflow"] = 10

engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))


async def close_db() -> None:
    await engine.dispose()
