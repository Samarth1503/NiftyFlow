from backend.core.config import settings
from backend.api.limiter import limiter
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.deps import SessionDep, CurrentUser
from backend.models.security import Security
from backend.models.schemas import SecurityCreate, SecurityResponse, StockDetailsResponse
from backend.worker.tasks import fetch_and_update_price
import logging

from backend.utils.market import verify_security_name
import asyncio

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("", response_model=SecurityResponse)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def create_security(
    request: Request,
    security_in: SecurityCreate,
    session: SessionDep,
    current_user: CurrentUser
):
    result = await session.execute(select(Security).where(Security.symbol == security_in.symbol))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Security with this symbol already exists")
        
    # Loose name validation
    is_valid, actual_name = await asyncio.to_thread(
        verify_security_name, 
        security_in.symbol, 
        security_in.exchange, 
        security_in.name
    )
    
    if not is_valid:
        raise HTTPException(
            status_code=400, 
            detail=f"Name mismatch. Provided: '{security_in.name}', but official symbol name is '{actual_name}'."
        )
    
    security = Security(**security_in.model_dump())
    session.add(security)
    await session.flush()
    await session.refresh(security)
    return security

@router.get("/search", response_model=list[SecurityResponse])
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def search_securities(request: Request, session: SessionDep, current_user: CurrentUser, q: str = ""):
    from sqlalchemy import or_
    if not q or len(q) < 2:
        return []
    
    search_term = f"{q}%"
    stmt = select(Security).where(
        or_(
            Security.symbol.ilike(search_term),
            Security.name.ilike(search_term)
        )
    ).order_by(Security.symbol).limit(15)
    
    result = await session.execute(stmt)
    return result.scalars().all()

@router.get("", response_model=list[SecurityResponse])
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def list_securities(request: Request, session: SessionDep, current_user: CurrentUser):
    result = await session.execute(select(Security).order_by(Security.symbol))
    return result.scalars().all()

@router.get("/indices")
async def get_indices(current_user: CurrentUser):
    from backend.utils.market import get_live_indices
    # We do not need session for this, just an external API call
    indices = await asyncio.to_thread(get_live_indices)
    return indices

@router.get("/predictions/bulk")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def get_bulk_predictions(request: Request, session: SessionDep, current_user: CurrentUser):
    from backend.models.prediction import Prediction
    stmt = select(Prediction).distinct(Prediction.security_id).order_by(Prediction.security_id, Prediction.prediction_date.desc())
    result = await session.execute(stmt)
    predictions = result.scalars().all()
    # Pydantic will serialize the ORM models. We return a dict.
    return {p.security_id: p for p in predictions}

@router.get("/symbol/{symbol}", response_model=StockDetailsResponse)
async def get_security_by_symbol(symbol: str, session: SessionDep, current_user: CurrentUser):
    from backend.models.security import LivePrice
    from backend.utils.market import get_stock_extended_details
    
    # Normalize input
    symbol = symbol.upper().strip()
    
    # Lookup in DB
    result = await session.execute(select(Security).where(Security.symbol == symbol))
    security = result.scalars().first()
    if not security:
        # Dynamically seed it if it's a valid yfinance ticker
        import yfinance as yf
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            info = await asyncio.to_thread(lambda: yf.Ticker(f"{symbol}.NS").info)
            if not info or ('regularMarketPrice' not in info and 'previousClose' not in info and 'shortName' not in info):
                info = await asyncio.to_thread(lambda: yf.Ticker(symbol).info)
                if not info or ('regularMarketPrice' not in info and 'previousClose' not in info and 'shortName' not in info):
                    raise HTTPException(status_code=404, detail="Security not found and could not be resolved.")
                exchange = None
            else:
                exchange = "NSE"
                
            actual_name = info.get('longName') or info.get('shortName') or symbol
            current_price = info.get('regularMarketPrice') or info.get('currentPrice') or info.get('previousClose') or 0.0
            
            # Transactionally add
            security = Security(symbol=symbol, name=actual_name, exchange=exchange)
            session.add(security)
            await session.flush()
            
            new_lp = LivePrice(security_id=security.id, current_price=current_price)
            session.add(new_lp)
            await session.flush()
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to seed {symbol}: {e}")
            raise HTTPException(status_code=404, detail="Security not found and could not be resolved.")
            
    price_res = await session.execute(select(LivePrice).where(LivePrice.security_id == security.id))
    live_price = price_res.scalars().first()
    
    # Fetch extended details from yfinance (Threaded because it's synchronous I/O)
    extended = await asyncio.to_thread(get_stock_extended_details, security.symbol, security.exchange)
    
    current_val = live_price.current_price if live_price else extended.get("previous_close")
    prev_close = extended.get("previous_close")
    
    change = None
    change_percent = None
    if current_val and prev_close:
        change = current_val - prev_close
        change_percent = (change / prev_close) * 100
        
    return {
        "id": security.id,
        "symbol": security.symbol,
        "name": security.name,
        "exchange": security.exchange,
        "current_price": current_val,
        "previous_close": prev_close,
        "change": change,
        "change_percent": change_percent,
        "open_price": extended.get("open_price"),
        "high_price": extended.get("high_price"),
        "low_price": extended.get("low_price"),
        "volume": extended.get("volume"),
        "avg_volume": extended.get("avg_volume"),
        "fifty_two_wk_low": extended.get("fifty_two_wk_low"),
        "eps": extended.get("eps"),
        "last_updated": live_price.updated_at if live_price else None,
        "historical_1m": extended.get("historical_1m", [])
    }

