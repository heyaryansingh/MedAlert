"""Appointment reminder utilities for MedAlert.

This module provides comprehensive appointment reminder functionality
including scheduling, notification generation, conflict detection,
and follow-up tracking.

Functions:
    generate_reminders: Create reminder notifications for appointments
    check_conflicts: Detect scheduling conflicts
    calculate_reminder_times: Determine when to send reminders
    format_appointment_message: Generate human-readable appointment details
    track_confirmation: Track patient confirmations and responses

Example:
    >>> from backend.utils.appointment_reminder import (
    ...     generate_reminders,
    ...     check_conflicts,
    ... )
    >>> appointment = {"date": "2024-04-15", "time": "10:00", "doctor": "Dr. Smith"}
    >>> reminders = generate_reminders(appointment)
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, List, Optional


class ReminderType(Enum):
    """Types of appointment reminders."""

    SMS = "sms"
    EMAIL = "email"
    PUSH = "push"
    IN_APP = "in_app"


class ReminderStatus(Enum):
    """Status of a reminder."""

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    ACKNOWLEDGED = "acknowledged"


class ConfirmationStatus(Enum):
    """Patient confirmation status."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    RESCHEDULED = "rescheduled"
    CANCELLED = "cancelled"
    NO_RESPONSE = "no_response"


@dataclass
class Appointment:
    """Represents a medical appointment.

    Attributes:
        id: Unique appointment identifier
        patient_id: Patient's unique identifier
        doctor_id: Doctor's unique identifier
        doctor_name: Doctor's display name
        scheduled_time: Appointment datetime
        duration_minutes: Expected duration in minutes
        appointment_type: Type of appointment (checkup, follow-up, etc.)
        location: Appointment location or clinic name
        notes: Additional notes for the appointment
        requires_preparation: Whether patient needs to prepare (fasting, etc.)
        preparation_instructions: Instructions if preparation needed
    """

    id: str
    patient_id: str
    doctor_id: str
    doctor_name: str
    scheduled_time: datetime
    duration_minutes: int = 30
    appointment_type: str = "checkup"
    location: str = ""
    notes: str = ""
    requires_preparation: bool = False
    preparation_instructions: str = ""


@dataclass
class Reminder:
    """Represents a scheduled reminder.

    Attributes:
        id: Unique reminder identifier
        appointment_id: Associated appointment ID
        reminder_type: How the reminder will be sent
        scheduled_time: When to send the reminder
        status: Current status of the reminder
        message: Reminder message content
        sent_at: When the reminder was actually sent
        acknowledged_at: When patient acknowledged the reminder
    """

    id: str
    appointment_id: str
    reminder_type: ReminderType
    scheduled_time: datetime
    status: ReminderStatus = ReminderStatus.PENDING
    message: str = ""
    sent_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None


@dataclass
class ConflictResult:
    """Result of conflict detection.

    Attributes:
        has_conflict: Whether a conflict was detected
        conflicting_appointments: List of conflicting appointment IDs
        conflict_type: Type of conflict (overlap, too_close, etc.)
        suggestion: Suggested alternative time if available
    """

    has_conflict: bool
    conflicting_appointments: List[str] = field(default_factory=list)
    conflict_type: str = ""
    suggestion: Optional[datetime] = None


def calculate_reminder_times(
    appointment_time: datetime,
    reminder_intervals: Optional[List[int]] = None,
) -> List[datetime]:
    """Calculate when reminders should be sent for an appointment.

    Args:
        appointment_time: The scheduled appointment datetime
        reminder_intervals: List of hours before appointment to send reminders.
            Defaults to [168, 24, 2] (1 week, 1 day, 2 hours before).

    Returns:
        List of datetime objects for when reminders should be sent.

    Example:
        >>> apt_time = datetime(2024, 4, 15, 10, 0, tzinfo=timezone.utc)
        >>> times = calculate_reminder_times(apt_time)
        >>> len(times)  # 3 reminders by default
        3
    """
    if reminder_intervals is None:
        # Default: 1 week, 1 day, 2 hours before
        reminder_intervals = [168, 24, 2]

    reminder_times = []
    now = datetime.now(timezone.utc)

    for hours_before in sorted(reminder_intervals, reverse=True):
        reminder_time = appointment_time - timedelta(hours=hours_before)
        # Only include reminders that are in the future
        if reminder_time > now:
            reminder_times.append(reminder_time)

    return reminder_times


