"""Health Insights Generator - Generate actionable health insights from patient data.

Analyzes medication adherence, vital signs, symptoms, and lifestyle data to generate
personalized health insights, trend analysis, and recommendations.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import statistics


class InsightType(Enum):
    """Types of health insights."""
    POSITIVE_TREND = "positive_trend"
    NEGATIVE_TREND = "negative_trend"
    ACHIEVEMENT = "achievement"
    RISK_ALERT = "risk_alert"
    RECOMMENDATION = "recommendation"
    PATTERN_DETECTED = "pattern_detected"


class InsightPriority(Enum):
    """Priority levels for insights."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class HealthInsight:
    """Individual health insight."""
    insight_id: str
    patient_id: str
    insight_type: InsightType
    priority: InsightPriority
    title: str
    description: str
    data_source: str
    timestamp: datetime
    actionable: bool
    action_items: List[str]
    related_metrics: Dict[str, float]


@dataclass
class VitalSignReading:
    """Vital sign measurement."""
    reading_type: str  # blood_pressure, heart_rate, temperature, etc.
    value: float
    unit: str
    timestamp: datetime
    notes: Optional[str] = None


@dataclass
class MedicationAdherence:
    """Medication adherence record."""
    medication_name: str
    prescribed_doses: int
    taken_doses: int
    adherence_rate: float
    period_days: int


