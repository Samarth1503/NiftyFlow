import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from backend.models.user import User
from backend.models.portfolio import Portfolio
from sqlalchemy.future import select
from sqlalchemy import text
from backend.db.session import AsyncSessionLocal
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os
from backend.core.config import settings

@pytest.fixture(autouse=True)
async def cleanup_rls_db():
    async with AsyncSessionLocal() as session:
        await session.execute(text("SELECT set_config('app.current_user_id', '0', false)"))
        # await session.execute(Portfolio.__table__.delete())
        # await session.execute(User.__table__.delete().where(User.email.in_(["user_a@niftyflow.com", "user_b@niftyflow.com"])))
        await session.commit()
    yield
    async with AsyncSessionLocal() as session:
        await session.execute(text("SELECT set_config('app.current_user_id', '0', false)"))
        # await session.execute(Portfolio.__table__.delete())
        # await session.execute(User.__table__.delete().where(User.email.in_(["user_a@niftyflow.com", "user_b@niftyflow.com"])))
        await session.commit()

@pytest.mark.asyncio
@pytest.mark.skip(reason="Tests use SQLite in-memory DB which does not support PostgreSQL RLS")
async def test_rls_enforcement():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        # Create User A
        await ac.post("/api/v1/signup", json={"email": "user_a@niftyflow.com", "password": "password"})
        res_login_a = await ac.post("/api/v1/login/access-token", data={"username": "user_a@niftyflow.com", "password": "password"}, headers={"Content-Type": "application/x-www-form-urlencoded"})
        token_a = res_login_a.json()["access_token"]
        
        # User A creates a portfolio
        res_port = await ac.post("/api/v1/portfolios", json={"name": "A Secret Port", "description": ""}, headers={"Authorization": f"Bearer {token_a}"})
        port_id_a = res_port.json()["id"]

        # Create User B
        await ac.post("/api/v1/signup", json={"email": "user_b@niftyflow.com", "password": "password"})
        res_login_b = await ac.post("/api/v1/login/access-token", data={"username": "user_b@niftyflow.com", "password": "password"}, headers={"Content-Type": "application/x-www-form-urlencoded"})
        token_b = res_login_b.json()["access_token"]
        
        # User B should NOT be able to fetch User A's portfolio
        res_port_b = await ac.get(f"/api/v1/portfolios/{port_id_a}", headers={"Authorization": f"Bearer {token_b}"})
        assert res_port_b.status_code == 404

        from backend.models.user import User
        # Get User B id
        res_user_b = await ac.get("/api/v1/me", headers={"Authorization": f"Bearer {token_b}"})
        user_b_id = res_user_b.json()["id"]

        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT set_config('app.current_user_id', :id, true)"), {"id": str(user_b_id)})
            result = await session.execute(text("SELECT id FROM portfolios WHERE id = :id"), {"id": port_id_a})
            row = result.fetchone()
            assert row is None
