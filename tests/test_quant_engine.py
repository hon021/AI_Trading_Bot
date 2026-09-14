from __future__ import annotations

import unittest

import pandas as pd

from app.strategy.quant_engine import QuantConfig, QuantEngine, Signal


def make_frame(rows: int, close: list[float]) -> pd.DataFrame:
    index = pd.date_range("2026-01-01", periods=rows, freq="h", tz="UTC")
    close_series = pd.Series(close, index=index, dtype=float)
    return pd.DataFrame(
        {
            "Open": close_series,
            "High": close_series + 1.0,
            "Low": close_series - 1.0,
            "Close": close_series,
            "Volume": 1000.0,
        },
        index=index,
    )


class QuantEngineTests(unittest.TestCase):
    def test_holds_until_minimum_history_exists(self) -> None:
        frame = make_frame(49, [100.0] * 49)

        result = QuantEngine().signal(frame)

        self.assertEqual(result, Signal.HOLD)

    def test_buy_requires_all_buy_conditions(self) -> None:
        close = [100.0 + index * 0.1 + (0.4 if index % 2 else -0.4) for index in range(50)]
        close.extend([105.2, 105.4, 105.6, 105.8, 106.0])
        frame = make_frame(len(close), close)
        config = QuantConfig(max_atr_pct=0.05)

        result = QuantEngine(config).signal(frame)

        self.assertEqual(result, Signal.BUY)

    def test_open_position_can_generate_sell(self) -> None:
        close = [110.0] * 50 + [109.0, 108.0, 107.0, 106.0, 105.0]
        frame = make_frame(len(close), close)

        result = QuantEngine().signal(frame, position_open=True)

        self.assertEqual(result, Signal.SELL)

    def test_signals_do_not_use_future_rows(self) -> None:
        rising = [100.0] * 50 + [101.0, 102.0, 103.0, 104.0, 105.0]
        frame = make_frame(len(rising), rising)
        engine = QuantEngine()

        full_signals = engine.signals(frame)
        prefix_signals = engine.signals(frame.iloc[:-1])

        self.assertEqual(full_signals.iloc[-2], prefix_signals.iloc[-1])


if __name__ == "__main__":
    unittest.main()
