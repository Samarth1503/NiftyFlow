import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from backend.models.user import User
from backend.models.security import Security
from backend.models.watchlist import Watchlist
from backend.models.portfolio import Portfolio, Holding, Transaction
from backend.db.session import AsyncSessionLocal
from sqlalchemy.future import select

test_email = "watchlisttest@niftyflow.com"
test_password = "watchlistpassword"

@pytest.fixture(autouse=True)
async def cleanup_db():
    async with AsyncSessionLocal() as session:
        # await session.execute(Watchlist.__table__.delete())
        await session.execute(Transaction.__table__.delete())
        # await session.execute(Holding.__table__.delete())
        # await session.execute(Portfolio.__table__.delete())
        # await session.execute(Security.__table__.delete())
        # await session.execute(User.__table__.delete().where(User.email == test_email))
        await session.commit()
        
    yield
    
    async with AsyncSessionLocal() as session:
        # await session.execute(Watchlist.__table__.delete())
        await session.execute(Transaction.__table__.delete())
        # await session.execute(Holding.__table__.delete())
        # await session.execute(Portfolio.__table__.delete())
        # await session.execute(Security.__table__.delete())
        # await session.execute(User.__table__.delete().where(User.email == test_email))
        await session.commit()

@pytest.mark.asyncio
async def test_watchlist_and_portfolio_untracked():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        # Signup & Login
        await ac.post("/api/v1/signup", json={"email": test_email, "password": test_password})
        res_login = await ac.post(
            "/api/v1/login/access-token",
            data={"username": test_email, "password": test_password},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        token = res_login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Add untracked stock to watchlist
        res_wl = await ac.post("/api/v1/watchlist/INFY", headers=headers)
        assert res_wl.status_code == 200
        assert res_wl.json()["message"] == "Added to watchlist."
        
        # Verify it's in watchlist
        res_get_wl = await ac.get("/api/v1/watchlist", headers=headers)
        assert res_get_wl.status_code == 200
        wl_data = res_get_wl.json()
        assert len(wl_data) == 1
        assert wl_data[0]["symbol"] == "INFY"
        assert wl_data[0]["name"] != ""
        
        # Test Portfolio Untracked Add
        # 1. Create Portfolio
        res_p = await ac.post("/api/v1/portfolios", json={"name": "Test Port", "description": ""}, headers=headers)
        assert res_p.status_code == 200
        port_id = res_p.json()["id"]
        
        # 2. Add untracked stock (e.g., TCS) to portfolio
        res_txn = await ac.post(f"/api/v1/portfolios/{port_id}/transactions", json={
            "symbol": "TCS",
            "transaction_type": "BUY",
            "quantity": 10,
            "price": 1500.0
        }, headers=headers)
        assert res_txn.status_code == 200
        
        # Verify it was added
        res_port_get = await ac.get(f"/api/v1/portfolios/{port_id}", headers=headers)
        port_data = res_port_get.json()
        assert len(port_data["holdings"]) == 1
        assert port_data["holdings"][0]["symbol"] == "TCS"
        assert port_data["holdings"][0]["quantity"] == 10
        
        # Clean up watchlist
        res_rm_wl = await ac.delete("/api/v1/watchlist/INFY", headers=headers)
        assert res_rm_wl.status_code == 200
        
        # Verify it's empty
        res_get_wl_empty = await ac.get("/api/v1/watchlist", headers=headers)
        assert len(res_get_wl_empty.json()) == 0
