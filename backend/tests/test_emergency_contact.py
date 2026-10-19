"""Tests for backend.utils.emergency_contact."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.utils.emergency_contact import EmergencyContactManager


def test_critical_alert_dedupes_medical_contacts_without_crash():
    m = EmergencyContactManager()
    m.add_contact("Doc", "555-123-4567", priority=2, is_medical_professional=True)
    m.add_contact("Spouse", "555-123-4568", priority=1)
    sent = m.trigger_alert("critical", "HR 180")
    assert [n.contact_name for n in sent] == ["Doc", "Spouse"]


def test_full_oxygen_saturation_does_not_alert():
    from backend.utils.emergency_contact import check_vital_thresholds_and_alert

    m = EmergencyContactManager()
    m.add_contact("Doc", "555-123-4567", priority=1, is_medical_professional=True)
    assert check_vital_thresholds_and_alert(m, "oxygen_saturation", 100) is None
    assert check_vital_thresholds_and_alert(m, "oxygen_saturation", 84)
