from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from backend.core.config import settings

engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    echo=False,
    future=True,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            if session.in_transaction():
                await session.commit()
        except Exception:
            if session.in_transaction():
                await session.rollback()
            raise
        finally:
            await session.close()

from contextlib import asynccontextmanager

@asynccontextmanager
async def WorkerSessionLocal():
    """Provides a database session with RLS bypassed for background tasks."""
    async with AsyncSessionLocal() as session:
        try:
            from sqlalchemy import text
            await session.execute(text("SELECT set_config('app.current_user_id', '-1', false)"))
            await session.commit()
            yield session
        finally:
            await session.close()
