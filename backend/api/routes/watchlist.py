from fastapi import APIRouter, HTTPException
from sqlalchemy.future import select
from backend.api.deps import SessionDep, CurrentUser
from backend.models.watchlist import Watchlist
from backend.models.security import Security
from backend.models.schemas import SecurityResponse
import asyncio
import yfinance as yf
import logging
from backend.models.security import LivePrice

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("", response_model=list[SecurityResponse])
async def get_watchlist(session: SessionDep, current_user: CurrentUser):
    # Join with Security to return details
    result = await session.execute(
        select(Security)
        .join(Watchlist, Watchlist.security_id == Security.id)
        .where(Watchlist.user_id == current_user.id)
        .order_by(Security.symbol)
    )
    return result.scalars().all()

@router.post("/{symbol}", response_model=dict)
async def add_to_watchlist(symbol: str, session: SessionDep, current_user: CurrentUser):
    symbol = symbol.upper().strip()
    
    # 1. Resolve security in DB
    result = await session.execute(select(Security).where(Security.symbol == symbol))
    security = result.scalars().first()
    
    # 2. If missing, initialize it
    if not security:
        # Validate using yfinance
        try:
            from backend.utils.market import resolve_symbol_info_sync
            try:
                info, exchange = await asyncio.to_thread(resolve_symbol_info_sync, symbol)
            except ValueError as ve:
                raise HTTPException(status_code=400, detail=str(ve))
            
            actual_name = info.get('longName') or info.get('shortName') or symbol
            current_price = info.get('regularMarketPrice') or info.get('currentPrice') or info.get('previousClose') or 0.0
            
            security = Security(symbol=symbol, name=actual_name, exchange=exchange)
            session.add(security)
            await session.flush() # get id
            
            # seed live price
            live_price = LivePrice(security_id=security.id, current_price=current_price)
            session.add(live_price)
            await session.flush()
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to resolve {symbol}: {e}")
            raise HTTPException(status_code=400, detail="Stock symbol could not be resolved via Yahoo Finance.")
            
    # 3. Add to Watchlist
    # Check if already in watchlist
    wl_result = await session.execute(
        select(Watchlist).where(Watchlist.user_id == current_user.id, Watchlist.security_id == security.id)
    )
    if wl_result.scalars().first():
        return {"status": "success", "message": "Already in watchlist."}
        
    watchlist_entry = Watchlist(user_id=current_user.id, security_id=security.id)
    session.add(watchlist_entry)
    await session.flush()
    return {"status": "success", "message": "Added to watchlist."}

@router.delete("/{symbol}")
async def remove_from_watchlist(symbol: str, session: SessionDep, current_user: CurrentUser):
    symbol = symbol.upper().strip()
    
    result = await session.execute(select(Security).where(Security.symbol == symbol))
    security = result.scalars().first()
    
    if not security:
        raise HTTPException(status_code=404, detail="Stock not found.")
        
    wl_result = await session.execute(
        select(Watchlist).where(Watchlist.user_id == current_user.id, Watchlist.security_id == security.id)
    )
    watchlist_entry = wl_result.scalars().first()
    
    if not watchlist_entry:
        raise HTTPException(status_code=404, detail="Stock not in watchlist.")
        
    await session.delete(watchlist_entry)
    await session.flush()
    return {"status": "success"}
