"""Medication taper schedule generator for MedAlert.

Generates safe, gradual dose-reduction schedules for medications that
require tapering (e.g., corticosteroids, benzodiazepines, SSRIs, opioids).
Supports linear, percentage-based, and custom step-down protocols.

DISCLAIMER: This is for educational/informational purposes only.
Always consult healthcare professionals for medical decisions.
Taper schedules must be verified by a licensed pharmacist or physician.

Functions:
    generate_linear_taper: Equal dose reductions over fixed intervals.
    generate_percentage_taper: Reduce by a percentage each step.
    generate_custom_taper: User-defined step-down schedule.
    estimate_taper_duration: Estimate total taper duration.
    check_taper_safety: Validate taper rate against safety guidelines.

Example:
    >>> schedule = generate_linear_taper(
    ...     starting_dose_mg=40.0,
    ...     target_dose_mg=0.0,
    ...     step_reduction_mg=5.0,
    ...     days_per_step=7,
    ... )
    >>> for step in schedule.steps:
    ...     print(f"Week {step.step_number}: {step.dose_mg}mg for {step.duration_days} days")
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from typing import List, Optional


class TaperMethod(Enum):
    """Supported tapering methods."""

    LINEAR = "linear"
    PERCENTAGE = "percentage"
    CUSTOM = "custom"


class TaperRisk(Enum):
    """Risk level for a taper schedule."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    UNSAFE = "unsafe"


@dataclass
class TaperStep:
    """Single step in a taper schedule.

    Attributes:
        step_number: 1-indexed step number.
        dose_mg: Dose in milligrams for this step.
        duration_days: Days to remain at this dose.
        start_date: When this step begins (if start_date provided).
        notes: Optional clinical notes for this step.
    """

    step_number: int
    dose_mg: float
    duration_days: int
    start_date: Optional[date] = None
    notes: str = ""


@dataclass
class TaperSchedule:
    """Complete taper schedule.

    Attributes:
        medication: Name of the medication being tapered.
        method: Tapering method used.
        starting_dose_mg: Initial dose.
        target_dose_mg: Final target dose.
        steps: Ordered list of taper steps.
        total_duration_days: Total duration of the taper.
        risk_level: Assessed risk level.
        warnings: Safety warnings.
    """

    medication: str
    method: TaperMethod
    starting_dose_mg: float
    target_dose_mg: float
    steps: List[TaperStep]
    total_duration_days: int
    risk_level: TaperRisk
    warnings: List[str] = field(default_factory=list)


# Medications known to require careful tapering
TAPER_REQUIRED_MEDICATIONS = {
    "prednisone": {"max_reduction_pct": 20, "min_step_days": 3},
    "prednisolone": {"max_reduction_pct": 20, "min_step_days": 3},
    "dexamethasone": {"max_reduction_pct": 15, "min_step_days": 5},
    "diazepam": {"max_reduction_pct": 10, "min_step_days": 7},
    "lorazepam": {"max_reduction_pct": 10, "min_step_days": 7},
    "alprazolam": {"max_reduction_pct": 10, "min_step_days": 7},
    "clonazepam": {"max_reduction_pct": 10, "min_step_days": 7},
    "sertraline": {"max_reduction_pct": 25, "min_step_days": 7},
    "paroxetine": {"max_reduction_pct": 10, "min_step_days": 14},
    "venlafaxine": {"max_reduction_pct": 15, "min_step_days": 7},
    "duloxetine": {"max_reduction_pct": 15, "min_step_days": 7},
    "oxycodone": {"max_reduction_pct": 10, "min_step_days": 7},
    "morphine": {"max_reduction_pct": 10, "min_step_days": 7},
    "gabapentin": {"max_reduction_pct": 20, "min_step_days": 7},
    "pregabalin": {"max_reduction_pct": 15, "min_step_days": 7},
}


