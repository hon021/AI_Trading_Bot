from __future__ import annotations

import unittest

from app.risk.risk_manager import PositionView, RiskConfig, RiskManager


class RiskManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manager = RiskManager()
        self.positions: dict[str, PositionView] = {}

    def test_sizes_position_with_risk_and_exposure_limits(self) -> None:
        decision = self.manager.evaluate_buy(
            symbol="SPY",
            market_price=100.0,
            atr_value=2.0,
            cash=500.0,
            positions=self.positions,
            equity=500.0,
            peak_equity=500.0,
        )

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.quantity, 0.999)
        self.assertAlmostEqual(decision.stop_price, 96.05)

    def test_rejects_second_position_for_same_symbol(self) -> None:
        positions = {
            "SPY": PositionView("SPY", 1.0, 100.0, 96.0),
        }

        decision = self.manager.evaluate_buy(
            symbol="SPY",
            market_price=100.0,
            atr_value=2.0,
            cash=500.0,
            positions=positions,
            equity=500.0,
            peak_equity=500.0,
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "position_already_open")

    def test_rejects_when_drawdown_limit_is_reached(self) -> None:
        decision = self.manager.evaluate_buy(
            symbol="SPY",
            market_price=100.0,
            atr_value=2.0,
            cash=500.0,
            positions=self.positions,
            equity=425.0,
            peak_equity=500.0,
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "drawdown_limit_reached")


if __name__ == "__main__":
    unittest.main()