class HealthInsightsGenerator:
    """Generate personalized health insights from patient data."""

    def __init__(self):
        self.insights: List[HealthInsight] = []

        # Normal ranges for vital signs
        self.vital_ranges = {
            'systolic_bp': (90, 120),
            'diastolic_bp': (60, 80),
            'heart_rate': (60, 100),
            'temperature': (36.5, 37.5),
            'oxygen_saturation': (95, 100),
            'blood_glucose': (70, 140)
        }

    def analyze_vital_trends(
        self,
        patient_id: str,
        readings: List[VitalSignReading],
        days_back: int = 30
    ) -> List[HealthInsight]:
        """Analyze trends in vital signs.

        Args:
            patient_id: Patient identifier
            readings: List of vital sign readings
            days_back: Number of days to analyze

        Returns:
            List of generated insights
        """
        insights = []
        cutoff_date = datetime.now() - timedelta(days=days_back)

        # Group readings by type
        readings_by_type: Dict[str, List[VitalSignReading]] = {}
        for reading in readings:
            if reading.timestamp >= cutoff_date:
                if reading.reading_type not in readings_by_type:
                    readings_by_type[reading.reading_type] = []
                readings_by_type[reading.reading_type].append(reading)

        # Analyze each vital sign type
        for vital_type, vital_readings in readings_by_type.items():
            if len(vital_readings) < 3:
                continue  # Need at least 3 readings for trend analysis

            # Sort by timestamp
            vital_readings.sort(key=lambda x: x.timestamp)

            values = [r.value for r in vital_readings]
            timestamps = [r.timestamp for r in vital_readings]

            # Calculate trend (simple linear regression slope)
            n = len(values)
            x = list(range(n))
            x_mean = sum(x) / n
            y_mean = sum(values) / n

            numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
            denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

            slope = numerator / denominator if denominator != 0 else 0

            # Detect trend direction
            recent_avg = statistics.mean(values[-3:])
            earlier_avg = statistics.mean(values[:3])

            # Check if values are in normal range
            normal_range = self.vital_ranges.get(vital_type)
            if normal_range:
                in_range = all(normal_range[0] <= v <= normal_range[1] for v in values[-3:])

                if not in_range:
                    insights.append(HealthInsight(
                        insight_id=f"{patient_id}_{vital_type}_range_{datetime.now().timestamp()}",
                        patient_id=patient_id,
                        insight_type=InsightType.RISK_ALERT,
                        priority=InsightPriority.HIGH,
                        title=f"{vital_type.replace('_', ' ').title()} Out of Range",
                        description=f"Recent {vital_type.replace('_', ' ')} readings are outside normal range ({normal_range[0]}-{normal_range[1]}). Current average: {recent_avg:.1f}.",
                        data_source=vital_type,
                        timestamp=datetime.now(),
                        actionable=True,
                        action_items=[
                            "Consult with your healthcare provider",
                            "Monitor readings more frequently",
                            "Review medication adherence"
                        ],
                        related_metrics={
                            'current_average': recent_avg,
                            'normal_min': normal_range[0],
                            'normal_max': normal_range[1]
                        }
                    ))

            # Trend insights
            if abs(recent_avg - earlier_avg) > earlier_avg * 0.1:  # 10% change
                if recent_avg > earlier_avg:
                    trend_direction = "increasing"
                    insight_type = InsightType.NEGATIVE_TREND if normal_range and recent_avg > normal_range[1] else InsightType.PATTERN_DETECTED
                else:
                    trend_direction = "decreasing"
                    insight_type = InsightType.POSITIVE_TREND if normal_range and earlier_avg > normal_range[1] else InsightType.PATTERN_DETECTED

                change_pct = ((recent_avg - earlier_avg) / earlier_avg) * 100

                insights.append(HealthInsight(
                    insight_id=f"{patient_id}_{vital_type}_trend_{datetime.now().timestamp()}",
                    patient_id=patient_id,
                    insight_type=insight_type,
                    priority=InsightPriority.MEDIUM,
                    title=f"{vital_type.replace('_', ' ').title()} Trending {trend_direction.title()}",
                    description=f"Your {vital_type.replace('_', ' ')} has been {trend_direction} by {abs(change_pct):.1f}% over the past {days_back} days.",
                    data_source=vital_type,
                    timestamp=datetime.now(),
                    actionable=True,
                    action_items=[
                        "Continue monitoring",
                        "Discuss trend with doctor at next visit"
                    ],
                    related_metrics={
                        'earlier_average': earlier_avg,
                        'recent_average': recent_avg,
                        'change_percent': change_pct
                    }
                ))

        return insights

    def analyze_medication_adherence(
        self,
        patient_id: str,
        adherence_data: List[MedicationAdherence]
    ) -> List[HealthInsight]:
        """Analyze medication adherence patterns.

        Args:
            patient_id: Patient identifier
            adherence_data: List of adherence records

        Returns:
            List of generated insights
        """
        insights = []

        for adherence in adherence_data:
            # Perfect adherence
            if adherence.adherence_rate >= 0.95:
                insights.append(HealthInsight(
                    insight_id=f"{patient_id}_{adherence.medication_name}_perfect_{datetime.now().timestamp()}",
                    patient_id=patient_id,
                    insight_type=InsightType.ACHIEVEMENT,
                    priority=InsightPriority.LOW,
                    title=f"Excellent Adherence: {adherence.medication_name}",
                    description=f"You've maintained {adherence.adherence_rate*100:.1f}% adherence for {adherence.medication_name}. Keep up the great work!",
                    data_source="medication_adherence",
                    timestamp=datetime.now(),
                    actionable=False,
                    action_items=[],
                    related_metrics={
                        'adherence_rate': adherence.adherence_rate,
                        'doses_taken': adherence.taken_doses,
                        'doses_prescribed': adherence.prescribed_doses
                    }
                ))

            # Low adherence
            elif adherence.adherence_rate < 0.80:
                priority = InsightPriority.HIGH if adherence.adherence_rate < 0.60 else InsightPriority.MEDIUM

                insights.append(HealthInsight(
                    insight_id=f"{patient_id}_{adherence.medication_name}_low_{datetime.now().timestamp()}",
                    patient_id=patient_id,
                    insight_type=InsightType.RISK_ALERT,
                    priority=priority,
                    title=f"Low Adherence: {adherence.medication_name}",
                    description=f"Your adherence to {adherence.medication_name} is {adherence.adherence_rate*100:.1f}%. Missing doses may reduce medication effectiveness.",
                    data_source="medication_adherence",
                    timestamp=datetime.now(),
                    actionable=True,
                    action_items=[
                        "Set medication reminders",
                        "Use pill organizer",
                        "Discuss challenges with your doctor",
                        "Consider alternative dosing schedule"
                    ],
                    related_metrics={
                        'adherence_rate': adherence.adherence_rate,
                        'missed_doses': adherence.prescribed_doses - adherence.taken_doses
                    }
                ))

        return insights

    def detect_patterns(
        self,
        patient_id: str,
        symptom_logs: List[Dict[str, any]]
    ) -> List[HealthInsight]:
        """Detect patterns in symptom logs.

        Args:
            patient_id: Patient identifier
            symptom_logs: List of symptom log entries

        Returns:
            List of pattern insights
        """
        insights = []

        # Group symptoms by type
        symptom_counts: Dict[str, List[datetime]] = {}

        for log in symptom_logs:
            symptom = log.get('symptom_type')
            timestamp = log.get('timestamp')

            if symptom and timestamp:
                if symptom not in symptom_counts:
                    symptom_counts[symptom] = []
                symptom_counts[symptom].append(timestamp)

        # Detect recurring symptoms
        for symptom, occurrences in symptom_counts.items():
            if len(occurrences) >= 3:
                # Check for temporal patterns (e.g., weekly recurrence)
                occurrences.sort()
                intervals = [
                    (occurrences[i+1] - occurrences[i]).days
                    for i in range(len(occurrences) - 1)
                ]

                if intervals:
                    avg_interval = statistics.mean(intervals)

                    if 6 <= avg_interval <= 8:  # Weekly pattern
                        insights.append(HealthInsight(
                            insight_id=f"{patient_id}_{symptom}_pattern_{datetime.now().timestamp()}",
                            patient_id=patient_id,
                            insight_type=InsightType.PATTERN_DETECTED,
                            priority=InsightPriority.MEDIUM,
                            title=f"Recurring Pattern: {symptom.title()}",
                            description=f"{symptom.title()} appears to occur weekly. Reported {len(occurrences)} times with average interval of {avg_interval:.1f} days.",
                            data_source="symptom_logs",
                            timestamp=datetime.now(),
                            actionable=True,
                            action_items=[
                                "Track potential triggers (diet, stress, activities)",
                                "Discuss pattern with healthcare provider",
                                "Consider preventive measures before typical onset"
                            ],
                            related_metrics={
                                'occurrences': len(occurrences),
                                'average_interval_days': avg_interval
                            }
                        ))

        return insights

    def generate_recommendations(
        self,
        patient_id: str,
        health_score: float,
        risk_factors: List[str]
    ) -> List[HealthInsight]:
        """Generate personalized health recommendations.

        Args:
            patient_id: Patient identifier
            health_score: Overall health score (0-100)
            risk_factors: List of identified risk factors

        Returns:
            List of recommendation insights
        """
        insights = []

        # Based on health score
        if health_score < 60:
            insights.append(HealthInsight(
                insight_id=f"{patient_id}_improve_health_{datetime.now().timestamp()}",
                patient_id=patient_id,
                insight_type=InsightType.RECOMMENDATION,
                priority=InsightPriority.HIGH,
                title="Focus on Health Improvement",
                description=f"Your current health score is {health_score:.1f}/100. There's significant room for improvement.",
                data_source="health_score",
                timestamp=datetime.now(),
                actionable=True,
                action_items=[
                    "Improve medication adherence",
                    "Regular vital sign monitoring",
                    "Schedule check-up with healthcare provider",
                    "Address identified risk factors"
                ],
                related_metrics={'health_score': health_score}
            ))

        elif health_score >= 80:
            insights.append(HealthInsight(
                insight_id=f"{patient_id}_maintain_health_{datetime.now().timestamp()}",
                patient_id=patient_id,
                insight_type=InsightType.ACHIEVEMENT,
                priority=InsightPriority.LOW,
                title="Excellent Health Management",
                description=f"Your health score is {health_score:.1f}/100. You're doing great!",
                data_source="health_score",
                timestamp=datetime.now(),
                actionable=False,
                action_items=["Continue current health practices"],
                related_metrics={'health_score': health_score}
            ))

        # Risk factor specific recommendations
        for risk_factor in risk_factors:
            insights.append(HealthInsight(
                insight_id=f"{patient_id}_{risk_factor}_{datetime.now().timestamp()}",
                patient_id=patient_id,
                insight_type=InsightType.RECOMMENDATION,
                priority=InsightPriority.MEDIUM,
                title=f"Address Risk Factor: {risk_factor.title()}",
                description=f"You have an identified risk factor: {risk_factor}. Taking action can improve your health outcomes.",
                data_source="risk_assessment",
                timestamp=datetime.now(),
                actionable=True,
                action_items=self._get_risk_factor_actions(risk_factor),
                related_metrics={}
            ))

        return insights

    def _get_risk_factor_actions(self, risk_factor: str) -> List[str]:
        """Get action items for specific risk factors."""
        actions_map = {
            'hypertension': [
                "Monitor blood pressure daily",
                "Reduce sodium intake",
                "Engage in regular physical activity",
                "Take prescribed medications consistently"
            ],
            'diabetes': [
                "Monitor blood glucose levels",
                "Follow diabetic meal plan",
                "Take medications as prescribed",
                "Regular physical activity"
            ],
            'obesity': [
                "Consult with nutritionist",
                "Create exercise routine",
                "Track caloric intake",
                "Set realistic weight loss goals"
            ]
        }

        return actions_map.get(risk_factor.lower(), [
            "Consult with healthcare provider",
            "Research risk factor management",
            "Create action plan"
        ])

    def generate_all_insights(
        self,
        patient_id: str,
        vital_readings: List[VitalSignReading],
        adherence_data: List[MedicationAdherence],
        symptom_logs: List[Dict],
        health_score: float,
        risk_factors: List[str]
    ) -> Dict[str, List[HealthInsight]]:
        """Generate comprehensive insights from all data sources.

        Args:
            patient_id: Patient identifier
            vital_readings: Vital sign readings
            adherence_data: Medication adherence records
            symptom_logs: Symptom log entries
            health_score: Overall health score
            risk_factors: Identified risk factors

        Returns:
            Dictionary categorizing insights by type
        """
        all_insights = []

        all_insights.extend(self.analyze_vital_trends(patient_id, vital_readings))
        all_insights.extend(self.analyze_medication_adherence(patient_id, adherence_data))
        all_insights.extend(self.detect_patterns(patient_id, symptom_logs))
        all_insights.extend(self.generate_recommendations(patient_id, health_score, risk_factors))

        # Categorize by type
        categorized = {
            'critical': [i for i in all_insights if i.priority == InsightPriority.CRITICAL],
            'high_priority': [i for i in all_insights if i.priority == InsightPriority.HIGH],
            'medium_priority': [i for i in all_insights if i.priority == InsightPriority.MEDIUM],
            'low_priority': [i for i in all_insights if i.priority == InsightPriority.LOW],
            'achievements': [i for i in all_insights if i.insight_type == InsightType.ACHIEVEMENT],
            'recommendations': [i for i in all_insights if i.insight_type == InsightType.RECOMMENDATION]
        }

        return categorized
