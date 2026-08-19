
import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from backend.models.user import User
from backend.db.session import AsyncSessionLocal

test_email = "graphqty@niftyflow.com"
test_password = "password123"

@pytest.fixture(autouse=True)
async def cleanup_db():
    async with AsyncSessionLocal() as session:
        from backend.models.portfolio import Portfolio
        await session.execute(Portfolio.__table__.delete())
        await session.execute(User.__table__.delete().where(User.email == test_email))
        await session.commit()

@pytest.mark.asyncio
async def test_quantity_and_graph():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        # Auth
        await ac.post("/api/v1/signup", json={"email": test_email, "password": test_password})
        login_res = await ac.post("/api/v1/login/access-token", data={"username": test_email, "password": test_password})
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create portfolio
        res = await ac.post("/api/v1/portfolios", json={"name": "Qty Graph Test"}, headers=headers)
        p_id = res.json()["id"]
        
        # Valid quantity
        res = await ac.post(f"/api/v1/portfolios/{p_id}/transactions", json={"symbol": "INFY.NS", "transaction_type": "BUY", "quantity": 10, "price": 100}, headers=headers)
        assert res.status_code == 200
        
        # Invalid quantities
        res = await ac.post(f"/api/v1/portfolios/{p_id}/transactions", json={"symbol": "INFY.NS", "transaction_type": "BUY", "quantity": 10.5, "price": 100}, headers=headers)
        assert res.status_code == 422
        
        res = await ac.post(f"/api/v1/portfolios/{p_id}/transactions", json={"symbol": "INFY.NS", "transaction_type": "BUY", "quantity": 0, "price": 100}, headers=headers)
        assert res.status_code == 422
        
        res = await ac.post(f"/api/v1/portfolios/{p_id}/transactions", json={"symbol": "INFY.NS", "transaction_type": "BUY", "quantity": -5, "price": 100}, headers=headers)
        assert res.status_code == 422
        
        # Historical Graph
        from datetime import datetime, timedelta
        old_date = datetime.now() - timedelta(days=15)
        await ac.post(f"/api/v1/portfolios/{p_id}/transactions", json={"symbol": "RELIANCE.NS", "transaction_type": "BUY", "quantity": 5, "price": 1000, "timestamp": old_date.isoformat()}, headers=headers)
        
        res = await ac.get(f"/api/v1/portfolios/{p_id}/chart", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 31
        
        # Verify Option B behavior
        assert data[0]["value"] == 0 # 30 days ago, no holdings
        assert data[-1]["value"] > 0 # Today, we hold INFY and RELIANCE

