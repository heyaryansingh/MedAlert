"""Patient health summary generator.

This module provides utilities for generating comprehensive health summaries
from patient data including vitals, symptoms, medications, and AI risk scores.
Useful for quick patient overview dashboards and doctor consultations.

Features:
    - Aggregate vital signs with trend analysis
    - Symptom frequency and severity tracking
    - Medication adherence summary
    - Risk score history and alerts
    - Export-ready summary generation

Example:
    >>> from backend.utils.health_summary import HealthSummaryGenerator
    >>> generator = HealthSummaryGenerator()
    >>> summary = await generator.generate_summary(patient_id, days=30)
    >>> print(summary.risk_level)
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import structlog

logger = structlog.get_logger(__name__)


class RiskLevel(str, Enum):
    """Patient risk level classification."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class TrendDirection(str, Enum):
    """Trend direction for vital signs."""

    IMPROVING = "improving"
    STABLE = "stable"
    WORSENING = "worsening"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass
class VitalSummary:
    """Summary statistics for a vital sign.

    Attributes:
        name: Vital sign name (e.g., "heart_rate").
        unit: Unit of measurement.
        min_value: Minimum recorded value.
        max_value: Maximum recorded value.
        avg_value: Average value.
        latest_value: Most recent reading.
        latest_timestamp: Timestamp of most recent reading.
        reading_count: Number of readings in period.
        trend: Trend direction over the period.
        out_of_range_count: Number of abnormal readings.
    """

    name: str
    unit: str
    min_value: float
    max_value: float
    avg_value: float
    latest_value: float
    latest_timestamp: datetime
    reading_count: int
    trend: TrendDirection
    out_of_range_count: int = 0


@dataclass
class SymptomSummary:
    """Summary of reported symptoms.

    Attributes:
        symptom: Symptom description.
        occurrences: Number of times reported.
        avg_severity: Average severity (1-10).
        max_severity: Maximum severity reported.
        first_reported: First occurrence timestamp.
        last_reported: Most recent occurrence.
    """

    symptom: str
    occurrences: int
    avg_severity: float
    max_severity: int
    first_reported: datetime
    last_reported: datetime


@dataclass
class AlertSummary:
    """Summary of patient alerts.

    Attributes:
        alert_type: Type of alert.
        count: Number of alerts of this type.
        unresolved_count: Number still unresolved.
        most_recent: Most recent alert timestamp.
        highest_severity: Highest severity seen.
    """

    alert_type: str
    count: int
    unresolved_count: int
    most_recent: datetime
    highest_severity: str


@dataclass
class MedicationSummary:
    """Summary of medication adherence.

    Attributes:
        medication_name: Name of the medication.
        dosage: Prescribed dosage.
        doses_expected: Expected doses in period.
        doses_taken: Confirmed doses taken.
        adherence_rate: Percentage of doses taken.
        last_dose: Timestamp of last confirmed dose.
    """

    medication_name: str
    dosage: str
    doses_expected: int
    doses_taken: int
    adherence_rate: float
    last_dose: Optional[datetime] = None


@dataclass
class HealthSummary:
    """Complete patient health summary.

    Attributes:
        patient_id: Patient identifier.
        generated_at: When the summary was generated.
        period_days: Number of days covered.
        risk_level: Overall risk assessment.
        risk_score: Numeric risk score (0-100).
        vitals: List of vital sign summaries.
        symptoms: List of symptom summaries.
        alerts: List of alert summaries.
        medications: List of medication adherence summaries.
        key_findings: Important observations.
        recommendations: Suggested actions.
    """

    patient_id: str
    generated_at: datetime
    period_days: int
    risk_level: RiskLevel
    risk_score: float
    vitals: List[VitalSummary] = field(default_factory=list)
    symptoms: List[SymptomSummary] = field(default_factory=list)
    alerts: List[AlertSummary] = field(default_factory=list)
    medications: List[MedicationSummary] = field(default_factory=list)
    key_findings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


# Normal ranges for vital signs
VITAL_RANGES = {
    "heart_rate": {"min": 60, "max": 100, "unit": "bpm"},
    "blood_pressure_systolic": {"min": 90, "max": 140, "unit": "mmHg"},
    "blood_pressure_diastolic": {"min": 60, "max": 90, "unit": "mmHg"},
    "temperature": {"min": 36.1, "max": 37.2, "unit": "°C"},
    "oxygen_saturation": {"min": 95, "max": 100, "unit": "%"},
    "respiratory_rate": {"min": 12, "max": 20, "unit": "breaths/min"},
}


