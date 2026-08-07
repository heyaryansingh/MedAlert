"""Tests for the polypharmacy risk scorer."""

import pytest

from backend.utils.polypharmacy_risk_scorer import (
    MedicationEntry,
    PolypharmacyRiskScorer,
    RiskLevel,
)


@pytest.fixture
def scorer():
    return PolypharmacyRiskScorer()


def _meds(*names):
    return [MedicationEntry(generic_name=name) for name in names]


def test_empty_regimen_is_low_risk(scorer):
    result = scorer.score([])

    assert result.medication_count == 0
    assert result.anticholinergic_burden_score == 0
    assert result.risk_level is RiskLevel.LOW
    assert result.high_burden_medications == []


def test_zero_burden_drugs_stay_below_the_burden_thresholds(scorer):
    result = scorer.score(_meds("metformin", "lisinopril"))

    assert result.anticholinergic_burden_score == 0
    assert result.risk_level is RiskLevel.LOW


def test_burden_scores_are_summed_across_the_regimen(scorer):
    result = scorer.score(_meds("diphenhydramine", "alprazolam", "warfarin"))

    assert result.anticholinergic_burden_score == 3 + 2 + 1


def test_unknown_drugs_contribute_no_burden(scorer):
    result = scorer.score(_meds("some-investigational-compound"))

    assert result.anticholinergic_burden_score == 0
    assert result.high_burden_medications == []


def test_drugs_scoring_two_or_more_are_flagged(scorer):
    result = scorer.score(_meds("amitriptyline", "zolpidem", "loperamide"))

    assert set(result.high_burden_medications) == {"amitriptyline", "zolpidem"}


def test_lookup_is_insensitive_to_case_and_whitespace(scorer):
    result = scorer.score(_meds("  Diphenhydramine  "))

    assert result.anticholinergic_burden_score == 3
    assert result.high_burden_medications == ["diphenhydramine"]


def test_the_same_drug_written_two_ways_is_reported_once(scorer):
    """The flagged list is normalized, so set() dedup actually collapses it."""
    result = scorer.score(_meds("Diphenhydramine", " diphenhydramine "))

    recommendation = next(
        line for line in result.recommendations if "burden and may warrant" in line
    )

    assert recommendation.count("diphenhydramine") == 1


def test_ten_medications_reach_hyperpolypharmacy(scorer):
    result = scorer.score(_meds(*["metformin"] * 10))

    assert result.risk_level is RiskLevel.SEVERE
    assert any("hyperpolypharmacy" in line for line in result.recommendations)


def test_five_medications_reach_polypharmacy(scorer):
    result = scorer.score(_meds(*["metformin"] * 5))

    assert result.risk_level is RiskLevel.HIGH
    assert any("polypharmacy" in line for line in result.recommendations)


def test_burden_alone_can_drive_severe_risk(scorer):
    """Two high-burden drugs total 6, which is severe even at a count of 2."""
    result = scorer.score(_meds("diphenhydramine", "amitriptyline"))

    assert result.medication_count == 2
    assert result.anticholinergic_burden_score == 6
    assert result.risk_level is RiskLevel.SEVERE


def test_clean_regimen_gets_a_reassuring_recommendation(scorer):
    result = scorer.score(_meds("metformin"))

    assert len(result.recommendations) == 1
    assert "No significant" in result.recommendations[0]


def test_every_result_carries_the_disclaimer(scorer):
    result = scorer.score(_meds("warfarin"))

    assert "does not" in result.disclaimer
    assert "healthcare professional" in result.disclaimer
