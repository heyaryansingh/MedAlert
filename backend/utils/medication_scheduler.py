"""Medication reminder scheduling and dosage tracking utilities.

This module provides functionality for scheduling medication reminders,
calculating optimal dosing times, and tracking medication adherence.

Functions:
    calculate_dose_times: Generate optimal dosing schedule
    create_reminder_schedule: Build complete reminder calendar
    check_drug_interactions: Validate medication combinations
    calculate_adherence_rate: Compute medication adherence statistics
    get_next_dose: Determine next scheduled dose time

Example:
    >>> from backend.utils.medication_scheduler import calculate_dose_times
    >>> times = calculate_dose_times(frequency=3, wake_time="07:00", sleep_time="22:00")
    >>> print(times)  # ["07:00", "13:00", "19:00"]
"""

from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple


class DoseFrequency(str, Enum):
    """Standard medication dosing frequencies."""
    ONCE_DAILY = "once_daily"
    TWICE_DAILY = "twice_daily"
    THREE_TIMES_DAILY = "three_times_daily"
    FOUR_TIMES_DAILY = "four_times_daily"
    EVERY_8_HOURS = "every_8_hours"
    EVERY_12_HOURS = "every_12_hours"
    AS_NEEDED = "as_needed"
    WEEKLY = "weekly"


class MealTiming(str, Enum):
    """Medication timing relative to meals."""
    WITH_FOOD = "with_food"
    BEFORE_FOOD = "before_food"
    AFTER_FOOD = "after_food"
    EMPTY_STOMACH = "empty_stomach"
    NO_RESTRICTION = "no_restriction"


@dataclass
class Medication:
    """Medication definition with dosing requirements."""
    name: str
    dose_amount: str
    frequency: DoseFrequency
    meal_timing: MealTiming = MealTiming.NO_RESTRICTION
    specific_times: Optional[List[str]] = None
    notes: str = ""
    interaction_groups: List[str] = field(default_factory=list)


@dataclass
class ScheduledDose:
    """A scheduled medication dose."""
    medication_name: str
    scheduled_time: datetime
    dose_amount: str
    meal_timing: MealTiming
    taken: bool = False
    taken_at: Optional[datetime] = None
    notes: str = ""


@dataclass
class AdherenceStats:
    """Medication adherence statistics."""
    total_scheduled: int
    total_taken: int
    adherence_rate: float
    on_time_rate: float
    missed_doses: int
    late_doses: int
    streak_current: int
    streak_best: int


def parse_time(time_str: str) -> time:
    """Parse time string in HH:MM format."""
    parts = time_str.split(":")
    return time(int(parts[0]), int(parts[1]))


def format_time(t: time) -> str:
    """Format time object as HH:MM string."""
    return f"{t.hour:02d}:{t.minute:02d}"


def calculate_dose_times(
    frequency: int,
    wake_time: str = "07:00",
    sleep_time: str = "22:00",
    meal_timing: MealTiming = MealTiming.NO_RESTRICTION,
) -> List[str]:
    """Calculate optimal medication dosing times.

    Distributes doses evenly throughout waking hours, considering
    meal timing requirements.

    Args:
        frequency: Number of doses per day (1-6)
        wake_time: Wake time in HH:MM format
        sleep_time: Sleep time in HH:MM format
        meal_timing: Meal timing requirement

    Returns:
        List of dose times in HH:MM format

    Example:
        >>> times = calculate_dose_times(3, "07:00", "22:00")
        >>> print(times)
        ["07:00", "13:00", "19:00"]
    """
    if frequency < 1 or frequency > 6:
        raise ValueError("Frequency must be between 1 and 6 doses per day")

    wake = parse_time(wake_time)
    sleep = parse_time(sleep_time)

    # Calculate waking hours
    wake_minutes = wake.hour * 60 + wake.minute
    sleep_minutes = sleep.hour * 60 + sleep.minute

    if sleep_minutes <= wake_minutes:
        sleep_minutes += 24 * 60

    waking_minutes = sleep_minutes - wake_minutes

    # Standard meal times for meal-timed medications
    meal_times = {
        "breakfast": "08:00",
        "lunch": "12:30",
        "dinner": "18:30",
    }

    if frequency == 1:
        if meal_timing == MealTiming.WITH_FOOD:
            return [meal_times["breakfast"]]
        return [wake_time]

    # Distribute evenly throughout waking hours
    interval = waking_minutes // (frequency + 1)
    times = []

    for i in range(1, frequency + 1):
        minutes = wake_minutes + (interval * i)
        if minutes >= 24 * 60:
            minutes -= 24 * 60
        hours = minutes // 60
        mins = minutes % 60
        times.append(f"{hours:02d}:{mins:02d}")

    # Adjust for meal timing if applicable
    if meal_timing == MealTiming.WITH_FOOD and frequency <= 3:
        meal_list = list(meal_times.values())[:frequency]
        return meal_list

    return times


