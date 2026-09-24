"""Status and health check endpoints."""

from fastapi import APIRouter
from datetime import datetime
import json
from pathlib import Path

from app.api.schemas import StatusResponse, HealthResponse

router = APIRouter(prefix="/status", tags=["status"])

REPORTS_DIR = Path(__file__).parent.parent.parent.parent / "reports"


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        message="API is running"
    )


@router.get("/system", response_model=StatusResponse)
async def system_status():
    """Get system status."""
    scheduler_state_file = REPORTS_DIR / ".scheduler_state.json"
    last_run = None
    scheduler_active = False
    
    if scheduler_state_file.exists():
        try:
            with open(scheduler_state_file, "r") as f:
                state = json.load(f)
                last_run = state.get("last_slot")
                scheduler_active = "last_slot" in state
        except Exception:
            pass
    
    return StatusResponse(
        status="running",
        last_run=last_run,
        next_run=None,  # TODO: calculate next scheduled run
        scheduler_active=scheduler_active,
        api_version="0.1.0",
        timestamp=datetime.utcnow().isoformat() + "Z"
    )
