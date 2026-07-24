"""Medication refill prediction system for proactive pharmacy management.

This module uses consumption patterns and ML to predict when patients will need
medication refills, enabling proactive reminders and pharmacy coordination.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import statistics


class RefillUrgency(Enum):
    """Refill urgency levels."""
    IMMEDIATE = "immediate"  # < 3 days supply
    URGENT = "urgent"  # 3-7 days
    SOON = "soon"  # 7-14 days
    SCHEDULED = "scheduled"  # 14-30 days
    NOT_NEEDED = "not_needed"  # > 30 days


@dataclass
class MedicationSupply:
    """Current medication supply status."""
    medication_id: str
    medication_name: str
    current_quantity: int
    daily_dose: float
    days_supply: int
    last_refill_date: datetime
    refill_history: List[datetime]
    adherence_rate: float  # 0.0 - 1.0


@dataclass
class RefillPrediction:
    """Refill prediction result."""
    medication_id: str
    medication_name: str
    predicted_refill_date: datetime
    days_until_refill: int
    urgency: RefillUrgency
    confidence: float
    recommended_action: str
    estimated_quantity_needed: int


class RefillPredictor:
    """Intelligent medication refill prediction system."""

    def __init__(self, buffer_days: int = 5):
        """Initialize refill predictor.

        Args:
            buffer_days: Safety buffer for refill predictions
        """
        self.buffer_days = buffer_days

    def predict_refill(
        self,
        supply: MedicationSupply
    ) -> RefillPrediction:
        """Predict when medication refill will be needed.

        Args:
            supply: Current medication supply status

        Returns:
            RefillPrediction with predicted date and urgency
        """
        # Calculate effective daily consumption based on adherence
        effective_daily_dose = supply.daily_dose * supply.adherence_rate

        # Calculate days until supply runs out
        if effective_daily_dose > 0:
            days_remaining = supply.current_quantity / effective_daily_dose
        else:
            # Zero consumption (e.g. adherence_rate == 0): cap instead of inf
            # so date arithmetic below stays valid
            days_remaining = 365.0

        # Adjust for historical consumption patterns
        if len(supply.refill_history) >= 2:
            avg_refill_interval = self._calculate_avg_refill_interval(
                supply.refill_history
            )
            days_since_last_refill = (datetime.now() - supply.last_refill_date).days

            # Weight historical pattern with current calculation
            days_remaining = (days_remaining * 0.7) + \
                           ((avg_refill_interval - days_since_last_refill) * 0.3)

        # Apply safety buffer
        days_until_refill = max(0, days_remaining - self.buffer_days)

        # Calculate predicted refill date
        predicted_date = datetime.now() + timedelta(days=days_until_refill)

        # Determine urgency
        urgency = self._classify_urgency(days_until_refill)

        # Calculate confidence based on data quality
        confidence = self._calculate_confidence(supply)

        # Generate recommendation
        recommendation = self._generate_recommendation(urgency, days_until_refill)

        # Estimate quantity needed (30-day supply typical)
        estimated_quantity = int(supply.daily_dose * 30)

        return RefillPrediction(
            medication_id=supply.medication_id,
            medication_name=supply.medication_name,
            predicted_refill_date=predicted_date,
            days_until_refill=int(days_until_refill),
            urgency=urgency,
            confidence=confidence,
            recommended_action=recommendation,
            estimated_quantity_needed=estimated_quantity
        )

    def predict_batch(
        self,
        supplies: List[MedicationSupply]
    ) -> List[RefillPrediction]:
        """Predict refills for multiple medications.

        Args:
            supplies: List of medication supply statuses

        Returns:
            List of refill predictions sorted by urgency
        """
        predictions = [self.predict_refill(supply) for supply in supplies]

        # Sort by urgency and days until refill
        urgency_order = {
            RefillUrgency.IMMEDIATE: 0,
            RefillUrgency.URGENT: 1,
            RefillUrgency.SOON: 2,
            RefillUrgency.SCHEDULED: 3,
            RefillUrgency.NOT_NEEDED: 4
        }

        predictions.sort(
            key=lambda p: (urgency_order[p.urgency], p.days_until_refill)
        )

        return predictions

    def identify_refill_conflicts(
        self,
        predictions: List[RefillPrediction]
    ) -> List[Dict]:
        """Identify medications needing refill at similar times.

        Args:
            predictions: List of refill predictions

        Returns:
            List of refill conflicts with consolidation opportunities
        """
        conflicts = []

        # Group by predicted date (within 3 days)
        for i, pred1 in enumerate(predictions):
            cluster = [pred1]

            for pred2 in predictions[i+1:]:
                days_diff = abs((pred1.predicted_refill_date -
                               pred2.predicted_refill_date).days)

                if days_diff <= 3:
                    cluster.append(pred2)

            if len(cluster) > 1:
                conflicts.append({
                    'refill_date': pred1.predicted_refill_date,
                    'medications': [p.medication_name for p in cluster],
                    'count': len(cluster),
                    'recommendation': 'Consolidate refills to reduce pharmacy visits'
                })

        return conflicts

    def calculate_cost_optimization(
        self,
        predictions: List[RefillPrediction],
        bulk_discount_threshold: int = 3
    ) -> Dict:
        """Calculate potential cost savings from consolidating refills.

        Args:
            predictions: Refill predictions
            bulk_discount_threshold: Number of meds for bulk discount

        Returns:
            Cost optimization analysis
        """
        # Identify near-term refills (within 30 days)
        near_term = [p for p in predictions if p.days_until_refill <= 30]

        # Estimate delivery fees
        individual_delivery_cost = len(near_term) * 5.99  # $5.99 per delivery

        # Consolidated delivery cost (1-2 deliveries)
        consolidated_deliveries = max(1, len(near_term) // bulk_discount_threshold)
        consolidated_cost = consolidated_deliveries * 5.99

        savings = individual_delivery_cost - consolidated_cost

        return {
            'total_refills': len(near_term),
            'individual_delivery_cost': individual_delivery_cost,
            'consolidated_cost': consolidated_cost,
            'potential_savings': savings,
            'recommended_deliveries': consolidated_deliveries
        }

    def detect_adherence_issues(
        self,
        supply: MedicationSupply,
        threshold: float = 0.8
    ) -> Optional[Dict]:
        """Detect potential adherence issues affecting refill timing.

        Args:
            supply: Medication supply status
            threshold: Minimum acceptable adherence rate

        Returns:
            Adherence issue details if detected
        """
        if supply.adherence_rate < threshold:
            # Calculate impact
            ideal_consumption = supply.daily_dose * \
                              (datetime.now() - supply.last_refill_date).days
            starting_quantity = supply.daily_dose * supply.days_supply
            actual_consumption = starting_quantity - supply.current_quantity
            missed_doses = ideal_consumption - actual_consumption

            return {
                'medication': supply.medication_name,
                'adherence_rate': supply.adherence_rate,
                'missed_doses_estimate': int(missed_doses),
                'concern_level': 'high' if supply.adherence_rate < 0.5 else 'moderate',
                'recommendation': 'Schedule adherence counseling session'
            }

        return None

    def _calculate_avg_refill_interval(
        self,
        refill_history: List[datetime]
    ) -> float:
        """Calculate average days between refills."""
        if len(refill_history) < 2:
            return 30.0  # Default to 30 days

        intervals = []
        for i in range(1, len(refill_history)):
            interval = (refill_history[i] - refill_history[i-1]).days
            intervals.append(interval)

        return statistics.mean(intervals)

    def _classify_urgency(self, days_until_refill: float) -> RefillUrgency:
        """Classify refill urgency based on days remaining."""
        if days_until_refill < 3:
            return RefillUrgency.IMMEDIATE
        elif days_until_refill < 7:
            return RefillUrgency.URGENT
        elif days_until_refill < 14:
            return RefillUrgency.SOON
        elif days_until_refill < 30:
            return RefillUrgency.SCHEDULED
        else:
            return RefillUrgency.NOT_NEEDED

    def _calculate_confidence(self, supply: MedicationSupply) -> float:
        """Calculate prediction confidence based on data quality."""
        confidence = 1.0

        # Reduce confidence if limited refill history
        if len(supply.refill_history) < 2:
            confidence *= 0.7
        elif len(supply.refill_history) < 5:
            confidence *= 0.85

        # Reduce confidence for poor adherence (less predictable)
        if supply.adherence_rate < 0.7:
            confidence *= 0.8

        # Reduce confidence for recent medication (< 60 days)
        if supply.refill_history:
            days_since_start = (datetime.now() - supply.refill_history[0]).days
        else:
            days_since_start = (datetime.now() - supply.last_refill_date).days
        if days_since_start < 60:
            confidence *= 0.75

        return round(confidence, 2)

    def _generate_recommendation(
        self,
        urgency: RefillUrgency,
        days_until_refill: int
    ) -> str:
        """Generate actionable recommendation based on urgency."""
        recommendations = {
            RefillUrgency.IMMEDIATE: (
                f"Refill immediately. Only {days_until_refill} days supply remaining. "
                "Contact pharmacy now to avoid running out."
            ),
            RefillUrgency.URGENT: (
                f"Schedule refill within 2 days. {days_until_refill} days supply left. "
                "Order now to ensure timely delivery."
            ),
            RefillUrgency.SOON: (
                f"Plan refill soon. {days_until_refill} days supply remaining. "
                "Add to next pharmacy order or delivery."
            ),
            RefillUrgency.SCHEDULED: (
                f"Refill scheduled in {days_until_refill} days. "
                "No immediate action needed. Monitor supply."
            ),
            RefillUrgency.NOT_NEEDED: (
                "Adequate supply. No refill needed at this time."
            )
        }

        return recommendations[urgency]


def generate_refill_calendar(
    predictions: List[RefillPrediction],
    days_ahead: int = 90
) -> Dict[str, List[RefillPrediction]]:
    """Generate refill calendar for planning.

    Args:
        predictions: Refill predictions
        days_ahead: Number of days to project

    Returns:
        Dictionary mapping dates to medications needing refill
    """
    calendar = {}

    cutoff_date = datetime.now() + timedelta(days=days_ahead)

    for pred in predictions:
        if pred.predicted_refill_date <= cutoff_date:
            date_key = pred.predicted_refill_date.strftime('%Y-%m-%d')

            if date_key not in calendar:
                calendar[date_key] = []

            calendar[date_key].append(pred)

    return calendar


def calculate_total_refill_burden(
    predictions: List[RefillPrediction]
) -> Dict:
    """Calculate overall refill management burden.

    Args:
        predictions: Refill predictions

    Returns:
        Burden analysis metrics
    """
    # Count by urgency
    urgency_counts = {}
    for urgency in RefillUrgency:
        urgency_counts[urgency.value] = sum(
            1 for p in predictions if p.urgency == urgency
        )

    # Calculate monthly refill frequency
    monthly_refills = sum(1 for p in predictions if p.days_until_refill <= 30)

    # Average confidence
    avg_confidence = statistics.mean([p.confidence for p in predictions]) \
                    if predictions else 0

    return {
        'total_medications': len(predictions),
        'monthly_refills': monthly_refills,
        'urgency_breakdown': urgency_counts,
        'average_confidence': round(avg_confidence, 2),
        'management_complexity': 'high' if monthly_refills > 5 else
                                'moderate' if monthly_refills > 2 else 'low'
    }
