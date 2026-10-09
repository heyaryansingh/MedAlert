"""Tests for backend.utils.drug_interaction_checker class-level fallbacks.

The pair table holds one example per hazard, so any other SSRI + MAOI
combination used to come back as "no significant interactions".
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.utils.drug_interaction_checker import (
    DrugInteractionChecker,
    InteractionSeverity,
    Medication,
)


def _med(name):
    return Medication(name=name, generic_name=name, drug_class="", dose="", frequency="daily")


def test_any_ssri_with_any_maoi_is_contraindicated():
    checker = DrugInteractionChecker()
    hits = checker.check_interactions([_med("Sertraline "), _med("tranylcypromine")])
    assert len(hits) == 1
    assert hits[0].severity is InteractionSeverity.CONTRAINDICATED
    assert {hits[0].drug1, hits[0].drug2} == {"sertraline", "tranylcypromine"}
    report = checker.generate_report([_med("sertraline"), _med("tranylcypromine")])
    assert report["risk_level"] == "CRITICAL"


def test_specific_pair_entry_wins_over_class_template():
    hits = DrugInteractionChecker().check_interactions([_med("ibuprofen"), _med("warfarin")])
    assert hits[0].management.startswith("Monitor INR")


def test_unknown_drugs_are_not_reported_as_safe():
    report = DrugInteractionChecker().generate_report([_med("metformin"), _med("lisinopril")])
    assert report["unrecognized_medications"] == ["metformin"]
    assert not any("No significant interactions" in r for r in report["recommendations"])


def test_all_known_and_clean_still_reports_no_interactions():
    report = DrugInteractionChecker().generate_report([_med("metoprolol"), _med("amlodipine")])
    assert report["total_interactions"] == 0
    assert "No significant interactions" in report["recommendations"][-1]
