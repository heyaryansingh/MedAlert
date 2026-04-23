"""Vital signs validation and clinical alerting utilities.

This module provides validation and clinical assessment functions for
vital sign measurements, with configurable normal ranges and alert
severity classification.

Functions:
    validate_vital_signs: Check vitals against normal ranges
    assess_vital_severity: Determine clinical alert severity
    get_vital_trend: Analyze trend direction from history
    format_vital_summary: Generate human-readable vital summary

Example:
    >>> from backend.utils.vital_validation import validate_vital_signs
    >>> result = validate_vital_signs(heart_rate=120, temperature=38.5)
    >>> print(result.alerts)  # ["Elevated heart rate", "Elevated temperature"]
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class VitalStatus(str, Enum):
    """Status classification for individual vital signs."""
    CRITICAL_LOW = "critical_low"
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL_HIGH = "critical_high"


class AlertSeverity(str, Enum):
    """Overall alert severity based on vital sign assessment."""
    NORMAL = "normal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class VitalRange:
    """Normal range definition for a vital sign.

    Attributes:
        critical_low: Value below which is critically abnormal
        low: Value below which is abnormally low
        high: Value above which is abnormally high
        critical_high: Value above which is critically abnormal
        unit: Unit of measurement for display
    """
    critical_low: Optional[float] = None
    low: Optional[float] = None
    high: Optional[float] = None
    critical_high: Optional[float] = None
    unit: str = ""


@dataclass
class VitalAssessment:
    """Assessment result for a single vital sign."""
    name: str
    value: float
    status: VitalStatus
    message: str
    unit: str


@dataclass
class ValidationResult:
    """Complete validation result for all vital signs."""
    assessments: List[VitalAssessment] = field(default_factory=list)
    overall_severity: AlertSeverity = AlertSeverity.NORMAL
    alerts: List[str] = field(default_factory=list)
    is_critical: bool = False


# Default normal ranges for adult vital signs
# Based on general clinical guidelines - adjust for age/condition as needed
ADULT_VITAL_RANGES: Dict[str, VitalRange] = {
    "heart_rate": VitalRange(
        critical_low=40,
        low=60,
        high=100,
        critical_high=150,
        unit="bpm"
    ),
    "blood_pressure_systolic": VitalRange(
        critical_low=70,
        low=90,
        high=140,
        critical_high=180,
        unit="mmHg"
    ),
    "blood_pressure_diastolic": VitalRange(
        critical_low=40,
        low=60,
        high=90,
        critical_high=120,
        unit="mmHg"
    ),
    "temperature": VitalRange(
        critical_low=35.0,
        low=36.0,
        high=37.8,
        critical_high=39.5,
        unit="°C"
    ),
    "oxygen_saturation": VitalRange(
        critical_low=88,
        low=94,
        high=None,  # High O2 sat is generally not alarming
        critical_high=None,
        unit="%"
    ),
    "respiratory_rate": VitalRange(
        critical_low=8,
        low=12,
        high=20,
        critical_high=30,
        unit="breaths/min"
    ),
}


def _classify_vital(
    value: float,
    vital_range: VitalRange
) -> Tuple[VitalStatus, str]:
    """Classify a vital sign value against its normal range.

    Args:
        value: The measured vital sign value
        vital_range: The normal range definition

    Returns:
        Tuple of (VitalStatus, descriptive message)
    """
    if vital_range.critical_low is not None and value < vital_range.critical_low:
        return VitalStatus.CRITICAL_LOW, f"Critically low ({value} {vital_range.unit})"

    if vital_range.critical_high is not None and value > vital_range.critical_high:
        return VitalStatus.CRITICAL_HIGH, f"Critically high ({value} {vital_range.unit})"

    if vital_range.low is not None and value < vital_range.low:
        return VitalStatus.LOW, f"Below normal ({value} {vital_range.unit})"

    if vital_range.high is not None and value > vital_range.high:
        return VitalStatus.HIGH, f"Above normal ({value} {vital_range.unit})"

    return VitalStatus.NORMAL, f"Normal ({value} {vital_range.unit})"


def validate_vital_signs(
    heart_rate: Optional[int] = None,
    blood_pressure_systolic: Optional[int] = None,
    blood_pressure_diastolic: Optional[int] = None,
    temperature: Optional[float] = None,
    oxygen_saturation: Optional[float] = None,
    respiratory_rate: Optional[int] = None,
    custom_ranges: Optional[Dict[str, VitalRange]] = None,
) -> ValidationResult:
    """Validate vital signs against normal ranges.

    Checks each provided vital sign against configurable normal ranges
    and generates alerts for abnormal values.

    Args:
        heart_rate: Heart rate in beats per minute
        blood_pressure_systolic: Systolic blood pressure in mmHg
        blood_pressure_diastolic: Diastolic blood pressure in mmHg
        temperature: Body temperature in Celsius
        oxygen_saturation: SpO2 percentage
        respiratory_rate: Breaths per minute
        custom_ranges: Optional custom ranges to override defaults

    Returns:
        ValidationResult with individual assessments and overall severity

    Example:
        >>> result = validate_vital_signs(heart_rate=120, temperature=38.5)
        >>> print(result.overall_severity)
        AlertSeverity.MEDIUM
    """
    ranges = {**ADULT_VITAL_RANGES}
    if custom_ranges:
        ranges.update(custom_ranges)

    result = ValidationResult()
    vitals_to_check = {
        "heart_rate": heart_rate,
        "blood_pressure_systolic": blood_pressure_systolic,
        "blood_pressure_diastolic": blood_pressure_diastolic,
        "temperature": temperature,
        "oxygen_saturation": oxygen_saturation,
        "respiratory_rate": respiratory_rate,
    }

    critical_count = 0
    high_count = 0

    for vital_name, value in vitals_to_check.items():
        if value is None:
            continue

        vital_range = ranges.get(vital_name)
        if vital_range is None:
            continue

        status, message = _classify_vital(float(value), vital_range)

        # Format display name
        display_name = vital_name.replace("_", " ").title()

        assessment = VitalAssessment(
            name=display_name,
            value=float(value),
            status=status,
            message=message,
            unit=vital_range.unit
        )
        result.assessments.append(assessment)

        # Generate alerts for abnormal values
        if status in (VitalStatus.CRITICAL_LOW, VitalStatus.CRITICAL_HIGH):
            result.alerts.append(f"CRITICAL: {display_name} - {message}")
            critical_count += 1
        elif status in (VitalStatus.LOW, VitalStatus.HIGH):
            result.alerts.append(f"Warning: {display_name} - {message}")
            high_count += 1

    # Determine overall severity
    if critical_count > 0:
        result.overall_severity = AlertSeverity.CRITICAL
        result.is_critical = True
    elif high_count >= 2:
        result.overall_severity = AlertSeverity.HIGH
    elif high_count == 1:
        result.overall_severity = AlertSeverity.MEDIUM
    elif len(result.alerts) > 0:
        result.overall_severity = AlertSeverity.LOW
    else:
        result.overall_severity = AlertSeverity.NORMAL

    return result


def get_vital_trend(
    values: List[float],
    threshold_pct: float = 10.0
) -> str:
    """Analyze trend direction from a series of vital sign measurements.

    Args:
        values: List of measurements in chronological order
        threshold_pct: Percentage change to consider significant

    Returns:
        Trend description: "increasing", "decreasing", "stable", or "fluctuating"

    Example:
        >>> values = [98, 100, 102, 105, 108]
        >>> print(get_vital_trend(values))
        "increasing"
    """
    if len(values) < 2:
        return "insufficient_data"

    first_half = sum(values[:len(values)//2]) / (len(values)//2)
    second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)

    if first_half == 0:
        return "stable"

    pct_change = ((second_half - first_half) / first_half) * 100

    if pct_change > threshold_pct:
        return "increasing"
    elif pct_change < -threshold_pct:
        return "decreasing"
    else:
        # Check for fluctuation
        variance = sum((v - sum(values)/len(values))**2 for v in values) / len(values)
        mean = sum(values) / len(values)
        cv = (variance ** 0.5) / mean * 100 if mean != 0 else 0

        if cv > threshold_pct:
            return "fluctuating"
        return "stable"


def format_vital_summary(result: ValidationResult) -> str:
    """Generate human-readable summary of vital sign assessment.

    Args:
        result: ValidationResult from validate_vital_signs()

    Returns:
        Formatted multi-line summary string

    Example:
        >>> result = validate_vital_signs(heart_rate=120)
        >>> print(format_vital_summary(result))
    """
    lines = ["=== Vital Signs Assessment ===", ""]

    for assessment in result.assessments:
        status_icon = {
            VitalStatus.CRITICAL_LOW: "🔴",
            VitalStatus.CRITICAL_HIGH: "🔴",
            VitalStatus.LOW: "🟡",
            VitalStatus.HIGH: "🟡",
            VitalStatus.NORMAL: "🟢",
        }.get(assessment.status, "⚪")

        lines.append(f"{status_icon} {assessment.name}: {assessment.message}")

    lines.append("")
    lines.append(f"Overall Status: {result.overall_severity.value.upper()}")

    if result.alerts:
        lines.append("")
        lines.append("Alerts:")
        for alert in result.alerts:
            lines.append(f"  • {alert}")

    return "\n".join(lines)


class BMICategory(str, Enum):
    """BMI classification categories based on WHO standards."""
    UNDERWEIGHT = "underweight"
    NORMAL = "normal"
    OVERWEIGHT = "overweight"
    OBESE_CLASS_1 = "obese_class_1"
    OBESE_CLASS_2 = "obese_class_2"
    OBESE_CLASS_3 = "obese_class_3"


@dataclass
class BMIResult:
    """BMI calculation and classification result.

    Attributes:
        bmi: Calculated BMI value
        category: WHO BMI classification
        is_healthy: Whether BMI is in healthy range
        risk_level: Associated health risk level
        recommendations: Health recommendations based on BMI
    """
    bmi: float
    category: BMICategory
    is_healthy: bool
    risk_level: str
    recommendations: List[str] = field(default_factory=list)


def calculate_bmi(
    weight_kg: float,
    height_cm: float,
) -> BMIResult:
    """Calculate Body Mass Index and classify health risk.

    Calculates BMI using the standard formula and classifies according
    to WHO guidelines. Provides health recommendations based on category.

    Args:
        weight_kg: Body weight in kilograms
        height_cm: Height in centimeters

    Returns:
        BMIResult with BMI value, category, and recommendations

    Example:
        >>> result = calculate_bmi(weight_kg=70, height_cm=175)
        >>> print(f"BMI: {result.bmi:.1f} - {result.category.value}")
        BMI: 22.9 - normal

    Raises:
        ValueError: If weight or height is not positive
    """
    if weight_kg <= 0 or height_cm <= 0:
        raise ValueError("Weight and height must be positive values")

    height_m = height_cm / 100
    bmi = weight_kg / (height_m ** 2)

    # Classify BMI according to WHO guidelines
    if bmi < 18.5:
        category = BMICategory.UNDERWEIGHT
        is_healthy = False
        risk_level = "Increased risk of malnutrition"
        recommendations = [
            "Consider consulting a nutritionist",
            "Focus on nutrient-dense foods",
            "Monitor for signs of nutritional deficiency",
        ]
    elif bmi < 25.0:
        category = BMICategory.NORMAL
        is_healthy = True
        risk_level = "Low risk"
        recommendations = [
            "Maintain current healthy lifestyle",
            "Regular physical activity recommended",
            "Balanced diet with adequate nutrients",
        ]
    elif bmi < 30.0:
        category = BMICategory.OVERWEIGHT
        is_healthy = False
        risk_level = "Increased risk of chronic conditions"
        recommendations = [
            "Consider lifestyle modifications",
            "Increase physical activity",
            "Review dietary habits",
            "Monitor blood pressure and glucose",
        ]
    elif bmi < 35.0:
        category = BMICategory.OBESE_CLASS_1
        is_healthy = False
        risk_level = "High risk of chronic conditions"
        recommendations = [
            "Medical consultation recommended",
            "Structured weight loss program advised",
            "Regular monitoring of cardiovascular markers",
            "Screen for sleep apnea and diabetes",
        ]
    elif bmi < 40.0:
        category = BMICategory.OBESE_CLASS_2
        is_healthy = False
        risk_level = "Very high risk of chronic conditions"
        recommendations = [
            "Urgent medical consultation recommended",
            "Consider medically supervised weight loss",
            "Regular cardiovascular and metabolic screening",
            "Evaluate for comorbidities",
        ]
    else:
        category = BMICategory.OBESE_CLASS_3
        is_healthy = False
        risk_level = "Extremely high risk - severe health concerns"
        recommendations = [
            "Immediate medical evaluation recommended",
            "Consider multidisciplinary weight management",
            "Screen for obesity-related complications",
            "Evaluate surgical intervention options if appropriate",
        ]

    return BMIResult(
        bmi=round(bmi, 1),
        category=category,
        is_healthy=is_healthy,
        risk_level=risk_level,
        recommendations=recommendations,
    )


@dataclass
class MAPResult:
    """Mean Arterial Pressure calculation result.

    Attributes:
        map_value: Calculated MAP in mmHg
        status: Clinical interpretation
        is_normal: Whether MAP is in normal range (70-100 mmHg)
    """
    map_value: float
    status: str
    is_normal: bool


def calculate_map(
    systolic: int,
    diastolic: int,
) -> MAPResult:
    """Calculate Mean Arterial Pressure (MAP).

    MAP is an important indicator of tissue perfusion. Normal range
    is 70-100 mmHg. Values outside this range may indicate inadequate
    or excessive perfusion pressure.

    Args:
        systolic: Systolic blood pressure in mmHg
        diastolic: Diastolic blood pressure in mmHg

    Returns:
        MAPResult with MAP value and clinical interpretation

    Example:
        >>> result = calculate_map(systolic=120, diastolic=80)
        >>> print(f"MAP: {result.map_value:.0f} mmHg - {result.status}")
        MAP: 93 mmHg - Normal

    Formula:
        MAP = (SBP + 2 * DBP) / 3
    """
    if systolic <= 0 or diastolic <= 0:
        raise ValueError("Blood pressure values must be positive")

    if diastolic >= systolic:
        raise ValueError("Systolic must be greater than diastolic")

    map_value = (systolic + 2 * diastolic) / 3

    if map_value < 60:
        status = "Critically low - risk of organ hypoperfusion"
        is_normal = False
    elif map_value < 70:
        status = "Low - monitor closely"
        is_normal = False
    elif map_value <= 100:
        status = "Normal"
        is_normal = True
    elif map_value <= 110:
        status = "Elevated - monitor for hypertension"
        is_normal = False
    else:
        status = "High - increased cardiovascular risk"
        is_normal = False

    return MAPResult(
        map_value=round(map_value, 1),
        status=status,
        is_normal=is_normal,
    )


def calculate_pulse_pressure(systolic: int, diastolic: int) -> Dict:
    """Calculate pulse pressure and assess cardiovascular risk.

    Pulse pressure (PP) is the difference between systolic and diastolic
    blood pressure. Normal range is 40-60 mmHg. Wide PP may indicate
    arterial stiffness; narrow PP may indicate reduced cardiac output.

    Args:
        systolic: Systolic blood pressure in mmHg
        diastolic: Diastolic blood pressure in mmHg

    Returns:
        Dictionary with pulse pressure value and risk assessment

    Example:
        >>> result = calculate_pulse_pressure(120, 80)
        >>> print(f"PP: {result['pulse_pressure']} - {result['status']}")
        PP: 40 - Normal
    """
    if systolic <= 0 or diastolic <= 0:
        raise ValueError("Blood pressure values must be positive")

    pulse_pressure = systolic - diastolic

    if pulse_pressure < 25:
        status = "Narrow - possible reduced cardiac output"
        risk = "elevated"
    elif pulse_pressure < 40:
        status = "Low normal"
        risk = "low"
    elif pulse_pressure <= 60:
        status = "Normal"
        risk = "low"
    elif pulse_pressure <= 80:
        status = "Wide - possible arterial stiffness"
        risk = "moderate"
    else:
        status = "Very wide - increased cardiovascular risk"
        risk = "high"

    return {
        "pulse_pressure": pulse_pressure,
        "status": status,
        "risk": risk,
        "unit": "mmHg",
    }
