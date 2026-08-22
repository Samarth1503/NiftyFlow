from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.db.base import Base

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    security_id = Column(Integer, ForeignKey("securities.id", ondelete="CASCADE"), nullable=False)
    
    # ML Outputs
    prediction_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    predicted_score = Column(Float, nullable=False) # Probability of outperformance
    model_version = Column(String, nullable=False, default="v1.0")

    # Relationships
    security = relationship("Security", backref="predictions")
