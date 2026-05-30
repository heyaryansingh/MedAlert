"""Medication Side Effects Tracker - Monitor and analyze medication side effects.

Tracks patient-reported side effects, severity patterns, correlations with medications,
and generates alerts for concerning patterns.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json


class SeverityLevel(Enum):
    """Side effect severity levels."""
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


class EffectCategory(Enum):
    """Side effect categories."""
    GASTROINTESTINAL = "gastrointestinal"
    NEUROLOGICAL = "neurological"
    CARDIOVASCULAR = "cardiovascular"
    DERMATOLOGICAL = "dermatological"
    RESPIRATORY = "respiratory"
    PSYCHOLOGICAL = "psychological"
    MUSCULOSKELETAL = "musculoskeletal"
    OTHER = "other"


@dataclass
class SideEffect:
    """Individual side effect record."""
    effect_id: str
    patient_id: str
    medication_name: str
    medication_dosage: str
    effect_type: str
    category: EffectCategory
    severity: SeverityLevel
    onset_date: datetime
    duration_days: Optional[int]
    description: str
    resolved: bool
    requires_medical_attention: bool


@dataclass
class SideEffectPattern:
    """Pattern analysis for side effects."""
    medication_name: str
    common_effects: List[Tuple[str, int]]  # (effect, frequency)
    severe_effects: List[str]
    average_onset_days: float
    resolution_rate: float
    patients_affected: int
    total_reports: int


class SideEffectsTracker:
    """Track and analyze medication side effects."""

    def __init__(self):
        self.effects: List[SideEffect] = []
        self.severity_thresholds = {
            SeverityLevel.MILD: 1,
            SeverityLevel.MODERATE: 3,
            SeverityLevel.SEVERE: 5,
            SeverityLevel.CRITICAL: 7
        }

    def report_side_effect(
        self,
        patient_id: str,
        medication_name: str,
        medication_dosage: str,
        effect_type: str,
        category: EffectCategory,
        severity: SeverityLevel,
        description: str,
        onset_date: Optional[datetime] = None
    ) -> SideEffect:
        """Report a new side effect.

        Args:
            patient_id: Patient identifier
            medication_name: Name of medication
            medication_dosage: Dosage information
            effect_type: Type of side effect
            category: Effect category
            severity: Severity level
            description: Detailed description
            onset_date: When effect started (defaults to now)

        Returns:
            Created SideEffect record
        """
        if onset_date is None:
            onset_date = datetime.now()

        effect = SideEffect(
            effect_id=f"{patient_id}_{medication_name}_{onset_date.timestamp()}",
            patient_id=patient_id,
            medication_name=medication_name,
            medication_dosage=medication_dosage,
            effect_type=effect_type,
            category=category,
            severity=severity,
            onset_date=onset_date,
            duration_days=None,
            description=description,
            resolved=False,
            requires_medical_attention=severity in [SeverityLevel.SEVERE, SeverityLevel.CRITICAL]
        )

        self.effects.append(effect)
        return effect

    def resolve_side_effect(self, effect_id: str, resolution_date: Optional[datetime] = None):
        """Mark a side effect as resolved.

        Args:
            effect_id: ID of the effect to resolve
            resolution_date: When effect resolved (defaults to now)
        """
        if resolution_date is None:
            resolution_date = datetime.now()

        for effect in self.effects:
            if effect.effect_id == effect_id:
                effect.resolved = True
                effect.duration_days = (resolution_date - effect.onset_date).days
                break

    def get_patient_effects(
        self,
        patient_id: str,
        active_only: bool = False
    ) -> List[SideEffect]:
        """Get all side effects for a patient.

        Args:
            patient_id: Patient identifier
            active_only: Only return unresolved effects

        Returns:
            List of side effects
        """
        patient_effects = [e for e in self.effects if e.patient_id == patient_id]

        if active_only:
            patient_effects = [e for e in patient_effects if not e.resolved]

        return sorted(patient_effects, key=lambda x: x.onset_date, reverse=True)

    def get_medication_effects(self, medication_name: str) -> List[SideEffect]:
        """Get all reported effects for a specific medication.

        Args:
            medication_name: Name of medication

        Returns:
            List of side effects
        """
        return [e for e in self.effects if e.medication_name.lower() == medication_name.lower()]

    def analyze_medication_pattern(self, medication_name: str) -> SideEffectPattern:
        """Analyze side effect patterns for a medication.

        Args:
            medication_name: Name of medication

        Returns:
            SideEffectPattern analysis
        """
        med_effects = self.get_medication_effects(medication_name)

        if not med_effects:
            return SideEffectPattern(
                medication_name=medication_name,
                common_effects=[],
                severe_effects=[],
                average_onset_days=0,
                resolution_rate=0,
                patients_affected=0,
                total_reports=0
            )

        # Count effect types
        effect_counts: Dict[str, int] = {}
        for effect in med_effects:
            effect_counts[effect.effect_type] = effect_counts.get(effect.effect_type, 0) + 1

        common_effects = sorted(effect_counts.items(), key=lambda x: x[1], reverse=True)

        # Identify severe effects
        severe_effects = list(set([
            e.effect_type for e in med_effects
            if e.severity in [SeverityLevel.SEVERE, SeverityLevel.CRITICAL]
        ]))

        # Calculate average onset (from prescription start)
        # Note: This would need prescription data for accuracy
        average_onset_days = 7.0  # Placeholder

        # Resolution rate
        resolved_count = sum(1 for e in med_effects if e.resolved)
        resolution_rate = resolved_count / len(med_effects) if med_effects else 0

        # Unique patients
        patients_affected = len(set(e.patient_id for e in med_effects))

        return SideEffectPattern(
            medication_name=medication_name,
            common_effects=common_effects[:10],
            severe_effects=severe_effects,
            average_onset_days=average_onset_days,
            resolution_rate=resolution_rate,
            patients_affected=patients_affected,
            total_reports=len(med_effects)
        )

    def check_for_alerts(self, patient_id: str) -> List[str]:
        """Check for concerning side effect patterns requiring attention.

        Args:
            patient_id: Patient to check

        Returns:
            List of alert messages
        """
        alerts = []
        patient_effects = self.get_patient_effects(patient_id, active_only=True)

        # Check for critical effects
        critical_effects = [e for e in patient_effects if e.severity == SeverityLevel.CRITICAL]
        if critical_effects:
            alerts.append(
                f"CRITICAL: {len(critical_effects)} critical side effect(s) reported. "
                "Immediate medical attention required."
            )

        # Check for multiple severe effects
        severe_effects = [e for e in patient_effects if e.severity == SeverityLevel.SEVERE]
        if len(severe_effects) >= 2:
            alerts.append(
                f"WARNING: {len(severe_effects)} severe side effects active. "
                "Consider medication review."
            )

        # Check for prolonged effects
        prolonged = [
            e for e in patient_effects
            if (datetime.now() - e.onset_date).days > 14
        ]
        if prolonged:
            alerts.append(
                f"NOTICE: {len(prolonged)} side effect(s) persisting over 2 weeks. "
                "Follow-up recommended."
            )

        # Check for multiple effects from same medication
        med_counts: Dict[str, int] = {}
        for effect in patient_effects:
            med_counts[effect.medication_name] = med_counts.get(effect.medication_name, 0) + 1

        for med, count in med_counts.items():
            if count >= 3:
                alerts.append(
                    f"WARNING: {count} active side effects from {med}. "
                    "Consider alternative medication."
                )

        return alerts

    def get_category_breakdown(self, patient_id: Optional[str] = None) -> Dict[str, int]:
        """Get breakdown of side effects by category.

        Args:
            patient_id: Optional patient filter

        Returns:
            Dictionary mapping categories to counts
        """
        effects = self.effects if patient_id is None else self.get_patient_effects(patient_id)

        breakdown: Dict[str, int] = {cat.value: 0 for cat in EffectCategory}

        for effect in effects:
            breakdown[effect.category.value] += 1

        return breakdown

    def generate_patient_report(self, patient_id: str) -> Dict:
        """Generate comprehensive side effects report for patient.

        Args:
            patient_id: Patient identifier

        Returns:
            Report dictionary
        """
        effects = self.get_patient_effects(patient_id)
        active_effects = [e for e in effects if not e.resolved]

        # Severity distribution
        severity_dist = {sev.value: 0 for sev in SeverityLevel}
        for effect in effects:
            severity_dist[effect.severity.value] += 1

        # Category breakdown
        category_breakdown = self.get_category_breakdown(patient_id)

        # Medication-specific counts
        med_counts: Dict[str, int] = {}
        for effect in effects:
            med_counts[effect.medication_name] = med_counts.get(effect.medication_name, 0) + 1

        return {
            'patient_id': patient_id,
            'total_effects_reported': len(effects),
            'active_effects': len(active_effects),
            'resolved_effects': len(effects) - len(active_effects),
            'severity_distribution': severity_dist,
            'category_breakdown': category_breakdown,
            'medications_with_effects': list(med_counts.keys()),
            'most_problematic_medication': max(med_counts.items(), key=lambda x: x[1])[0] if med_counts else None,
            'alerts': self.check_for_alerts(patient_id),
            'recent_effects': [
                {
                    'medication': e.medication_name,
                    'effect': e.effect_type,
                    'severity': e.severity.value,
                    'onset': e.onset_date.isoformat(),
                    'resolved': e.resolved
                }
                for e in active_effects[:5]
            ]
        }

    def compare_medications(
        self,
        medication_names: List[str]
    ) -> Dict[str, SideEffectPattern]:
        """Compare side effect profiles of multiple medications.

        Args:
            medication_names: List of medication names to compare

        Returns:
            Dictionary mapping medication names to their patterns
        """
        return {
            med: self.analyze_medication_pattern(med)
            for med in medication_names
        }

    def export_data(self, patient_id: Optional[str] = None) -> str:
        """Export side effects data as JSON.

        Args:
            patient_id: Optional patient filter

        Returns:
            JSON string
        """
        effects = self.effects if patient_id is None else self.get_patient_effects(patient_id)

        data = [
            {
                'effect_id': e.effect_id,
                'patient_id': e.patient_id,
                'medication_name': e.medication_name,
                'medication_dosage': e.medication_dosage,
                'effect_type': e.effect_type,
                'category': e.category.value,
                'severity': e.severity.value,
                'onset_date': e.onset_date.isoformat(),
                'duration_days': e.duration_days,
                'description': e.description,
                'resolved': e.resolved,
                'requires_medical_attention': e.requires_medical_attention
            }
            for e in effects
        ]

        return json.dumps(data, indent=2)
