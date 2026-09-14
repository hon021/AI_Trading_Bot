"""Reproducible, point-in-time backtester for the quantitative strategy."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from math import inf, sqrt
from typing import Mapping

import pandas as pd

from app.paper_trading.paper_broker import PaperBroker, Trade
from app.strategy.quant_engine import QuantEngine, Signal


DEFAULT_DECISION_TIMES = (time(10, 0), time(12, 0), time(14, 0), time(15, 30))


@dataclass(frozen=True)
class BacktestConfig:
    initial_cash: float = 500.0
    decision_times: tuple[time, ...] = DEFAULT_DECISION_TIMES
    liquidate_at_end: bool = True
    bars_per_year: int = 252 * 7
    start_timestamp: pd.Timestamp | None = None
    end_timestamp: pd.Timestamp | None = None


@dataclass(frozen=True)
class BacktestResult:
    metrics: dict[str, float]
    benchmark_metrics: dict[str, float]
    trades: tuple[Trade, ...]
    equity_curve: pd.Series
    benchmark_equity: pd.Series


@dataclass(frozen=True)
class _PendingOrder:
    symbol: str
    side: Signal
    atr_value: float
    reason: str


class Backtester:
    """Run the strategy without allowing future rows into a decision."""

    def __init__(
        self,
        *,
        engine: QuantEngine | None = None,
        config: BacktestConfig | None = None,
    ) -> None:
        self.engine = engine or QuantEngine()
        self.config = config or BacktestConfig()

    def run(self, frames: Mapping[str, pd.DataFrame]) -> BacktestResult:
        """Run a multi-symbol backtest over timestamp-indexed OHLCV frames."""
        if not frames:
            raise ValueError("At least one symbol frame is required")
        prepared = {symbol: self._prepare_frame(frame, symbol) for symbol, frame in frames.items()}
        timestamps = sorted(set().union(*(frame.index for frame in prepared.values())))
        broker = PaperBroker(initial_cash=self.config.initial_cash)
        pending: dict[pd.Timestamp, list[_PendingOrder]] = {}
        equity_values: list[float] = []
        equity_index: list[pd.Timestamp] = []

        for timestamp in timestamps:
            in_evaluation_window = self._in_evaluation_window(timestamp)
            rows = {
                symbol: frame.loc[timestamp]
                for symbol, frame in prepared.items()
                if timestamp in frame.index
            }
            self._execute_pending(timestamp, rows, pending, broker)
            stopped_symbols = self._execute_stops(timestamp, rows, broker)
            current_prices = {symbol: float(row["Close"]) for symbol, row in rows.items()}
            broker.mark_to_market(current_prices)

            if in_evaluation_window and self._is_decision_time(timestamp):
                for symbol, frame in prepared.items():
                    if symbol not in rows or symbol in stopped_symbols:
                        continue
                    row_position = frame.index.get_loc(timestamp)
                    if isinstance(row_position, slice) or row_position + 1 >= len(frame):
                        continue
                    history = frame.iloc[: row_position + 1]
                    position_open = symbol in broker.positions
                    signal = self.engine.signal(history, position_open=position_open)
                    if signal == Signal.HOLD:
                        continue
                    execution_timestamp = frame.index[row_position + 1]
                    if not self._in_evaluation_window(execution_timestamp):
                        continue
                    if any(
                        order.symbol == symbol for order in pending.get(execution_timestamp, [])
                    ):
                        continue
                    atr_value = float(self.engine.enrich(history).iloc[-1]["ATR14"])
                    if pd.isna(atr_value):
                        continue
                    pending.setdefault(execution_timestamp, []).append(
                        _PendingOrder(symbol, signal, atr_value, "strategy_signal")
                    )

            if in_evaluation_window:
                equity_values.append(broker.equity(current_prices))
                equity_index.append(timestamp)

        evaluation_timestamps = [
            timestamp for timestamp in timestamps if self._in_evaluation_window(timestamp)
        ]
        if self.config.liquidate_at_end and evaluation_timestamps:
            final_timestamp = evaluation_timestamps[-1]
            self._liquidate_at_end(prepared, broker, final_timestamp)
            if equity_values:
                equity_values[-1] = broker.equity(
                    {
                        symbol: self._price_at_or_before(frame, final_timestamp)
                        for symbol, frame in prepared.items()
                    }
                )

        equity_curve = pd.Series(equity_values, index=pd.DatetimeIndex(equity_index), name="equity")
        benchmark = self._buy_and_hold(prepared, pd.DatetimeIndex(evaluation_timestamps))
        return BacktestResult(
            metrics=self._metrics(equity_curve, broker.trades),
            benchmark_metrics=self._metrics(benchmark, []),
            trades=tuple(broker.trades),
            equity_curve=equity_curve,
            benchmark_equity=benchmark,
        )

    def _execute_pending(
        self,
        timestamp: pd.Timestamp,
        rows: Mapping[str, pd.Series],
        pending: dict[pd.Timestamp, list[_PendingOrder]],
        broker: PaperBroker,
    ) -> None:
        for order in pending.pop(timestamp, []):
            row = rows.get(order.symbol)
            if row is None:
                continue
            market_price = float(row["Open"])
            if order.side == Signal.BUY:
                broker.buy(order.symbol, market_price, order.atr_value, timestamp=timestamp.to_pydatetime())
            elif order.side == Signal.SELL:
                broker.sell(
                    order.symbol,
                    market_price,
                    timestamp=timestamp.to_pydatetime(),
                    reason=order.reason,
                )

    def _execute_stops(
        self,
        timestamp: pd.Timestamp,
        rows: Mapping[str, pd.Series],
        broker: PaperBroker,
    ) -> set[str]:
        stopped: set[str] = set()
        for symbol, position in list(broker.positions.items()):
            row = rows.get(symbol)
            if row is None or float(row["Low"]) > position.stop_price:
                continue
            stop_market_price = min(float(row["Open"]), position.stop_price)
            broker.sell(
                symbol,
                stop_market_price,
                timestamp=timestamp.to_pydatetime(),
                reason="stop_loss",
            )
            stopped.add(symbol)
        return stopped

    def _liquidate_at_end(
        self,
        frames: Mapping[str, pd.DataFrame],
        broker: PaperBroker,
        timestamp: pd.Timestamp,
    ) -> None:
        for symbol in list(broker.positions):
            broker.sell(
                symbol,
                float(frames[symbol].iloc[-1]["Close"]),
                timestamp=timestamp.to_pydatetime(),
                reason="end_of_backtest",
            )

    def _buy_and_hold(
        self,
        frames: Mapping[str, pd.DataFrame],
        timestamps: pd.DatetimeIndex,
    ) -> pd.Series:
        symbols = sorted(frames)
        first_timestamp = timestamps[0]
        first_prices = {
            symbol: self._price_at_or_after(frame, first_timestamp, "Open")
            for symbol, frame in frames.items()
        }
        commission_rate = 0.001
        slippage_rate = 0.0005
        allocation = self.config.initial_cash / len(symbols)
        quantities = {
            symbol: allocation / (price * (1 + slippage_rate))
            for symbol, price in first_prices.items()
        }
        entry_cost = sum(
            quantity * price * (1 + slippage_rate) * (1 + commission_rate)
            for (quantity, price) in zip(quantities.values(), first_prices.values())
        )
        residual_cash = self.config.initial_cash - entry_cost
        values = []
        for timestamp in timestamps:
            value = residual_cash
            for symbol, quantity in quantities.items():
                frame = frames[symbol]
                if timestamp in frame.index:
                    price = float(frame.loc[timestamp]["Close"])
                else:
                    prior = frame.loc[frame.index <= timestamp]
                    if prior.empty:
                        continue
                    price = float(prior.iloc[-1]["Close"])
                value += quantity * price
            values.append(value)
        return pd.Series(values, index=timestamps, name="buy_and_hold")

    def _metrics(
        self,
        equity: pd.Series,
        trades: list[Trade],
        *,
        initial_equity: float | None = None,
    ) -> dict[str, float]:
        if equity.empty:
            return {}
        starting_equity = initial_equity or self.config.initial_cash
        returns = equity.pct_change().dropna()
        total_return = equity.iloc[-1] / starting_equity - 1
        running_max = equity.cummax().clip(lower=starting_equity)
        drawdowns = equity / running_max - 1
        max_drawdown = float(drawdowns.min())
        volatility = float(returns.std(ddof=1)) if len(returns) > 1 else 0.0
        sharpe = (
            float(returns.mean() / volatility * sqrt(self.config.bars_per_year))
            if volatility > 0
            else 0.0
        )
        sells = [trade for trade in trades if trade.accepted and trade.side == "SELL"]
        winners = [trade.realized_pnl for trade in sells if trade.realized_pnl > 0]
        losers = [trade.realized_pnl for trade in sells if trade.realized_pnl < 0]
        gross_loss = abs(sum(losers))
        profit_factor = sum(winners) / gross_loss if gross_loss else (inf if winners else 0.0)
        return {
            "initial_equity": float(starting_equity),
            "final_equity": float(equity.iloc[-1]),
            "total_return": float(total_return),
            "max_drawdown": max_drawdown,
            "sharpe_ratio": sharpe,
            "win_rate": len(winners) / len(sells) if sells else 0.0,
            "profit_factor": float(profit_factor),
            "closed_trades": float(len(sells)),
            "accepted_trades": float(sum(trade.accepted for trade in trades)),
            "rejected_trades": float(sum(not trade.accepted for trade in trades)),
            "fees": float(sum(trade.commission for trade in trades)),
        }

    @staticmethod
    def _prepare_frame(frame: pd.DataFrame, symbol: str) -> pd.DataFrame:
        required = {"Open", "High", "Low", "Close", "Volume"}
        missing = required.difference(frame.columns)
        if missing:
            raise ValueError(f"{symbol}: missing columns: {', '.join(sorted(missing))}")
        if not isinstance(frame.index, pd.DatetimeIndex) or frame.index.tz is None:
            raise ValueError(f"{symbol}: index must be timezone-aware DatetimeIndex")
        if frame.index.has_duplicates or not frame.index.is_monotonic_increasing:
            raise ValueError(f"{symbol}: index must be unique and sorted")
        return frame.sort_index()

    def _is_decision_time(self, timestamp: pd.Timestamp) -> bool:
        local_timestamp = timestamp.tz_convert("America/New_York")
        return local_timestamp.time() in self.config.decision_times

    @staticmethod
    def _price_at_or_before(frame: pd.DataFrame, timestamp: pd.Timestamp) -> float:
        available = frame.loc[frame.index <= timestamp]
        if available.empty:
            return float(frame.iloc[0]["Close"])
        return float(available.iloc[-1]["Close"])

    @staticmethod
    def _price_at_or_after(
        frame: pd.DataFrame,
        timestamp: pd.Timestamp,
        column: str,
    ) -> float:
        available = frame.loc[frame.index >= timestamp]
        if available.empty:
            return float(frame.iloc[-1][column])
        return float(available.iloc[0][column])

    def _in_evaluation_window(self, timestamp: pd.Timestamp) -> bool:
        if self.config.start_timestamp is not None and timestamp < self.config.start_timestamp:
            return False
        if self.config.end_timestamp is not None and timestamp > self.config.end_timestamp:
            return False
        return True
