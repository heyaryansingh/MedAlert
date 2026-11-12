from datetime import datetime, timedelta

from utils.appointment_reminder import calculate_reminder_times


def test_naive_appointment_time_does_not_crash():
    apt = datetime.utcnow() + timedelta(days=10)
    assert len(calculate_reminder_times(apt)) == 3


def test_non_positive_intervals_skipped():
    apt = datetime.utcnow() + timedelta(days=10)
    assert len(calculate_reminder_times(apt, [24, 0, -5])) == 1
