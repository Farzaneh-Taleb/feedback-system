from __future__ import annotations
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, index=True)
    feedback = relationship("Feedback", back_populates="customer", cascade="all, delete-orphan")

class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    message = Column(Text, nullable=False)
    sentiment_label = Column(String, index=True)
    sentiment_score = Column(Float)
    topic = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    customer = relationship("Customer", back_populates="feedback")

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    feedback_id = Column(Integer, ForeignKey("feedback.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    reason = Column(String, default="negative_sentiment")
