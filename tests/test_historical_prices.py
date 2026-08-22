import pytest
import asyncio
from backend.models.historical_price import HistoricalPrice
from backend.models.security import Security
from backend.db.session import AsyncSessionLocal
from sqlalchemy import insert, delete
from main import app
import httpx
import datetime

@pytest.fixture(autouse=True)
async def cleanup():
    async with AsyncSessionLocal() as session:
        await session.execute(delete(HistoricalPrice))
        await session.execute(delete(Security).where(Security.symbol == 'TESTHIST'))
        await session.commit()
    yield
    async with AsyncSessionLocal() as session:
        await session.execute(delete(HistoricalPrice))
        await session.execute(delete(Security).where(Security.symbol == 'TESTHIST'))
        await session.commit()

@pytest.mark.asyncio
async def test_historical_prices_api():
    async with AsyncSessionLocal() as session:
        sec = Security(symbol='TESTHIST', name='Test Hist', exchange='NSE')
        session.add(sec)
        await session.commit()
        await session.refresh(sec)
        
        # Insert some historical prices
        today = datetime.date.today()
        stmt = insert(HistoricalPrice).values([
            {"security_id": sec.id, "date": today - datetime.timedelta(days=2), "close_price": 100.0},
            {"security_id": sec.id, "date": today - datetime.timedelta(days=1), "close_price": 105.0},
            {"security_id": sec.id, "date": today, "close_price": 102.5},
        ])
        await session.execute(stmt)
        await session.commit()
        
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        # Mock auth for endpoints if necessary, but this endpoint uses CurrentUser
        # We need a token
        await ac.post("/api/v1/signup", json={"email": "hist@example.com", "password": "pass"})
        res = await ac.post("/api/v1/login/access-token", data={"username": "hist@example.com", "password": "pass"})
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await ac.get(f"/api/v1/securities/symbol/TESTHIST/history", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        
        # Ensure ordered by date asc
        assert data[0]["price"] == 100.0
        assert data[1]["price"] == 105.0
        assert data[2]["price"] == 102.5
        
        # Ensure format is correct
        assert "date" in data[0]
        assert data[0]["date"] == (today - datetime.timedelta(days=2)).isoformat()