def generate_reminders(
    appointment: Appointment,
    reminder_types: Optional[List[ReminderType]] = None,
    reminder_intervals: Optional[List[int]] = None,
) -> List[Reminder]:
    """Generate reminder objects for an appointment.

    Creates a set of reminders based on the appointment details,
    specified intervals, and communication channels.

    Args:
        appointment: The appointment to create reminders for
        reminder_types: Types of reminders to generate.
            Defaults to [PUSH, IN_APP].
        reminder_intervals: Hours before appointment for each reminder.

    Returns:
        List of Reminder objects ready to be scheduled.

    Example:
        >>> apt = Appointment(
        ...     id="apt-1",
        ...     patient_id="pat-1",
        ...     doctor_id="doc-1",
        ...     doctor_name="Dr. Smith",
        ...     scheduled_time=datetime(2024, 4, 15, 10, 0, tzinfo=timezone.utc)
        ... )
        >>> reminders = generate_reminders(apt)
    """
    if reminder_types is None:
        reminder_types = [ReminderType.PUSH, ReminderType.IN_APP]

    reminder_times = calculate_reminder_times(
        appointment.scheduled_time,
        reminder_intervals,
    )

    reminders = []
    reminder_count = 0

    for reminder_time in reminder_times:
        for reminder_type in reminder_types:
            reminder_count += 1
            message = format_appointment_message(
                appointment,
                reminder_time,
            )

            reminder = Reminder(
                id=f"{appointment.id}-rem-{reminder_count}",
                appointment_id=appointment.id,
                reminder_type=reminder_type,
                scheduled_time=reminder_time,
                message=message,
            )
            reminders.append(reminder)

    return reminders


def format_appointment_message(
    appointment: Appointment,
    reminder_time: datetime,
) -> str:
    """Generate a human-readable appointment reminder message.

    Creates a formatted message suitable for notifications,
    including key appointment details.

    Args:
        appointment: The appointment details
        reminder_time: When this reminder is being sent

    Returns:
        Formatted reminder message string.

    Example:
        >>> apt = Appointment(...)
        >>> message = format_appointment_message(apt, datetime.now())
    """
    time_until = appointment.scheduled_time - reminder_time

    # Format time remaining
    days = time_until.days
    hours = time_until.seconds // 3600

    if days > 0:
        time_str = f"in {days} day{'s' if days > 1 else ''}"
    elif hours > 0:
        time_str = f"in {hours} hour{'s' if hours > 1 else ''}"
    else:
        minutes = time_until.seconds // 60
        time_str = f"in {minutes} minute{'s' if minutes > 1 else ''}"

    # Format appointment time
    apt_time = appointment.scheduled_time.strftime("%A, %B %d at %I:%M %p")

    lines = [
        f"Appointment Reminder: Your appointment with {appointment.doctor_name} is {time_str}.",
        f"",
        f"When: {apt_time}",
        f"Type: {appointment.appointment_type.replace('_', ' ').title()}",
    ]

    if appointment.location:
        lines.append(f"Location: {appointment.location}")

    if appointment.requires_preparation:
        lines.append("")
        lines.append(f"Preparation required: {appointment.preparation_instructions}")

    lines.append("")
    lines.append("Reply CONFIRM to confirm or RESCHEDULE to change your appointment.")

    return "\n".join(lines)


