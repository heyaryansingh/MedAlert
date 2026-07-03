"""
Polypharmacy Risk Scorer for MedAlert

Estimates a patient's overall polypharmacy burden risk based on the number
of concurrent medications and their individual anticholinergic/sedative
load, using a simplified adaptation of published anticholinergic burden
scoring approaches.

Features:
- Medication count risk banding (polypharmacy / hyperpolypharmacy thresholds)
- Per-drug anticholinergic/sedative burden lookup
- Aggregate burden score with risk level classification
- Plain-language, non-prescriptive recommendations

This module is informational only. It does NOT provide dosing instructions,
does NOT recommend starting, stopping, or changing any medication, and is
NOT a substitute for clinical judgment.

DISCLAIMER: This is for educational/informational purposes only.
Always consult a licensed healthcare professional or pharmacist before
making any medication decisions.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List


class RiskLevel(Enum):
    """Overall polypharmacy risk classification."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    SEVERE = "severe"


# Simplified anticholinergic/sedative burden weights (0-3 scale), loosely
# modeled on published anticholinergic cognitive burden scales. Keyed by
# generic drug name, lowercase. This is a small illustrative reference table,
# not a comprehensive clinical database.
_ANTICHOLINERGIC_BURDEN: Dict[str, int] = {
    "diphenhydramine": 3,
    "amitriptyline": 3,
    "paroxetine": 3,
    "oxybutynin": 3,
    "chlorpheniramine": 3,
    "hydroxyzine": 3,
    "cyclobenzaprine": 2,
    "loperamide": 1,
    "ranitidine": 1,
    "warfarin": 1,
    "furosemide": 1,
    "prednisone": 1,
    "metformin": 0,
    "lisinopril": 0,
    "atorvastatin": 0,
    "levothyroxine": 0,
    "amlodipine": 0,
    "omeprazole": 1,
    "sertraline": 1,
    "trazodone": 1,
    "alprazolam": 2,
    "zolpidem": 2,
    "quetiapine": 2,
}

_DEFAULT_BURDEN = 0


@dataclass
class MedicationEntry:
    """A single medication in the patient's regimen, for risk scoring only.

    Note: dose/frequency are intentionally not required or used here, since
    this scorer never issues dosing guidance.
    """
    generic_name: str
    drug_class: str = ""


@dataclass
class PolypharmacyRiskResult:
    """Result of a polypharmacy risk assessment."""
    medication_count: int
    anticholinergic_burden_score: int
    high_burden_medications: List[str]
    risk_level: RiskLevel
    recommendations: List[str] = field(default_factory=list)
    disclaimer: str = (
        "This assessment is for informational purposes only and does not "
        "constitute medical advice. It does not recommend starting, "
        "stopping, or adjusting any medication. Consult a licensed "
        "healthcare professional or pharmacist for guidance."
    )


class PolypharmacyRiskScorer:
    """Scores overall polypharmacy risk for a patient's medication list."""

    # Medication count thresholds per common clinical definitions.
    POLYPHARMACY_THRESHOLD = 5
    HYPERPOLYPHARMACY_THRESHOLD = 10

    def _lookup_burden(self, generic_name: str) -> int:
        return _ANTICHOLINERGIC_BURDEN.get(generic_name.strip().lower(), _DEFAULT_BURDEN)

    def score(self, medications: List[MedicationEntry]) -> PolypharmacyRiskResult:
        """Compute a polypharmacy risk assessment for a medication list.

        Args:
            medications: List of MedicationEntry objects (generic name only
                is required; no dose/frequency data is used or needed).

        Returns:
            PolypharmacyRiskResult with medication count, aggregate
            anticholinergic burden score, flagged high-burden medications,
            an overall risk level, and plain-language recommendations.
        """
        medication_count = len(medications)

        burdens = [
            (med.generic_name, self._lookup_burden(med.generic_name))
            for med in medications
        ]
        total_burden = sum(b for _, b in burdens)
        high_burden_medications = [name for name, b in burdens if b >= 2]

        risk_level = self._classify_risk(medication_count, total_burden)
        recommendations = self._build_recommendations(
            medication_count, total_burden, high_burden_medications, risk_level
        )

        return PolypharmacyRiskResult(
            medication_count=medication_count,
            anticholinergic_burden_score=total_burden,
            high_burden_medications=high_burden_medications,
            risk_level=risk_level,
            recommendations=recommendations,
        )

    def _classify_risk(self, medication_count: int, total_burden: int) -> RiskLevel:
        if medication_count >= self.HYPERPOLYPHARMACY_THRESHOLD or total_burden >= 6:
            return RiskLevel.SEVERE
        if medication_count >= self.POLYPHARMACY_THRESHOLD or total_burden >= 3:
            return RiskLevel.HIGH
        if medication_count >= 3 or total_burden >= 1:
            return RiskLevel.MODERATE
        return RiskLevel.LOW

    def _build_recommendations(
        self,
        medication_count: int,
        total_burden: int,
        high_burden_medications: List[str],
        risk_level: RiskLevel,
    ) -> List[str]:
        recommendations: List[str] = []

        if medication_count >= self.HYPERPOLYPHARMACY_THRESHOLD:
            recommendations.append(
                f"Patient is on {medication_count} medications (hyperpolypharmacy "
                "range). Consider requesting a comprehensive medication review "
                "with a pharmacist or physician."
            )
        elif medication_count >= self.POLYPHARMACY_THRESHOLD:
            recommendations.append(
                f"Patient is on {medication_count} medications (polypharmacy "
                "range). A periodic medication review may be worthwhile."
            )

        if high_burden_medications:
            joined = ", ".join(sorted(set(high_burden_medications)))
            recommendations.append(
                f"The following medications carry higher anticholinergic/sedative "
                f"burden and may warrant discussion with a prescriber: {joined}."
            )

        if risk_level in (RiskLevel.HIGH, RiskLevel.SEVERE):
            recommendations.append(
                "Combined medication count and burden suggest an elevated risk of "
                "side effects such as cognitive impairment, dizziness, or falls. "
                "Discuss with a healthcare professional."
            )

        if not recommendations:
            recommendations.append(
                "No significant polypharmacy or anticholinergic burden concerns "
                "identified at this time."
            )

        return recommendations
