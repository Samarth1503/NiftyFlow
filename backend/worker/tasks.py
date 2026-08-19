import asyncio
import yfinance as yf
from backend.worker.celery_app import celery_app
from backend.db.session import WorkerSessionLocal
from backend.models.security import LivePrice
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql import func
import logging

logger = logging.getLogger(__name__)

async def _update_price_in_db(security_id: int, price: float):
    async with WorkerSessionLocal() as session:
        stmt = insert(LivePrice).values(
            security_id=security_id, 
            current_price=price,
            updated_at=func.now()
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=['security_id'],
            set_=dict(current_price=price, updated_at=func.now())
        )
        await session.execute(stmt)
        await session.commit()

import time

async def _fetch_and_update_async(yf_symbol: str, security_id: int):
    from backend.utils.market_data import market_data_provider
    todays_data = await market_data_provider.get_history(yf_symbol, period='1d')
    current_price = todays_data['Close'].iloc[-1]
    await _update_price_in_db(security_id, float(current_price))
    return current_price

@celery_app.task(bind=True, max_retries=3)
def fetch_and_update_price(self, symbol: str, security_id: int, exchange: str = None):
    task_id = self.request.id or "sync-test-execution"
    retry_count = self.request.retries
    start_time = time.time()
    
    logger.info(f"event=task_started task_name=fetch_and_update_price task_id={task_id} stock_symbol={symbol} exchange={exchange} security_id={security_id} retry_count={retry_count}")
    
    from backend.utils.market import format_yf_symbol
    yf_symbol = format_yf_symbol(symbol, exchange)
        
    try:
        current_price = asyncio.run(_fetch_and_update_async(yf_symbol, security_id))
        
        duration_ms = int((time.time() - start_time) * 1000)
        logger.info(f"event=task_completed task_name=fetch_and_update_price task_id={task_id} stock_symbol={symbol} yf_symbol={yf_symbol} security_id={security_id} current_price={current_price:.2f} duration_ms={duration_ms}")
        
        return current_price
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        error_msg = str(e).replace('\n', ' ').replace('\r', '')
        logger.error(f"event=task_failed task_name=fetch_and_update_price task_id={task_id} stock_symbol={symbol} yf_symbol={yf_symbol} error_type={type(e).__name__} error_msg='{error_msg}' duration_ms={duration_ms}")
        
        logger.warning(f"event=task_retry task_name=fetch_and_update_price task_id={task_id} stock_symbol={symbol} retry_count={retry_count} reason='{error_msg}'")
        raise self.retry(exc=e, countdown=10)