def check_conflicts(
    new_appointment: Appointment,
    existing_appointments: List[Appointment],
    buffer_minutes: int = 15,
) -> ConflictResult:
    """Check for scheduling conflicts with existing appointments.

    Detects overlapping appointments or appointments that are too close
    together to be practical.

    Args:
        new_appointment: The proposed new appointment
        existing_appointments: List of existing appointments to check against
        buffer_minutes: Minimum gap required between appointments

    Returns:
        ConflictResult with conflict details and suggestions.

    Example:
        >>> existing = [Appointment(...)]
        >>> new_apt = Appointment(...)
        >>> result = check_conflicts(new_apt, existing)
        >>> if result.has_conflict:
        ...     print(f"Conflict with: {result.conflicting_appointments}")
    """
    new_start = new_appointment.scheduled_time
    new_end = new_start + timedelta(minutes=new_appointment.duration_minutes)

    conflicts = []
    conflict_type = ""

    for existing in existing_appointments:
        # Skip same appointment (for updates)
        if existing.id == new_appointment.id:
            continue

        # Skip if different patient for the new appointment
        if existing.patient_id != new_appointment.patient_id:
            continue

        existing_start = existing.scheduled_time
        existing_end = existing_start + timedelta(minutes=existing.duration_minutes)

        # Check for overlap
        if new_start < existing_end and new_end > existing_start:
            conflicts.append(existing.id)
            conflict_type = "overlap"

        # Check if too close (within buffer)
        elif (
            abs((new_start - existing_end).total_seconds()) < buffer_minutes * 60
            or abs((existing_start - new_end).total_seconds()) < buffer_minutes * 60
        ):
            conflicts.append(existing.id)
            if not conflict_type:
                conflict_type = "too_close"

    if not conflicts:
        return ConflictResult(has_conflict=False)

    # Try to suggest an alternative time
    suggestion = find_next_available_slot(
        new_appointment,
        existing_appointments,
        buffer_minutes,
    )

    return ConflictResult(
        has_conflict=True,
        conflicting_appointments=conflicts,
        conflict_type=conflict_type,
        suggestion=suggestion,
    )


def find_next_available_slot(
    appointment: Appointment,
    existing_appointments: List[Appointment],
    buffer_minutes: int = 15,
    search_days: int = 7,
) -> Optional[datetime]:
    """Find the next available time slot for an appointment.

    Searches forward from the proposed time to find a gap
    that can accommodate the appointment.

    Args:
        appointment: The appointment needing a slot
        existing_appointments: Existing appointments to work around
        buffer_minutes: Required gap between appointments
        search_days: How many days ahead to search

    Returns:
        Next available datetime, or None if none found in search range.
    """
    proposed_start = appointment.scheduled_time
    duration = timedelta(minutes=appointment.duration_minutes)
    buffer = timedelta(minutes=buffer_minutes)
    search_end = proposed_start + timedelta(days=search_days)

    # Filter to relevant appointments (same patient)
    patient_appointments = [
        a for a in existing_appointments
        if a.patient_id == appointment.patient_id and a.id != appointment.id
    ]

    # Sort by start time
    patient_appointments.sort(key=lambda a: a.scheduled_time)

    # Start searching from proposed time
    candidate = proposed_start

    while candidate < search_end:
        candidate_end = candidate + duration

        # Check if this slot works
        is_available = True
        for existing in patient_appointments:
            existing_start = existing.scheduled_time
            existing_end = existing_start + timedelta(minutes=existing.duration_minutes)

            # Check for overlap including buffer
            if (
                candidate < existing_end + buffer
                and candidate_end + buffer > existing_start
            ):
                is_available = False
                # Jump to after this appointment
                candidate = existing_end + buffer
                break

        if is_available:
            # Check it's during reasonable hours (8am - 6pm)
            if 8 <= candidate.hour < 18:
                return candidate

        # Move to next potential slot
        candidate += timedelta(minutes=30)

    return None


