"""Download and validate the initial ETF universe."""

from __future__ import annotations

import argparse
from pathlib import Path

from app.data.market_data import download_universe


DEFAULT_SYMBOLS = ("SPY", "QQQ", "IWM")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--symbol",
        dest="symbols",
        action="append",
        help="Symbol to download; repeat the option to override the default universe.",
    )
    parser.add_argument("--interval", default="1h")
    parser.add_argument(
        "--period",
        default="60d",
        help="Relative period accepted by yfinance, for example 60d or 730d.",
    )
    parser.add_argument("--output-dir", type=Path, default=Path("data/raw"))
    args = parser.parse_args()

    symbols = tuple(args.symbols) if args.symbols else DEFAULT_SYMBOLS
    datasets = download_universe(
        symbols=symbols,
        output_dir=args.output_dir,
        interval=args.interval,
        period=args.period,
    )
    for dataset in datasets:
        print(
            f"{dataset.symbol}: {dataset.rows} rows, "
            f"{dataset.start.isoformat()} -> {dataset.end.isoformat()} "
            f"({dataset.path})"
        )


if __name__ == "__main__":
    main()
