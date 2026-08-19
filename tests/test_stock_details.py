import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from backend.models.user import User
from backend.models.security import Security
from backend.db.session import AsyncSessionLocal

test_email = "detailstest@niftyflow.com"
test_password = "detailspassword"

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
async def test_stock_details_api():
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
        
        # 2. Add a security
        from unittest.mock import patch
        with patch('backend.api.routes.securities.verify_security_name') as mock_verify:
            mock_verify.return_value = (True, "Reliance Industries")
            
            await ac.post("/api/v1/securities", json={"symbol": "RELIANCE", "name": "Reliance Industries", "exchange": "NSE"}, headers=headers)

        # 3. Test symbol lookup using valid symbol
        # We mock get_stock_extended_details to not actually hit yahoo finance during tests
        with patch('backend.utils.market.get_stock_extended_details') as mock_details:
            mock_details.return_value = {
                "open_price": 2500.0,
                "high_price": 2550.0,
                "low_price": 2490.0,
                "volume": 1000000,
                "avg_volume": 1200000,
                "fifty_two_wk_low": 2000.0,
                "eps": 80.5,
                "previous_close": 2480.0,
                "historical_1m": [
                    {"timestamp": "2024-01-01", "price": 2400.0},
                    {"timestamp": "2024-01-02", "price": 2450.0}
                ]
            }

            res_details = await ac.get("/api/v1/securities/symbol/RELIANCE", headers=headers)
            assert res_details.status_code == 200
            
            data = res_details.json()
            assert data["symbol"] == "RELIANCE"
            assert data["name"] == "Reliance Industries"
            assert data["open_price"] == 2500.0
            assert data["previous_close"] == 2480.0
            # change should be calculated correctly if current_val and prev_close are present
            # current_val = 2480.0 (since no LivePrice injected). So change = 0
            assert data["change"] == 0.0
            assert len(data["historical_1m"]) == 2

        # 4. Test lowercase lookup
        with patch('backend.utils.market.get_stock_extended_details') as mock_details:
            mock_details.return_value = {}
            res_details_lower = await ac.get("/api/v1/securities/symbol/reliance", headers=headers)
            assert res_details_lower.status_code == 200
            assert res_details_lower.json()["symbol"] == "RELIANCE"
            
        # 5. Test unknown stock 404
        res_404 = await ac.get("/api/v1/securities/symbol/DOESNOTEXIST", headers=headers)
        assert res_404.status_code == 404
        assert "not found" in res_404.json()["detail"].lower()
