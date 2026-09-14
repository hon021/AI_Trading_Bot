"""Pydantic models for API responses."""

from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class SignalResponse(BaseModel):
    """Signal from the quant engine."""
    timestamp: str
    symbol: str
    signal: str  # BUY, SELL, HOLD
    indicators: Dict[str, float]
    reason: Optional[str] = None


class PortfolioPosition(BaseModel):
    """Open position in portfolio."""
    symbol: str
    quantity: float
    entry_price: float
    current_price: Optional[float] = None
    unrealized_pnl: Optional[float] = None


class PortfolioResponse(BaseModel):
    """Current portfolio state."""
    cash: float
    invested_value: float
    total_value: float
    unrealized_pnl: float
    positions: list[PortfolioPosition]
    timestamp: str


class TradeResponse(BaseModel):
    """Completed trade record."""
    id: Optional[int] = None
    timestamp: str
    symbol: str
    side: str  # BUY or SELL
    quantity: float
    price: float
    commission: float
    slippage: float
    pnl: Optional[float] = None


class BacktestMetrics(BaseModel):
    """Backtesting metrics."""
    initial_equity: float
    final_equity: float
    total_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    profit_factor: float
    num_trades: int
    total_commission: float


class StatusResponse(BaseModel):
    """System status."""
    status: str  # "running", "idle", "error"
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    scheduler_active: bool
    api_version: str
    timestamp: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    message: str
