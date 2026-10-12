"""Tests for symptom checker red flag escalation."""

from utils.symptom_checker import SymptomChecker, UrgencyLevel, check_emergency


def test_urgent_red_flag_escalates():
    result = SymptomChecker().assess_symptoms(["shortness of breath"])
    assert result.urgency_level == UrgencyLevel.URGENT


def test_urgent_partial_match_escalates():
    result = SymptomChecker().assess_symptoms(["fainting spells"])
    assert result.urgency_level == UrgencyLevel.URGENT


def test_emergency_not_downgraded_by_urgent():
    is_emergency, _ = check_emergency(["chest pain", "fainting"])
    assert is_emergency
    is_emergency, _ = check_emergency(["fainting", "chest pain"])
    assert is_emergency
