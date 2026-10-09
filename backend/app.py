"""Flask application for ChainForecast."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from backend.analyzer import analyze_prices, demo_prices, fetch_live_prices
from backend.blockchain_client import register_prediction

app = Flask(__name__)


def make_prediction(ticker: str, demo: bool) -> dict:
    frame = demo_prices() if demo else fetch_live_prices(ticker)
    prediction = analyze_prices(frame, ticker)
    result = prediction.to_dict()
    result["mode"] = "demo" if demo else "live"
    try:
        result["transaction_hash"] = register_prediction(
            prediction.ticker, prediction.signal, prediction.prediction_hash
        )
        result["blockchain_status"] = (
            "recorded" if result["transaction_hash"] else "disabled"
        )
    except Exception as error:
        result["transaction_hash"] = None
        result["blockchain_status"] = f"not recorded: {error}"
    return result


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "blockchain_enabled": os.getenv("BLOCKCHAIN_ENABLED", "false")})


@app.post("/api/predict")
def predict():
    payload = request.get_json(silent=True) or request.form
    ticker = str(payload.get("ticker", "AAPL")).strip().upper()
    raw_demo = payload.get("demo", True)
    demo = raw_demo if isinstance(raw_demo, bool) else str(raw_demo).lower() in {"1", "true", "on", "yes"}
    try:
        return jsonify(make_prediction(ticker, demo))
    except Exception as error:
        return jsonify({"error": str(error)}), 400


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)