class HealthSummaryGenerator:
    """Generates comprehensive health summaries for patients.

    This class aggregates patient data from various sources to create
    actionable health summaries for medical professionals.

    Example:
        >>> generator = HealthSummaryGenerator(db)
        >>> summary = await generator.generate_summary("patient_123", days=30)
        >>> print(f"Risk level: {summary.risk_level}")
    """

    def __init__(self, db: Any = None) -> None:
        """Initialize the summary generator.

        Args:
            db: Database connection/client for data retrieval.
        """
        self.db = db

    async def generate_summary(
        self,
        patient_id: str,
        days: int = 30,
    ) -> HealthSummary:
        """Generate a complete health summary for a patient.

        Args:
            patient_id: Patient identifier.
            days: Number of days to include in summary.

        Returns:
            HealthSummary with all aggregated data.
        """
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        # Generate sub-summaries
        vitals = await self._summarize_vitals(patient_id, start_date, end_date)
        symptoms = await self._summarize_symptoms(patient_id, start_date, end_date)
        alerts = await self._summarize_alerts(patient_id, start_date, end_date)
        medications = await self._summarize_medications(patient_id, start_date, end_date)

        # Calculate risk
        risk_score, risk_level = self._calculate_risk(vitals, symptoms, alerts)

        # Generate findings and recommendations
        findings = self._generate_findings(vitals, symptoms, alerts)
        recommendations = self._generate_recommendations(risk_level, vitals, symptoms)

        summary = HealthSummary(
            patient_id=patient_id,
            generated_at=datetime.now(timezone.utc),
            period_days=days,
            risk_level=risk_level,
            risk_score=risk_score,
            vitals=vitals,
            symptoms=symptoms,
            alerts=alerts,
            medications=medications,
            key_findings=findings,
            recommendations=recommendations,
        )

        logger.info(
            "health_summary_generated",
            patient_id=patient_id,
            risk_level=risk_level.value,
            days=days,
        )

        return summary

    async def _summarize_vitals(
        self,
        patient_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> List[VitalSummary]:
        """Summarize vital signs for the period.

        Args:
            patient_id: Patient identifier.
            start_date: Period start.
            end_date: Period end.

        Returns:
            List of vital sign summaries.
        """
        summaries = []

        # Simulated data retrieval - replace with actual DB query
        vital_data = await self._get_vitals_data(patient_id, start_date, end_date)

        for vital_name, readings in vital_data.items():
            if not readings:
                continue

            ranges = VITAL_RANGES.get(vital_name, {"min": 0, "max": 100, "unit": ""})
            values = [r["value"] for r in readings]

            # Count out of range
            out_of_range = sum(
                1
                for v in values
                if v < ranges["min"] or v > ranges["max"]
            )

            # Calculate trend
            trend = self._calculate_trend(values)

            summaries.append(
                VitalSummary(
                    name=vital_name,
                    unit=ranges["unit"],
                    min_value=min(values),
                    max_value=max(values),
                    avg_value=sum(values) / len(values),
                    latest_value=values[-1],
                    latest_timestamp=readings[-1]["timestamp"],
                    reading_count=len(readings),
                    trend=trend,
                    out_of_range_count=out_of_range,
                )
            )

        return summaries

    async def _summarize_symptoms(
        self,
        patient_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> List[SymptomSummary]:
        """Summarize reported symptoms for the period.

        Args:
            patient_id: Patient identifier.
            start_date: Period start.
            end_date: Period end.

        Returns:
            List of symptom summaries.
        """
        # Simulated data retrieval - replace with actual DB query
        symptom_data = await self._get_symptoms_data(patient_id, start_date, end_date)

        summaries = []
        symptom_groups: Dict[str, List[Dict]] = {}

        for entry in symptom_data:
            symptom = entry["description"].lower()
            if symptom not in symptom_groups:
                symptom_groups[symptom] = []
            symptom_groups[symptom].append(entry)

        for symptom, entries in symptom_groups.items():
            severities = [e["severity"] for e in entries if e.get("severity")]
            timestamps = [e["timestamp"] for e in entries]

            summaries.append(
                SymptomSummary(
                    symptom=symptom,
                    occurrences=len(entries),
                    avg_severity=sum(severities) / len(severities) if severities else 0.0,
                    max_severity=max(severities) if severities else 0,
                    first_reported=min(timestamps),
                    last_reported=max(timestamps),
                )
            )

        return sorted(summaries, key=lambda x: x.occurrences, reverse=True)

    async def _summarize_alerts(
        self,
        patient_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> List[AlertSummary]:
        """Summarize alerts for the period.

        Args:
            patient_id: Patient identifier.
            start_date: Period start.
            end_date: Period end.

        Returns:
            List of alert summaries.
        """
        # Simulated data retrieval - replace with actual DB query
        alert_data = await self._get_alerts_data(patient_id, start_date, end_date)

        summaries = []
        alert_groups: Dict[str, List[Dict]] = {}

        for alert in alert_data:
            alert_type = alert["alert_type"]
            if alert_type not in alert_groups:
                alert_groups[alert_type] = []
            alert_groups[alert_type].append(alert)

        severity_order = ["low", "medium", "high", "critical"]

        for alert_type, alerts in alert_groups.items():
            unresolved = sum(1 for a in alerts if not a.get("resolved", False))
            severities = [a.get("severity", "low") for a in alerts]
            highest = max(severities, key=lambda s: severity_order.index(s))

            summaries.append(
                AlertSummary(
                    alert_type=alert_type,
                    count=len(alerts),
                    unresolved_count=unresolved,
                    most_recent=max(a["timestamp"] for a in alerts),
                    highest_severity=highest,
                )
            )

        return sorted(summaries, key=lambda x: x.count, reverse=True)

    async def _summarize_medications(
        self,
        patient_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> List[MedicationSummary]:
        """Summarize medication adherence for the period.

        Args:
            patient_id: Patient identifier.
            start_date: Period start.
            end_date: Period end.

        Returns:
            List of medication summaries.
        """
        # Simulated - replace with actual DB query
        return []

    def _calculate_trend(self, values: List[float]) -> TrendDirection:
        """Calculate trend direction from a series of values.

        Args:
            values: List of values in chronological order.

        Returns:
            TrendDirection enum value.
        """
        if len(values) < 3:
            return TrendDirection.INSUFFICIENT_DATA

        # Simple trend: compare first and last thirds
        third = len(values) // 3
        first_avg = sum(values[:third]) / third
        last_avg = sum(values[-third:]) / third

        diff_pct = ((last_avg - first_avg) / first_avg) * 100 if first_avg != 0 else 0

        if abs(diff_pct) < 5:
            return TrendDirection.STABLE
        elif diff_pct > 0:
            return TrendDirection.WORSENING  # Higher values generally worse for vitals
        else:
            return TrendDirection.IMPROVING

    def _calculate_risk(
        self,
        vitals: List[VitalSummary],
        symptoms: List[SymptomSummary],
        alerts: List[AlertSummary],
    ) -> Tuple[float, RiskLevel]:
        """Calculate overall risk score and level.

        Args:
            vitals: Vital sign summaries.
            symptoms: Symptom summaries.
            alerts: Alert summaries.

        Returns:
            Tuple of (risk_score 0-100, RiskLevel).
        """
        score = 0.0

        # Vitals contribution (max 40 points)
        vital_score = 0.0
        for vital in vitals:
            if vital.out_of_range_count > 0:
                vital_score += min(vital.out_of_range_count * 2, 10)
            if vital.trend == TrendDirection.WORSENING:
                vital_score += 5
        score += min(vital_score, 40)

        # Symptoms contribution (max 30 points)
        symptom_score = 0.0
        for symptom in symptoms:
            symptom_score += min(symptom.avg_severity, 10) * (symptom.occurrences / 10)
        score += min(symptom_score, 30)

        # Alerts contribution (max 30 points)
        alert_score = 0.0
        severity_weights = {"low": 1, "medium": 2, "high": 5, "critical": 10}
        for alert in alerts:
            weight = severity_weights.get(alert.highest_severity, 1)
            alert_score += alert.unresolved_count * weight
        score += min(alert_score, 30)

        # Determine risk level
        if score >= 70:
            level = RiskLevel.CRITICAL
        elif score >= 50:
            level = RiskLevel.HIGH
        elif score >= 25:
            level = RiskLevel.MODERATE
        else:
            level = RiskLevel.LOW

        return min(score, 100), level

    def _generate_findings(
        self,
        vitals: List[VitalSummary],
        symptoms: List[SymptomSummary],
        alerts: List[AlertSummary],
    ) -> List[str]:
        """Generate key findings from the data.

        Args:
            vitals: Vital sign summaries.
            symptoms: Symptom summaries.
            alerts: Alert summaries.

        Returns:
            List of finding strings.
        """
        findings = []

        # Vital findings
        for vital in vitals:
            if vital.out_of_range_count > 0:
                findings.append(
                    f"{vital.name.replace('_', ' ').title()} out of range "
                    f"{vital.out_of_range_count} times in period"
                )
            if vital.trend == TrendDirection.WORSENING:
                findings.append(f"{vital.name.replace('_', ' ').title()} showing worsening trend")

        # Symptom findings
        for symptom in symptoms[:3]:  # Top 3
            if symptom.avg_severity >= 7:
                findings.append(
                    f"High severity {symptom.symptom} reported {symptom.occurrences} times"
                )

        # Alert findings
        unresolved_critical = sum(
            a.unresolved_count for a in alerts if a.highest_severity == "critical"
        )
        if unresolved_critical > 0:
            findings.append(f"{unresolved_critical} unresolved critical alerts")

        return findings

    def _generate_recommendations(
        self,
        risk_level: RiskLevel,
        vitals: List[VitalSummary],
        symptoms: List[SymptomSummary],
    ) -> List[str]:
        """Generate recommendations based on findings.

        Args:
            risk_level: Overall risk level.
            vitals: Vital sign summaries.
            symptoms: Symptom summaries.

        Returns:
            List of recommendation strings.
        """
        recommendations = []

        if risk_level == RiskLevel.CRITICAL:
            recommendations.append("Immediate medical review recommended")
        elif risk_level == RiskLevel.HIGH:
            recommendations.append("Schedule follow-up within 24-48 hours")

        for vital in vitals:
            if vital.out_of_range_count > 3:
                recommendations.append(
                    f"Increase monitoring frequency for {vital.name.replace('_', ' ')}"
                )

        if any(s.avg_severity >= 7 for s in symptoms):
            recommendations.append("Review pain management plan")

        return recommendations

    # Placeholder data retrieval methods - implement with actual DB queries
    async def _get_vitals_data(
        self,
        patient_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, List[Dict]]:
        """Retrieve vitals data from database. Override in production."""
        return {}

    async def _get_symptoms_data(
        self,
        patient_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Dict]:
        """Retrieve symptoms data from database. Override in production."""
        return []

    async def _get_alerts_data(
        self,
        patient_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Dict]:
        """Retrieve alerts data from database. Override in production."""
        return []


def format_summary_text(summary: HealthSummary) -> str:
    """Format a health summary as readable text.

    Args:
        summary: HealthSummary to format.

    Returns:
        Formatted text summary.
    """
    lines = [
        f"Health Summary - Patient {summary.patient_id}",
        f"Generated: {summary.generated_at.strftime('%Y-%m-%d %H:%M UTC')}",
        f"Period: Last {summary.period_days} days",
        "",
        f"Risk Level: {summary.risk_level.value.upper()} (Score: {summary.risk_score:.0f}/100)",
        "",
    ]

    if summary.key_findings:
        lines.append("Key Findings:")
        for finding in summary.key_findings:
            lines.append(f"  • {finding}")
        lines.append("")

    if summary.recommendations:
        lines.append("Recommendations:")
        for rec in summary.recommendations:
            lines.append(f"  • {rec}")
        lines.append("")

    if summary.vitals:
        lines.append("Vital Signs:")
        for vital in summary.vitals:
            lines.append(
                f"  • {vital.name}: {vital.latest_value} {vital.unit} "
                f"(avg: {vital.avg_value:.1f}, trend: {vital.trend.value})"
            )
        lines.append("")

    if summary.alerts:
        lines.append("Alerts Summary:")
        for alert in summary.alerts:
            lines.append(
                f"  • {alert.alert_type}: {alert.count} total, "
                f"{alert.unresolved_count} unresolved"
            )

    return "\n".join(lines)
