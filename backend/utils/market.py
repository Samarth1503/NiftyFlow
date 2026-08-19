import yfinance as yf
import difflib
import logging

logger = logging.getLogger(__name__)

def format_yf_symbol(symbol: str, exchange: str = None) -> str:
    """Format the symbol for yfinance based on the exchange."""
    if symbol.startswith("^"):
        return symbol
        
    if not exchange:
        return symbol
    
    exchange = exchange.upper()
    if exchange == "NSE" and not symbol.endswith(".NS"):
        return f"{symbol}.NS"
    elif exchange == "BSE" and not symbol.endswith(".BO"):
        return f"{symbol}.BO"
    return symbol

def verify_security_name(symbol: str, exchange: str, expected_name: str) -> tuple[bool, str]:
    """
    Loosely checks if the provided stock name matches the actual name fetched from yfinance.
    Returns (is_valid, actual_name).
    """
    yf_symbol = format_yf_symbol(symbol, exchange)
    
    try:
        ticker = yf.Ticker(yf_symbol)
        info = ticker.info
        
        # Some yfinance versions/tickers don't return 'info' properly, or return a 404 proxy dict
        if not info or 'regularMarketPrice' not in info and 'previousClose' not in info and 'shortName' not in info:
            logger.warning(f"Could not fetch comprehensive info for {yf_symbol}")
            return True, "" # Don't block if API fails
            
        actual_name = info.get('longName') or info.get('shortName') or ""
        if not actual_name:
            return True, "" # Don't block if name is missing
            
        # Clean strings for loose comparison
        def clean_name(n: str):
            n = n.lower()
            for stop_word in [" ltd", " limited", " inc", " corp", " corporation", ".", ","]:
                n = n.replace(stop_word, "")
            return n.strip()
            
        expected_clean = clean_name(expected_name)
        actual_clean = clean_name(actual_name)
        
        # Direct substring check
        if expected_clean in actual_clean or actual_clean in expected_clean:
            return True, actual_name
            
        # Fuzzy match check
        ratio = difflib.SequenceMatcher(None, expected_clean, actual_clean).ratio()
        if ratio > 0.4:
            return True, actual_name
            
        return False, actual_name
        
    except Exception as e:
        logger.error(f"Error validating name for {yf_symbol}: {e}")
        # If network fails or rate limited, default to allowing it to prevent blocking UX
        return True, ""

def get_live_indices():
    """Fetch live data for key Indian market indices using yfinance."""
    indices_map = {
        "^NSEI": "NIFTY 50",
        "^BSESN": "SENSEX",
        "^NSEBANK": "Nifty Bank",
        "^CNXIT": "Nifty IT"
    }
    
    results = []
    try:
        tickers = yf.Tickers(" ".join(indices_map.keys()))
        for symbol, name in indices_map.items():
            try:
                info = tickers.tickers[symbol].info
                if info and ('regularMarketPrice' in info or 'previousClose' in info):
                    price = info.get('regularMarketPrice') or info.get('currentPrice') or info.get('previousClose')
                    prev_close = info.get('previousClose', price)
                    
                    if price and prev_close:
                        change = price - prev_close
                        percent = (change / prev_close) * 100
                        results.append({
                            "symbol": symbol,
                            "name": name,
                            "price": f"{price:,.2f}",
                            "change": f"{change:,.2f}",
                            "percent": f"{percent:+.2f}%",
                            "isUp": change >= 0
                        })
                        continue
            except Exception as e:
                logger.warning(f"Error fetching individual index {symbol}: {e}")
                pass
                
            # Fallback if specific ticker fails
            results.append({
                "name": name,
                "price": "0.00",
                "change": "0.00",
                "percent": "0.00%",
                "isUp": False
            })
    except Exception as e:
        logger.error(f"Error fetching live indices: {e}")
        # Fallback empty data
        for name in indices_map.values():
            results.append({
                "name": name,
                "price": "N/A",
                "change": "0.00",
                "percent": "0.00%",
                "isUp": False
            })
            
    return results
            
def get_stock_extended_details(symbol: str, exchange: str = None) -> dict:
    """
    Fetch extended stock details for the UI (Open, High, Low, Vol, EPS, Historical 1M data).
    """
    yf_symbol = format_yf_symbol(symbol, exchange)
    details = {
        "open_price": None,
        "high_price": None,
        "low_price": None,
        "volume": None,
        "avg_volume": None,
        "fifty_two_wk_low": None,
        "eps": None,
        "previous_close": None,
        "historical_1m": []
    }
    
    try:
        ticker = yf.Ticker(yf_symbol)
        
        # 1. Fetch info
        info = ticker.info
        if info:
            details["open_price"] = info.get("open") or info.get("regularMarketOpen")
            details["high_price"] = info.get("dayHigh") or info.get("regularMarketDayHigh")
            details["low_price"] = info.get("dayLow") or info.get("regularMarketDayLow")
            details["volume"] = info.get("volume") or info.get("regularMarketVolume")
            details["avg_volume"] = info.get("averageVolume")
            details["fifty_two_wk_low"] = info.get("fiftyTwoWeekLow")
            details["eps"] = info.get("trailingEps") or info.get("forwardEps")
            details["previous_close"] = info.get("previousClose") or info.get("regularMarketPreviousClose")
            
        # 2. Fetch 1 month history (daily)
        hist = ticker.history(period="1mo")
        if not hist.empty:
            for date, row in hist.iterrows():
                details["historical_1m"].append({
                    "timestamp": date.strftime("%Y-%m-%d"),
                    "price": row["Close"]
                })
                
    except Exception as e:
        logger.error(f"Error fetching extended details for {yf_symbol}: {e}")
        
    return details

