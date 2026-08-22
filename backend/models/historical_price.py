from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, UniqueConstraint
from backend.db.base import Base

class HistoricalPrice(Base):
    __tablename__ = "historical_prices"

    id = Column(Integer, primary_key=True, index=True)
    security_id = Column(Integer, ForeignKey("securities.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    close_price = Column(Float, nullable=False)

    __table_args__ = (
        UniqueConstraint('security_id', 'date', name='uq_security_date'),
    )
