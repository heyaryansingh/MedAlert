from utils.emergency_contact import EmergencyContactManager


def _mgr():
    m = EmergencyContactManager()
    m.add_contact("Spec", "555-010-0004", priority=5, is_medical_professional=True)
    m.add_contact("Doc", "555-010-0001", priority=1, is_medical_professional=True)
    m.add_contact("Fam", "555-010-0002", priority=2)
    return m


def test_critical_alerts_medical_by_priority():
    sent = _mgr().trigger_alert("critical", "x", max_contacts=1)
    assert [n.contact_name for n in sent] == ["Doc"]


def test_negative_max_contacts_sends_none():
    assert _mgr().trigger_alert("critical", "x", max_contacts=-1) == []
