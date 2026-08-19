import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "NiftyFlow"
    
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "nifty_user"
    POSTGRES_PASSWORD: str = "nifty_password"
    POSTGRES_DB: str = "niftyflow"
    POSTGRES_PORT: int = 5432
    
    SECRET_KEY: str = "super_secret_key_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security Configurations
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    RATE_LIMIT_DEFAULT: str = "120/minute"
    RATE_LIMIT_AUTH: str = "5/minute"
    RATE_LIMIT_MARKET_DATA: str = "30/minute"
    
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None

    # Background Scheduling Configuration
    STOCK_FULL_UPDATE_TIME: str = "21:00"
    STOCK_FULL_UPDATE_TIMEZONE: str = "UTC"
    STOCK_ACTIVE_UPDATE_INTERVAL_MINUTES: int = 15
    
    # yfinance Throttle Configuration
    YFINANCE_BATCH_SIZE: int = 50
    YFINANCE_REQUEST_DELAY_SECONDS: float = 1.0

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

settings = Settings()
