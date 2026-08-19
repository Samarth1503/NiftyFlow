from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    is_superuser: bool
    
    model_config = ConfigDict(from_attributes=True)

class SecurityCreate(BaseModel):
    symbol: str
    name: str
    exchange: Optional[str] = None

class SecurityResponse(BaseModel):
    id: int
    symbol: str
    name: str
    exchange: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

from datetime import datetime
from typing import List

class StockHistoricalPrice(BaseModel):
    timestamp: str
    price: float

class StockDetailsResponse(BaseModel):
    id: int
    symbol: str
    name: str
    exchange: Optional[str] = None
    current_price: Optional[float] = None
    previous_close: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
    open_price: Optional[float] = None
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    volume: Optional[int] = None
    avg_volume: Optional[int] = None
    fifty_two_wk_low: Optional[float] = None
    eps: Optional[float] = None
    last_updated: Optional[datetime] = None
    historical_1m: List[StockHistoricalPrice] = []

    model_config = ConfigDict(from_attributes=True)

class PortfolioCreate(BaseModel):
    name: str
    description: Optional[str] = None

class PortfolioResponse(BaseModel):
    id: int
    user_id: int
    name: str
    description: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class HoldingCreate(BaseModel):
    security_id: int
    quantity: int = Field(..., gt=0)
    price: float

class HoldingResponse(BaseModel):
    id: int
    security_id: int
    quantity: int = Field(..., gt=0)
    average_buy_price: float
    invested_value: float
    current_value: Optional[float] = None
    pnl: Optional[float] = None
    pnl_percent: Optional[float] = None
    symbol: Optional[str] = None  # Populated from join

    model_config = ConfigDict(from_attributes=True)

class PortfolioDetailResponse(PortfolioResponse):
    holdings: List[HoldingResponse] = []
    total_invested: float = 0.0
    total_current: float = 0.0
    total_pnl: float = 0.0
    total_pnl_percent: float = 0.0


from backend.models.portfolio import TransactionType

class TransactionCreate(BaseModel):
    security_id: int | None = None
    symbol: str | None = None
    transaction_type: TransactionType
    quantity: int = Field(..., gt=0)
    price: float
    timestamp: datetime | None = None

class TransactionResponse(BaseModel):
    id: int
    portfolio_id: int
    security_id: int
    transaction_type: TransactionType
    quantity: int = Field(..., gt=0)
    price: float
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class PredictionResponse(BaseModel):
    id: int
    security_id: int
    prediction_date: datetime
    predicted_score: float
    model_version: str

    model_config = ConfigDict(from_attributes=True)


class PasswordRecovery(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str

