from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from backend.db.base import Base

class Security(Base):
    __tablename__ = "securities"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    exchange = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class LivePrice(Base):
    __tablename__ = "live_prices"

    security_id = Column(Integer, ForeignKey("securities.id", ondelete="CASCADE"), primary_key=True)
    current_price = Column(Float, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
