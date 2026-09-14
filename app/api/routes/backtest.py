"""Backtest results endpoints."""

from fastapi import APIRouter
from pathlib import Path
import json

from app.api.schemas import BacktestMetrics

router = APIRouter(prefix="/backtest", tags=["backtest"])

REPORTS_DIR = Path(__file__).parent.parent.parent.parent / "reports"


@router.get("/latest")
async def get_latest_backtest():
    """Get latest backtest results."""
    summary_file = REPORTS_DIR / "backtest_summary.json"
    
    if not summary_file.exists():
        return {"message": "No backtest data available"}
    
    try:
        with open(summary_file, "r") as f:
            data = json.load(f)
            return data
    except Exception as e:
        return {"error": str(e)}


@router.get("/metrics/{period}")
async def get_metrics_by_period(period: str):
    """Get backtest metrics for a specific period (development, validation, out_of_sample)."""
    summary_file = REPORTS_DIR / "backtest_summary.json"
    
    if not summary_file.exists():
        return {"message": "No backtest data available"}
    
    try:
        with open(summary_file, "r") as f:
            data = json.load(f)
            if "periods" in data and period in data["periods"]:
                return data["periods"][period]
            return {"message": f"Period '{period}' not found"}
    except Exception as e:
        return {"error": str(e)}
