from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from backend.core.config import settings
from backend.api.main import api_router
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from backend.api.limiter import limiter
import redis.asyncio as redis

import logging

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Event-driven portfolio analytics and decision support platform.",
    version="1.0.0"
)

logger = logging.getLogger(__name__)
if settings.SECRET_KEY == "super_secret_key_change_in_production":
    logger.warning("CRITICAL SECURITY WARNING: SECRET_KEY is set to default. MUST BE CHANGED IN PRODUCTION.")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "ok", "project": settings.PROJECT_NAME}
