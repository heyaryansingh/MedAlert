"""Medication adherence analytics and tracking utilities.

This module provides comprehensive medication adherence monitoring including
pattern analysis, streak tracking, and predictive adherence scoring.

Typical usage:
    >>> from backend.utils.adherence_analytics import (
    ...     calculate_adherence_rate,
    ...     analyze_adherence_patterns,
    ...     predict_adherence_risk
    ... )
    >>> rate = calculate_adherence_rate(medication_logs, target_doses=30)
    >>> patterns = analyze_adherence_patterns(medication_logs)
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
from pydantic import BaseModel


class MedicationLog(BaseModel):
    """Model for medication intake log entry."""

    medication_id: str
    medication_name: str
    timestamp: datetime
    taken: bool
    dose_amount: Optional[float] = None
    scheduled_time: Optional[datetime] = None
    reason_skipped: Optional[str] = None


class AdherenceMetrics(BaseModel):
    """Comprehensive adherence metrics for a medication."""

    medication_id: str
    medication_name: str
    adherence_rate: float
    total_doses_prescribed: int
    total_doses_taken: int
    total_doses_missed: int
    current_streak: int
    longest_streak: int
    avg_delay_minutes: float
    on_time_rate: float
    days_analyzed: int
    risk_score: float


def calculate_adherence_rate(
    logs: List[MedicationLog],
    target_doses: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> float:
    """Calculate medication adherence rate (MPR - Medication Possession Ratio).

    Args:
        logs: List of medication log entries.
        target_doses: Expected number of doses in period (if None, uses scheduled doses).
        start_date: Start date for calculation (if None, uses first log).
        end_date: End date for calculation (if None, uses last log).

    Returns:
        Adherence rate as percentage (0-100). Values >= 80% are considered good adherence.

    Example:
        >>> rate = calculate_adherence_rate(logs, target_doses=30)
        >>> print(f"Adherence: {rate:.1f}%")
    """
    if not logs:
        return 0.0

    # Filter by date range
    filtered_logs = logs
    if start_date:
        filtered_logs = [log for log in filtered_logs if log.timestamp >= start_date]
    if end_date:
        filtered_logs = [log for log in filtered_logs if log.timestamp <= end_date]

    if not filtered_logs:
        return 0.0

    doses_taken = sum(1 for log in filtered_logs if log.taken)

    # Use target doses if provided, otherwise use total logs as denominator
    if target_doses is not None:
        denominator = target_doses
    else:
        denominator = len(filtered_logs)

    if denominator == 0:
        return 0.0

    adherence_rate = (doses_taken / denominator) * 100.0
    return min(adherence_rate, 100.0)  # Cap at 100%


def analyze_adherence_patterns(
    logs: List[MedicationLog],
    window_days: int = 30,
) -> Dict[str, any]:
    """Analyze medication adherence patterns and identify trends.

    Args:
        logs: List of medication log entries.
        window_days: Number of days to analyze for patterns.

    Returns:
        Dictionary containing:
        - day_of_week_adherence: Adherence rate by day of week
        - time_of_day_adherence: Adherence rate by time of day (morning/afternoon/evening/night)
        - weekly_trend: Adherence rate for each week in the analysis window
        - missed_dose_reasons: Frequency count of reasons for missed doses

    Example:
        >>> patterns = analyze_adherence_patterns(logs)
        >>> print(f"Best day: {max(patterns['day_of_week_adherence'].items(), key=lambda x: x[1])}")
    """
    if not logs:
        return {
            "day_of_week_adherence": {},
            "time_of_day_adherence": {},
            "weekly_trend": [],
            "missed_dose_reasons": {},
        }

    # Sort logs by timestamp
    sorted_logs = sorted(logs, key=lambda x: x.timestamp)

    # Filter to window
    cutoff_date = datetime.now() - timedelta(days=window_days)
    recent_logs = [log for log in sorted_logs if log.timestamp >= cutoff_date]

    if not recent_logs:
        return {
            "day_of_week_adherence": {},
            "time_of_day_adherence": {},
            "weekly_trend": [],
            "missed_dose_reasons": {},
        }

    # Day of week analysis
    day_stats = {i: {"taken": 0, "total": 0} for i in range(7)}
    for log in recent_logs:
        day = log.timestamp.weekday()
        day_stats[day]["total"] += 1
        if log.taken:
            day_stats[day]["taken"] += 1

    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_of_week_adherence = {
        day_names[day]: (
            (stats["taken"] / stats["total"] * 100) if stats["total"] > 0 else 0.0
        )
        for day, stats in day_stats.items()
    }

    # Time of day analysis
    time_buckets = {
        "morning": {"taken": 0, "total": 0},  # 6 AM - 12 PM
        "afternoon": {"taken": 0, "total": 0},  # 12 PM - 6 PM
        "evening": {"taken": 0, "total": 0},  # 6 PM - 10 PM
        "night": {"taken": 0, "total": 0},  # 10 PM - 6 AM
    }

    for log in recent_logs:
        hour = log.timestamp.hour
        if 6 <= hour < 12:
            bucket = "morning"
        elif 12 <= hour < 18:
            bucket = "afternoon"
        elif 18 <= hour < 22:
            bucket = "evening"
        else:
            bucket = "night"

        time_buckets[bucket]["total"] += 1
        if log.taken:
            time_buckets[bucket]["taken"] += 1

    time_of_day_adherence = {
        bucket: (
            (stats["taken"] / stats["total"] * 100) if stats["total"] > 0 else 0.0
        )
        for bucket, stats in time_buckets.items()
    }

    # Weekly trend
    weekly_stats = {}
    for log in recent_logs:
        week_start = log.timestamp - timedelta(days=log.timestamp.weekday())
        week_key = week_start.strftime("%Y-%m-%d")

        if week_key not in weekly_stats:
            weekly_stats[week_key] = {"taken": 0, "total": 0}

        weekly_stats[week_key]["total"] += 1
        if log.taken:
            weekly_stats[week_key]["taken"] += 1

    weekly_trend = [
        {
            "week_start": week,
            "adherence_rate": (
                (stats["taken"] / stats["total"] * 100) if stats["total"] > 0 else 0.0
            ),
        }
        for week, stats in sorted(weekly_stats.items())
    ]

    # Missed dose reasons
    missed_dose_reasons = {}
    for log in recent_logs:
        if not log.taken and log.reason_skipped:
            reason = log.reason_skipped
            missed_dose_reasons[reason] = missed_dose_reasons.get(reason, 0) + 1

    return {
        "day_of_week_adherence": day_of_week_adherence,
        "time_of_day_adherence": time_of_day_adherence,
        "weekly_trend": weekly_trend,
        "missed_dose_reasons": missed_dose_reasons,
    }


def calculate_streaks(logs: List[MedicationLog]) -> Tuple[int, int]:
    """Calculate current and longest adherence streaks.

    Args:
        logs: List of medication log entries, sorted by timestamp.

    Returns:
        Tuple of (current_streak, longest_streak) in days.

    Example:
        >>> current, longest = calculate_streaks(logs)
        >>> print(f"Current streak: {current} days, Best: {longest} days")
    """
    if not logs:
        return 0, 0

    sorted_logs = sorted(logs, key=lambda x: x.timestamp)

    current_streak = 0
    longest_streak = 0
    temp_streak = 0
    last_date = None

    for log in sorted_logs:
        log_date = log.timestamp.date()

        if log.taken:
            # Check if this is consecutive day
            if last_date is None or (log_date - last_date).days == 1:
                temp_streak += 1
            elif (log_date - last_date).days == 0:
                # Same-day dose (multi-dose regimen) doesn't extend or break the day streak
                pass
            else:
                # Streak broken
                longest_streak = max(longest_streak, temp_streak)
                temp_streak = 1

            last_date = log_date
            current_streak = temp_streak
        else:
            # Missed dose breaks streak
            longest_streak = max(longest_streak, temp_streak)
            temp_streak = 0
            current_streak = 0
            last_date = log_date

    longest_streak = max(longest_streak, temp_streak)

    return current_streak, longest_streak


def calculate_on_time_rate(
    logs: List[MedicationLog],
    tolerance_minutes: int = 30,
) -> float:
    """Calculate percentage of doses taken within tolerance window of scheduled time.

    Args:
        logs: List of medication log entries with scheduled_time set.
        tolerance_minutes: Minutes before/after scheduled time considered on-time.

    Returns:
        On-time rate as percentage (0-100).

    Example:
        >>> on_time = calculate_on_time_rate(logs, tolerance_minutes=15)
        >>> print(f"On-time rate: {on_time:.1f}%")
    """
    if not logs:
        return 0.0

    # Filter logs with scheduled time
    scheduled_logs = [log for log in logs if log.scheduled_time is not None and log.taken]

    if not scheduled_logs:
        return 0.0

    on_time_count = 0
    total_delays_minutes = 0

    for log in scheduled_logs:
        delay = abs((log.timestamp - log.scheduled_time).total_seconds() / 60)
        total_delays_minutes += delay

        if delay <= tolerance_minutes:
            on_time_count += 1

    on_time_rate = (on_time_count / len(scheduled_logs)) * 100.0
    return on_time_rate


def predict_adherence_risk(
    logs: List[MedicationLog],
    recent_window_days: int = 7,
) -> float:
    """Predict risk of non-adherence based on recent patterns.

    Uses multiple factors to compute a risk score:
    - Recent adherence trend
    - Streak length
    - Pattern consistency
    - Missed dose frequency

    Args:
        logs: List of medication log entries.
        recent_window_days: Number of recent days to emphasize in prediction.

    Returns:
        Risk score from 0 (low risk) to 100 (high risk).

    Example:
        >>> risk = predict_adherence_risk(logs)
        >>> if risk > 70:
        ...     print("High risk - intervention recommended")
    """
    if not logs:
        return 100.0  # No data = high risk

    sorted_logs = sorted(logs, key=lambda x: x.timestamp)

    # Factor 1: Recent adherence rate (50% weight)
    cutoff = datetime.now() - timedelta(days=recent_window_days)
    recent_logs = [log for log in sorted_logs if log.timestamp >= cutoff]

    if recent_logs:
        recent_taken = sum(1 for log in recent_logs if log.taken)
        recent_adherence = (recent_taken / len(recent_logs)) * 100
        recent_risk = 100 - recent_adherence
    else:
        recent_risk = 100.0

    # Factor 2: Streak status (25% weight)
    current_streak, _ = calculate_streaks(sorted_logs)
    streak_risk = 100 - min(current_streak * 10, 100)  # 10 day streak = 0 risk

    # Factor 3: Consistency/variance (25% weight)
    if len(recent_logs) >= 7:
        # Calculate daily adherence variance
        daily_adherence = []
        for i in range(recent_window_days):
            day_start = datetime.now() - timedelta(days=i + 1)
            day_end = day_start + timedelta(days=1)
            day_logs = [
                log
                for log in recent_logs
                if day_start <= log.timestamp < day_end
            ]
            if day_logs:
                day_rate = sum(1 for log in day_logs if log.taken) / len(day_logs)
                daily_adherence.append(day_rate)

        if daily_adherence:
            variance = np.std(daily_adherence) * 100
            consistency_risk = min(variance * 2, 100)  # High variance = high risk
        else:
            consistency_risk = 50.0
    else:
        consistency_risk = 50.0  # Not enough data

    # Compute weighted risk score
    risk_score = (
        recent_risk * 0.5 + streak_risk * 0.25 + consistency_risk * 0.25
    )

    return float(min(risk_score, 100.0))


def generate_adherence_report(
    logs: List[MedicationLog],
    medication_id: str,
    medication_name: str,
    analysis_days: int = 30,
) -> AdherenceMetrics:
    """Generate comprehensive adherence metrics report for a medication.

    Args:
        logs: List of medication log entries.
        medication_id: ID of the medication.
        medication_name: Name of the medication.
        analysis_days: Number of days to include in analysis.

    Returns:
        AdherenceMetrics object with comprehensive metrics.

    Example:
        >>> report = generate_adherence_report(logs, "MED001", "Metformin")
        >>> print(f"Adherence: {report.adherence_rate:.1f}%")
        >>> print(f"Risk Score: {report.risk_score:.1f}")
    """
    cutoff_date = datetime.now() - timedelta(days=analysis_days)
    filtered_logs = [log for log in logs if log.timestamp >= cutoff_date]

    if not filtered_logs:
        return AdherenceMetrics(
            medication_id=medication_id,
            medication_name=medication_name,
            adherence_rate=0.0,
            total_doses_prescribed=0,
            total_doses_taken=0,
            total_doses_missed=0,
            current_streak=0,
            longest_streak=0,
            avg_delay_minutes=0.0,
            on_time_rate=0.0,
            days_analyzed=0,
            risk_score=100.0,
        )

    # Calculate metrics
    adherence_rate = calculate_adherence_rate(filtered_logs)
    total_doses_prescribed = len(filtered_logs)
    total_doses_taken = sum(1 for log in filtered_logs if log.taken)
    total_doses_missed = total_doses_prescribed - total_doses_taken

    current_streak, longest_streak = calculate_streaks(filtered_logs)
    on_time_rate = calculate_on_time_rate(filtered_logs)

    # Average delay
    scheduled_logs = [
        log for log in filtered_logs if log.scheduled_time is not None and log.taken
    ]
    if scheduled_logs:
        delays = [
            abs((log.timestamp - log.scheduled_time).total_seconds() / 60)
            for log in scheduled_logs
        ]
        avg_delay_minutes = float(np.mean(delays))
    else:
        avg_delay_minutes = 0.0

    risk_score = predict_adherence_risk(filtered_logs, recent_window_days=7)

    return AdherenceMetrics(
        medication_id=medication_id,
        medication_name=medication_name,
        adherence_rate=adherence_rate,
        total_doses_prescribed=total_doses_prescribed,
        total_doses_taken=total_doses_taken,
        total_doses_missed=total_doses_missed,
        current_streak=current_streak,
        longest_streak=longest_streak,
        avg_delay_minutes=avg_delay_minutes,
        on_time_rate=on_time_rate,
        days_analyzed=analysis_days,
        risk_score=risk_score,
    )
