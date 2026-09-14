from __future__ import annotations

import unittest
from datetime import datetime, timezone

from app.paper_trading.paper_broker import PaperBroker


TIMESTAMP = datetime(2026, 9, 12, 14, 0, tzinfo=timezone.utc)


class PaperBrokerTests(unittest.TestCase):
    def test_buy_applies_costs_and_creates_position(self) -> None:
        broker = PaperBroker()

        trade = broker.buy("SPY", market_price=100.0, atr_value=2.0, timestamp=TIMESTAMP)

        self.assertTrue(trade.accepted)
        self.assertEqual(trade.side, "BUY")
        self.assertEqual(trade.quantity, 0.999)
        self.assertIn("SPY", broker.positions)
        self.assertLess(broker.cash, 500.0)
        self.assertGreater(trade.commission, 0.0)
        self.assertEqual(trade.timestamp, TIMESTAMP)

    def test_duplicate_buy_is_rejected_and_recorded(self) -> None:
        broker = PaperBroker()
        broker.buy("SPY", market_price=100.0, atr_value=2.0, timestamp=TIMESTAMP)

        trade = broker.buy("SPY", market_price=101.0, atr_value=2.0, timestamp=TIMESTAMP)

        self.assertFalse(trade.accepted)
        self.assertEqual(trade.reason, "position_already_open")
        self.assertEqual(len(broker.trades), 2)

    def test_sell_closes_position_and_records_realized_pnl(self) -> None:
        broker = PaperBroker()
        broker.buy("SPY", market_price=100.0, atr_value=2.0, timestamp=TIMESTAMP)
        cash_after_buy = broker.cash

        trade = broker.sell("SPY", market_price=110.0, timestamp=TIMESTAMP)

        self.assertTrue(trade.accepted)
        self.assertNotIn("SPY", broker.positions)
        self.assertGreater(trade.realized_pnl, 0.0)
        self.assertGreater(broker.cash, cash_after_buy)
        self.assertAlmostEqual(broker.equity(), broker.cash)

    def test_sell_without_position_is_rejected(self) -> None:
        broker = PaperBroker()

        trade = broker.sell("SPY", market_price=100.0, timestamp=TIMESTAMP)

        self.assertFalse(trade.accepted)
        self.assertEqual(trade.reason, "position_not_open")
        self.assertEqual(len(broker.trades), 1)


if __name__ == "__main__":
    unittest.main()
