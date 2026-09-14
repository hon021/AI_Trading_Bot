"""Market data download and validation for the initial paper-trading experiment."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd
import yfinance as yf


REQUIRED_COLUMNS = ("Open", "High", "Low", "Close", "Volume")


class MarketDataError(ValueError):
    """Raised when downloaded market data cannot be used safely."""


@dataclass(frozen=True)
class DownloadedDataset:
    symbol: str
    interval: str
    rows: int
    start: pd.Timestamp
    end: pd.Timestamp
    path: Path


def download_symbol(
    symbol: str,
    output_dir: Path,
    *,
    interval: str = "1h",
    period: str = "60d",
) -> DownloadedDataset:
    """Download one symbol, validate it, and cache it as a CSV file."""
    if not symbol or not symbol.isascii():
        raise MarketDataError("Symbol must be a non-empty ASCII string")

    frame = yf.download(
        tickers=symbol,
        period=period,
        interval=interval,
        auto_adjust=False,
        actions=False,
        progress=False,
        threads=False,
        group_by="column",
    )
    frame = _normalise_columns(frame)
    validate_frame(frame, symbol)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{symbol}_{interval}.csv"
    frame.to_csv(output_path, index_label="timestamp_utc")

    return DownloadedDataset(
        symbol=symbol,
        interval=interval,
        rows=len(frame),
        start=frame.index[0],
        end=frame.index[-1],
        path=output_path,
    )


def validate_frame(frame: pd.DataFrame, symbol: str = "unknown") -> None:
    """Reject missing, duplicated, unordered, or invalid OHLCV data."""
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in frame]
    if missing_columns:
        raise MarketDataError(
            f"{symbol}: missing required columns: {', '.join(missing_columns)}"
        )
    if frame.empty:
        raise MarketDataError(f"{symbol}: provider returned no rows")
    if not isinstance(frame.index, pd.DatetimeIndex):
        raise MarketDataError(f"{symbol}: index is not datetime-based")
    if frame.index.tz is None:
        raise MarketDataError(f"{symbol}: timestamps must include a timezone")
    if frame.index.has_duplicates:
        raise MarketDataError(f"{symbol}: duplicated timestamps found")
    if not frame.index.is_monotonic_increasing:
        raise MarketDataError(f"{symbol}: timestamps are not ordered")
    if frame[list(REQUIRED_COLUMNS)].isna().any().any():
        raise MarketDataError(f"{symbol}: missing OHLCV values found")
    if (frame["High"] < frame["Low"]).any():
        raise MarketDataError(f"{symbol}: High is below Low")
    if (frame["Volume"] < 0).any():
        raise MarketDataError(f"{symbol}: negative volume found")


def download_universe(
    symbols: Iterable[str],
    output_dir: Path,
    *,
    interval: str = "1h",
    period: str = "60d",
) -> list[DownloadedDataset]:
    """Download and validate every symbol without mixing their datasets."""
    return [
        download_symbol(
            symbol=symbol,
            output_dir=output_dir,
            interval=interval,
            period=period,
        )
        for symbol in symbols
    ]


def _normalise_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Flatten the single-symbol columns returned by some yfinance versions."""
    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = frame.columns.get_level_values(0)
    if not isinstance(frame.index, pd.DatetimeIndex):
        return frame
    return frame.tz_convert("UTC").sort_index()
