import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from backend.models.user import User
from backend.models.security import Security, LivePrice
from backend.models.portfolio import Portfolio, Holding
from sqlalchemy.future import select
from backend.db.session import AsyncSessionLocal

test_email = "portfoliotest@niftyflow.com"
test_password = "portfoliopassword"

@pytest.fixture(autouse=True)
async def cleanup_portfolio_db():
    # Setup - clear any old test data
    async with AsyncSessionLocal() as session:
        # await session.execute(Portfolio.__table__.delete())
        # await session.execute(LivePrice.__table__.delete())
        # await session.execute(Security.__table__.delete())
        # await session.execute(User.__table__.delete().where(User.email == test_email))
        await session.commit()
        
    yield
    
    # Teardown
    async with AsyncSessionLocal() as session:
        # await session.execute(Portfolio.__table__.delete())
        # await session.execute(LivePrice.__table__.delete())
        # await session.execute(Security.__table__.delete())
        # await session.execute(User.__table__.delete().where(User.email == test_email))
        await session.commit()

@pytest.mark.asyncio
async def test_portfolios_and_holdings():
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
        
        # 2. Create Security
        # We patch the verify_security_name to bypass external Yahoo Finance call during test
        from unittest.mock import patch
        with patch('backend.api.routes.securities.verify_security_name') as mock_verify:
            mock_verify.return_value = (True, "Mock Security Inc.")
            
            res_sec = await ac.post(
                "/api/v1/securities",
                json={"symbol": "TESTSEC", "name": "Test Security", "exchange": "NSE"},
                headers=headers
            )
            assert res_sec.status_code == 200
            sec_id = res_sec.json()["id"]

        # 3. Create Portfolio
        res_port = await ac.post(
            "/api/v1/portfolios",
            json={"name": "Retirement Fund", "description": "Long term"},
            headers=headers
        )
        assert res_port.status_code == 200
        port_id = res_port.json()["id"]
        
        # 4. Add Transaction (Buy 10 shares at 100)
        res_txn1 = await ac.post(
            f"/api/v1/portfolios/{port_id}/transactions",
            json={"security_id": sec_id, "transaction_type": "BUY", "quantity": 10, "price": 100.0},
            headers=headers
        )
        assert res_txn1.status_code == 200
        assert res_txn1.json()["quantity"] == 10
        assert res_txn1.json()["price"] == 100.0
        
        # 5. Add More Transaction (Buy 5 shares at 130)
        res_txn2 = await ac.post(
            f"/api/v1/portfolios/{port_id}/transactions",
            json={"security_id": sec_id, "transaction_type": "BUY", "quantity": 5, "price": 130.0},
            headers=headers
        )
        assert res_txn2.status_code == 200

        # 6. Check Portfolio Details
        res_p_detail1 = await ac.get(f"/api/v1/portfolios/{port_id}", headers=headers)
        assert res_p_detail1.status_code == 200
        data1 = res_p_detail1.json()
        assert data1["total_invested"] == 1650.0 # (10*100) + (5*130)
        
        # 7. Test Insufficient Sell
        res_txn3 = await ac.post(
            f"/api/v1/portfolios/{port_id}/transactions",
            json={"security_id": sec_id, "transaction_type": "SELL", "quantity": 20, "price": 150.0},
            headers=headers
        )
        assert res_txn3.status_code == 400

        # 8. Test Valid Sell (Sell 5 shares at 150)
        res_txn4 = await ac.post(
            f"/api/v1/portfolios/{port_id}/transactions",
            json={"security_id": sec_id, "transaction_type": "SELL", "quantity": 5, "price": 150.0},
            headers=headers
        )
        assert res_txn4.status_code == 200
        
        # 9. Verify History
        res_history = await ac.get(f"/api/v1/portfolios/{port_id}/transactions", headers=headers)
        assert res_history.status_code == 200
        history = res_history.json()
        assert len(history) == 3

        # 10. Inject LivePrice into DB
        async with AsyncSessionLocal() as session:
            lp = LivePrice(security_id=sec_id, current_price=120.0)
            session.add(lp)
            await session.commit()
            
        # 11. Check Portfolio P&L after Sell
        res_p_detail2 = await ac.get(f"/api/v1/portfolios/{port_id}", headers=headers)
        assert res_p_detail2.status_code == 200
        data2 = res_p_detail2.json()
        
        # Qty left = 10. Avg Buy = 110. Invested = 1100.
        # Current = 10 * 120 = 1200. P&L = 100. P&L% = (100/1100)*100 = 9.09%
        assert data2["total_invested"] == 1100.0
        assert data2["total_current"] == 1200.0
        assert data2["total_pnl"] == 100.0
        assert round(data2["total_pnl_percent"], 2) == 9.09
