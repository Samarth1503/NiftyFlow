import pytest
import asyncio
from unittest.mock import patch, MagicMock
from backend.worker.schedule_tasks import run_stock_updates
from backend.models.security import Security
from backend.models.portfolio import Holding, Portfolio
from backend.models.user import User
from backend.db.session import AsyncSessionLocal

test_email = "celerytest@niftyflow.com"

@pytest.fixture(autouse=True)
async def cleanup_db():
    async with AsyncSessionLocal() as session:
        await session.execute(Holding.__table__.delete())
        await session.execute(Portfolio.__table__.delete())
        await session.execute(Security.__table__.delete())
        await session.execute(User.__table__.delete().where(User.email == test_email))
        await session.commit()
    yield
    async with AsyncSessionLocal() as session:
        await session.execute(Holding.__table__.delete())
        await session.execute(Portfolio.__table__.delete())
        await session.execute(Security.__table__.delete())
        await session.execute(User.__table__.delete().where(User.email == test_email))
        await session.commit()

@pytest.mark.asyncio
async def test_run_stock_updates_full():
    # Setup Data
    async with AsyncSessionLocal() as session:
        sec1 = Security(symbol="RELIANCE", name="Reliance", exchange="NSE")
        sec2 = Security(symbol="TCS", name="TCS", exchange="NSE")
        session.add_all([sec1, sec2])
        await session.commit()

    # Mock Redis Lock
    mock_redis = MagicMock()
    mock_lock = AsyncMockLock()
    mock_redis.lock.return_value = mock_lock

    with patch('redis.asyncio.from_url', return_value=mock_redis):
        with patch('backend.worker.schedule_tasks._update_stocks_batch') as mock_batch:
            mock_batch.return_value = (2, 0)
            
            await run_stock_updates("test-id", "test-task", False)
            
            # The batch processor should be called
            assert mock_batch.called
            args, _ = mock_batch.call_args
            assert len(args[0]) == 2
            assert args[0][0].symbol == "RELIANCE"

@pytest.mark.asyncio
async def test_run_stock_updates_active():
    async with AsyncSessionLocal() as session:
        user = User(email=test_email, hashed_password="pw")
        session.add(user)
        await session.flush()
        
        sec1 = Security(symbol="RELIANCE", name="Reliance", exchange="NSE")
        sec2 = Security(symbol="TCS", name="TCS", exchange="NSE")
        session.add_all([sec1, sec2])
        await session.flush()

        from sqlalchemy import text
        await session.execute(text("SELECT set_config('app.current_user_id', :id, true)"), {"id": str(user.id)})
        
        port = Portfolio(user_id=user.id, name="Test Port")
        session.add(port)
        await session.flush()
        
        # Only sec1 is active (in portfolio)
        holding = Holding(portfolio_id=port.id, security_id=sec1.id, quantity=10, average_buy_price=100)
        session.add(holding)
        await session.commit()

    mock_redis = MagicMock()
    mock_lock = AsyncMockLock()
    mock_redis.lock.return_value = mock_lock

    with patch('redis.asyncio.from_url', return_value=mock_redis):
        with patch('backend.worker.schedule_tasks._update_stocks_batch') as mock_batch:
            mock_batch.return_value = (1, 0)
            
            await run_stock_updates("test-id-active", "test-task", True)
            
            assert mock_batch.called
            args, _ = mock_batch.call_args
            assert len(args[0]) == 1
            assert args[0][0].symbol == "RELIANCE"  # TCS should be excluded since it's not in portfolio

class AsyncMockLock:
    def __init__(self):
        self.acquired = False
    
    async def acquire(self, blocking=False):
        self.acquired = True
        return True
        
    async def release(self):
        self.acquired = False
