from fastapi import APIRouter
from backend.api.routes import auth, portfolios, securities, watchlist, news, contact

api_router = APIRouter()
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(portfolios.router, prefix="/portfolios", tags=["portfolios"])
api_router.include_router(securities.router, prefix="/securities", tags=["securities"])
api_router.include_router(watchlist.router, prefix="/watchlist", tags=["watchlist"])
api_router.include_router(news.router, prefix="/news", tags=["news"])
api_router.include_router(contact.router, prefix="/contact", tags=["contact"])