def generate_linear_taper(
    starting_dose_mg: float,
    target_dose_mg: float = 0.0,
    step_reduction_mg: float = 5.0,
    days_per_step: int = 7,
    medication: str = "unknown",
    start_date: Optional[date] = None,
) -> TaperSchedule:
    """Generate a linear taper schedule with equal dose reductions.

    Args:
        starting_dose_mg: Current dose in mg.
        target_dose_mg: Target dose (default 0 for full discontinuation).
        step_reduction_mg: Amount to reduce per step.
        days_per_step: Days at each dose level.
        medication: Name of medication.
        start_date: Optional start date for the schedule.

    Returns:
        TaperSchedule with linear step-down.

    Raises:
        ValueError: If doses or reduction are invalid.
    """
    if starting_dose_mg <= 0:
        raise ValueError("Starting dose must be positive")
    if target_dose_mg < 0:
        raise ValueError("Target dose cannot be negative")
    if step_reduction_mg <= 0:
        raise ValueError("Step reduction must be positive")
    if starting_dose_mg <= target_dose_mg:
        raise ValueError("Starting dose must exceed target dose")

    steps = []
    current_dose = starting_dose_mg
    step_num = 1
    current_date = start_date

    while current_dose > target_dose_mg:
        step = TaperStep(
            step_number=step_num,
            dose_mg=round(current_dose, 2),
            duration_days=days_per_step,
            start_date=current_date,
        )
        steps.append(step)

        current_dose -= step_reduction_mg
        if current_dose < target_dose_mg:
            current_dose = target_dose_mg
        step_num += 1
        if current_date:
            current_date = current_date + timedelta(days=days_per_step)

    # Final step at target dose
    if steps and steps[-1].dose_mg != target_dose_mg:
        steps.append(
            TaperStep(
                step_number=step_num,
                dose_mg=target_dose_mg,
                duration_days=days_per_step,
                start_date=current_date,
                notes="Target dose reached" if target_dose_mg > 0 else "Discontinuation",
            )
        )

    total_days = sum(s.duration_days for s in steps)
    risk = _assess_risk(medication, starting_dose_mg, total_days, steps)
    warnings = _generate_warnings(medication, steps)

    return TaperSchedule(
        medication=medication,
        method=TaperMethod.LINEAR,
        starting_dose_mg=starting_dose_mg,
        target_dose_mg=target_dose_mg,
        steps=steps,
        total_duration_days=total_days,
        risk_level=risk,
        warnings=warnings,
    )


def generate_percentage_taper(
    starting_dose_mg: float,
    target_dose_mg: float = 0.0,
    reduction_pct: float = 10.0,
    days_per_step: int = 7,
    medication: str = "unknown",
    min_dose_mg: float = 0.5,
    start_date: Optional[date] = None,
) -> TaperSchedule:
    """Generate a percentage-based taper (reduces by X% each step).

    This produces a gentler taper at lower doses, which is often
    clinically preferred to avoid withdrawal at low levels.

    Args:
        starting_dose_mg: Current dose in mg.
        target_dose_mg: Target dose.
        reduction_pct: Percentage to reduce each step (1-50).
        days_per_step: Days at each dose level.
        medication: Name of medication.
        min_dose_mg: Minimum dose before discontinuation.
        start_date: Optional start date.

    Returns:
        TaperSchedule with percentage-based steps.
    """
    if not 1 <= reduction_pct <= 50:
        raise ValueError("Reduction percentage must be between 1 and 50")
    if starting_dose_mg <= 0:
        raise ValueError("Starting dose must be positive")

    steps = []
    current_dose = starting_dose_mg
    step_num = 1
    current_date = start_date

    while current_dose > target_dose_mg and current_dose >= min_dose_mg:
        steps.append(
            TaperStep(
                step_number=step_num,
                dose_mg=round(current_dose, 2),
                duration_days=days_per_step,
                start_date=current_date,
            )
        )
        current_dose *= (1 - reduction_pct / 100)
        step_num += 1
        if current_date:
            current_date = current_date + timedelta(days=days_per_step)

    # Final discontinuation step
    steps.append(
        TaperStep(
            step_number=step_num,
            dose_mg=target_dose_mg,
            duration_days=days_per_step,
            start_date=current_date,
            notes="Target dose reached" if target_dose_mg > 0 else "Discontinuation",
        )
    )

    total_days = sum(s.duration_days for s in steps)
    risk = _assess_risk(medication, starting_dose_mg, total_days, steps)
    warnings = _generate_warnings(medication, steps)

    return TaperSchedule(
        medication=medication,
        method=TaperMethod.PERCENTAGE,
        starting_dose_mg=starting_dose_mg,
        target_dose_mg=target_dose_mg,
        steps=steps,
        total_duration_days=total_days,
        risk_level=risk,
        warnings=warnings,
    )


def generate_custom_taper(
    medication: str,
    dose_steps: List[tuple],
    start_date: Optional[date] = None,
) -> TaperSchedule:
    """Generate a taper from explicit (dose_mg, duration_days) pairs.

    Args:
        medication: Name of medication.
        dose_steps: List of (dose_mg, duration_days) tuples in order.
        start_date: Optional start date.

    Returns:
        TaperSchedule with custom steps.

    Raises:
        ValueError: If dose_steps is empty.
    """
    if not dose_steps:
        raise ValueError("dose_steps must not be empty")

    steps = []
    current_date = start_date

    for i, (dose, days) in enumerate(dose_steps, 1):
        steps.append(
            TaperStep(
                step_number=i,
                dose_mg=round(dose, 2),
                duration_days=days,
                start_date=current_date,
            )
        )
        if current_date:
            current_date = current_date + timedelta(days=days)

    starting = steps[0].dose_mg
    target = steps[-1].dose_mg
    total_days = sum(s.duration_days for s in steps)
    risk = _assess_risk(medication, starting, total_days, steps)
    warnings = _generate_warnings(medication, steps)

    return TaperSchedule(
        medication=medication,
        method=TaperMethod.CUSTOM,
        starting_dose_mg=starting,
        target_dose_mg=target,
        steps=steps,
        total_duration_days=total_days,
        risk_level=risk,
        warnings=warnings,
    )


