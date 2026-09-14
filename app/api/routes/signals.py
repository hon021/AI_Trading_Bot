"""Signal endpoints."""

from fastapi import APIRouter
from datetime import datetime
import json
from pathlib import Path

from app.api.schemas import SignalResponse

router = APIRouter(prefix="/signals", tags=["signals"])

REPORTS_DIR = Path(__file__).parent.parent.parent.parent / "reports"


@router.get("/latest", response_model=list[SignalResponse])
async def get_latest_signals():
    """Get latest signals from the quant engine."""
    signals_file = REPORTS_DIR / "latest_signals.json"
    
    if not signals_file.exists():
        return []
    
    try:
        with open(signals_file, "r") as f:
            data = json.load(f)
            # Adapt to your signal format
            if isinstance(data, list):
                signals = []
                for sig in data:
                    signals.append(SignalResponse(
                        timestamp=sig.get("timestamp", ""),
                        symbol=sig.get("symbol", ""),
                        signal=sig.get("signal", "HOLD"),
                        indicators=sig.get("indicators", {}),
                        reason=sig.get("reason", None)
                    ))
                return signals
            return []
    except Exception:
        return []


@router.get("/history", response_model=list[SignalResponse])
async def get_signals_history(limit: int = 100):
    """Get historical signals (limited)."""
    # TODO: Read from database or trades.csv
    return []
