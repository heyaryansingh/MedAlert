"""Tests for backend.utils.vital_validation.

Covers vital sign classification/alerting, trend analysis, BMI,
Mean Arterial Pressure, and pulse pressure calculations.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from backend.utils.vital_validation import (
    AlertSeverity,
    BMICategory,
    VitalStatus,
    calculate_bmi,
    calculate_map,
    calculate_pulse_pressure,
    get_vital_trend,
    validate_vital_signs,
)


class TestValidateVitalSigns:
    def test_all_normal_vitals(self):
        result = validate_vital_signs(
            heart_rate=70,
            blood_pressure_systolic=115,
            blood_pressure_diastolic=75,
            temperature=37.0,
            oxygen_saturation=98,
            respiratory_rate=16,
        )
        assert result.overall_severity == AlertSeverity.NORMAL
        assert result.is_critical is False
        assert result.alerts == []
        assert len(result.assessments) == 6

    def test_single_high_vital_is_medium_severity(self):
        result = validate_vital_signs(heart_rate=120)
        assert result.overall_severity == AlertSeverity.MEDIUM
        assert result.is_critical is False
        assert len(result.alerts) == 1

    def test_two_high_vitals_is_high_severity(self):
        result = validate_vital_signs(heart_rate=120, temperature=38.5)
        assert result.overall_severity == AlertSeverity.HIGH
        assert result.is_critical is False

    def test_critical_vital_overrides_severity(self):
        result = validate_vital_signs(heart_rate=160)
        assert result.overall_severity == AlertSeverity.CRITICAL
        assert result.is_critical is True
        assert result.alerts[0].startswith("CRITICAL:")

    def test_none_values_are_skipped(self):
        result = validate_vital_signs(heart_rate=70)
        assert len(result.assessments) == 1
        assert result.assessments[0].name == "Heart Rate"

    def test_no_vitals_provided(self):
        result = validate_vital_signs()
        assert result.assessments == []
        assert result.overall_severity == AlertSeverity.NORMAL
        assert result.is_critical is False

    def test_low_heart_rate_flagged(self):
        result = validate_vital_signs(heart_rate=50)
        assert result.assessments[0].status == VitalStatus.LOW

    def test_critical_low_heart_rate(self):
        result = validate_vital_signs(heart_rate=35)
        assert result.assessments[0].status == VitalStatus.CRITICAL_LOW
        assert result.is_critical is True

    def test_oxygen_saturation_has_no_high_threshold(self):
        # oxygen_saturation.high/critical_high are None, so any high value is normal
        result = validate_vital_signs(oxygen_saturation=100)
        assert result.assessments[0].status == VitalStatus.NORMAL

    def test_custom_ranges_override_defaults(self):
        from backend.utils.vital_validation import VitalRange

        custom = {"heart_rate": VitalRange(low=40, high=200, unit="bpm")}
        result = validate_vital_signs(heart_rate=120, custom_ranges=custom)
        assert result.assessments[0].status == VitalStatus.NORMAL

    def test_assessment_unit_matches_range(self):
        result = validate_vital_signs(temperature=37.0)
        assert result.assessments[0].unit == "°C"


class TestGetVitalTrend:
    def test_insufficient_data_single_value(self):
        assert get_vital_trend([98.0]) == "insufficient_data"

    def test_insufficient_data_empty(self):
        assert get_vital_trend([]) == "insufficient_data"

    def test_increasing_trend(self):
        assert get_vital_trend([98, 100, 102, 120, 130]) == "increasing"

    def test_decreasing_trend(self):
        assert get_vital_trend([130, 120, 102, 100, 98]) == "decreasing"

    def test_stable_trend(self):
        assert get_vital_trend([98, 98, 99, 98, 98]) == "stable"

    def test_custom_threshold(self):
        # Small change flagged as increasing with a very low threshold
        assert get_vital_trend([100, 101], threshold_pct=0.5) == "increasing"


class TestCalculateBmi:
    def test_normal_bmi(self):
        result = calculate_bmi(weight_kg=70, height_cm=175)
        assert result.category == BMICategory.NORMAL
        assert result.is_healthy is True
        assert result.bmi == pytest.approx(22.9, abs=0.05)

    def test_underweight_bmi(self):
        result = calculate_bmi(weight_kg=45, height_cm=175)
        assert result.category == BMICategory.UNDERWEIGHT
        assert result.is_healthy is False

    def test_overweight_bmi(self):
        result = calculate_bmi(weight_kg=85, height_cm=175)
        assert result.category == BMICategory.OVERWEIGHT
        assert result.is_healthy is False

    def test_obese_class_3_bmi(self):
        result = calculate_bmi(weight_kg=140, height_cm=170)
        assert result.category == BMICategory.OBESE_CLASS_3
        assert result.is_healthy is False
        assert len(result.recommendations) > 0

    def test_zero_weight_raises(self):
        with pytest.raises(ValueError):
            calculate_bmi(weight_kg=0, height_cm=175)

    def test_negative_height_raises(self):
        with pytest.raises(ValueError):
            calculate_bmi(weight_kg=70, height_cm=-10)


class TestCalculateMap:
    def test_normal_map(self):
        result = calculate_map(systolic=120, diastolic=80)
        assert result.map_value == pytest.approx(93.3, abs=0.1)
        assert result.is_normal is True
        assert result.status == "Normal"

    def test_critically_low_map(self):
        result = calculate_map(systolic=70, diastolic=45)
        assert result.map_value < 60
        assert result.is_normal is False
        assert "Critically low" in result.status

    def test_high_map(self):
        result = calculate_map(systolic=200, diastolic=120)
        assert result.is_normal is False
        assert "High" in result.status

    def test_diastolic_gte_systolic_raises(self):
        with pytest.raises(ValueError):
            calculate_map(systolic=80, diastolic=90)

    def test_non_positive_values_raise(self):
        with pytest.raises(ValueError):
            calculate_map(systolic=0, diastolic=-5)


class TestCalculatePulsePressure:
    def test_normal_pulse_pressure(self):
        result = calculate_pulse_pressure(120, 80)
        assert result["pulse_pressure"] == 40
        assert result["status"] == "Normal"
        assert result["risk"] == "low"

    def test_narrow_pulse_pressure(self):
        result = calculate_pulse_pressure(100, 85)
        assert result["pulse_pressure"] == 15
        assert result["risk"] == "elevated"

    def test_wide_pulse_pressure(self):
        result = calculate_pulse_pressure(160, 80)
        assert result["pulse_pressure"] == 80
        assert result["risk"] == "moderate"

    def test_very_wide_pulse_pressure(self):
        result = calculate_pulse_pressure(190, 70)
        assert result["pulse_pressure"] == 120
        assert result["risk"] == "high"

    def test_non_positive_values_raise(self):
        with pytest.raises(ValueError):
            calculate_pulse_pressure(0, 80)
