"""QT interval correction and drug-induced QT prolongation risk assessment.

This module provides QTc calculation using standard correction formulas and
a risk assessment for QT prolongation and Torsade de Pointes (TdP) based on
a patient's medication list, corrected QT interval, and clinical risk
factors. This is a decision-support aid, not a diagnostic tool.

Functions:
    calculate_qtc: Correct a raw QT interval for heart rate
    classify_qtc_risk: Classify a QTc value into a risk category
    get_drug_qt_risk: Look up a medication's known TdP risk category
    assess_qt_risk: Combine drug list, QTc, and risk factors into a
        single risk assessment with recommendations

Example:
    >>> from backend.utils.qt_prolongation_checker import assess_qt_risk
    >>> result = assess_qt_risk(
    ...     medications=["citalopram", "azithromycin"],
    ...     qtc_ms=470,
    ...     sex="female",
    ...     risk_factors=["hypokalemia"],
    ... )
    >>> print(result.risk_level)  # "high"
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Literal, Optional

QtcFormula = Literal["bazett", "fridericia", "framingham", "hodges"]


class TdPRiskCategory(str, Enum):
    """CredibleMeds-style Torsade de Pointes risk categorization for drugs."""
    KNOWN_RISK = "known_risk"
    POSSIBLE_RISK = "possible_risk"
    CONDITIONAL_RISK = "conditional_risk"
    NONE = "none"


class QtcClassification(str, Enum):
    """Clinical classification of a corrected QT interval."""
    NORMAL = "normal"
    BORDERLINE = "borderline"
    PROLONGED = "prolonged"
    SEVERELY_PROLONGED = "severely_prolonged"


# Curated subset of well-documented QT-prolonging medications by generic
# name (lowercase). Not exhaustive; intended for decision-support triage,
# not as a substitute for a full drug interaction database.
QT_PROLONGING_DRUGS = {
    # Known risk of TdP
    "amiodarone": TdPRiskCategory.KNOWN_RISK,
    "sotalol": TdPRiskCategory.KNOWN_RISK,
    "dofetilide": TdPRiskCategory.KNOWN_RISK,
    "quinidine": TdPRiskCategory.KNOWN_RISK,
    "citalopram": TdPRiskCategory.KNOWN_RISK,
    "haloperidol": TdPRiskCategory.KNOWN_RISK,
    "methadone": TdPRiskCategory.KNOWN_RISK,
    "ondansetron": TdPRiskCategory.KNOWN_RISK,
    "erythromycin": TdPRiskCategory.KNOWN_RISK,
    "azithromycin": TdPRiskCategory.KNOWN_RISK,
    "clarithromycin": TdPRiskCategory.KNOWN_RISK,
    "moxifloxacin": TdPRiskCategory.KNOWN_RISK,
    # Possible risk of TdP
    "escitalopram": TdPRiskCategory.POSSIBLE_RISK,
    "fluconazole": TdPRiskCategory.POSSIBLE_RISK,
    "quetiapine": TdPRiskCategory.POSSIBLE_RISK,
    "risperidone": TdPRiskCategory.POSSIBLE_RISK,
    "levofloxacin": TdPRiskCategory.POSSIBLE_RISK,
    "ciprofloxacin": TdPRiskCategory.POSSIBLE_RISK,
    "venlafaxine": TdPRiskCategory.POSSIBLE_RISK,
    # Conditional risk (risk mainly under specific conditions, e.g.
    # electrolyte imbalance or congenital long QT)
    "amitriptyline": TdPRiskCategory.CONDITIONAL_RISK,
    "metronidazole": TdPRiskCategory.CONDITIONAL_RISK,
    "loperamide": TdPRiskCategory.CONDITIONAL_RISK,
    "omeprazole": TdPRiskCategory.CONDITIONAL_RISK,
}

# QTc thresholds in ms, sex-specific per standard clinical cutoffs.
_QTC_THRESHOLDS = {
    "male": {"borderline": 431, "prolonged": 451, "severe": 500},
    "female": {"borderline": 451, "prolonged": 471, "severe": 500},
}


@dataclass
class DrugQtRisk:
    """QT risk info for a single medication."""
    drug: str
    risk_category: TdPRiskCategory


@dataclass
class QtRiskAssessment:
    """Combined QT prolongation / TdP risk assessment."""
    qtc_ms: Optional[float]
    qtc_classification: Optional[QtcClassification]
    drug_risks: List[DrugQtRisk] = field(default_factory=list)
    additional_risk_factors: List[str] = field(default_factory=list)
    risk_score: int = 0
    risk_level: str = "low"
    recommendations: List[str] = field(default_factory=list)


def calculate_qtc(
    qt_ms: float,
    rr_interval_sec: Optional[float] = None,
    heart_rate_bpm: Optional[float] = None,
    formula: QtcFormula = "fridericia",
) -> float:
    """Calculate the corrected QT interval (QTc) from a raw QT measurement.

    Args:
        qt_ms: Measured QT interval in milliseconds.
        rr_interval_sec: RR interval in seconds. Provide this or
            heart_rate_bpm.
        heart_rate_bpm: Heart rate in beats per minute, used to derive the
            RR interval if rr_interval_sec is not given.
        formula: Correction formula to use. Fridericia is generally
            preferred over Bazett, which over-corrects at high heart rates.

    Returns:
        Corrected QT interval in milliseconds.

    Raises:
        ValueError: If neither rr_interval_sec nor heart_rate_bpm is given,
            or if qt_ms / heart rate are non-positive.
    """
    if qt_ms <= 0:
        raise ValueError("qt_ms must be positive")

    if rr_interval_sec is None:
        if heart_rate_bpm is None or heart_rate_bpm <= 0:
            raise ValueError("Provide rr_interval_sec or a positive heart_rate_bpm")
        rr_interval_sec = 60.0 / heart_rate_bpm

    if rr_interval_sec <= 0:
        raise ValueError("rr_interval_sec must be positive")

    if formula == "bazett":
        qtc = qt_ms / (rr_interval_sec ** 0.5)
    elif formula == "fridericia":
        qtc = qt_ms / (rr_interval_sec ** (1 / 3))
    elif formula == "framingham":
        qtc = qt_ms + 154 * (1 - rr_interval_sec)
    elif formula == "hodges":
        heart_rate = 60.0 / rr_interval_sec
        qtc = qt_ms + 1.75 * (heart_rate - 60)
    else:
        raise ValueError(f"Unknown formula: {formula}")

    return round(qtc, 1)


def classify_qtc_risk(qtc_ms: float, sex: Literal["male", "female"] = "male") -> QtcClassification:
    """Classify a QTc value into a clinical risk category.

    Args:
        qtc_ms: Corrected QT interval in milliseconds.
        sex: Patient sex, used to select sex-specific thresholds.

    Returns:
        QtcClassification for the given value.
    """
    sex_key = sex if sex in _QTC_THRESHOLDS else "male"
    thresholds = _QTC_THRESHOLDS[sex_key]

    if qtc_ms >= thresholds["severe"]:
        return QtcClassification.SEVERELY_PROLONGED
    if qtc_ms >= thresholds["prolonged"]:
        return QtcClassification.PROLONGED
    if qtc_ms >= thresholds["borderline"]:
        return QtcClassification.BORDERLINE
    return QtcClassification.NORMAL


def get_drug_qt_risk(drug_name: str) -> TdPRiskCategory:
    """Look up the known TdP risk category for a medication.

    Args:
        drug_name: Generic or brand drug name (case-insensitive).

    Returns:
        TdPRiskCategory.NONE if the drug is not in the curated list.
    """
    return QT_PROLONGING_DRUGS.get(drug_name.strip().lower(), TdPRiskCategory.NONE)


def assess_qt_risk(
    medications: List[str],
    qtc_ms: Optional[float] = None,
    sex: Literal["male", "female"] = "male",
    risk_factors: Optional[List[str]] = None,
) -> QtRiskAssessment:
    """Assess combined QT prolongation / Torsade de Pointes risk.

    Combines the number and severity of QT-prolonging medications, the
    patient's own QTc (if known), and additional clinical risk factors
    (e.g. hypokalemia, hypomagnesemia, bradycardia, structural heart
    disease) into a single risk score and actionable recommendations.

    Args:
        medications: List of medication names the patient is taking.
        qtc_ms: Patient's known corrected QT interval, if available.
        sex: Patient sex, used for QTc classification thresholds.
        risk_factors: Additional clinical risk factors present.

    Returns:
        QtRiskAssessment with risk_level of "low", "moderate", "high", or
        "critical".
    """
    risk_factors = risk_factors or []
    drug_risks = [
        DrugQtRisk(drug=med, risk_category=get_drug_qt_risk(med))
        for med in medications
    ]

    score = 0
    for dr in drug_risks:
        if dr.risk_category == TdPRiskCategory.KNOWN_RISK:
            score += 3
        elif dr.risk_category == TdPRiskCategory.POSSIBLE_RISK:
            score += 2
        elif dr.risk_category == TdPRiskCategory.CONDITIONAL_RISK:
            score += 1

    known_risk_count = sum(
        1 for dr in drug_risks if dr.risk_category == TdPRiskCategory.KNOWN_RISK
    )
    if known_risk_count >= 2:
        # Concurrent known-risk QT-prolonging drugs compound risk sharply.
        score += 3

    qtc_classification: Optional[QtcClassification] = None
    if qtc_ms is not None:
        qtc_classification = classify_qtc_risk(qtc_ms, sex)
        if qtc_classification == QtcClassification.SEVERELY_PROLONGED:
            score += 5
        elif qtc_classification == QtcClassification.PROLONGED:
            score += 3
        elif qtc_classification == QtcClassification.BORDERLINE:
            score += 1

    score += len(risk_factors)

    if score >= 8:
        risk_level = "critical"
    elif score >= 5:
        risk_level = "high"
    elif score >= 2:
        risk_level = "moderate"
    else:
        risk_level = "low"

    recommendations: List[str] = []
    risky_drugs = [dr.drug for dr in drug_risks if dr.risk_category != TdPRiskCategory.NONE]
    if risky_drugs:
        recommendations.append(
            f"Review QT-prolonging medications: {', '.join(risky_drugs)}"
        )
    if known_risk_count >= 2:
        recommendations.append(
            "Multiple known QT-prolonging drugs present; consider alternatives "
            "or ECG monitoring."
        )
    if qtc_classification in (QtcClassification.PROLONGED, QtcClassification.SEVERELY_PROLONGED):
        recommendations.append(
            "Baseline QTc is prolonged; obtain cardiology input before adding "
            "further QT-prolonging agents."
        )
    if risk_factors:
        recommendations.append(
            f"Address modifiable risk factors: {', '.join(risk_factors)}"
        )
    if risk_level in ("high", "critical") and not recommendations:
        recommendations.append("Consider ECG monitoring given elevated QT risk score.")
    if not recommendations:
        recommendations.append("No significant QT prolongation risk identified.")

    return QtRiskAssessment(
        qtc_ms=qtc_ms,
        qtc_classification=qtc_classification,
        drug_risks=drug_risks,
        additional_risk_factors=risk_factors,
        risk_score=score,
        risk_level=risk_level,
        recommendations=recommendations,
    )
