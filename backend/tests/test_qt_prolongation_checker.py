"""Tests for backend.utils.qt_prolongation_checker.

Covers QTc correction formulas, sex-specific classification thresholds, drug
lookup, and the combined Torsade de Pointes risk score — including the
duplicate-medication case that used to double-count a single drug and raise a
multi-drug alert on its own.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from backend.utils.qt_prolongation_checker import (
    QtcClassification,
    TdPRiskCategory,
    assess_qt_risk,
    calculate_qtc,
    classify_qtc_risk,
    get_drug_qt_risk,
)


# --- calculate_qtc ---------------------------------------------------------


def test_bazett_and_fridericia_agree_at_60_bpm():
    # At an RR of exactly 1 second every correction reduces to the raw QT.
    assert calculate_qtc(400, rr_interval_sec=1.0, formula="bazett") == 400.0
    assert calculate_qtc(400, rr_interval_sec=1.0, formula="fridericia") == 400.0
    assert calculate_qtc(400, rr_interval_sec=1.0, formula="framingham") == 400.0
    assert calculate_qtc(400, rr_interval_sec=1.0, formula="hodges") == 400.0


def test_bazett_over_corrects_relative_to_fridericia_at_high_rates():
    bazett = calculate_qtc(360, heart_rate_bpm=100, formula="bazett")
    fridericia = calculate_qtc(360, heart_rate_bpm=100, formula="fridericia")

    assert bazett > fridericia


def test_heart_rate_is_converted_to_an_rr_interval():
    from_rate = calculate_qtc(400, heart_rate_bpm=75)
    from_rr = calculate_qtc(400, rr_interval_sec=0.8)

    assert from_rate == from_rr


def test_hodges_adds_a_fixed_correction_per_beat_over_sixty():
    assert calculate_qtc(400, heart_rate_bpm=80, formula="hodges") == 435.0


def test_framingham_correction_matches_its_definition():
    # QTc = QT + 154 * (1 - RR)
    assert calculate_qtc(400, rr_interval_sec=0.8, formula="framingham") == pytest.approx(
        430.8
    )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"qt_ms": 0, "rr_interval_sec": 1.0},
        {"qt_ms": -10, "rr_interval_sec": 1.0},
        {"qt_ms": 400, "rr_interval_sec": 0},
        {"qt_ms": 400, "heart_rate_bpm": 0},
        {"qt_ms": 400},
    ],
)
def test_invalid_inputs_are_rejected(kwargs):
    with pytest.raises(ValueError):
        calculate_qtc(**kwargs)


def test_unknown_formula_is_rejected():
    with pytest.raises(ValueError, match="Unknown formula"):
        calculate_qtc(400, rr_interval_sec=1.0, formula="nonsense")


# --- classify_qtc_risk -----------------------------------------------------


@pytest.mark.parametrize(
    "qtc,expected",
    [
        (400, QtcClassification.NORMAL),
        (430, QtcClassification.NORMAL),
        (431, QtcClassification.BORDERLINE),
        (451, QtcClassification.PROLONGED),
        (500, QtcClassification.SEVERELY_PROLONGED),
        (520, QtcClassification.SEVERELY_PROLONGED),
    ],
)
def test_male_thresholds(qtc, expected):
    assert classify_qtc_risk(qtc, sex="male") == expected


def test_female_thresholds_sit_twenty_ms_higher():
    # 440 ms is borderline for a man and still normal for a woman.
    assert classify_qtc_risk(440, sex="male") == QtcClassification.BORDERLINE
    assert classify_qtc_risk(440, sex="female") == QtcClassification.NORMAL


def test_unknown_sex_falls_back_to_male_thresholds():
    assert classify_qtc_risk(440, sex="unspecified") == classify_qtc_risk(440, sex="male")


# --- get_drug_qt_risk ------------------------------------------------------


def test_drug_lookup_ignores_case_and_padding():
    assert get_drug_qt_risk("  AmioDarone ") == TdPRiskCategory.KNOWN_RISK


def test_unlisted_drug_carries_no_recorded_risk():
    assert get_drug_qt_risk("acetaminophen") == TdPRiskCategory.NONE


# --- assess_qt_risk --------------------------------------------------------


def test_no_risk_factors_scores_low():
    result = assess_qt_risk(["acetaminophen", "lisinopril"])

    assert result.risk_score == 0
    assert result.risk_level == "low"
    assert result.recommendations == ["No significant QT prolongation risk identified."]


def test_two_known_risk_drugs_compound_into_high_risk():
    result = assess_qt_risk(["amiodarone", "haloperidol"])

    # 3 + 3 for the drugs, plus 3 for the concurrent-known-risk penalty.
    assert result.risk_score == 9
    assert result.risk_level == "critical"
    assert any("Multiple known" in r for r in result.recommendations)


def test_a_repeated_drug_is_counted_once():
    once = assess_qt_risk(["amiodarone"])
    twice = assess_qt_risk(["Amiodarone", "amiodarone"])

    assert twice.risk_score == once.risk_score
    assert len(twice.drug_risks) == 1
    # The repeat alone must not read as two concurrent QT-prolonging drugs.
    assert not any("Multiple known" in r for r in twice.recommendations)


def test_duplicates_with_stray_whitespace_are_the_same_drug():
    result = assess_qt_risk([" sotalol", "sotalol "])

    assert [dr.drug for dr in result.drug_risks] == ["sotalol"]


def test_blank_medication_entries_are_dropped():
    result = assess_qt_risk(["", "   ", "amiodarone"])

    assert [dr.drug for dr in result.drug_risks] == ["amiodarone"]


def test_distinct_known_risk_drugs_still_trigger_the_multi_drug_alert():
    result = assess_qt_risk(["Amiodarone", "amiodarone", "sotalol"])

    assert len(result.drug_risks) == 2
    assert any("Multiple known" in r for r in result.recommendations)


def test_prolonged_qtc_raises_the_score_and_advises_cardiology():
    result = assess_qt_risk(["escitalopram"], qtc_ms=480, sex="male")

    assert result.qtc_classification == QtcClassification.PROLONGED
    assert result.risk_score == 5  # 2 for possible-risk drug + 3 for prolonged QTc
    assert result.risk_level == "high"
    assert any("cardiology" in r for r in result.recommendations)


def test_severely_prolonged_qtc_dominates_the_score():
    result = assess_qt_risk([], qtc_ms=520)

    assert result.qtc_classification == QtcClassification.SEVERELY_PROLONGED
    assert result.risk_score == 5


def test_additional_risk_factors_each_add_a_point():
    baseline = assess_qt_risk(["quetiapine"])
    with_factors = assess_qt_risk(
        ["quetiapine"], risk_factors=["hypokalemia", "bradycardia"]
    )

    assert with_factors.risk_score == baseline.risk_score + 2
    assert with_factors.additional_risk_factors == ["hypokalemia", "bradycardia"]
    assert any("modifiable risk factors" in r for r in with_factors.recommendations)


def test_qtc_is_not_classified_when_it_is_unknown():
    result = assess_qt_risk(["amiodarone"])

    assert result.qtc_ms is None
    assert result.qtc_classification is None