def estimate_taper_duration(
    starting_dose_mg: float,
    target_dose_mg: float,
    reduction_pct: float,
    days_per_step: int,
    min_dose_mg: float = 0.5,
) -> int:
    """Estimate total taper duration in days without generating full schedule.

    Args:
        starting_dose_mg: Current dose.
        target_dose_mg: Target dose.
        reduction_pct: Percentage reduction per step.
        days_per_step: Days per step.
        min_dose_mg: Minimum dose before stop.

    Returns:
        Estimated total days.
    """
    current = starting_dose_mg
    total_days = 0
    while current > target_dose_mg and current >= min_dose_mg:
        total_days += days_per_step
        current *= (1 - reduction_pct / 100)
    total_days += days_per_step  # final discontinuation step
    return total_days


def check_taper_safety(
    medication: str,
    schedule: TaperSchedule,
) -> dict:
    """Validate a taper schedule against known safety guidelines.

    Args:
        medication: Medication name (case-insensitive).
        schedule: The taper schedule to check.

    Returns:
        Dict with 'safe' bool, 'risk' level, and 'issues' list.
    """
    med_key = medication.lower().strip()
    guidelines = TAPER_REQUIRED_MEDICATIONS.get(med_key)
    issues = []

    if not guidelines:
        return {
            "safe": True,
            "risk": TaperRisk.LOW.value,
            "issues": ["No specific guidelines found; general caution advised"],
        }

    max_pct = guidelines["max_reduction_pct"]
    min_days = guidelines["min_step_days"]

    for i in range(1, len(schedule.steps)):
        prev = schedule.steps[i - 1].dose_mg
        curr = schedule.steps[i].dose_mg
        if prev > 0:
            reduction = (prev - curr) / prev * 100
            if reduction > max_pct + 1:  # +1 for rounding tolerance
                issues.append(
                    f"Step {i+1}: {reduction:.0f}% reduction exceeds "
                    f"recommended max {max_pct}% for {medication}"
                )

        if schedule.steps[i - 1].duration_days < min_days:
            issues.append(
                f"Step {i}: {schedule.steps[i-1].duration_days} days is below "
                f"recommended minimum {min_days} days for {medication}"
            )

    risk = TaperRisk.LOW if not issues else TaperRisk.HIGH
    return {
        "safe": len(issues) == 0,
        "risk": risk.value,
        "issues": issues,
    }


def _assess_risk(
    medication: str,
    starting_dose: float,
    total_days: int,
    steps: List[TaperStep],
) -> TaperRisk:
    """Assess overall risk of a taper schedule."""
    med_key = medication.lower().strip()

    # Known high-risk medications
    high_risk_meds = {"alprazolam", "oxycodone", "morphine", "paroxetine"}
    if med_key in high_risk_meds:
        if total_days < 28:
            return TaperRisk.UNSAFE
        if total_days < 56:
            return TaperRisk.HIGH

    if med_key in TAPER_REQUIRED_MEDICATIONS:
        guidelines = TAPER_REQUIRED_MEDICATIONS[med_key]
        for i in range(1, len(steps)):
            prev = steps[i - 1].dose_mg
            curr = steps[i].dose_mg
            if prev > 0:
                reduction = (prev - curr) / prev * 100
                if reduction > guidelines["max_reduction_pct"] * 1.5:
                    return TaperRisk.UNSAFE
                if reduction > guidelines["max_reduction_pct"]:
                    return TaperRisk.HIGH

        return TaperRisk.MODERATE

    return TaperRisk.LOW


def _generate_warnings(
    medication: str,
    steps: List[TaperStep],
) -> List[str]:
    """Generate clinical warnings for a taper schedule."""
    warnings = []
    med_key = medication.lower().strip()

    warnings.append(
        "DISCLAIMER: This schedule is for informational purposes only. "
        "Always consult your healthcare provider before changing medication doses."
    )

    if med_key in {"diazepam", "lorazepam", "alprazolam", "clonazepam"}:
        warnings.append(
            "Benzodiazepine withdrawal can cause seizures. "
            "Medical supervision is strongly recommended."
        )

    if med_key in {"oxycodone", "morphine"}:
        warnings.append(
            "Opioid tapering should be done under close medical supervision. "
            "Watch for withdrawal symptoms."
        )

    if med_key in {"prednisone", "prednisolone", "dexamethasone"}:
        warnings.append(
            "Abrupt corticosteroid discontinuation can cause adrenal crisis. "
            "Do not skip taper steps."
        )

    if med_key in {"sertraline", "paroxetine", "venlafaxine", "duloxetine"}:
        warnings.append(
            "SSRI/SNRI discontinuation syndrome may include dizziness, "
            "nausea, and mood changes. Report symptoms to your provider."
        )

    return warnings
