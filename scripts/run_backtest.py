"""Run the initial backtest and save reproducible reports."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from app.backtesting.engine import BacktestConfig, Backtester


def load_frames(
    data_dir: Path,
    *,
    as_of: pd.Timestamp | None = None,
) -> dict[str, pd.DataFrame]:
    if as_of is not None and as_of.tzinfo is None:
        raise ValueError("as_of must be timezone-aware")
    frames = {}
    for path in sorted(data_dir.glob("*_1h.csv")):
        symbol = path.stem.removesuffix("_1h")
        frame = pd.read_csv(
            path,
            index_col="timestamp_utc",
            parse_dates=["timestamp_utc"],
        )
        if as_of is not None:
            frame = frame.loc[
                frame.index + pd.to_timedelta(1, unit="h") <= as_of.tz_convert("UTC")
            ]
        if not frame.empty:
            frames[symbol] = frame
    if not frames:
        raise FileNotFoundError(f"No *_1h.csv files found in {data_dir}")
    return frames


def build_periods(frames: dict[str, pd.DataFrame]) -> dict[str, tuple[pd.Timestamp, pd.Timestamp]]:
    timestamps = sorted(set().union(*(frame.index for frame in frames.values())))
    if len(timestamps) < 12:
        raise ValueError("At least 12 timestamps are required for three periods")
    development_end = timestamps[len(timestamps) // 2 - 1]
    validation_end = timestamps[(len(timestamps) * 3) // 4 - 1]
    return {
        "development": (timestamps[0], development_end),
        "validation": (timestamps[len(timestamps) // 2], validation_end),
        "out_of_sample": (timestamps[(len(timestamps) * 3) // 4], timestamps[-1]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a reproducible hourly backtest")
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw"))
    parser.add_argument(
        "--as-of",
        type=pd.Timestamp,
        default=pd.Timestamp(datetime.now(timezone.utc)),
        help="UTC timestamp used to exclude hourly bars that were not yet closed",
    )
    args = parser.parse_args()
    data_dir = args.data_dir
    as_of = args.as_of
    if as_of.tzinfo is None:
        parser.error("--as-of must include a timezone, for example +00:00")
    as_of = as_of.tz_convert("UTC")
    report_dir = Path("reports")
    report_dir.mkdir(parents=True, exist_ok=True)

    frames = load_frames(data_dir, as_of=as_of)
    periods = build_periods(frames)
    period_results = {}
    for name, (start, end) in periods.items():
        result = Backtester(
            config=BacktestConfig(start_timestamp=start, end_timestamp=end)
        ).run(frames)
        period_results[name] = {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "metrics": result.metrics,
            "benchmark_metrics": result.benchmark_metrics,
            "accepted_trades": sum(trade.accepted for trade in result.trades),
        }

    result = Backtester().run(frames)
    summary = {
        "symbols": sorted(frames),
        "data_dir": str(data_dir),
        "as_of_utc": as_of.isoformat(),
        "datasets": {
            symbol: {
                "sha256": hashlib.sha256(
                    (data_dir / f"{symbol}_1h.csv").read_bytes()
                ).hexdigest(),
                "bars_used": len(frame),
                "first_bar_utc": frame.index[0].isoformat(),
                "last_closed_bar_utc": frame.index[-1].isoformat(),
            }
            for symbol, frame in frames.items()
        },
        "strategy": "quant_only_v0.1.0",
        "split": "50% development / 25% validation / 25% out_of_sample",
        "periods": period_results,
        "metrics": result.metrics,
        "benchmark_metrics": result.benchmark_metrics,
    }
    (report_dir / "backtest_summary.json").write_text(
        json.dumps(summary, indent=2, allow_nan=False),
        encoding="utf-8",
    )
    equity = pd.concat([result.equity_curve, result.benchmark_equity], axis=1)
    equity.to_csv(report_dir / "equity_curve.csv", index_label="timestamp_utc")
    trades = pd.DataFrame(asdict(trade) for trade in result.trades)
    if not trades.empty:
        trades["timestamp"] = trades["timestamp"].map(lambda value: value.isoformat())
    trades.to_csv(report_dir / "trades.csv", index=False)
    print(f"Saved reports to {report_dir}")
    print(json.dumps(summary, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()