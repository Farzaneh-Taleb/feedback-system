from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class FeedbackCreate(BaseModel):
    customer_id: str = Field(..., description="External customer identifier")
    message: str

class FeedbackOut(BaseModel):
    id: int
    customer_id: str
    message: str
    sentiment_label: str
    sentiment_score: float
    topic: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class AlertOut(BaseModel):
    id: int
    feedback_id: int
    created_at: datetime
    reason: str
    model_config = ConfigDict(from_attributes=True)
