import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from backend.models.user import User
from backend.models.security import Security
from sqlalchemy.future import select
from backend.db.session import AsyncSessionLocal

test_email = "searchtest@niftyflow.com"
test_password = "searchpassword"

@pytest.fixture(autouse=True)
async def cleanup_db():
    async with AsyncSessionLocal() as session:
        await session.execute(Security.__table__.delete())
        await session.execute(User.__table__.delete().where(User.email == test_email))
        await session.commit()
        
    yield
    
    async with AsyncSessionLocal() as session:
        await session.execute(Security.__table__.delete())
        await session.execute(User.__table__.delete().where(User.email == test_email))
        await session.commit()

@pytest.mark.asyncio
async def test_securities_list_search_api():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        
        # 1. Signup & Login
        await ac.post("/api/v1/signup", json={"email": test_email, "password": test_password})
        res_login = await ac.post(
            "/api/v1/login/access-token",
            data={"username": test_email, "password": test_password},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        token = res_login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Add multiple securities out of order to test deterministic sorting
        from unittest.mock import patch
        with patch('backend.api.routes.securities.verify_security_name') as mock_verify:
            mock_verify.return_value = (True, "Mock Name")
            
            await ac.post("/api/v1/securities", json={"symbol": "ZETA", "name": "Zeta Corp", "exchange": "NSE"}, headers=headers)
            await ac.post("/api/v1/securities", json={"symbol": "ALPHA", "name": "Alpha Corp", "exchange": "NSE"}, headers=headers)
            await ac.post("/api/v1/securities", json={"symbol": "RELIANCE", "name": "Reliance Industries Limited", "exchange": "NSE"}, headers=headers)
            await ac.post("/api/v1/securities", json={"symbol": "INFY", "name": "Infosys Limited", "exchange": "NSE"}, headers=headers)

        # 3. GET /securities/ (Used by frontend for local stock list search)
        res_list = await ac.get("/api/v1/securities", headers=headers)
        assert res_list.status_code == 200
        
        data = res_list.json()
        assert len(data) == 4
        
        # 4. Assert correct schema (only basic info, no price/user info)
        assert "symbol" in data[0]
        assert "name" in data[0]
        assert "id" in data[0]
        assert "exchange" in data[0]
        assert "current_price" not in data[0]
        
        # 5. Assert deterministic sorting (Alphabetical by symbol)
        assert data[0]["symbol"] == "ALPHA"
        assert data[1]["symbol"] == "INFY"
        assert data[2]["symbol"] == "RELIANCE"
        assert data[3]["symbol"] == "ZETA"
