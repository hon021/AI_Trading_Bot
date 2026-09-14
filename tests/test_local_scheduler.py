from __future__ import annotations

import unittest
from datetime import datetime, timezone

from scripts.local_scheduler import scheduled_slot


class LocalSchedulerTests(unittest.TestCase):
    def test_returns_weekday_slot_in_new_york_time(self) -> None:
        now = datetime(2026, 9, 14, 14, 0, tzinfo=timezone.utc)

        self.assertEqual(scheduled_slot(now), "2026-09-14T10:00:00")

    def test_ignores_weekends_and_non_scheduled_minutes(self) -> None:
        weekend = datetime(2026, 9, 12, 14, 0, tzinfo=timezone.utc)
        between_slots = datetime(2026, 9, 14, 15, 15, tzinfo=timezone.utc)

        self.assertIsNone(scheduled_slot(weekend))
        self.assertIsNone(scheduled_slot(between_slots))

    def test_handles_daylight_saving_time(self) -> None:
        winter_slot = datetime(2026, 1, 5, 15, 0, tzinfo=timezone.utc)

        self.assertEqual(scheduled_slot(winter_slot), "2026-01-05T10:00:00")


if __name__ == "__main__":
    unittest.main()
