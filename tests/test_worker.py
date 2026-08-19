import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, MagicMock
from main import app
from backend.models.user import User
from backend.models.security import Security, LivePrice
from backend.db.session import AsyncSessionLocal
from sqlalchemy import delete
from sqlalchemy.future import select

test_email = "worker_test@example.com"
test_password = "TestPassword123!"

@pytest_asyncio.fixture(autouse=True)
async def cleanup():
    async with AsyncSessionLocal() as session:
        await session.execute(delete(User).where(User.email == test_email))
        await session.execute(delete(Security).where(Security.symbol == "MOCKTICKER"))
        await session.commit()
    yield
    async with AsyncSessionLocal() as session:
        await session.execute(delete(User).where(User.email == test_email))
        await session.execute(delete(Security).where(Security.symbol == "MOCKTICKER"))
        await session.commit()

@pytest.mark.asyncio
async def test_worker_and_api():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        
        # Setup Auth
        await ac.post("/api/v1/signup", json={"email": test_email, "password": test_password})
        res_login = await ac.post(
            "/api/v1/login/access-token",
            data={"username": test_email, "password": test_password},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        token = res_login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Create Security
        res_sec = await ac.post(
            "/api/v1/securities", 
            json={"symbol": "MOCKTICKER", "name": "Mock Ticker Inc.", "exchange": "NSE"},
            headers=headers
        )
        assert res_sec.status_code == 200
        sec_id = res_sec.json()["id"]

        # 2. Trigger Task API (We mock .delay so we don't need real celery running)
        with patch('backend.api.routes.securities.fetch_and_update_price.delay') as mock_delay:
            mock_delay.return_value = MagicMock(id="mock-task-id")
            res_refresh = await ac.post(f"/api/v1/securities/{sec_id}/refresh", headers=headers)
            assert res_refresh.status_code == 200
            assert res_refresh.json()["task_id"] == "mock-task-id"
            mock_delay.assert_called_once_with("MOCKTICKER", sec_id, "NSE")

        # 3. Test the actual Task logic (market_data_provider logic)
        from backend.worker.tasks import fetch_and_update_price, _update_price_in_db
        import pandas as pd

        with patch('backend.worker.tasks.asyncio.run') as mock_run:
            mock_run.return_value = 150.5

            # Call the task synchronously
            result = fetch_and_update_price("MOCKTICKER", sec_id, "NSE")
            
            assert result == 150.5
            mock_run.assert_called_once()

        # 4. Verify DB write logic directly (in the correct event loop)
        await _update_price_in_db(sec_id, 150.5)
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(LivePrice).where(LivePrice.security_id == sec_id))
            lp = result.scalars().first()
            assert lp is not None
            assert lp.current_price == 150.5
