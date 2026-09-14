#!/usr/bin/env python
"""Quick test of the API endpoints."""

import json
import urllib.request
import urllib.error
import sys

BASE_URL = "http://127.0.0.1:8000"
ENDPOINTS = [
    "/",
    "/api/v1",
    "/status/health",
    "/status/system",
    "/signals/latest",
    "/portfolio/summary",
    "/trades/history?limit=5",
    "/backtest/latest",
]


def test_endpoint(url):
    """Test a single endpoint."""
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
            print(f"✓ {url}")
            print(f"  Status: {response.status}")
            return True
    except urllib.error.URLError as e:
        print(f"✗ {url} - Connection error: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"✗ {url} - JSON error: {e}")
        return False
    except Exception as e:
        print(f"✗ {url} - Error: {e}")
        return False


def main():
    print("Testing AI Trading Bot API endpoints...\n")
    
    passed = 0
    failed = 0
    
    for endpoint in ENDPOINTS:
        url = BASE_URL + endpoint
        if test_endpoint(url):
            passed += 1
        else:
            failed += 1
    
    print(f"\n\nResults: {passed} passed, {failed} failed")
    print(f"\nAPI Documentation available at: {BASE_URL}/docs")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
