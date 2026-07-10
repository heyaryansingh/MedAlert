"""Tests for backend.utils.taper_schedule.

Covers linear/percentage/custom taper generation, duration estimation,
safety-guideline checking, and risk assessment for medication tapers.
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from backend.utils.taper_schedule import (
    TaperMethod,
    TaperRisk,
    check_taper_safety,
    estimate_taper_duration,
    generate_custom_taper,
    generate_linear_taper,
    generate_percentage_taper,
)


class TestGenerateLinearTaper:
    def test_basic_linear_schedule(self):
        schedule = generate_linear_taper(
            starting_dose_mg=20.0, target_dose_mg=0.0, step_reduction_mg=5.0, days_per_step=7
        )
        assert schedule.method == TaperMethod.LINEAR
        assert schedule.steps[0].dose_mg == 20.0
        assert schedule.steps[-1].dose_mg == 0.0

    def test_reaches_exact_target_without_extra_step(self):
        # 20 -> 15 -> 10 -> 5 -> 0 lands exactly on target; no duplicate final step.
        schedule = generate_linear_taper(
            starting_dose_mg=20.0, target_dose_mg=0.0, step_reduction_mg=5.0
        )
        doses = [s.dose_mg for s in schedule.steps]
        assert doses == [20.0, 15.0, 10.0, 5.0, 0.0]

    def test_uneven_reduction_clips_to_target(self):
        # 20 -> 13 -> 6 -> would go negative, so clips to target 0.
        schedule = generate_linear_taper(
            starting_dose_mg=20.0, target_dose_mg=0.0, step_reduction_mg=7.0
        )
        assert schedule.steps[-1].dose_mg == 0.0
        assert all(s.dose_mg >= 0.0 for s in schedule.steps)

    def test_total_duration_matches_step_count(self):
        schedule = generate_linear_taper(
            starting_dose_mg=20.0, target_dose_mg=0.0, step_reduction_mg=5.0, days_per_step=7
        )
        assert schedule.total_duration_days == len(schedule.steps) * 7

    def test_start_date_propagates_across_steps(self):
        start = date(2024, 1, 1)
        schedule = generate_linear_taper(
            starting_dose_mg=10.0,
            target_dose_mg=0.0,
            step_reduction_mg=5.0,
            days_per_step=7,
            start_date=start,
        )
        assert schedule.steps[0].start_date == start
        assert schedule.steps[1].start_date == date(2024, 1, 8)

    @pytest.mark.parametrize(
        "starting,target,step",
        [(0.0, 0.0, 5.0), (-5.0, 0.0, 5.0), (10.0, -1.0, 5.0), (10.0, 5.0, 0.0), (5.0, 10.0, 5.0)],
    )
    def test_invalid_inputs_raise(self, starting, target, step):
        with pytest.raises(ValueError):
            generate_linear_taper(starting_dose_mg=starting, target_dose_mg=target, step_reduction_mg=step)


class TestGeneratePercentageTaper:
    def test_basic_percentage_schedule(self):
        schedule = generate_percentage_taper(
            starting_dose_mg=20.0, target_dose_mg=0.0, reduction_pct=10.0
        )
        assert schedule.method == TaperMethod.PERCENTAGE
        assert schedule.steps[0].dose_mg == 20.0
        assert schedule.steps[-1].dose_mg == 0.0

    def test_final_step_always_discontinuation(self):
        schedule = generate_percentage_taper(
            starting_dose_mg=5.0, target_dose_mg=0.0, reduction_pct=50.0, min_dose_mg=0.5
        )
        assert schedule.steps[-1].dose_mg == 0.0
        assert "Discontinuation" in schedule.steps[-1].notes

    def test_target_reached_note_when_target_nonzero(self):
        schedule = generate_percentage_taper(
            starting_dose_mg=20.0, target_dose_mg=5.0, reduction_pct=20.0
        )
        assert schedule.steps[-1].dose_mg == 5.0
        assert "Target dose reached" in schedule.steps[-1].notes

    def test_min_dose_mg_stops_the_loop_early(self):
        schedule = generate_percentage_taper(
            starting_dose_mg=1.0, target_dose_mg=0.0, reduction_pct=10.0, min_dose_mg=0.9
        )
        # Loop should exit almost immediately since current_dose drops below min_dose_mg fast.
        assert schedule.steps[-1].dose_mg == 0.0

    @pytest.mark.parametrize("pct", [0.0, -5.0, 51.0, 100.0])
    def test_invalid_reduction_pct_raises(self, pct):
        with pytest.raises(ValueError):
            generate_percentage_taper(starting_dose_mg=20.0, reduction_pct=pct)

    def test_invalid_starting_dose_raises(self):
        with pytest.raises(ValueError):
            generate_percentage_taper(starting_dose_mg=0.0, reduction_pct=10.0)


class TestGenerateCustomTaper:
    def test_basic_custom_schedule(self):
        schedule = generate_custom_taper(
            medication="prednisone", dose_steps=[(20.0, 7), (10.0, 7), (0.0, 7)]
        )
        assert schedule.method == TaperMethod.CUSTOM
        assert schedule.starting_dose_mg == 20.0
        assert schedule.target_dose_mg == 0.0
        assert schedule.total_duration_days == 21

    def test_empty_dose_steps_raises(self):
        with pytest.raises(ValueError):
            generate_custom_taper(medication="prednisone", dose_steps=[])

    def test_start_date_propagates(self):
        start = date(2024, 3, 1)
        schedule = generate_custom_taper(
            medication="prednisone", dose_steps=[(20.0, 5), (10.0, 5)], start_date=start
        )
        assert schedule.steps[0].start_date == start
        assert schedule.steps[1].start_date == date(2024, 3, 6)


class TestEstimateTaperDuration:
    def test_returns_positive_int(self):
        days = estimate_taper_duration(
            starting_dose_mg=20.0, target_dose_mg=0.0, reduction_pct=10.0, days_per_step=7
        )
        assert isinstance(days, int)
        assert days > 0

    def test_matches_generated_schedule_order_of_magnitude(self):
        estimated = estimate_taper_duration(
            starting_dose_mg=20.0, target_dose_mg=0.0, reduction_pct=10.0, days_per_step=7
        )
        schedule = generate_percentage_taper(
            starting_dose_mg=20.0, target_dose_mg=0.0, reduction_pct=10.0, days_per_step=7
        )
        assert estimated == schedule.total_duration_days


class TestCheckTaperSafety:
    def test_unknown_medication_returns_safe_with_caution_note(self):
        schedule = generate_linear_taper(starting_dose_mg=20.0, medication="unknownmed")
        result = check_taper_safety("unknownmed", schedule)
        assert result["safe"] is True
        assert "No specific guidelines" in result["issues"][0]

    def test_compliant_schedule_is_safe(self):
        # prednisone allows max_reduction_pct=20, min_step_days=3.
        schedule = generate_percentage_taper(
            starting_dose_mg=20.0,
            target_dose_mg=0.0,
            reduction_pct=15.0,
            days_per_step=3,
            medication="prednisone",
        )
        result = check_taper_safety("prednisone", schedule)
        assert result["safe"] is True
        assert result["issues"] == []

    def test_excessive_reduction_flagged_unsafe(self):
        # alprazolam allows max_reduction_pct=10; 50% per step wildly exceeds it.
        schedule = generate_percentage_taper(
            starting_dose_mg=4.0,
            target_dose_mg=0.0,
            reduction_pct=50.0,
            days_per_step=7,
            medication="alprazolam",
        )
        result = check_taper_safety("alprazolam", schedule)
        assert result["safe"] is False
        assert result["risk"] == TaperRisk.HIGH.value
        assert any("exceeds recommended max" in issue for issue in result["issues"])

    def test_too_short_step_duration_flagged(self):
        # paroxetine requires min_step_days=14; using 1 day should be flagged.
        schedule = generate_custom_taper(
            medication="paroxetine", dose_steps=[(20.0, 1), (10.0, 1), (0.0, 1)]
        )
        result = check_taper_safety("paroxetine", schedule)
        assert result["safe"] is False
        assert any("below recommended minimum" in issue for issue in result["issues"])

    def test_medication_lookup_is_case_insensitive(self):
        schedule = generate_linear_taper(starting_dose_mg=20.0, medication="Prednisone")
        lower_result = check_taper_safety("prednisone", schedule)
        mixed_result = check_taper_safety("  PREDNISONE  ", schedule)
        # Guideline lookup itself is case/whitespace-insensitive; only the
        # issue message text echoes the raw input, so compare safe/risk only.
        assert mixed_result["safe"] == lower_result["safe"]
        assert mixed_result["risk"] == lower_result["risk"]


class TestRiskAssessmentIntegration:
    def test_high_risk_medication_short_taper_is_unsafe(self):
        # alprazolam with < 28 total days is UNSAFE regardless of step size.
        schedule = generate_linear_taper(
            starting_dose_mg=2.0,
            target_dose_mg=0.0,
            step_reduction_mg=1.0,
            days_per_step=7,
            medication="alprazolam",
        )
        assert schedule.total_duration_days < 28
        assert schedule.risk_level == TaperRisk.UNSAFE

    def test_unlisted_medication_defaults_to_low_risk(self):
        schedule = generate_linear_taper(starting_dose_mg=20.0, medication="ibuprofen")
        assert schedule.risk_level == TaperRisk.LOW

    def test_guideline_medication_gentle_taper_is_moderate(self):
        # gabapentin allows 20% max reduction; 10% steps stay within it -> MODERATE.
        schedule = generate_percentage_taper(
            starting_dose_mg=900.0,
            target_dose_mg=0.0,
            reduction_pct=10.0,
            days_per_step=7,
            medication="gabapentin",
        )
        assert schedule.risk_level == TaperRisk.MODERATE

    def test_benzodiazepine_warning_present(self):
        schedule = generate_linear_taper(starting_dose_mg=10.0, medication="diazepam")
        assert any("seizures" in w for w in schedule.warnings)

    def test_opioid_warning_present(self):
        schedule = generate_linear_taper(
            starting_dose_mg=30.0, step_reduction_mg=3.0, days_per_step=7, medication="oxycodone"
        )
        assert any("Opioid tapering" in w for w in schedule.warnings)

    def test_corticosteroid_warning_present(self):
        schedule = generate_linear_taper(starting_dose_mg=20.0, medication="prednisone")
        assert any("adrenal crisis" in w for w in schedule.warnings)

    def test_ssri_warning_present(self):
        schedule = generate_linear_taper(starting_dose_mg=100.0, medication="sertraline")
        assert any("discontinuation syndrome" in w for w in schedule.warnings)

    def test_disclaimer_always_present(self):
        schedule = generate_linear_taper(starting_dose_mg=20.0, medication="ibuprofen")
        assert any("informational purposes only" in w for w in schedule.warnings)
