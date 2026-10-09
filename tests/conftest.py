import asyncio
import pytest
import pytest_asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

@pytest.fixture(scope="session")
def event_loop():
    """
    Forces pytest-asyncio to use a single event loop for the test session.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

from backend.db.base import Base
from backend.db.session import get_db
import backend.db.session as session_module
from main import app

app.state.limiter.enabled = False

# Isolated SQLite in-memory database per test
@pytest_asyncio.fixture(scope="function")
async def db_session():
    # Use StaticPool and check_same_thread=False for in-memory sqlite with async
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    TestingSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    # Patch WorkerSessionLocal everywhere
    with patch.object(session_module, "WorkerSessionLocal", TestingSessionLocal):
        # We also need to patch the ones imported directly into tasks
        import backend.worker.tasks
        import backend.worker.schedule_tasks
        with patch.object(backend.worker.tasks, "WorkerSessionLocal", TestingSessionLocal, create=True):
            with patch.object(backend.worker.schedule_tasks, "WorkerSessionLocal", TestingSessionLocal, create=True):
                async with TestingSessionLocal() as session:
                    yield session
        
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        
    await engine.dispose()

@pytest.fixture(scope="function", autouse=True)
def override_get_db(db_session):
    async def _override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)

@pytest_asyncio.fixture(scope="function")
async def async_client(override_get_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
