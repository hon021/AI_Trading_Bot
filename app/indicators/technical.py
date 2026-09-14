"""Deterministic technical indicators for OHLCV market data."""

from __future__ import annotations

import pandas as pd


def ema(series: pd.Series, period: int) -> pd.Series:
    """Calculate an exponential moving average."""
    _validate_period(period)
    return series.astype(float).ewm(span=period, adjust=False, min_periods=period).mean()


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate RSI using Wilder's smoothed average gains and losses."""
    _validate_period(period)
    delta = close.astype(float).diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)
    average_gain = gains.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    average_loss = losses.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    relative_strength = average_gain / average_loss
    result = 100 - (100 / (1 + relative_strength))
    result = result.where(average_loss != 0, 100.0)
    return result.where(average_gain != 0, 0.0)


def atr(frame: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate ATR as the rolling mean of True Range."""
    _validate_period(period)
    required = {"High", "Low", "Close"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing OHLC columns: {', '.join(sorted(missing))}")

    previous_close = frame["Close"].astype(float).shift(1)
    true_range = pd.concat(
        [
            frame["High"].astype(float) - frame["Low"].astype(float),
            (frame["High"].astype(float) - previous_close).abs(),
            (frame["Low"].astype(float) - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return true_range.rolling(window=period, min_periods=period).mean()


def _validate_period(period: int) -> None:
    if not isinstance(period, int) or period < 1:
        raise ValueError("period must be a positive integer")
