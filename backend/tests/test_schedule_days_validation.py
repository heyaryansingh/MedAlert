"""Tests that create_reminder_schedule rejects a non-positive day span."""

from datetime import datetime

import pytest

from backend.utils.medication_scheduler import (
    DoseFrequency,
    Medication,
    create_reminder_schedule,
)

MEDS = [Medication("Aspirin", "100mg", DoseFrequency.ONCE_DAILY)]


@pytest.mark.parametrize("days", [0, -3])
def test_non_positive_days_raises_instead_of_empty_schedule(days):
    with pytest.raises(ValueError):
        create_reminder_schedule(MEDS, datetime(2026, 1, 1), days=days)


def test_one_day_still_schedules_doses():
    assert create_reminder_schedule(MEDS, datetime(2026, 1, 1), days=1)
