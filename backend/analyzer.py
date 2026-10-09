"""Explainable stock-pattern analysis using Dynamic Time Warping."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Iterable

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PatternMatch:
    end_date: str
    distance: float
    forward_return_percent: float


@dataclass(frozen=True)
class Prediction:
    ticker: str
    signal: str
    expected_return_percent: float
    confidence_percent: float
    latest_price: float
    rsi_14: float
    sma_20: float
    sma_50: float
    annualized_volatility_percent: float
    window_days: int
    horizon_days: int
    matches: list[PatternMatch]
    prediction_hash: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def normalize(values: Iterable[float]) -> np.ndarray:
    array = np.asarray(list(values), dtype=float)
    deviation = array.std()
    if deviation == 0:
        return np.zeros_like(array)
    return (array - array.mean()) / deviation


def dtw_distance(first: Iterable[float], second: Iterable[float]) -> float:
    """Return classic DTW distance normalized by total sequence length."""
    a = np.asarray(list(first), dtype=float)
    b = np.asarray(list(second), dtype=float)
    matrix = np.full((len(a) + 1, len(b) + 1), np.inf)
    matrix[0, 0] = 0.0

    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            cost = abs(a[i - 1] - b[j - 1])
            matrix[i, j] = cost + min(
                matrix[i - 1, j], matrix[i, j - 1], matrix[i - 1, j - 1]
            )
    return float(matrix[-1, -1] / (len(a) + len(b)))


def calculate_rsi(close: pd.Series, period: int = 14) -> float:
    differences = close.diff()
    gains = differences.clip(lower=0).rolling(period).mean()
    losses = (-differences.clip(upper=0)).rolling(period).mean()
    latest_loss = float(losses.iloc[-1])
    if latest_loss == 0:
        return 100.0
    relative_strength = float(gains.iloc[-1]) / latest_loss
    return float(100 - (100 / (1 + relative_strength)))


def prediction_fingerprint(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(canonical.encode("utf-8")).hexdigest()


def analyze_prices(
    prices: pd.DataFrame,
    ticker: str,
    window: int = 20,
    horizon: int = 5,
    neighbors: int = 5,
) -> Prediction:
    if "Close" not in prices:
        raise ValueError("Price data must include a Close column")

    frame = prices[["Close"]].dropna().copy()
    minimum_rows = (window * 3) + horizon
    if len(frame) < minimum_rows:
        raise ValueError(f"At least {minimum_rows} closing prices are required")

    close = frame["Close"].astype(float)
    target = normalize(close.iloc[-window:])
    candidates: list[PatternMatch] = []

    # Stop before the target period and reserve horizon days for each outcome.
    last_start = len(close) - (window * 2) - horizon
    for start in range(0, last_start + 1):
        end = start + window
        candidate = normalize(close.iloc[start:end])
        distance = dtw_distance(target, candidate)
        start_price = float(close.iloc[end - 1])
        future_price = float(close.iloc[end + horizon - 1])
        forward_return = ((future_price / start_price) - 1) * 100
        candidates.append(
            PatternMatch(
                end_date=str(frame.index[end - 1].date()),
                distance=round(distance, 6),
                forward_return_percent=round(forward_return, 3),
            )
        )

    closest = sorted(candidates, key=lambda item: item.distance)[:neighbors]
    weights = np.asarray([1 / (item.distance + 1e-6) for item in closest])
    outcomes = np.asarray([item.forward_return_percent for item in closest])
    expected_return = float(np.average(outcomes, weights=weights))

    if expected_return > 0.5:
        signal = "BUY"
        agreement = float(np.average(outcomes > 0, weights=weights))
    elif expected_return < -0.5:
        signal = "SELL"
        agreement = float(np.average(outcomes < 0, weights=weights))
    else:
        signal = "HOLD"
        agreement = float(np.average(np.abs(outcomes) <= 1.0, weights=weights))

    confidence = min(95.0, max(50.0, agreement * 100))
    returns = close.pct_change().dropna()
    volatility = float(returns.std() * np.sqrt(252) * 100)

    values = {
        "ticker": ticker.upper(),
        "signal": signal,
        "expected_return_percent": round(expected_return, 3),
        "confidence_percent": round(confidence, 1),
        "latest_price": round(float(close.iloc[-1]), 2),
        "rsi_14": round(calculate_rsi(close), 2),
        "sma_20": round(float(close.rolling(20).mean().iloc[-1]), 2),
        "sma_50": round(float(close.rolling(50).mean().iloc[-1]), 2),
        "annualized_volatility_percent": round(volatility, 2),
        "window_days": window,
        "horizon_days": horizon,
        "matches": closest,
    }
    hashable = {**values, "matches": [asdict(match) for match in closest]}
    return Prediction(**values, prediction_hash=prediction_fingerprint(hashable))


def demo_prices(rows: int = 320) -> pd.DataFrame:
    """Generate deterministic, market-like data for a zero-key demo."""
    random = np.random.default_rng(42)
    trend = np.linspace(0, 24, rows)
    seasonal = 6 * np.sin(np.linspace(0, 12 * np.pi, rows))
    noise = random.normal(0, 1.1, rows).cumsum() * 0.35
    close = 100 + trend + seasonal + noise
    return pd.DataFrame(
        {"Close": close},
        index=pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=rows),
    )


def fetch_live_prices(ticker: str, period: str = "3y") -> pd.DataFrame:
    import yfinance as yf

    data = yf.download(ticker, period=period, progress=False, auto_adjust=True)
    if data.empty:
        raise ValueError(f"No market data returned for {ticker}")
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    return data

