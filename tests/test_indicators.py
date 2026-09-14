from __future__ import annotations

import unittest

import pandas as pd

from app.indicators.technical import atr, ema, rsi


class IndicatorTests(unittest.TestCase):
    def test_ema_uses_period_as_minimum_history(self) -> None:
        values = pd.Series([1.0, 2.0, 3.0, 4.0])

        result = ema(values, period=3)

        self.assertEqual(result.iloc[:2].isna().sum(), 2)
        self.assertAlmostEqual(result.iloc[2], 2.25)

    def test_rsi_is_high_for_consistent_gains(self) -> None:
        values = pd.Series(range(1, 20), dtype=float)

        result = rsi(values, period=14)

        self.assertEqual(result.iloc[:14].isna().sum(), 14)
        self.assertEqual(result.iloc[-1], 100.0)

    def test_atr_uses_high_low_and_previous_close(self) -> None:
        frame = pd.DataFrame(
            {
                "High": [11.0, 13.0, 14.0],
                "Low": [9.0, 10.0, 12.0],
                "Close": [10.0, 12.0, 13.0],
            }
        )

        result = atr(frame, period=2)

        self.assertTrue(pd.isna(result.iloc[0]))
        self.assertAlmostEqual(result.iloc[1], 2.5)
        self.assertAlmostEqual(result.iloc[2], 2.5)


if __name__ == "__main__":
    unittest.main()
