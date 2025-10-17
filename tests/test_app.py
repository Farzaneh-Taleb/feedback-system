import os
os.environ["TESTING"] = "1"  # use offline stub in nlp

from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine

client = TestClient(app)

def setup_module(module):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def test_store_and_retrieve_feedback():
    r = client.post("/feedback", json={"customer_id":"cust_123","message":"Great product!"})
    assert r.status_code == 200
    data = r.json()
    assert data["customer_id"] == "cust_123"
    assert data["sentiment_label"] in ["positive", "neutral", "negative"]
    assert data["topic"] in ["product_quality", "delivery", "pricing", "customer_service", "other"]

    r2 = client.get("/feedback", params={"customer_id": "cust_123"})
    assert r2.status_code == 200
    items = r2.json()
    assert any(it["id"] == data["id"] for it in items)

def test_negative_triggers_alert():
    r = client.post("/feedback", json={"customer_id":"cust_bad","message":"Terrible and defective."})
    assert r.status_code == 200
    ra = client.get("/alerts")
    assert ra.status_code == 200
    alerts = ra.json()
    assert any(a["reason"] == "negative_sentiment" for a in alerts)
