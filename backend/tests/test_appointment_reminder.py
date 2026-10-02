from datetime import datetime

from utils.appointment_reminder import Appointment, find_next_available_slot


def _apt(i, hh, mm=0, dur=30):
    return Appointment(id=i, patient_id="p", doctor_id="d", doctor_name="Dr",
                       scheduled_time=datetime(2030, 1, 1, hh, mm), duration_minutes=dur)


def test_slot_must_end_before_closing():
    # 17:45 + 30min would end 18:15; must roll to next morning
    slot = find_next_available_slot(_apt("n", 17, 45), [])
    assert slot == datetime(2030, 1, 2, 8, 15)


def test_slot_ending_exactly_at_closing_ok():
    assert find_next_available_slot(_apt("n", 17, 30), []) == datetime(2030, 1, 1, 17, 30)
