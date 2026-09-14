"""Deterministic long-only paper broker with an in-memory trade ledger."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping

from app.risk.risk_manager import PositionView, RiskConfig, RiskManager


@dataclass
class Position:
    symbol: str
    quantity: float
    average_price: float
    stop_price: float
    cost_basis: float

    def as_view(self) -> PositionView:
        return PositionView(
            symbol=self.symbol,
            quantity=self.quantity,
            average_price=self.average_price,
            stop_price=self.stop_price,
        )


@dataclass(frozen=True)
class Trade:
    timestamp: datetime
    symbol: str
    side: str
    quantity: float
    market_price: float
    execution_price: float | None
    gross_value: float
    commission: float
    realized_pnl: float
    accepted: bool
    reason: str
    cash_after: float


class PaperBroker:
    """Simulate long-only BUY and SELL operations without broker connectivity."""

    def __init__(
        self,
        *,
        initial_cash: float = 500.0,
        risk_manager: RiskManager | None = None,
    ) -> None:
        if initial_cash <= 0:
            raise ValueError("initial_cash must be positive")
        self.cash = initial_cash
        self.positions: dict[str, Position] = {}
        self.trades: list[Trade] = []
        self.realized_pnl = 0.0
        self.total_fees = 0.0
        self.peak_equity = initial_cash
        self._last_prices: dict[str, float] = {}
        self.risk_manager = risk_manager or RiskManager(
            RiskConfig(initial_capital=initial_cash)
        )

    def buy(
        self,
        symbol: str,
        market_price: float,
        atr_value: float,
        *,
        timestamp: datetime | None = None,
    ) -> Trade:
        """Attempt a full new position and record approval or rejection."""
        self._validate_price(market_price)
        self._last_prices[symbol] = market_price
        equity = self.equity()
        decision = self.risk_manager.evaluate_buy(
            symbol=symbol,
            market_price=market_price,
            atr_value=atr_value,
            cash=self.cash,
            positions={key: position.as_view() for key, position in self.positions.items()},
            equity=equity,
            peak_equity=self.peak_equity,
        )
        if not decision.allowed:
            return self._record_rejected(
                symbol=symbol,
                side="BUY",
                market_price=market_price,
                reason=decision.reason,
                timestamp=timestamp,
            )

        execution_price = market_price * (1 + self.risk_manager.config.slippage_rate)
        gross_value = execution_price * decision.quantity
        commission = gross_value * self.risk_manager.config.commission_rate
        total_cost = gross_value + commission
        self.cash -= total_cost
        self.total_fees += commission
        self.positions[symbol] = Position(
            symbol=symbol,
            quantity=decision.quantity,
            average_price=execution_price,
            stop_price=decision.stop_price or 0.0,
            cost_basis=gross_value,
        )
        trade = Trade(
            timestamp=self._timestamp(timestamp),
            symbol=symbol,
            side="BUY",
            quantity=decision.quantity,
            market_price=market_price,
            execution_price=execution_price,
            gross_value=gross_value,
            commission=commission,
            realized_pnl=0.0,
            accepted=True,
            reason=decision.reason,
            cash_after=self.cash,
        )
        self.trades.append(trade)
        self._update_peak()
        return trade

    def sell(
        self,
        symbol: str,
        market_price: float,
        *,
        timestamp: datetime | None = None,
        reason: str = "signal",
    ) -> Trade:
        """Close the full long position for a symbol and record the trade."""
        self._validate_price(market_price)
        self._last_prices[symbol] = market_price
        position = self.positions.get(symbol)
        if position is None:
            return self._record_rejected(
                symbol=symbol,
                side="SELL",
                market_price=market_price,
                reason="position_not_open",
                timestamp=timestamp,
            )

        execution_price = market_price * (1 - self.risk_manager.config.slippage_rate)
        gross_value = execution_price * position.quantity
        commission = gross_value * self.risk_manager.config.commission_rate
        proceeds = gross_value - commission
        realized_pnl = proceeds - position.cost_basis
        self.cash += proceeds
        self.realized_pnl += realized_pnl
        self.total_fees += commission
        quantity = position.quantity
        del self.positions[symbol]
        trade = Trade(
            timestamp=self._timestamp(timestamp),
            symbol=symbol,
            side="SELL",
            quantity=quantity,
            market_price=market_price,
            execution_price=execution_price,
            gross_value=gross_value,
            commission=commission,
            realized_pnl=realized_pnl,
            accepted=True,
            reason=reason,
            cash_after=self.cash,
        )
        self.trades.append(trade)
        self._update_peak()
        return trade

    def equity(self, prices: Mapping[str, float] | None = None) -> float:
        """Return cash plus marked-to-market value of open positions."""
        current_prices = dict(self._last_prices)
        if prices:
            current_prices.update(prices)
        invested_value = sum(
            position.quantity * current_prices.get(symbol, position.average_price)
            for symbol, position in self.positions.items()
        )
        return self.cash + invested_value

    def mark_to_market(self, prices: Mapping[str, float]) -> float:
        """Update known prices and the equity peak, then return current equity."""
        for symbol, price in prices.items():
            self._validate_price(price)
            self._last_prices[symbol] = price
        current_equity = self.equity()
        self.peak_equity = max(self.peak_equity, current_equity)
        return current_equity

    def _record_rejected(
        self,
        *,
        symbol: str,
        side: str,
        market_price: float,
        reason: str,
        timestamp: datetime | None,
    ) -> Trade:
        trade = Trade(
            timestamp=self._timestamp(timestamp),
            symbol=symbol,
            side=side,
            quantity=0.0,
            market_price=market_price,
            execution_price=None,
            gross_value=0.0,
            commission=0.0,
            realized_pnl=0.0,
            accepted=False,
            reason=reason,
            cash_after=self.cash,
        )
        self.trades.append(trade)
        return trade

    def _update_peak(self) -> None:
        self.peak_equity = max(self.peak_equity, self.equity())

    @staticmethod
    def _timestamp(timestamp: datetime | None) -> datetime:
        value = timestamp or datetime.now(timezone.utc)
        if value.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")
        return value.astimezone(timezone.utc)

    @staticmethod
    def _validate_price(price: float) -> None:
        if price <= 0:
            raise ValueError("market_price must be positive")
