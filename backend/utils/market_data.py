import asyncio
import logging
import yfinance as yf
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

logger = logging.getLogger(__name__)

class MarketDataProvider:
    def __init__(self, request_delay: float = 1.0):
        self.request_delay = request_delay

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(Exception)
    )
    def _fetch_history(self, symbol: str, period: str = "1y"):
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        if df is None or df.empty:
            raise ValueError(f"No history found for {symbol}")
        return df
        
    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(Exception)
    )
    def _fetch_info(self, symbol: str):
        ticker = yf.Ticker(symbol)
        info = ticker.info
        if not info:
            raise ValueError(f"No info found for {symbol}")
        return info

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(Exception)
    )
    def _fetch_financials(self, symbol: str):
        ticker = yf.Ticker(symbol)
        inc = ticker.income_stmt
        earn = ticker.earnings_dates
        financials = {}
        if inc is not None and not inc.empty:
            inc_df = inc.fillna(0)
            inc_df.columns = inc_df.columns.astype(str)
            financials = inc_df.to_dict()
            
        earnings = {}
        if earn is not None and not earn.empty:
            earn_df = earn.fillna(0)
            earn_df.index = earn_df.index.astype(str)
            earnings = earn_df.head(8).to_dict('index')
            
        return {"financials": financials, "earnings": earnings}

    async def get_history(self, symbol: str, period: str = "1y"):
        await asyncio.sleep(self.request_delay)
        return await asyncio.to_thread(self._fetch_history, symbol, period)

    async def get_info(self, symbol: str):
        await asyncio.sleep(self.request_delay)
        return await asyncio.to_thread(self._fetch_info, symbol)
        
    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(Exception)
    )
    def _fetch_batch(self, symbols: str, period: str = "6mo"):
        return yf.download(symbols, period=period, group_by="ticker", progress=False)

    async def get_batch(self, symbols: str, period: str = "6mo"):
        await asyncio.sleep(self.request_delay)
        return await asyncio.to_thread(self._fetch_batch, symbols, period)

market_data_provider = MarketDataProvider()
