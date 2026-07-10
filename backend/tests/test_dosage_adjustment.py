"""Tests for backend.utils.dosage_adjustment.

Covers renal/hepatic classification and adjustment factors, weight-based
and pediatric dosing, therapeutic drug monitoring range checks, and the
combined suggest_adjustment recommendation engine.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from backend.utils.dosage_adjustment import (
    AdjustmentReason,
    HepaticCategory,
    RenalCategory,
    calculate_hepatic_adjustment,
    calculate_pediatric_dose,
    calculate_renal_adjustment,
    calculate_weight_based_dose,
    classify_hepatic_function,
    classify_renal_function,
    suggest_adjustment,
    therapeutic_range_check,
)


class TestClassifyRenalFunction:
    def test_normal_at_boundary(self):
        assert classify_renal_function(90) == RenalCategory.NORMAL

    def test_mild(self):
        assert classify_renal_function(75) == RenalCategory.MILD

    def test_moderate(self):
        assert classify_renal_function(45) == RenalCategory.MODERATE

    def test_severe(self):
        assert classify_renal_function(20) == RenalCategory.SEVERE

    def test_esrd(self):
        assert classify_renal_function(10) == RenalCategory.ESRD


class TestCalculateRenalAdjustment:
    def test_normal_renal_function_no_adjustment(self):
        assert calculate_renal_adjustment("gentamicin", 95) == pytest.approx(1.0)

    def test_aminoglycoside_moderate_impairment(self):
        assert calculate_renal_adjustment("gentamicin", 45) == pytest.approx(0.6)

    def test_unknown_drug_uses_default_category(self):
        factor = calculate_renal_adjustment("unknown_drug_xyz", 45)
        assert factor == pytest.approx(0.75)

    def test_known_default_category_drug(self):
        assert calculate_renal_adjustment("vancomycin", 20) == pytest.approx(0.5)


class TestCalculateHepaticAdjustment:
    def test_class_a_no_adjustment(self):
        assert calculate_hepatic_adjustment(6) == pytest.approx(1.0)

    def test_class_b_reduces_25_pct(self):
        assert calculate_hepatic_adjustment(8) == pytest.approx(0.75)

    def test_class_c_reduces_50_pct(self):
        assert calculate_hepatic_adjustment(12) == pytest.approx(0.5)


class TestClassifyHepaticFunction:
    def test_none(self):
        assert classify_hepatic_function(4) == HepaticCategory.NONE

    def test_mild_a(self):
        assert classify_hepatic_function(6) == HepaticCategory.MILD_A

    def test_moderate_b(self):
        assert classify_hepatic_function(8) == HepaticCategory.MODERATE_B

    def test_severe_c(self):
        assert classify_hepatic_function(12) == HepaticCategory.SEVERE_C


class TestCalculateWeightBasedDose:
    def test_basic_calculation(self):
        assert calculate_weight_based_dose(5.0, 70) == pytest.approx(350.0)

    def test_caps_at_max_dose(self):
        assert calculate_weight_based_dose(10.0, 100, max_dose_mg=500) == pytest.approx(500.0)

    def test_rounds_to_one_decimal(self):
        assert calculate_weight_based_dose(1.0 / 3, 10) == pytest.approx(3.3)


class TestCalculatePediatricDose:
    def test_clark_rule(self):
        # weight_lb = 20 * 2.205 = 44.1; (44.1 / 150) * 100 = 29.4
        dose = calculate_pediatric_dose(100, child_weight_kg=20, method="clark")
        assert dose == pytest.approx(29.4)

    def test_young_rule(self):
        # (6 / (6 + 12)) * 100 = 33.3
        dose = calculate_pediatric_dose(100, child_age_years=6, method="young")
        assert dose == pytest.approx(33.3)

    def test_missing_required_param_returns_adult_dose(self):
        dose = calculate_pediatric_dose(100, method="clark")
        assert dose == 100


class TestTherapeuticRangeCheck:
    def test_within_range(self):
        result = therapeutic_range_check("vancomycin", 15.0)
        assert result.status == "therapeutic"

    def test_below_range(self):
        result = therapeutic_range_check("vancomycin", 5.0)
        assert result.status == "sub_therapeutic"

    def test_above_range_but_not_toxic(self):
        result = therapeutic_range_check("vancomycin", 25.0)
        assert result.status == "supra_therapeutic"

    def test_toxic_level(self):
        result = therapeutic_range_check("vancomycin", 45.0)
        assert result.status == "toxic"

    def test_unknown_drug(self):
        result = therapeutic_range_check("not_a_real_drug", 10.0)
        assert result.status == "unknown_drug"
        assert result.unit == "unknown"

    def test_drug_name_normalized_with_spaces(self):
        result = therapeutic_range_check("valproic acid", 75.0)
        assert result.status == "therapeutic"


class TestSuggestAdjustment:
    def test_no_parameters_gives_no_adjustment(self):
        rec = suggest_adjustment(drug_name="metformin", current_dose_mg=500)
        assert rec.reasons == [AdjustmentReason.NONE]
        assert rec.recommended_dose_mg == pytest.approx(500)
        assert rec.adjustment_factor == pytest.approx(1.0)

    def test_renal_impairment_reduces_dose(self):
        rec = suggest_adjustment(
            drug_name="gentamicin",
            current_dose_mg=120,
            creatinine_clearance=45.0,
        )
        assert AdjustmentReason.RENAL_IMPAIRMENT in rec.reasons
        assert rec.recommended_dose_mg == pytest.approx(120 * 0.6, rel=1e-3)

    def test_esrd_adds_warning(self):
        rec = suggest_adjustment(
            drug_name="gentamicin",
            current_dose_mg=120,
            creatinine_clearance=10.0,
        )
        assert any("dialysis" in w.lower() for w in rec.warnings)

    def test_hepatic_impairment_reduces_dose(self):
        rec = suggest_adjustment(
            drug_name="vancomycin",
            current_dose_mg=1000,
            child_pugh_score=12,
        )
        assert AdjustmentReason.HEPATIC_IMPAIRMENT in rec.reasons
        assert rec.recommended_dose_mg == pytest.approx(500.0)

    def test_geriatric_adjustment_applied_for_elderly(self):
        rec = suggest_adjustment(
            drug_name="vancomycin",
            current_dose_mg=1000,
            age_years=70,
        )
        assert AdjustmentReason.GERIATRIC in rec.reasons
        assert rec.recommended_dose_mg == pytest.approx(850.0)

    def test_very_elderly_gets_larger_reduction(self):
        rec = suggest_adjustment(
            drug_name="vancomycin",
            current_dose_mg=1000,
            age_years=85,
        )
        assert rec.recommended_dose_mg == pytest.approx(750.0)

    def test_toxic_tdm_level_halves_dose_and_warns(self):
        rec = suggest_adjustment(
            drug_name="vancomycin",
            current_dose_mg=1000,
            measured_level=45.0,
        )
        assert AdjustmentReason.THERAPEUTIC_LEVEL in rec.reasons
        assert rec.recommended_dose_mg == pytest.approx(500.0)
        assert any("TOXIC" in w for w in rec.warnings)

    def test_sub_therapeutic_tdm_increases_dose(self):
        rec = suggest_adjustment(
            drug_name="vancomycin",
            current_dose_mg=1000,
            measured_level=5.0,
        )
        assert rec.recommended_dose_mg == pytest.approx(1250.0)

    def test_multiple_factors_lowers_confidence(self):
        rec = suggest_adjustment(
            drug_name="gentamicin",
            current_dose_mg=120,
            creatinine_clearance=45.0,
            child_pugh_score=12,
            age_years=70,
        )
        assert len(rec.reasons) > 2
        assert rec.confidence == "low"
        assert any("pharmacist review" in w for w in rec.warnings)

    def test_single_factor_gives_high_confidence(self):
        rec = suggest_adjustment(
            drug_name="gentamicin",
            current_dose_mg=120,
            creatinine_clearance=45.0,
        )
        assert rec.confidence == "high"
