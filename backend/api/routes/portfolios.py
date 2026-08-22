from fastapi import APIRouter, HTTPException
from sqlalchemy.future import select
from sqlalchemy import func
from backend.api.deps import SessionDep, CurrentUser
from backend.models.portfolio import Portfolio, Holding, Transaction, TransactionType
from backend.models.security import Security, LivePrice
from backend.models.schemas import (
    PortfolioCreate, 
    PortfolioResponse, 
    TransactionCreate,
    TransactionResponse,
    HoldingResponse, 
    PortfolioDetailResponse
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("", response_model=PortfolioResponse)
async def create_portfolio(
    portfolio_in: PortfolioCreate,
    session: SessionDep,
    current_user: CurrentUser
):
    portfolio = Portfolio(**portfolio_in.model_dump(), user_id=current_user.id)
    session.add(portfolio)
    await session.flush()
    await session.refresh(portfolio)
    
    logger.info(f"event=portfolio_created portfolio_id={portfolio.id} user_id={current_user.id}")
    return portfolio

@router.get("", response_model=list[PortfolioResponse])
async def list_portfolios(
    session: SessionDep,
    current_user: CurrentUser
):
    result = await session.execute(
        select(Portfolio).where(Portfolio.user_id == current_user.id)
    )
    portfolios = result.scalars().all()
    return portfolios

@router.post("/{portfolio_id}/transactions", response_model=TransactionResponse)
async def add_transaction(
    portfolio_id: int,
    transaction_in: TransactionCreate,
    session: SessionDep,
    current_user: CurrentUser
):
    if transaction_in.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than 0")
    if transaction_in.price < 0:
        raise HTTPException(status_code=400, detail="Price cannot be negative")

    if not transaction_in.security_id and not transaction_in.symbol:
        raise HTTPException(status_code=400, detail="Must provide either security_id or symbol")

    # Verify portfolio ownership
    p_res = await session.execute(
        select(Portfolio).where(Portfolio.id == portfolio_id, Portfolio.user_id == current_user.id)
    )
    portfolio = p_res.scalars().first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    security_id = transaction_in.security_id
    
    # If no ID provided, try to resolve by symbol
    if not security_id and transaction_in.symbol:
        symbol = transaction_in.symbol.upper().strip()
        s_res = await session.execute(select(Security).where(Security.symbol == symbol))
        security = s_res.scalars().first()
        
        if security:
            security_id = security.id
        else:
            # Need to create it!
            from backend.models.security import LivePrice
            import yfinance as yf
            import asyncio
            
            try:
                from backend.utils.market import resolve_symbol_info_sync
                try:
                    info, exchange = await asyncio.to_thread(resolve_symbol_info_sync, symbol)
                except ValueError as ve:
                    raise HTTPException(status_code=400, detail=f"Stock symbol '{symbol}' could not be resolved.")
                    
                actual_name = info.get('longName') or info.get('shortName') or symbol
                current_price = info.get('regularMarketPrice') or info.get('currentPrice') or info.get('previousClose') or 0.0
                
                # Transactionally add
                new_sec = Security(symbol=symbol, name=actual_name, exchange=exchange)
                session.add(new_sec)
                await session.flush()
                
                new_lp = LivePrice(security_id=new_sec.id, current_price=current_price)
                session.add(new_lp)
                await session.flush()
                
                security_id = new_sec.id
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Failed to seed {symbol}: {e}")
                raise HTTPException(status_code=400, detail="Stock symbol could not be resolved via Yahoo Finance.")

    # Verify security exists
    s_res = await session.execute(select(Security).where(Security.id == security_id))
    security = s_res.scalars().first()
    if not security:
        raise HTTPException(status_code=404, detail="Security not found")

    # Find existing holding
    h_res = await session.execute(
        select(Holding).where(
            Holding.portfolio_id == portfolio_id, 
            Holding.security_id == security_id
        )
    )
    holding = h_res.scalars().first()

    if transaction_in.transaction_type == TransactionType.BUY:
        if holding:
            # Calculate new average buy price
            total_value = (holding.quantity * holding.average_buy_price) + (transaction_in.quantity * transaction_in.price)
            holding.quantity += transaction_in.quantity
            holding.average_buy_price = total_value / holding.quantity
        else:
            holding = Holding(
                portfolio_id=portfolio_id,
                security_id=security_id,
                quantity=transaction_in.quantity,
                average_buy_price=transaction_in.price
            )
            session.add(holding)
    else: # SELL
        if not holding or holding.quantity < transaction_in.quantity:
            raise HTTPException(status_code=400, detail="Insufficient quantity to sell")
        
        holding.quantity -= transaction_in.quantity
        if holding.quantity == 0:
            session.delete(holding)
            
    # Record the transaction
    transaction = Transaction(
        portfolio_id=portfolio_id,
        security_id=security_id,
        transaction_type=transaction_in.transaction_type,
        quantity=transaction_in.quantity,
        price=transaction_in.price
    )
    if transaction_in.timestamp:
        transaction.timestamp = transaction_in.timestamp
    
    session.add(transaction)
    
    logger.info(f"event=transaction_executed type={transaction_in.transaction_type.value} portfolio_id={portfolio_id} security_id={security_id} qty={transaction_in.quantity} price={transaction_in.price}")

    await session.flush()
    await session.refresh(transaction)
    
    return transaction

@router.get("/{portfolio_id}/transactions", response_model=list[TransactionResponse])
async def get_transactions(
    portfolio_id: int,
    session: SessionDep,
    current_user: CurrentUser
):
    # Verify portfolio ownership
    p_res = await session.execute(
        select(Portfolio).where(Portfolio.id == portfolio_id, Portfolio.user_id == current_user.id)
    )
    if not p_res.scalars().first():
        raise HTTPException(status_code=404, detail="Portfolio not found")
        
    result = await session.execute(
        select(Transaction).where(Transaction.portfolio_id == portfolio_id).order_by(Transaction.timestamp.desc())
    )
    return result.scalars().all()

@router.get("/{portfolio_id}", response_model=PortfolioDetailResponse)
async def get_portfolio(
    portfolio_id: int,
    session: SessionDep,
    current_user: CurrentUser
):
    # Fetch portfolio
    p_res = await session.execute(
        select(Portfolio).where(Portfolio.id == portfolio_id, Portfolio.user_id == current_user.id)
    )
    portfolio = p_res.scalars().first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
        
    # Fetch holdings along with current live prices
    h_res = await session.execute(
        select(Holding, Security.symbol, LivePrice.current_price)
        .join(Security, Security.id == Holding.security_id)
        .outerjoin(LivePrice, LivePrice.security_id == Security.id)
        .where(Holding.portfolio_id == portfolio_id)
    )
    
    rows = h_res.all()
    
    holdings_out = []
    total_invested = 0.0
    total_current = 0.0
    
    for holding, symbol, current_price in rows:
        invested_value = holding.quantity * holding.average_buy_price
        total_invested += invested_value
        
        c_val = None
        pnl = None
        pnl_percent = None
        
        if current_price is not None:
            c_val = holding.quantity * current_price
            pnl = c_val - invested_value
            pnl_percent = (pnl / invested_value * 100) if invested_value > 0 else 0
            total_current += c_val
            
        holdings_out.append({
            "id": holding.id,
            "security_id": holding.security_id,
            "quantity": holding.quantity,
            "average_buy_price": holding.average_buy_price,
            "invested_value": invested_value,
            "current_value": c_val,
            "pnl": pnl,
            "pnl_percent": pnl_percent,
            "symbol": symbol
        })
        
    overall_pnl = total_current - total_invested
    overall_pnl_percent = (overall_pnl / total_invested * 100) if total_invested > 0 else 0.0
    
    return {
        "id": portfolio.id,
        "user_id": portfolio.user_id,
        "name": portfolio.name,
        "description": portfolio.description,
        "created_at": portfolio.created_at,
        "holdings": holdings_out,
        "total_invested": total_invested,
        "total_current": total_current,
        "total_pnl": overall_pnl,
        "total_pnl_percent": overall_pnl_percent
    }

@router.get("/{portfolio_id}/chart")
async def get_portfolio_chart(portfolio_id: int, session: SessionDep, current_user: CurrentUser):
    p_res = await session.execute(
        select(Portfolio).where(Portfolio.id == portfolio_id, Portfolio.user_id == current_user.id)
    )
    portfolio = p_res.scalars().first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
        
    t_res = await session.execute(
        select(Transaction).where(Transaction.portfolio_id == portfolio_id).order_by(Transaction.timestamp)
    )
    transactions = t_res.scalars().all()
    
    security_ids = {t.security_id for t in transactions}
    if not security_ids:
        return []
        
    s_res = await session.execute(
        select(Security).where(Security.id.in_(security_ids))
    )
    securities = {s.id: s for s in s_res.scalars().all()}
    
    from backend.utils.market import format_yf_symbol
    import yfinance as yf
    import asyncio
    
    historical_prices = {}
    
    def fetch_hist(sec):
        yf_sym = format_yf_symbol(sec.symbol, sec.exchange)
        hist = yf.Ticker(yf_sym).history(period="1mo")
        dates = {}
        for d, row in hist.iterrows():
            dates[d.date()] = float(row["Close"])
        return sec.id, dates
        
    loop = asyncio.get_running_loop()
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor() as pool:
        futures = [loop.run_in_executor(pool, fetch_hist, s) for s in securities.values()]
        results = await asyncio.gather(*futures)
        for sec_id, dates in results:
            historical_prices[sec_id] = dates
            
    from datetime import datetime, timedelta
    today = datetime.now().date()
    days = [today - timedelta(days=i) for i in range(30, -1, -1)]
    
    chart_data = []
    
    for d in days:
        holdings_qty = {}
        for t in transactions:
            if t.timestamp.date() <= d:
                if t.transaction_type == TransactionType.BUY:
                    holdings_qty[t.security_id] = holdings_qty.get(t.security_id, 0) + t.quantity
                else:
                    holdings_qty[t.security_id] = holdings_qty.get(t.security_id, 0) - t.quantity
                    
        total_val = 0
        for sid, qty in holdings_qty.items():
            if qty > 0:
                sec_hist = historical_prices.get(sid, {})
                price = 0
                for lookback in range(10):
                    pd = d - timedelta(days=lookback)
                    if pd in sec_hist:
                        price = sec_hist[pd]
                        break
                total_val += qty * price
                
        chart_data.append({
            "date": d.strftime("%b %d"),
            "value": total_val
        })
        
    return chart_data

