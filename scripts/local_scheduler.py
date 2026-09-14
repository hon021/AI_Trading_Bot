"""Local weekday scheduler for the four daily analysis slots."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time as time_module
from datetime import datetime, time, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


MARKET_TIMEZONE = ZoneInfo("America/New_York")
SCHEDULE_TIMES = (time(10, 0), time(12, 0), time(14, 0), time(15, 30))
STATE_PATH = Path("reports/.scheduler_state.json")
LOG_PATH = Path("reports/scheduler.log")


def scheduled_slot(now: datetime) -> str | None:
    """Return the current weekday slot key, or None outside scheduled minutes."""
    local_now = now.astimezone(MARKET_TIMEZONE)
    if local_now.weekday() >= 5:
        return None
    current_time = local_now.time().replace(second=0, microsecond=0)
    if current_time not in SCHEDULE_TIMES:
        return None
    return f"{local_now.date().isoformat()}T{current_time.isoformat()}"


def run_cycle(slot: str) -> int:
    """Run one analysis subprocess and append a scheduler log entry."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [sys.executable, "-m", "scripts.run_analysis"],
        check=False,
        capture_output=True,
        text=True,
    )
    timestamp = datetime.now(timezone.utc).isoformat()
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(f"{timestamp} slot={slot} exit_code={completed.returncode}\n")
        if completed.stdout:
            log_file.write(completed.stdout)
        if completed.stderr:
            log_file.write(completed.stderr)
    return completed.returncode


def load_state() -> dict[str, str]:
    if not STATE_PATH.exists():
        return {}
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def save_state(state: dict[str, str]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = STATE_PATH.with_suffix(".tmp")
    temporary_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    temporary_path.replace(STATE_PATH)


def run_scheduler(*, poll_seconds: int = 20, run_now: bool = False) -> None:
    """Poll the local clock until interrupted with Ctrl+C."""
    if poll_seconds < 1:
        raise ValueError("poll_seconds must be positive")
    state = load_state()
    if run_now:
        slot = "manual"
        run_cycle(slot)
        state["last_slot"] = slot
        save_state(state)
        return

    print("Local scheduler active. Press Ctrl+C to stop.")
    while True:
        now = datetime.now(MARKET_TIMEZONE)
        slot = scheduled_slot(now)
        if slot and state.get("last_slot") != slot:
            exit_code = run_cycle(slot)
            state["last_slot"] = slot
            state["last_exit_code"] = str(exit_code)
            save_state(state)
            print(f"{now.isoformat()} slot={slot} exit_code={exit_code}")
        time_module.sleep(poll_seconds)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--poll-seconds", type=int, default=20)
    parser.add_argument(
        "--run-now",
        action="store_true",
        help="Run one analysis cycle immediately instead of waiting for a slot.",
    )
    args = parser.parse_args()
    run_scheduler(poll_seconds=args.poll_seconds, run_now=args.run_now)


if __name__ == "__main__":
    main()
