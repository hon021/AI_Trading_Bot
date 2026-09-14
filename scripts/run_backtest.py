"""Run the initial backtest and save reproducible reports."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from app.backtesting.engine import BacktestConfig, Backtester


def load_frames(data_dir: Path) -> dict[str, pd.DataFrame]:
    frames = {}
    for path in sorted(data_dir.glob("*_1h.csv")):
        symbol = path.stem.removesuffix("_1h")
        frames[symbol] = pd.read_csv(
            path,
            index_col="timestamp_utc",
            parse_dates=["timestamp_utc"],
        )
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
    data_dir = Path("data/raw")
    report_dir = Path("reports")
    report_dir.mkdir(parents=True, exist_ok=True)

    frames = load_frames(data_dir)
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