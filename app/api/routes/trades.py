"""Trade history endpoints."""

from fastapi import APIRouter
from pathlib import Path
import pandas as pd

from app.api.schemas import TradeResponse

router = APIRouter(prefix="/trades", tags=["trades"])

REPORTS_DIR = Path(__file__).parent.parent.parent.parent / "reports"


@router.get("/history", response_model=list[TradeResponse])
async def get_trades_history(limit: int = 100):
    """Get trade history."""
    trades_file = REPORTS_DIR / "trades.csv"
    
    if not trades_file.exists():
        return []
    
    try:
        df = pd.read_csv(trades_file, nrows=limit)
        trades = []
        for _, row in df.iterrows():
            trades.append(TradeResponse(
                timestamp=str(row.get("timestamp", "")),
                symbol=str(row.get("symbol", "")),
                side=str(row.get("side", "")),
                quantity=float(row.get("quantity", 0)),
                price=float(row.get("price", 0)),
                commission=float(row.get("commission", 0)),
                slippage=float(row.get("slippage", 0)),
                pnl=float(row.get("pnl", 0)) if "pnl" in df.columns else None
            ))
        return trades
    except Exception:
        return []


@router.get("/stats")
async def get_trade_statistics():
    """Get trade statistics."""
    trades_file = REPORTS_DIR / "trades.csv"
    
    if not trades_file.exists():
        return {"message": "No trades data available"}
    
    try:
        df = pd.read_csv(trades_file)
        return {
            "total_trades": len(df),
            "total_commission": float(df["commission"].sum()) if "commission" in df.columns else 0,
            "total_slippage": float(df["slippage"].sum()) if "slippage" in df.columns else 0,
        }
    except Exception:
        return {"message": "Error reading trades data"}
