"""Deterministic signal engine for the initial quantitative strategy."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import pandas as pd

from app.indicators.technical import atr, ema, rsi


class Signal(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass(frozen=True)
class QuantConfig:
    fast_ema_period: int = 20
    slow_ema_period: int = 50
    rsi_period: int = 14
    atr_period: int = 14
    buy_rsi_min: float = 50.0
    buy_rsi_max: float = 70.0
    sell_rsi_threshold: float = 40.0
    max_atr_pct: float = 0.05
    minimum_history: int = 50


class QuantEngine:
    """Calculate indicators and signals without position or risk side effects."""

    def __init__(self, config: QuantConfig | None = None) -> None:
        self.config = config or QuantConfig()

    def enrich(self, frame: pd.DataFrame) -> pd.DataFrame:
        """Return a copy with strategy indicators and ATR percentage."""
        required = {"Open", "High", "Low", "Close", "Volume"}
        missing = required.difference(frame.columns)
        if missing:
            raise ValueError(f"Missing OHLCV columns: {', '.join(sorted(missing))}")

        enriched = frame.copy()
        enriched["EMA20"] = ema(enriched["Close"], self.config.fast_ema_period)
        enriched["EMA50"] = ema(enriched["Close"], self.config.slow_ema_period)
        enriched["RSI14"] = rsi(enriched["Close"], self.config.rsi_period)
        enriched["ATR14"] = atr(enriched, self.config.atr_period)
        enriched["ATR_pct"] = enriched["ATR14"] / enriched["Close"]
        return enriched

    def signal(self, frame: pd.DataFrame, position_open: bool = False) -> Signal:
        """Return the signal for the last closed row in the supplied frame."""
        if len(frame) < self.config.minimum_history:
            return Signal.HOLD

        enriched = self.enrich(frame)
        latest = enriched.iloc[-1]
        if latest[["EMA20", "EMA50", "RSI14", "ATR14", "ATR_pct"]].isna().any():
            return Signal.HOLD

        if position_open:
            if (
                latest["EMA20"] < latest["EMA50"]
                or latest["Close"] < latest["EMA20"]
                or latest["RSI14"] < self.config.sell_rsi_threshold
            ):
                return Signal.SELL
            return Signal.HOLD

        if (
            latest["EMA20"] > latest["EMA50"]
            and latest["Close"] > latest["EMA20"]
            and self.config.buy_rsi_min <= latest["RSI14"] <= self.config.buy_rsi_max
            and latest["ATR_pct"] <= self.config.max_atr_pct
        ):
            return Signal.BUY
        return Signal.HOLD

    def signals(self, frame: pd.DataFrame) -> pd.Series:
        """Return candidate BUY signals using only each row's closed data.

        Position state, SELL decisions, and risk approval belong to later layers.
        """
        enriched = self.enrich(frame)
        signals = pd.Series(Signal.HOLD.value, index=enriched.index, dtype="object")
        valid = enriched[["EMA20", "EMA50", "RSI14", "ATR14", "ATR_pct"]].notna().all(axis=1)
        buy = (
            valid
            & (enriched["EMA20"] > enriched["EMA50"])
            & (enriched["Close"] > enriched["EMA20"])
            & enriched["RSI14"].between(self.config.buy_rsi_min, self.config.buy_rsi_max)
            & (enriched["ATR_pct"] <= self.config.max_atr_pct)
        )
        signals.loc[buy] = Signal.BUY.value
        return signals
