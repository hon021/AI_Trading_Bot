"""Deterministic risk checks and position sizing for long-only paper trading."""

from __future__ import annotations

from dataclasses import dataclass
from math import floor
from typing import Mapping


@dataclass(frozen=True)
class RiskConfig:
    initial_capital: float = 500.0
    risk_per_trade: float = 5.0
    max_position_fraction: float = 0.20
    max_total_exposure_fraction: float = 0.40
    max_positions: int = 2
    max_drawdown_fraction: float = 0.15
    quantity_decimals: int = 3
    minimum_quantity: float = 0.001
    slippage_rate: float = 0.0005
    commission_rate: float = 0.001


@dataclass(frozen=True)
class RiskDecision:
    allowed: bool
    reason: str
    quantity: float = 0.0
    stop_price: float | None = None


@dataclass(frozen=True)
class PositionView:
    symbol: str
    quantity: float
    average_price: float
    stop_price: float | None = None


class RiskManager:
    """Apply the strategy's position and exposure limits before a BUY."""

    def __init__(self, config: RiskConfig | None = None) -> None:
        self.config = config or RiskConfig()

    def evaluate_buy(
        self,
        *,
        symbol: str,
        market_price: float,
        atr_value: float,
        cash: float,
        positions: Mapping[str, PositionView],
        equity: float,
        peak_equity: float,
    ) -> RiskDecision:
        """Return an approved quantity and stop or a reason for rejection."""
        if market_price <= 0 or atr_value <= 0 or cash < 0 or equity <= 0:
            return RiskDecision(False, "invalid_market_or_portfolio_values")
        if symbol in positions:
            return RiskDecision(False, "position_already_open")
        if len(positions) >= self.config.max_positions:
            return RiskDecision(False, "maximum_positions_reached")
        if peak_equity <= 0:
            return RiskDecision(False, "invalid_peak_equity")
        if equity <= peak_equity * (1 - self.config.max_drawdown_fraction):
            return RiskDecision(False, "drawdown_limit_reached")

        current_exposure = sum(
            position.quantity * position.average_price for position in positions.values()
        )
        max_position_value = equity * self.config.max_position_fraction
        max_total_exposure = equity * self.config.max_total_exposure_fraction
        available_exposure = max_total_exposure - current_exposure
        if available_exposure <= 0:
            return RiskDecision(False, "maximum_total_exposure_reached")

        entry_price = market_price * (1 + self.config.slippage_rate)
        stop_distance = 2 * atr_value
        quantity_by_risk = self.config.risk_per_trade / stop_distance
        quantity_by_position = max_position_value / entry_price
        quantity_by_total_exposure = available_exposure / entry_price
        quantity = min(quantity_by_risk, quantity_by_position, quantity_by_total_exposure)
        quantity = self._floor_quantity(quantity)
        if quantity < self.config.minimum_quantity:
            return RiskDecision(False, "quantity_below_minimum")

        gross = entry_price * quantity
        total_cost = gross * (1 + self.config.commission_rate)
        if total_cost > cash:
            quantity = self._floor_quantity(
                cash / (entry_price * (1 + self.config.commission_rate))
            )
            if quantity < self.config.minimum_quantity:
                return RiskDecision(False, "insufficient_cash")

        return RiskDecision(
            allowed=True,
            reason="approved",
            quantity=quantity,
            stop_price=entry_price - stop_distance,
        )

    def _floor_quantity(self, quantity: float) -> float:
        factor = 10**self.config.quantity_decimals
        return floor(quantity * factor) / factor
