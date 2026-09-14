"""Run one scheduled market-analysis cycle and save candidate signals."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from app.data.market_data import download_universe
from app.strategy.quant_engine import QuantEngine


SYMBOLS = ("SPY", "QQQ", "IWM")
MARKET_TIMEZONE = ZoneInfo("America/New_York")
DATA_DIR = Path("data/raw")
REPORT_DIR = Path("reports")


def run_analysis(
    *,
    now: datetime | None = None,
    symbols: tuple[str, ...] = SYMBOLS,
) -> dict:
    """Download data, use only closed hourly bars, and save candidate signals."""
    current_time = now or datetime.now(timezone.utc)
    if current_time.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    current_time = current_time.astimezone(timezone.utc)
    datasets = download_universe(symbols, DATA_DIR, interval="1h", period="60d")
    engine = QuantEngine()
    signals: dict[str, dict[str, str | None]] = {}

    for dataset in datasets:
        path = dataset.path
        frame = pd.read_csv(path, index_col="timestamp_utc", parse_dates=["timestamp_utc"])
        closed = frame.loc[
            frame.index + pd.to_timedelta(1, unit="h") <= pd.Timestamp(current_time)
        ]
        signal = engine.signal(closed).value if not closed.empty else "HOLD"
        latest_timestamp = closed.index[-1].isoformat() if not closed.empty else None
        signals[dataset.symbol] = {
            "signal": signal,
            "latest_closed_bar_utc": latest_timestamp,
        }

    result = {
        "run_timestamp_utc": current_time.isoformat(),
        "run_timestamp_new_york": current_time.astimezone(MARKET_TIMEZONE).isoformat(),
        "mode": "quant_only_candidate_signals",
        "paper_trade_executed": False,
        "signals": signals,
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "latest_signals.json").write_text(
        json.dumps(result, indent=2),
        encoding="utf-8",
    )
    return result


def main() -> None:
    result = run_analysis()
    for symbol, details in result["signals"].items():
        print(f"{symbol}: {details['signal']} ({details['latest_closed_bar_utc']})")


if __name__ == "__main__":
    main()