def create_reminder_schedule(
    medications: List[Medication],
    start_date: datetime,
    days: int = 7,
    wake_time: str = "07:00",
    sleep_time: str = "22:00",
) -> List[ScheduledDose]:
    """Create a complete medication reminder schedule.

    Generates scheduled doses for all medications over a specified period.

    Args:
        medications: List of medications to schedule
        start_date: Start date for the schedule
        days: Number of days to schedule (default: 7)
        wake_time: Daily wake time
        sleep_time: Daily sleep time

    Returns:
        List of ScheduledDose objects sorted by time

    Example:
        >>> meds = [Medication("Aspirin", "100mg", DoseFrequency.ONCE_DAILY)]
        >>> schedule = create_reminder_schedule(meds, datetime.now(), days=7)
    """
    schedule: List[ScheduledDose] = []

    frequency_map = {
        DoseFrequency.ONCE_DAILY: 1,
        DoseFrequency.TWICE_DAILY: 2,
        DoseFrequency.THREE_TIMES_DAILY: 3,
        DoseFrequency.FOUR_TIMES_DAILY: 4,
        DoseFrequency.EVERY_8_HOURS: 3,
        DoseFrequency.EVERY_12_HOURS: 2,
        DoseFrequency.WEEKLY: 1,
        DoseFrequency.AS_NEEDED: 0,
    }

    for med in medications:
        if med.frequency == DoseFrequency.AS_NEEDED:
            continue

        freq = frequency_map.get(med.frequency, 1)

        if med.specific_times:
            dose_times = med.specific_times
        else:
            dose_times = calculate_dose_times(
                freq, wake_time, sleep_time, med.meal_timing
            )

        day_interval = 7 if med.frequency == DoseFrequency.WEEKLY else 1

        current_date = start_date
        end_date = start_date + timedelta(days=days)

        while current_date < end_date:
            for dose_time in dose_times:
                t = parse_time(dose_time)
                scheduled_datetime = datetime.combine(current_date.date(), t)

                if scheduled_datetime >= start_date and scheduled_datetime < end_date:
                    schedule.append(
                        ScheduledDose(
                            medication_name=med.name,
                            scheduled_time=scheduled_datetime,
                            dose_amount=med.dose_amount,
                            meal_timing=med.meal_timing,
                            notes=med.notes,
                        )
                    )

            current_date += timedelta(days=day_interval)

    # Sort by scheduled time
    schedule.sort(key=lambda x: x.scheduled_time)
    return schedule


# Common drug interaction groups
INTERACTION_GROUPS = {
    "blood_thinners": ["warfarin", "aspirin", "heparin", "clopidogrel"],
    "nsaids": ["ibuprofen", "naproxen", "aspirin", "diclofenac"],
    "ace_inhibitors": ["lisinopril", "enalapril", "ramipril"],
    "potassium_sparing": ["spironolactone", "amiloride", "triamterene"],
    "statins": ["atorvastatin", "simvastatin", "rosuvastatin"],
    "antacids": ["omeprazole", "pantoprazole", "famotidine"],
    "ssri": ["fluoxetine", "sertraline", "paroxetine", "escitalopram"],
    "maoi": ["phenelzine", "tranylcypromine", "selegiline"],
}

# Known problematic combinations
INTERACTION_WARNINGS = [
    ({"blood_thinners", "nsaids"}, "high", "Increased bleeding risk"),
    ({"ace_inhibitors", "potassium_sparing"}, "high", "Risk of hyperkalemia"),
    ({"ssri", "maoi"}, "critical", "Serotonin syndrome risk"),
    ({"blood_thinners", "ssri"}, "medium", "Moderate bleeding risk increase"),
    ({"statins", "antacids"}, "low", "May reduce statin absorption"),
]


def check_drug_interactions(
    medications: List[Medication],
) -> List[Dict[str, str]]:
    """Check for potential drug interactions between medications.

    Args:
        medications: List of medications to check

    Returns:
        List of interaction warnings with severity and description

    Example:
        >>> meds = [
        ...     Medication("Warfarin", "5mg", DoseFrequency.ONCE_DAILY,
        ...                interaction_groups=["blood_thinners"]),
        ...     Medication("Ibuprofen", "400mg", DoseFrequency.THREE_TIMES_DAILY,
        ...                interaction_groups=["nsaids"])
        ... ]
        >>> warnings = check_drug_interactions(meds)
        >>> print(warnings[0]["severity"])
        "high"
    """
    warnings: List[Dict[str, str]] = []

    # Collect all interaction groups from medications
    all_groups: set = set()
    med_groups: Dict[str, List[str]] = {}

    for med in medications:
        med_groups[med.name] = med.interaction_groups
        all_groups.update(med.interaction_groups)

    # Check against known interactions
    for groups, severity, description in INTERACTION_WARNINGS:
        if groups.issubset(all_groups):
            # Find which medications are involved
            involved = []
            for med_name, med_group_list in med_groups.items():
                if any(g in groups for g in med_group_list):
                    involved.append(med_name)

            if len(involved) >= 2:
                warnings.append({
                    "medications": ", ".join(involved),
                    "severity": severity,
                    "description": description,
                    "recommendation": get_interaction_recommendation(severity),
                })

    return warnings