@router.get("/symbol/{symbol}/history")
@limiter.limit(settings.RATE_LIMIT_MARKET_DATA)
async def get_security_history(request: Request, symbol: str, session: SessionDep, current_user: CurrentUser, period: str = "6mo"):
    from backend.models.historical_price import HistoricalPrice
    symbol = symbol.upper().strip()
    
    # Lookup in DB
    result = await session.execute(select(Security).where(Security.symbol == symbol))
    security = result.scalars().first()
    if not security:
        raise HTTPException(status_code=404, detail="Security not found")
        
    hist_res = await session.execute(
        select(HistoricalPrice)
        .where(HistoricalPrice.security_id == security.id)
        .order_by(HistoricalPrice.date.asc())
    )
    historical_prices = hist_res.scalars().all()
    
    # Simple mapping of period to days for DB filtering
    days_map = {"1d": 1, "5d": 5, "1mo": 30, "3mo": 90, "6mo": 180, "1y": 365, "ytd": 365, "max": 3650}
    target_days = days_map.get(period.lower(), 180)
    
    import datetime
    cutoff_date = datetime.date.today() - datetime.timedelta(days=target_days)
    
    # If client asks for > 6mo, our DB might not have it (we only keep 6mo for batch updates)
    # We should fetch directly from yf for those large periods to keep DB small
    if target_days > 180 or not historical_prices:
        from backend.utils.market import format_yf_symbol
        from backend.utils.market_data import market_data_provider
        
        yf_symbol = format_yf_symbol(security.symbol, security.exchange)
        try:
            hist = await market_data_provider.get_history(yf_symbol, period=period)
            if not hist.empty:
                return [
                    {
                        "date": date.date().isoformat(),
                        "price": row['Close']
                    }
                    for date, row in hist.iterrows()
                ]
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Fallback history fetch failed: {e}")
            
    # Return from DB (filtered)
    return [
        {
            "date": hp.date.isoformat(),
            "price": hp.close_price
        }
        for hp in historical_prices if hp.date >= cutoff_date
    ]

@router.get("/{security_id}")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def get_security(request: Request, security_id: int, session: SessionDep, current_user: CurrentUser):
    from backend.models.security import LivePrice
    result = await session.execute(select(Security).where(Security.id == security_id))
    security = result.scalars().first()
    if not security:
        raise HTTPException(status_code=404, detail="Security not found")
    
    price_res = await session.execute(select(LivePrice).where(LivePrice.security_id == security_id))
    live_price = price_res.scalars().first()
    
    return {
        "id": security.id,
        "symbol": security.symbol,
        "name": security.name,
        "exchange": security.exchange,
        "current_price": live_price.current_price if live_price else None,
        "last_updated": live_price.updated_at if live_price else None
    }

@router.get("/symbol/{symbol}/financials")
@limiter.limit(settings.RATE_LIMIT_MARKET_DATA)
async def get_security_financials(request: Request, symbol: str, session: SessionDep, current_user: CurrentUser):
    from backend.utils.market import format_yf_symbol
    from backend.utils.market_data import market_data_provider
    
    symbol = symbol.upper().strip()
    result = await session.execute(select(Security).where(Security.symbol == symbol))
    security = result.scalars().first()
    if not security:
        raise HTTPException(status_code=404, detail="Security not found")
        
    yf_symbol = format_yf_symbol(security.symbol, security.exchange)
        
    try:
        data = await market_data_provider.get_financials(yf_symbol)
        return data
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error fetching financials: {e}")
        return {"financials": {}, "earnings": {}}

@router.get("/{security_id}/predictions")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def get_predictions(request: Request, security_id: int, session: SessionDep, current_user: CurrentUser):
    from backend.models.prediction import Prediction
    result = await session.execute(select(Prediction).where(Prediction.security_id == security_id).order_by(Prediction.prediction_date.desc()))
    predictions = result.scalars().all()
    return predictions

@router.post("/{security_id}/refresh")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def trigger_price_refresh(
    request: Request,
    security_id: int,
    session: SessionDep,
    current_user: CurrentUser
):
    result = await session.execute(select(Security).where(Security.id == security_id))
    security = result.scalars().first()
    if not security:
        raise HTTPException(status_code=404, detail="Security not found")
        
    # Trigger Celery Task
    task = fetch_and_update_price.delay(security.symbol, security.id, security.exchange)
    return {"message": "Price refresh triggered", "task_id": task.id}
