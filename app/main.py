from __future__ import annotations
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from sqlalchemy.orm import Session
from typing import List, Optional
from .database import Base, engine, get_db
from . import models, schemas, nlp

import logging
logger = logging.getLogger("uvicorn.error")

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Feedback Intelligence Backend (GPT-only)", version="0.4.0")

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_class=HTMLResponse)
def root():
    return RedirectResponse(url="/static/index.html")

def _get_or_create_customer(db: Session, external_id: str) -> models.Customer:
    cust = db.query(models.Customer).filter(models.Customer.external_id == external_id).first()
    if not cust:
        cust = models.Customer(external_id=external_id)
        db.add(cust)
        db.commit()
        db.refresh(cust)
    return cust

def _maybe_alert(db: Session, fb: models.Feedback):
    if fb.sentiment_label == "negative":
        alert = models.Alert(feedback_id=fb.id, reason="negative_sentiment")
        db.add(alert)
        db.commit()
        logger.warning(f"ALERT: Negative feedback {fb.id} from customer {fb.customer_id}: {fb.message[:80]}...")

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.post("/feedback", response_model=schemas.FeedbackOut)
def create_feedback(payload: schemas.FeedbackCreate, db: Session = Depends(get_db)):
    if not payload.message or not payload.customer_id:
        raise HTTPException(status_code=400, detail="customer_id and message are required.")
    cust = _get_or_create_customer(db, payload.customer_id)
    label, score, top = nlp.analyze(payload.message)
    fb = models.Feedback(
        customer_id=cust.id,
        message=payload.message,
        sentiment_label=label,
        sentiment_score=score,
        topic=top,
    )
    db.add(fb)
    db.commit()
    db.refresh(fb)
    _maybe_alert(db, fb)
    return schemas.FeedbackOut(
        id=fb.id,
        customer_id=cust.external_id,
        message=fb.message,
        sentiment_label=fb.sentiment_label,
        sentiment_score=fb.sentiment_score,
        topic=fb.topic,
        created_at=fb.created_at,
    )

@app.get("/feedback", response_model=List[schemas.FeedbackOut])
def list_feedback(customer_id: Optional[str] = Query(default=None), db: Session = Depends(get_db)):
    q = db.query(models.Feedback, models.Customer).join(models.Customer, models.Customer.id == models.Feedback.customer_id)
    if customer_id:
        q = q.filter(models.Customer.external_id == customer_id)
    rows = q.order_by(models.Feedback.created_at.desc()).all()
    return [
        schemas.FeedbackOut(
            id=fb.id,
            customer_id=cust.external_id,
            message=fb.message,
            sentiment_label=fb.sentiment_label,
            sentiment_score=fb.sentiment_score,
            topic=fb.topic,
            created_at=fb.created_at,
        )
        for fb, cust in rows
    ]

@app.get("/customers/{external_id}/feedback", response_model=List[schemas.FeedbackOut])
def list_feedback_by_customer(external_id: str, db: Session = Depends(get_db)):
    cust = db.query(models.Customer).filter(models.Customer.external_id == external_id).first()
    if not cust:
        return []
    rows = db.query(models.Feedback).filter(models.Feedback.customer_id == cust.id).order_by(models.Feedback.created_at.desc()).all()
    return [
        schemas.FeedbackOut(
            id=fb.id,
            customer_id=cust.external_id,
            message=fb.message,
            sentiment_label=fb.sentiment_label,
            sentiment_score=fb.sentiment_score,
            topic=fb.topic,
            created_at=fb.created_at,
        ) for fb in rows
    ]

@app.get("/alerts", response_model=List[schemas.AlertOut])
def list_alerts(db: Session = Depends(get_db)):
    rows = db.query(models.Alert).order_by(models.Alert.created_at.desc()).all()
    return [schemas.AlertOut.model_validate(a, from_attributes=True) for a in rows]
