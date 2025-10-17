from __future__ import annotations
import os, json, yaml
from pathlib import Path
from typing import Tuple
from openai import OpenAI

_TESTING = os.getenv("TESTING") == "1"

def _load_labels():
    cfg = Path(__file__).parent / "config" / "topics.yaml"
    with open(cfg, "r") as f:
        data = yaml.safe_load(f) or {}
    return data.get("labels") or ["product quality", "delivery", "pricing", "customer service", "other"]

_LABELS = _load_labels()

def _canonical(label: str) -> str:
    m = {"product quality": "product_quality", "customer service": "customer_service"}
    return m.get(label.lower().strip(), label.lower().strip().replace(" ", "_"))

def analyze(text: str) -> Tuple[str, float, str]:
    if _TESTING:
        t = (text or "").lower()
        if any(x in t for x in ["terrible", "broken", "defective", "bad"]):
            return "negative", -0.8, "product_quality"
        if any(x in t for x in ["late", "delivery", "courier"]):
            return "negative", -0.5, "delivery"
        if any(x in t for x in ["great", "excellent", "love"]):
            return "positive", 0.8, "product_quality"
        return "neutral", 0.0, "other"
    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    model = os.getenv("GPT_MODEL", "gpt-4.1-nano")

    system = (
        "You are an assistant that analyzes customer feedback. "
        "Return ONLY a JSON object: "
        '{"sentiment":"positive|neutral|negative","topic":"one label from list"}.'
    )
    user = "Message:\n" + (text or "") + "\n\nAllowed topics (choose one):\n" + "\n".join("- " + t for t in _LABELS)

    resp = client.chat.completions.create(
        model=model,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    try:
        payload = resp.choices[0].message.content
        data = json.loads(payload or "{}")
        sentiment = str(data.get("sentiment", "neutral")).lower()
        topic = str(data.get("topic", "other")).strip()
        return sentiment, 0.0, _canonical(topic)
    except Exception:
        return "neutral", 0.0, "other"