def track_confirmation(
    appointment_id: str,
    response: str,
) -> Dict[str, str]:
    """Process and track patient confirmation response.

    Parses patient responses to reminders and returns
    appropriate actions and status updates.

    Args:
        appointment_id: The appointment being responded to
        response: Patient's response text

    Returns:
        Dictionary with status and action to take.

    Example:
        >>> result = track_confirmation("apt-1", "CONFIRM")
        >>> result["status"]
        'confirmed'
    """
    response_lower = response.strip().lower()

    if response_lower in ["confirm", "yes", "y", "confirmed"]:
        return {
            "status": ConfirmationStatus.CONFIRMED.value,
            "action": "mark_confirmed",
            "message": "Thank you for confirming your appointment!",
        }

    elif response_lower in ["reschedule", "change", "move"]:
        return {
            "status": ConfirmationStatus.RESCHEDULED.value,
            "action": "initiate_reschedule",
            "message": "We'll contact you shortly to reschedule your appointment.",
        }

    elif response_lower in ["cancel", "no", "n", "cancelled"]:
        return {
            "status": ConfirmationStatus.CANCELLED.value,
            "action": "cancel_appointment",
            "message": "Your appointment has been cancelled. Please call us to reschedule.",
        }

    else:
        return {
            "status": ConfirmationStatus.PENDING.value,
            "action": "need_clarification",
            "message": "We didn't understand your response. "
                       "Please reply CONFIRM, RESCHEDULE, or CANCEL.",
        }


def get_upcoming_appointments(
    patient_id: str,
    appointments: List[Appointment],
    days_ahead: int = 7,
) -> List[Appointment]:
    """Get a patient's upcoming appointments.

    Filters and sorts appointments for the specified time window.

    Args:
        patient_id: Patient to get appointments for
        appointments: List of all appointments
        days_ahead: How many days to look ahead

    Returns:
        List of upcoming appointments, sorted by time.
    """
    now = datetime.now(timezone.utc)
    cutoff = now + timedelta(days=days_ahead)

    upcoming = [
        apt for apt in appointments
        if apt.patient_id == patient_id
        and now <= apt.scheduled_time <= cutoff
    ]

    return sorted(upcoming, key=lambda a: a.scheduled_time)


def calculate_no_show_risk(
    patient_history: List[Dict],
    appointment: Appointment,
) -> Dict[str, float]:
    """Calculate risk of patient not showing up.

    Analyzes patient history to estimate no-show probability
    and recommend appropriate reminder frequency.

    Args:
        patient_history: List of past appointment records with status
        appointment: The upcoming appointment to assess

    Returns:
        Dictionary with risk score and recommendations.

    Example:
        >>> history = [{"status": "attended"}, {"status": "no_show"}]
        >>> risk = calculate_no_show_risk(history, apt)
        >>> print(f"No-show risk: {risk['risk_score']:.0%}")
    """
    if not patient_history:
        return {
            "risk_score": 0.2,  # Default moderate-low risk
            "confidence": "low",
            "recommended_reminders": 3,
            "recommend_call": False,
        }

    # Calculate no-show rate
    total = len(patient_history)
    no_shows = sum(
        1 for apt in patient_history
        if apt.get("status") == "no_show"
    )
    cancellations = sum(
        1 for apt in patient_history
        if apt.get("status") == "cancelled"
    )

    no_show_rate = no_shows / total if total > 0 else 0
    cancellation_rate = cancellations / total if total > 0 else 0

    # Adjust risk based on recent history (last 5 appointments)
    recent = patient_history[-5:]
    recent_no_shows = sum(
        1 for apt in recent if apt.get("status") == "no_show"
    )
    recent_factor = 1 + (recent_no_shows * 0.1)

    risk_score = min(1.0, (no_show_rate * 0.6 + cancellation_rate * 0.2) * recent_factor)

    return {
        "risk_score": risk_score,
        "confidence": "high" if total >= 5 else "medium" if total >= 2 else "low",
        "recommended_reminders": 5 if risk_score > 0.4 else 3 if risk_score > 0.2 else 2,
        "recommend_call": risk_score > 0.5,
    }
