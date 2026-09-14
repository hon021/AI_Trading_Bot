"""Portfolio endpoints."""

from fastapi import APIRouter
from datetime import datetime
from pathlib import Path
import json

from app.api.schemas import PortfolioResponse, PortfolioPosition

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

REPORTS_DIR = Path(__file__).parent.parent.parent.parent / "reports"


@router.get("/summary", response_model=PortfolioResponse)
async def get_portfolio_summary():
    """Get current portfolio summary."""
    # TODO: Read from backtest_summary.json or live state
    return PortfolioResponse(
        cash=500.0,
        invested_value=0.0,
        total_value=500.0,
        unrealized_pnl=0.0,
        positions=[],
        timestamp=datetime.utcnow().isoformat() + "Z"
    )


@router.get("/positions", response_model=list[PortfolioPosition])
async def get_open_positions():
    """Get all open positions."""
    # TODO: Read from paper broker state or backtest results
    return []
