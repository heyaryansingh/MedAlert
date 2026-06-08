"""Dosage adjustment recommendation engine for MedAlert.

Provides rule-based dosage adjustment suggestions based on patient
characteristics (age, weight, renal/hepatic function) and therapeutic
drug monitoring (TDM) results.

DISCLAIMER: This is for educational/informational purposes only.
Always consult healthcare professionals for medical decisions.
Dosage adjustments must be verified by a licensed pharmacist or physician.

Functions:
    calculate_renal_adjustment: Adjust dose for renal impairment (CrCl-based)
    calculate_hepatic_adjustment: Adjust dose for hepatic impairment
    calculate_weight_based_dose: Weight-based dosing calculation
    calculate_pediatric_dose: Pediatric dose estimation (Clark's/Young's rules)
    therapeutic_range_check: Check if drug level is within therapeutic range
    suggest_adjustment: Generate dosage adjustment recommendation

Example:
    >>> from backend.utils.dosage_adjustment import suggest_adjustment
    >>> rec = suggest_adjustment(
    ...     drug_name="gentamicin",
    ...     current_dose_mg=120,
    ...     creatinine_clearance=45.0,
    ...     weight_kg=70,
    ... )
    >>> print(rec.recommendation)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class AdjustmentReason(str, Enum):
    """Reason for dosage adjustment."""

    RENAL_IMPAIRMENT = "renal_impairment"
    HEPATIC_IMPAIRMENT = "hepatic_impairment"
    WEIGHT_BASED = "weight_based"
    PEDIATRIC = "pediatric"
    GERIATRIC = "geriatric"
    THERAPEUTIC_LEVEL = "therapeutic_level"
    NONE = "no_adjustment_needed"


class RenalCategory(str, Enum):
    """Renal function categories based on creatinine clearance (mL/min)."""

    NORMAL = "normal"  # >= 90
    MILD = "mild_impairment"  # 60-89
    MODERATE = "moderate_impairment"  # 30-59
    SEVERE = "severe_impairment"  # 15-29
    ESRD = "end_stage_renal_disease"  # < 15


class HepaticCategory(str, Enum):
    """Hepatic impairment categories (Child-Pugh classification)."""

    NONE = "none"
    MILD_A = "child_pugh_a"  # Score 5-6
    MODERATE_B = "child_pugh_b"  # Score 7-9
    SEVERE_C = "child_pugh_c"  # Score 10-15


@dataclass
class DosageRecommendation:
    """Dosage adjustment recommendation result.

    Attributes:
        drug_name: Name of the medication.
        current_dose_mg: Current dose in milligrams.
        recommended_dose_mg: Recommended adjusted dose in milligrams.
        adjustment_factor: Multiplication factor applied (1.0 = no change).
        reasons: List of adjustment reasons applied.
        recommendation: Human-readable recommendation text.
        warnings: List of clinical warnings.
        confidence: Confidence level (high/medium/low) in the recommendation.
    """

    drug_name: str
    current_dose_mg: float
    recommended_dose_mg: float
    adjustment_factor: float
    reasons: List[AdjustmentReason]
    recommendation: str
    warnings: List[str]
    confidence: str = "medium"


@dataclass
class TherapeuticRangeResult:
    """Result of therapeutic drug monitoring range check.

    Attributes:
        drug_name: Name of the medication.
        measured_level: Measured drug concentration.
        unit: Concentration unit.
        therapeutic_min: Lower bound of therapeutic range.
        therapeutic_max: Upper bound of therapeutic range.
        status: Whether level is sub-therapeutic, therapeutic, or toxic.
        recommendation: Suggested action.
    """

    drug_name: str
    measured_level: float
    unit: str
    therapeutic_min: float
    therapeutic_max: float
    status: str
    recommendation: str


# Common therapeutic ranges (trough levels, mcg/mL unless noted)
THERAPEUTIC_RANGES: Dict[str, Dict] = {
    "vancomycin": {"min": 10.0, "max": 20.0, "unit": "mcg/mL", "toxic": 40.0},
    "gentamicin": {"min": 0.5, "max": 2.0, "unit": "mcg/mL", "toxic": 12.0},
    "digoxin": {"min": 0.8, "max": 2.0, "unit": "ng/mL", "toxic": 2.5},
    "lithium": {"min": 0.6, "max": 1.2, "unit": "mEq/L", "toxic": 1.5},
    "phenytoin": {"min": 10.0, "max": 20.0, "unit": "mcg/mL", "toxic": 30.0},
    "carbamazepine": {"min": 4.0, "max": 12.0, "unit": "mcg/mL", "toxic": 15.0},
    "valproic_acid": {"min": 50.0, "max": 100.0, "unit": "mcg/mL", "toxic": 150.0},
    "theophylline": {"min": 10.0, "max": 20.0, "unit": "mcg/mL", "toxic": 25.0},
    "cyclosporine": {"min": 100.0, "max": 400.0, "unit": "ng/mL", "toxic": 500.0},
    "tacrolimus": {"min": 5.0, "max": 15.0, "unit": "ng/mL", "toxic": 20.0},
    "methotrexate": {"min": 0.0, "max": 0.1, "unit": "umol/L", "toxic": 1.0},
    "amikacin": {"min": 1.0, "max": 8.0, "unit": "mcg/mL", "toxic": 35.0},
}

# Renal adjustment factors by drug category
RENAL_ADJUSTMENT_FACTORS: Dict[str, Dict[str, float]] = {
    "aminoglycoside": {
        RenalCategory.NORMAL.value: 1.0,
        RenalCategory.MILD.value: 0.85,
        RenalCategory.MODERATE.value: 0.6,
        RenalCategory.SEVERE.value: 0.3,
        RenalCategory.ESRD.value: 0.2,
    },
    "default": {
        RenalCategory.NORMAL.value: 1.0,
        RenalCategory.MILD.value: 0.9,
        RenalCategory.MODERATE.value: 0.75,
        RenalCategory.SEVERE.value: 0.5,
        RenalCategory.ESRD.value: 0.25,
    },
}

# Drug-to-category mapping
DRUG_CATEGORIES: Dict[str, str] = {
    "gentamicin": "aminoglycoside",
    "amikacin": "aminoglycoside",
    "tobramycin": "aminoglycoside",
    "vancomycin": "default",
    "digoxin": "default",
    "lithium": "default",
    "metformin": "default",
}


def classify_renal_function(creatinine_clearance: float) -> RenalCategory:
    """Classify renal function based on creatinine clearance.

    Args:
        creatinine_clearance: Creatinine clearance in mL/min.

    Returns:
        Renal function category.
    """
    if creatinine_clearance >= 90:
        return RenalCategory.NORMAL
    elif creatinine_clearance >= 60:
        return RenalCategory.MILD
    elif creatinine_clearance >= 30:
        return RenalCategory.MODERATE
    elif creatinine_clearance >= 15:
        return RenalCategory.SEVERE
    else:
        return RenalCategory.ESRD


def calculate_renal_adjustment(
    drug_name: str,
    creatinine_clearance: float,
) -> float:
    """Calculate dose adjustment factor for renal impairment.

    Uses creatinine clearance (Cockcroft-Gault) to determine the
    appropriate dose reduction factor for renally-cleared medications.

    Args:
        drug_name: Medication name (lowercase).
        creatinine_clearance: Creatinine clearance in mL/min.

    Returns:
        Dose adjustment factor (0.0-1.0). Multiply current dose by this.
    """
    category = classify_renal_function(creatinine_clearance)
    drug_cat = DRUG_CATEGORIES.get(drug_name.lower(), "default")
    factors = RENAL_ADJUSTMENT_FACTORS.get(drug_cat, RENAL_ADJUSTMENT_FACTORS["default"])
    return factors.get(category.value, 1.0)


def calculate_hepatic_adjustment(
    child_pugh_score: int,
) -> float:
    """Calculate dose adjustment factor for hepatic impairment.

    Uses Child-Pugh score to determine dose reduction.

    Args:
        child_pugh_score: Child-Pugh score (5-15).

    Returns:
        Dose adjustment factor (0.0-1.0).
    """
    if child_pugh_score <= 6:
        return 1.0  # Class A - usually no adjustment
    elif child_pugh_score <= 9:
        return 0.75  # Class B - reduce by 25%
    else:
        return 0.5  # Class C - reduce by 50%


def classify_hepatic_function(child_pugh_score: int) -> HepaticCategory:
    """Classify hepatic function based on Child-Pugh score.

    Args:
        child_pugh_score: Score from 5 to 15.

    Returns:
        Hepatic impairment category.
    """
    if child_pugh_score <= 4:
        return HepaticCategory.NONE
    elif child_pugh_score <= 6:
        return HepaticCategory.MILD_A
    elif child_pugh_score <= 9:
        return HepaticCategory.MODERATE_B
    else:
        return HepaticCategory.SEVERE_C


def calculate_weight_based_dose(
    dose_per_kg: float,
    weight_kg: float,
    max_dose_mg: Optional[float] = None,
) -> float:
    """Calculate weight-based dosing.

    Args:
        dose_per_kg: Target dose in mg/kg.
        weight_kg: Patient weight in kilograms.
        max_dose_mg: Maximum dose cap in mg (optional).

    Returns:
        Calculated dose in milligrams.
    """
    dose = dose_per_kg * weight_kg
    if max_dose_mg is not None:
        dose = min(dose, max_dose_mg)
    return round(dose, 1)


def calculate_pediatric_dose(
    adult_dose_mg: float,
    child_weight_kg: Optional[float] = None,
    child_age_years: Optional[float] = None,
    method: str = "clark",
) -> float:
    """Estimate pediatric dose from adult dose.

    Supports Clark's rule (weight-based) and Young's rule (age-based).

    Args:
        adult_dose_mg: Standard adult dose in milligrams.
        child_weight_kg: Child's weight in kg (for Clark's rule).
        child_age_years: Child's age in years (for Young's rule).
        method: Calculation method ('clark' or 'young').

    Returns:
        Estimated pediatric dose in milligrams.
    """
    if method == "clark" and child_weight_kg is not None:
        # Clark's rule: (weight_lb / 150) * adult_dose
        weight_lb = child_weight_kg * 2.205
        return round((weight_lb / 150) * adult_dose_mg, 1)
    elif method == "young" and child_age_years is not None:
        # Young's rule: (age / (age + 12)) * adult_dose
        return round((child_age_years / (child_age_years + 12)) * adult_dose_mg, 1)
    else:
        return adult_dose_mg


def therapeutic_range_check(
    drug_name: str,
    measured_level: float,
) -> TherapeuticRangeResult:
    """Check if a measured drug level is within therapeutic range.

    Args:
        drug_name: Medication name (lowercase).
        measured_level: Measured serum concentration.

    Returns:
        TherapeuticRangeResult with status and recommendation.
    """
    drug_key = drug_name.lower().replace(" ", "_")
    range_info = THERAPEUTIC_RANGES.get(drug_key)

    if range_info is None:
        return TherapeuticRangeResult(
            drug_name=drug_name,
            measured_level=measured_level,
            unit="unknown",
            therapeutic_min=0.0,
            therapeutic_max=0.0,
            status="unknown_drug",
            recommendation=f"Therapeutic range for '{drug_name}' not in database. "
            "Consult pharmacist for appropriate monitoring.",
        )

    t_min = range_info["min"]
    t_max = range_info["max"]
    toxic = range_info.get("toxic", t_max * 2)
    unit = range_info["unit"]

    if measured_level >= toxic:
        status = "toxic"
        rec = (
            f"URGENT: {drug_name} level ({measured_level} {unit}) is in the TOXIC range "
            f"(>= {toxic} {unit}). Hold dose and contact prescriber immediately."
        )
    elif measured_level > t_max:
        status = "supra_therapeutic"
        rec = (
            f"{drug_name} level ({measured_level} {unit}) is above therapeutic range "
            f"({t_min}-{t_max} {unit}). Consider dose reduction."
        )
    elif measured_level < t_min:
        status = "sub_therapeutic"
        rec = (
            f"{drug_name} level ({measured_level} {unit}) is below therapeutic range "
            f"({t_min}-{t_max} {unit}). Consider dose increase if clinically indicated."
        )
    else:
        status = "therapeutic"
        rec = (
            f"{drug_name} level ({measured_level} {unit}) is within therapeutic range "
            f"({t_min}-{t_max} {unit}). No dose adjustment needed."
        )

    return TherapeuticRangeResult(
        drug_name=drug_name,
        measured_level=measured_level,
        unit=unit,
        therapeutic_min=t_min,
        therapeutic_max=t_max,
        status=status,
        recommendation=rec,
    )


def suggest_adjustment(
    drug_name: str,
    current_dose_mg: float,
    creatinine_clearance: Optional[float] = None,
    child_pugh_score: Optional[int] = None,
    weight_kg: Optional[float] = None,
    age_years: Optional[float] = None,
    measured_level: Optional[float] = None,
) -> DosageRecommendation:
    """Generate a comprehensive dosage adjustment recommendation.

    Evaluates multiple patient factors and returns a single recommendation
    combining all applicable adjustments.

    Args:
        drug_name: Medication name.
        current_dose_mg: Current dose in milligrams.
        creatinine_clearance: Creatinine clearance in mL/min (optional).
        child_pugh_score: Child-Pugh score 5-15 (optional).
        weight_kg: Patient weight in kg (optional).
        age_years: Patient age in years (optional).
        measured_level: Measured serum drug level (optional).

    Returns:
        DosageRecommendation with adjusted dose and clinical context.
    """
    adjustment_factor = 1.0
    reasons: List[AdjustmentReason] = []
    warnings: List[str] = []
    notes: List[str] = []

    # Renal adjustment
    if creatinine_clearance is not None:
        renal_cat = classify_renal_function(creatinine_clearance)
        renal_factor = calculate_renal_adjustment(drug_name, creatinine_clearance)
        if renal_factor < 1.0:
            adjustment_factor *= renal_factor
            reasons.append(AdjustmentReason.RENAL_IMPAIRMENT)
            notes.append(
                f"Renal adjustment ({renal_cat.value}): "
                f"CrCl {creatinine_clearance:.0f} mL/min -> {renal_factor:.0%} of normal dose"
            )
        if renal_cat == RenalCategory.ESRD:
            warnings.append(
                "End-stage renal disease detected. Consider dialysis dosing "
                "supplementation and consult nephrology."
            )

    # Hepatic adjustment
    if child_pugh_score is not None:
        hepatic_cat = classify_hepatic_function(child_pugh_score)
        hepatic_factor = calculate_hepatic_adjustment(child_pugh_score)
        if hepatic_factor < 1.0:
            adjustment_factor *= hepatic_factor
            reasons.append(AdjustmentReason.HEPATIC_IMPAIRMENT)
            notes.append(
                f"Hepatic adjustment ({hepatic_cat.value}): "
                f"Child-Pugh {child_pugh_score} -> {hepatic_factor:.0%} of normal dose"
            )
        if hepatic_cat == HepaticCategory.SEVERE_C:
            warnings.append(
                "Severe hepatic impairment (Child-Pugh C). Some medications are "
                "contraindicated. Verify with pharmacist."
            )

    # Geriatric adjustment
    if age_years is not None and age_years >= 65:
        geriatric_factor = 0.85 if age_years < 80 else 0.75
        adjustment_factor *= geriatric_factor
        reasons.append(AdjustmentReason.GERIATRIC)
        notes.append(
            f"Geriatric adjustment (age {age_years:.0f}): "
            f"Start low at {geriatric_factor:.0%} of standard dose"
        )
        warnings.append(
            "Elderly patient: Monitor closely for adverse effects. "
            "Consider slower titration schedule."
        )

    # TDM-based adjustment
    if measured_level is not None:
        tdm_result = therapeutic_range_check(drug_name, measured_level)
        if tdm_result.status == "toxic":
            adjustment_factor *= 0.5
            reasons.append(AdjustmentReason.THERAPEUTIC_LEVEL)
            warnings.append(f"TOXIC level detected: {tdm_result.recommendation}")
        elif tdm_result.status == "supra_therapeutic":
            adjustment_factor *= 0.75
            reasons.append(AdjustmentReason.THERAPEUTIC_LEVEL)
            notes.append(f"Level adjustment: {tdm_result.recommendation}")
        elif tdm_result.status == "sub_therapeutic":
            adjustment_factor *= 1.25
            reasons.append(AdjustmentReason.THERAPEUTIC_LEVEL)
            notes.append(f"Level adjustment: {tdm_result.recommendation}")

    # Calculate final dose
    recommended_dose = round(current_dose_mg * adjustment_factor, 1)

    # Build recommendation text
    if not reasons:
        reasons.append(AdjustmentReason.NONE)
        recommendation_text = (
            f"No dosage adjustment indicated for {drug_name} "
            f"{current_dose_mg} mg based on available parameters."
        )
    else:
        adjustment_pct = (1 - adjustment_factor) * 100
        direction = "decrease" if adjustment_factor < 1.0 else "increase"
        recommendation_text = (
            f"Recommend {direction} of {drug_name} from {current_dose_mg} mg "
            f"to {recommended_dose} mg ({abs(adjustment_pct):.0f}% {direction}). "
            f"Reasons: {', '.join(n for n in notes)}."
        )

    # Confidence assessment
    if len(reasons) == 1 and AdjustmentReason.NONE not in reasons:
        confidence = "high"
    elif len(reasons) > 2:
        confidence = "low"  # Multiple interacting factors
        warnings.append(
            "Multiple adjustment factors applied. Recommend pharmacist review "
            "for potential compounding effects."
        )
    else:
        confidence = "medium"

    return DosageRecommendation(
        drug_name=drug_name,
        current_dose_mg=current_dose_mg,
        recommended_dose_mg=recommended_dose,
        adjustment_factor=round(adjustment_factor, 3),
        reasons=reasons,
        recommendation=recommendation_text,
        warnings=warnings,
        confidence=confidence,
    )
