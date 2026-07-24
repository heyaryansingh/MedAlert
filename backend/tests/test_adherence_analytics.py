"""Tests for backend.utils.adherence_analytics.calculate_streaks.

Covers day-based streak counting, including multi-dose-per-day regimens
which log more than one taken dose on the same calendar date.
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.utils.adherence_analytics import MedicationLog, calculate_streaks


def _log(day: str, hour: int, taken: bool) -> MedicationLog:
    return MedicationLog(
        medication_id="med-1",
        medication_name="Test Med",
        timestamp=datetime.fromisoformat(f"{day}T{hour:02d}:00:00"),
        taken=taken,
    )


class TestCalculateStreaks:
    def test_consecutive_daily_doses(self):
        logs = [
            _log("2026-01-01", 8, True),
            _log("2026-01-02", 8, True),
            _log("2026-01-03", 8, True),
        ]
        current, longest = calculate_streaks(logs)
        assert current == 3
        assert longest == 3

    def test_same_day_multi_dose_does_not_break_streak(self):
        logs = [
            _log("2026-01-01", 8, True),
            _log("2026-01-01", 20, True),
            _log("2026-01-02", 8, True),
            _log("2026-01-02", 20, True),
            _log("2026-01-03", 8, True),
            _log("2026-01-03", 20, True),
        ]
        current, longest = calculate_streaks(logs)
        assert current == 3
        assert longest == 3

    def test_missed_dose_breaks_streak(self):
        logs = [
            _log("2026-01-01", 8, True),
            _log("2026-01-02", 8, True),
            _log("2026-01-03", 8, False),
            _log("2026-01-04", 8, True),
        ]
        current, longest = calculate_streaks(logs)
        assert current == 1
        assert longest == 2

    def test_empty_logs(self):
        assert calculate_streaks([]) == (0, 0)
