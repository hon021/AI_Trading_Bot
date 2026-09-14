"""FastAPI application for AI Trading Bot."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import status, signals, portfolio, trades, backtest

app = FastAPI(
    title="AI Trading Bot API",
    description="REST API for AI Trading Bot paper trading system",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(status.router)
app.include_router(signals.router)
app.include_router(portfolio.router)
app.include_router(trades.router)
app.include_router(backtest.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "AI Trading Bot API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }


@app.get("/api/v1")
async def api_v1_info():
    """API v1 information."""
    return {
        "version": "0.1.0",
        "endpoints": {
            "status": "/status/health, /status/system",
            "signals": "/signals/latest, /signals/history",
            "portfolio": "/portfolio/summary, /portfolio/positions",
            "trades": "/trades/history, /trades/stats",
            "backtest": "/backtest/latest, /backtest/metrics/{period}"
        }
    }
