#!/usr/bin/env python
"""Run the FastAPI server for the AI Trading Bot."""

import uvicorn
import argparse
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Run AI Trading Bot API server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload on file changes")
    
    args = parser.parse_args()
    
    logger.info(f"Starting AI Trading Bot API on {args.host}:{args.port}")
    logger.info("API Documentation: http://{}:{}/docs".format(args.host, args.port))
    
    uvicorn.run(
        "app.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )


if __name__ == "__main__":
    main()
