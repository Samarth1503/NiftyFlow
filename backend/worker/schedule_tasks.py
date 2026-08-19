import asyncio
import time
import logging
import traceback
import yfinance as yf

from backend.worker.celery_app import celery_app
from backend.db.session import WorkerSessionLocal
from backend.models.security import Security, LivePrice
from backend.models.portfolio import Holding
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql import func
from backend.utils.market import format_yf_symbol

# Use standard config or defaults
from backend.core.config import settings
BATCH_SIZE = getattr(settings, 'YFINANCE_BATCH_SIZE', 50)
DELAY_SEC = getattr(settings, 'YFINANCE_REQUEST_DELAY_SECONDS', 1.0)

logger = logging.getLogger(__name__)

from backend.models.historical_price import HistoricalPrice
import pandas as pd

async def _upsert_live_price(session, security_id: int, price: float):
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

async def _upsert_historical_prices(session, security_id: int, hist_df):
    if hist_df.empty: return
    
    # Extract index as dates and 'Close' as prices
    records = []
    for date_obj, row in hist_df.iterrows():
        # pandas index is usually datetime
        d = date_obj.date()
        p = float(row['Close'])
        records.append({
            "security_id": security_id,
            "date": d,
            "close_price": p
        })
        
    if not records:
        return
        
    stmt = insert(HistoricalPrice).values(records)
    # on conflict do nothing since past closing prices rarely change
    stmt = stmt.on_conflict_do_nothing(
        index_elements=['security_id', 'date']
    )
    await session.execute(stmt)
    
    # Also delete anything older than 6 months (approx 180 days)
    six_months_ago = pd.Timestamp.now().date() - pd.Timedelta(days=180)
    del_stmt = HistoricalPrice.__table__.delete().where(
        HistoricalPrice.security_id == security_id,
        HistoricalPrice.date < six_months_ago
    )
    await session.execute(del_stmt)

async def _update_stocks_batch(stocks, task_id: str, task_name: str):
    success = 0
    failed = 0
    
    if not stocks:
        return 0, 0
        
    yf_symbols = [format_yf_symbol(stock.symbol, stock.exchange) for stock in stocks]
    symbols_str = " ".join(yf_symbols)
    
    try:
        def fetch_batch():
            return yf.download(symbols_str, period="6mo", group_by="ticker", progress=False)
            
        data = await asyncio.to_thread(fetch_batch)
    except Exception as e:
        logger.error(f"event=batch_download_failed task_name={task_name} error='{e}'")
        return 0, len(stocks)
        
    async with WorkerSessionLocal() as session:
        for stock, yf_symbol in zip(stocks, yf_symbols):
            try:
                # Extract the dataframe for the specific ticker
                stock_data = data[yf_symbol]
                
                # Drop rows where 'Close' is NaN (e.g. invalid symbols)
                hist = stock_data.dropna(subset=['Close'])
                
                if hist.empty:
                    raise ValueError(f"No price data found for {yf_symbol}")
                    
                latest_price = float(hist['Close'].iloc[-1])
                
                await _upsert_live_price(session, stock.id, latest_price)
                await _upsert_historical_prices(session, stock.id, hist)
                
                success += 1
                logger.debug(f"event=stock_updated task_name={task_name} task_id={task_id} symbol={stock.symbol} price={latest_price:.2f}")
                
            except Exception as e:
                failed += 1
                error_msg = str(e).replace('\n', ' ').replace('\r', '')
                logger.warning(f"event=stock_update_failed task_name={task_name} task_id={task_id} symbol={stock.symbol} error='{error_msg}'")
                
        await session.commit()
    
    # Rate limiting delay between batches instead of individual stocks
    await asyncio.sleep(DELAY_SEC)
    
    return success, failed


async def run_stock_updates(task_id: str, task_name: str, get_active_only: bool):
    import redis.asyncio as redis
    
    start_time = time.time()
    logger.info(f"event=task_started task_name={task_name} task_id={task_id} mode={'active_only' if get_active_only else 'full'}")
    
    # Try to acquire a distributed lock to prevent overlapping update tasks
    try:
        r = redis.from_url(settings.REDIS_URL)
        lock = r.lock("stock_updates_lock", timeout=3600)  # Max 1 hr lock
        acquired = await lock.acquire(blocking=False)
        
        if not acquired:
            logger.warning(f"event=task_skipped_due_to_lock task_name={task_name} task_id={task_id} msg='Another stock update is already running'")
            await r.close()
            return
            
    except Exception as e:
        logger.error(f"event=redis_lock_error task_name={task_name} error='{e}'")
        # Proceed cautiously if Redis is completely down but Celery somehow started? 
        # Actually Celery uses Redis, so if Redis is down, we wouldn't be here.
        return
        
    try:
        async with WorkerSessionLocal() as session:
            if get_active_only:
                stmt = select(Security).join(Holding, Holding.security_id == Security.id).distinct()
            else:
                stmt = select(Security)
                
            result = await session.execute(stmt)
            stocks = result.scalars().all()
        
        total_stocks = len(stocks)
        logger.info(f"event=universe_discovered task_name={task_name} task_id={task_id} count={total_stocks}")
        
        if total_stocks == 0:
            logger.info(f"event=task_completed task_name={task_name} task_id={task_id} total=0 success=0 failed=0 duration_s=0.0")
            return
            
        total_success = 0
        total_failed = 0
        
        for i in range(0, total_stocks, BATCH_SIZE):
            batch = stocks[i:i + BATCH_SIZE]
            logger.info(f"event=processing_batch task_name={task_name} task_id={task_id} batch_start={i} batch_size={len(batch)}")
            
            success, failed = await _update_stocks_batch(batch, task_id, task_name)
            total_success += success
            total_failed += failed
            
        duration = time.time() - start_time
        logger.info(f"event=task_completed task_name={task_name} task_id={task_id} total={total_stocks} success={total_success} failed={total_failed} duration_s={duration:.2f}")
    finally:
        try:
            await lock.release()
            await r.close()
        except Exception:
            pass


@celery_app.task(bind=True, name="stock.update_all_prices")
def update_all_stock_prices(self):
    """Nightly task to update all stored stocks."""
    task_id = self.request.id or "sync-test-execution"
    asyncio.run(run_stock_updates(task_id, "stock.update_all_prices", get_active_only=False))


@celery_app.task(bind=True, name="stock.update_active_prices")
def update_active_stock_prices(self):
    """Frequent task to update actively tracked stocks."""
    task_id = self.request.id or "sync-test-execution"
    asyncio.run(run_stock_updates(task_id, "stock.update_active_prices", get_active_only=True))

