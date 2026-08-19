from fastapi import APIRouter
import yfinance as yf
import asyncio
import time
from typing import List

router = APIRouter()

# Simple in-memory cache since Redis is overkill just for news in Phase 4
# (or we could use Redis but this avoids adding Redis as a hard dependency if it fails)
NEWS_CACHE = {"data": [], "timestamp": 0}
CACHE_TTL = 1800  # 30 minutes

def fetch_yf_news(symbol: str):
    try:
        ticker = yf.Ticker(symbol)
        return ticker.news
    except Exception:
        return []

@router.get("")
async def get_market_news(symbol: str = "^NSEI"):
    """Fetch recent market news for a symbol (defaults to Nifty 50)."""
    current_time = time.time()
    
    # Use cache if we are fetching the default market news
    if symbol == "^NSEI" and current_time - NEWS_CACHE["timestamp"] < CACHE_TTL and NEWS_CACHE["data"]:
        return NEWS_CACHE["data"]
        
    try:
        raw_news = await asyncio.to_thread(fetch_yf_news, symbol)
        
        # Format news
        formatted_news = []
        for item in raw_news:
            if not isinstance(item, dict):
                continue
                
            content = item.get("content", item) # Fallback to item itself if structure differs
            
            title = content.get("title", "Market Update")
            
            provider = content.get("provider", {})
            publisher = provider.get("displayName", "Market News") if isinstance(provider, dict) else "Market News"
            
            click_url = content.get("clickThroughUrl", {})
            link = click_url.get("url", "#") if isinstance(click_url, dict) else "#"
            
            pub_time = content.get("pubDate")
            if pub_time:
                # Convert ISO string "2026-08-11T03:52:09Z" to ms timestamp or keep as is
                from datetime import datetime
                try:
                    dt = datetime.strptime(pub_time, "%Y-%m-%dT%H:%M:%SZ")
                    published_at = int(dt.timestamp() * 1000)
                except Exception:
                    published_at = current_time * 1000
            else:
                published_at = current_time * 1000
                
            thumbnail_obj = content.get("thumbnail", {})
            resolutions = thumbnail_obj.get("resolutions", []) if isinstance(thumbnail_obj, dict) else []
            thumbnail = resolutions[0].get("url") if resolutions and isinstance(resolutions[0], dict) else None

            formatted_news.append({
                "title": title,
                "publisher": publisher,
                "link": link,
                "publishedAt": published_at,
                "thumbnail": thumbnail
            })
            
        if symbol == "^NSEI":
            NEWS_CACHE["data"] = formatted_news
            NEWS_CACHE["timestamp"] = current_time
            
        return formatted_news
    except Exception:
        return []
