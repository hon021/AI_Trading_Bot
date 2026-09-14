from __future__ import annotations

import unittest

import pandas as pd

from app.backtesting.engine import BacktestConfig, Backtester


def make_backtest_frame() -> pd.DataFrame:
    initial_close = [
        100.0 + index * 0.1 + (0.4 if index % 2 else -0.4)
        for index in range(50)
    ]
    close = initial_close + [105.2, 105.4, 99.0]
    index = list(pd.date_range("2026-01-01 13:00", periods=50, freq="h", tz="UTC"))
    index.extend(
        pd.DatetimeIndex(
            [
                "2026-01-03 15:00+00:00",
                "2026-01-03 16:00+00:00",
                "2026-01-03 17:00+00:00",
            ]
        )
    )
    close_series = pd.Series(close, index=index, dtype=float)
    return pd.DataFrame(
        {
            "Open": close_series,
            "High": close_series + 1.0,
            "Low": close_series - 1.0,
            "Close": close_series,
            "Volume": 1000.0,
        },
        index=close_series.index,
    )


class BacktesterTests(unittest.TestCase):
    def test_orders_execute_on_next_bar_and_gap_stop_uses_open(self) -> None:
        frame = make_backtest_frame()
        result = Backtester(
            config=BacktestConfig(decision_times=(pd.Timestamp("10:00").time(),))
        ).run({"SPY": frame})

        accepted = [trade for trade in result.trades if trade.accepted]
        self.assertEqual([trade.side for trade in accepted], ["BUY", "SELL"])
        self.assertEqual(accepted[0].timestamp.hour, 16)
        self.assertEqual(accepted[1].reason, "stop_loss")
        self.assertAlmostEqual(accepted[1].market_price, 99.0)
        self.assertEqual(result.metrics["closed_trades"], 1.0)

    def test_same_input_is_reproducible(self) -> None:
        frame = make_backtest_frame()
        config = BacktestConfig(decision_times=(pd.Timestamp("10:00").time(),))
        first = Backtester(config=config).run({"SPY": frame})
        second = Backtester(config=config).run({"SPY": frame})

        self.assertEqual(first.metrics, second.metrics)
        self.assertEqual(first.equity_curve.tolist(), second.equity_curve.tolist())
        self.assertEqual(
            [(trade.side, trade.reason, trade.quantity) for trade in first.trades],
            [(trade.side, trade.reason, trade.quantity) for trade in second.trades],
        )


if __name__ == "__main__":
    unittest.main()