def get_interaction_recommendation(severity: str) -> str:
    """Get recommendation based on interaction severity."""
    recommendations = {
        "critical": "DO NOT combine these medications. Consult doctor immediately.",
        "high": "Use with extreme caution. Consult doctor before use.",
        "medium": "Monitor for side effects. Consider alternative timing.",
        "low": "Generally safe but monitor for reduced effectiveness.",
    }
    return recommendations.get(severity, "Consult your healthcare provider.")


def calculate_adherence_rate(
    doses: List[ScheduledDose],
    on_time_window_minutes: int = 60,
) -> AdherenceStats:
    """Calculate medication adherence statistics.

    Analyzes dose records to compute adherence metrics including
    on-time percentage and streak tracking.

    Args:
        doses: List of scheduled doses with taken status
        on_time_window_minutes: Window in minutes to consider "on time"

    Returns:
        AdherenceStats with computed metrics

    Example:
        >>> doses = [ScheduledDose(..., taken=True), ScheduledDose(..., taken=False)]
        >>> stats = calculate_adherence_rate(doses)
        >>> print(f"Adherence: {stats.adherence_rate:.1%}")
    """
    if not doses:
        return AdherenceStats(
            total_scheduled=0,
            total_taken=0,
            adherence_rate=0.0,
            on_time_rate=0.0,
            missed_doses=0,
            late_doses=0,
            streak_current=0,
            streak_best=0,
        )

    total = len(doses)
    taken = sum(1 for d in doses if d.taken)
    missed = total - taken

    # Calculate on-time doses
    on_time = 0
    late = 0
    window = timedelta(minutes=on_time_window_minutes)

    for dose in doses:
        if dose.taken and dose.taken_at:
            diff = abs(dose.taken_at - dose.scheduled_time)
            if diff <= window:
                on_time += 1
            else:
                late += 1

    # Calculate streaks
    streak_current = 0
    streak_best = 0
    current_streak = 0

    # Sort by time for streak calculation
    sorted_doses = sorted(doses, key=lambda x: x.scheduled_time)

    for dose in sorted_doses:
        if dose.taken:
            current_streak += 1
            streak_best = max(streak_best, current_streak)
        else:
            current_streak = 0

    # Current streak is from most recent
    for dose in reversed(sorted_doses):
        if dose.taken:
            streak_current += 1
        else:
            break

    adherence_rate = taken / total if total > 0 else 0.0
    on_time_rate = on_time / taken if taken > 0 else 0.0

    return AdherenceStats(
        total_scheduled=total,
        total_taken=taken,
        adherence_rate=adherence_rate,
        on_time_rate=on_time_rate,
        missed_doses=missed,
        late_doses=late,
        streak_current=streak_current,
        streak_best=streak_best,
    )


def get_next_dose(
    schedule: List[ScheduledDose],
    current_time: Optional[datetime] = None,
) -> Optional[ScheduledDose]:
    """Get the next scheduled dose that hasn't been taken.

    Args:
        schedule: List of scheduled doses
        current_time: Reference time (defaults to now)

    Returns:
        Next scheduled dose or None if all doses are complete

    Example:
        >>> next_dose = get_next_dose(schedule)
        >>> if next_dose:
        ...     print(f"Next: {next_dose.medication_name} at {next_dose.scheduled_time}")
    """
    if current_time is None:
        current_time = datetime.now()

    upcoming = [
        dose for dose in schedule
        if not dose.taken and dose.scheduled_time >= current_time
    ]

    if not upcoming:
        return None

    return min(upcoming, key=lambda x: x.scheduled_time)


def format_schedule_summary(
    schedule: List[ScheduledDose],
    date: Optional[datetime] = None,
) -> str:
    """Generate human-readable schedule summary for a day.

    Args:
        schedule: List of scheduled doses
        date: Date to summarize (defaults to today)

    Returns:
        Formatted multi-line summary string
    """
    if date is None:
        date = datetime.now()

    target_date = date.date()

    day_doses = [
        d for d in schedule
        if d.scheduled_time.date() == target_date
    ]

    if not day_doses:
        return f"No medications scheduled for {target_date}"

    lines = [f"=== Medication Schedule for {target_date} ===", ""]

    for dose in sorted(day_doses, key=lambda x: x.scheduled_time):
        time_str = dose.scheduled_time.strftime("%H:%M")
        status = "✓" if dose.taken else "○"

        meal_note = ""
        if dose.meal_timing == MealTiming.WITH_FOOD:
            meal_note = " (with food)"
        elif dose.meal_timing == MealTiming.EMPTY_STOMACH:
            meal_note = " (empty stomach)"

        lines.append(f"{status} {time_str} - {dose.medication_name} {dose.dose_amount}{meal_note}")

    taken = sum(1 for d in day_doses if d.taken)
    total = len(day_doses)
    lines.append("")
    lines.append(f"Progress: {taken}/{total} doses completed")

    return "\n".join(lines)
