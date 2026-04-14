"""Emergency contact management and alert system.

This module provides utilities for managing emergency contacts and
triggering alerts during critical health situations.

Features:
- Emergency contact registry with priority levels
- Alert triggering based on vital sign thresholds
- Contact notification history tracking
- Escalation chain management
- Multi-channel contact methods (SMS, email, call placeholders)

Example:
    >>> from utils.emergency_contact import EmergencyContactManager
    >>> manager = EmergencyContactManager()
    >>> manager.add_contact("Dr. Smith", "555-1234", priority=1, relationship="Primary Physician")
    >>> manager.trigger_alert("critical", "Heart rate critically high: 180 bpm")
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional


class ContactMethod(Enum):
    """Available methods for contacting emergency contacts."""

    SMS = "sms"
    EMAIL = "email"
    PHONE_CALL = "phone_call"
    PUSH_NOTIFICATION = "push"


class AlertSeverity(Enum):
    """Severity levels for emergency alerts."""

    INFO = "info"
    WARNING = "warning"
    URGENT = "urgent"
    CRITICAL = "critical"


@dataclass
class EmergencyContact:
    """Represents an emergency contact.

    Attributes:
        name: Contact's full name.
        phone: Primary phone number.
        email: Email address (optional).
        relationship: Relationship to patient (e.g., "Spouse", "Doctor").
        priority: Contact priority (1 = highest priority, contacted first).
        preferred_method: Preferred contact method.
        is_medical_professional: Whether this contact is a healthcare provider.
        notes: Additional notes about the contact.
        created_at: When the contact was added.
    """

    name: str
    phone: str
    email: Optional[str] = None
    relationship: str = "Emergency Contact"
    priority: int = 5
    preferred_method: ContactMethod = ContactMethod.PHONE_CALL
    is_medical_professional: bool = False
    notes: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class AlertNotification:
    """Record of an alert notification sent to a contact.

    Attributes:
        contact_name: Name of the contacted person.
        method: How they were contacted.
        severity: Severity level of the alert.
        message: Alert message content.
        sent_at: When the notification was sent.
        acknowledged: Whether the contact acknowledged receipt.
        acknowledged_at: When they acknowledged (if applicable).
    """

    contact_name: str
    method: ContactMethod
    severity: AlertSeverity
    message: str
    sent_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None


class EmergencyContactManager:
    """Manages emergency contacts and alert notifications.

    Provides methods for adding, removing, and organizing emergency contacts,
    as well as triggering alerts and tracking notification history.

    Example:
        >>> manager = EmergencyContactManager()
        >>> manager.add_contact("Jane Doe", "555-0100", relationship="Spouse", priority=1)
        >>> manager.add_contact("Dr. Johnson", "555-0200", relationship="Cardiologist",
        ...                     priority=2, is_medical_professional=True)
        >>> contacts = manager.get_contacts_by_priority()
    """

    def __init__(self) -> None:
        """Initialize the emergency contact manager."""
        self._contacts: Dict[str, EmergencyContact] = {}
        self._notification_history: List[AlertNotification] = []
        self._escalation_delay_seconds = 300  # 5 minutes between escalation levels

    def add_contact(
        self,
        name: str,
        phone: str,
        email: Optional[str] = None,
        relationship: str = "Emergency Contact",
        priority: int = 5,
        preferred_method: ContactMethod = ContactMethod.PHONE_CALL,
        is_medical_professional: bool = False,
        notes: str = "",
    ) -> EmergencyContact:
        """Add a new emergency contact.

        Args:
            name: Contact's full name.
            phone: Primary phone number.
            email: Email address (optional).
            relationship: Relationship to patient.
            priority: Contact priority (1-10, lower = higher priority).
            preferred_method: How to contact them.
            is_medical_professional: Whether they're a healthcare provider.
            notes: Additional notes.

        Returns:
            The created EmergencyContact.

        Raises:
            ValueError: If phone number is invalid format.

        Example:
            >>> contact = manager.add_contact(
            ...     "Dr. Smith", "555-1234",
            ...     email="smith@hospital.org",
            ...     relationship="Primary Physician",
            ...     priority=1,
            ...     is_medical_professional=True
            ... )
        """
        # Basic phone validation
        cleaned_phone = "".join(c for c in phone if c.isdigit() or c == "+")
        if len(cleaned_phone) < 10:
            raise ValueError(f"Invalid phone number: {phone}")

        contact = EmergencyContact(
            name=name,
            phone=phone,
            email=email,
            relationship=relationship,
            priority=max(1, min(10, priority)),  # Clamp to 1-10
            preferred_method=preferred_method,
            is_medical_professional=is_medical_professional,
            notes=notes,
        )

        self._contacts[name] = contact
        return contact

    def remove_contact(self, name: str) -> bool:
        """Remove an emergency contact by name.

        Args:
            name: The contact's name to remove.

        Returns:
            True if removed, False if not found.
        """
        if name in self._contacts:
            del self._contacts[name]
            return True
        return False

    def get_contact(self, name: str) -> Optional[EmergencyContact]:
        """Get a contact by name.

        Args:
            name: The contact's name.

        Returns:
            The EmergencyContact or None if not found.
        """
        return self._contacts.get(name)

    def get_all_contacts(self) -> List[EmergencyContact]:
        """Get all emergency contacts.

        Returns:
            List of all EmergencyContact objects.
        """
        return list(self._contacts.values())

    def get_contacts_by_priority(self) -> List[EmergencyContact]:
        """Get contacts sorted by priority (highest priority first).

        Returns:
            List of contacts sorted by priority level.
        """
        return sorted(self._contacts.values(), key=lambda c: c.priority)

    def get_medical_professionals(self) -> List[EmergencyContact]:
        """Get only contacts who are medical professionals.

        Returns:
            List of healthcare provider contacts.
        """
        return [c for c in self._contacts.values() if c.is_medical_professional]

    def trigger_alert(
        self,
        severity: str | AlertSeverity,
        message: str,
        escalate: bool = True,
        max_contacts: int = 3,
    ) -> List[AlertNotification]:
        """Trigger an emergency alert to contacts.

        Sends notifications to contacts based on alert severity and
        contact priority. For critical alerts, contacts all high-priority
        contacts simultaneously.

        Args:
            severity: Alert severity level (string or AlertSeverity enum).
            message: Alert message to send.
            escalate: Whether to escalate through priority levels.
            max_contacts: Maximum number of contacts to alert.

        Returns:
            List of AlertNotification records for sent alerts.

        Example:
            >>> notifications = manager.trigger_alert(
            ...     "critical",
            ...     "Patient heart rate critically low: 35 bpm"
            ... )
            >>> print(f"Alerted {len(notifications)} contacts")
        """
        if isinstance(severity, str):
            severity = AlertSeverity(severity.lower())

        notifications = []
        contacts = self.get_contacts_by_priority()

        # For critical alerts, also include medical professionals
        if severity == AlertSeverity.CRITICAL:
            medical = self.get_medical_professionals()
            contacts = list(dict.fromkeys(medical + contacts))  # Dedupe, preserve order

        # Determine how many contacts to notify based on severity
        if severity == AlertSeverity.CRITICAL:
            contacts_to_notify = contacts[:max_contacts]
        elif severity == AlertSeverity.URGENT:
            contacts_to_notify = contacts[:2]
        else:
            contacts_to_notify = contacts[:1]

        # Send notifications
        for contact in contacts_to_notify:
            notification = self._send_notification(contact, severity, message)
            notifications.append(notification)
            self._notification_history.append(notification)

        return notifications

    def _send_notification(
        self,
        contact: EmergencyContact,
        severity: AlertSeverity,
        message: str,
    ) -> AlertNotification:
        """Send a notification to a single contact.

        This is a placeholder that would integrate with actual
        notification services (Twilio, SendGrid, etc.).

        Args:
            contact: The contact to notify.
            severity: Alert severity level.
            message: Message content.

        Returns:
            AlertNotification record.
        """
        # In production, this would call actual notification services
        # For now, we create a record of the intended notification

        notification = AlertNotification(
            contact_name=contact.name,
            method=contact.preferred_method,
            severity=severity,
            message=message,
        )

        # Log the notification attempt (placeholder for actual sending)
        print(
            f"[ALERT] Sending {severity.value.upper()} alert to {contact.name} "
            f"via {contact.preferred_method.value}: {message[:50]}..."
        )

        return notification

    def acknowledge_alert(self, contact_name: str) -> bool:
        """Mark the most recent alert to a contact as acknowledged.

        Args:
            contact_name: Name of the contact acknowledging.

        Returns:
            True if an alert was acknowledged, False otherwise.
        """
        for notification in reversed(self._notification_history):
            if notification.contact_name == contact_name and not notification.acknowledged:
                notification.acknowledged = True
                notification.acknowledged_at = datetime.now(timezone.utc)
                return True
        return False

    def get_notification_history(
        self,
        contact_name: Optional[str] = None,
        severity: Optional[AlertSeverity] = None,
        limit: int = 50,
    ) -> List[AlertNotification]:
        """Get notification history with optional filters.

        Args:
            contact_name: Filter by contact name.
            severity: Filter by severity level.
            limit: Maximum records to return.

        Returns:
            List of AlertNotification records.
        """
        history = self._notification_history.copy()

        if contact_name:
            history = [n for n in history if n.contact_name == contact_name]

        if severity:
            history = [n for n in history if n.severity == severity]

        # Return most recent first
        return sorted(history, key=lambda n: n.sent_at, reverse=True)[:limit]


def check_vital_thresholds_and_alert(
    manager: EmergencyContactManager,
    vital_type: str,
    value: float,
    patient_name: str = "Patient",
) -> Optional[List[AlertNotification]]:
    """Check vital signs against thresholds and trigger alerts if needed.

    Evaluates vital sign values against predefined critical and warning
    thresholds and automatically triggers appropriate alerts.

    Args:
        manager: The EmergencyContactManager to use for alerts.
        vital_type: Type of vital sign (heart_rate, blood_pressure_systolic,
                    blood_pressure_diastolic, oxygen_saturation, temperature).
        value: The vital sign value to check.
        patient_name: Name of the patient for the alert message.

    Returns:
        List of AlertNotifications if alert was triggered, None otherwise.

    Example:
        >>> notifications = check_vital_thresholds_and_alert(
        ...     manager, "heart_rate", 185, "John Doe"
        ... )
    """
    # Define thresholds: (critical_low, warning_low, warning_high, critical_high)
    thresholds: Dict[str, tuple] = {
        "heart_rate": (40, 50, 100, 150),
        "blood_pressure_systolic": (70, 90, 140, 180),
        "blood_pressure_diastolic": (40, 50, 90, 110),
        "oxygen_saturation": (85, 92, 100, 100),  # Can't be too high
        "temperature": (95.0, 96.8, 99.5, 103.0),  # In Fahrenheit
        "respiratory_rate": (8, 12, 20, 30),
    }

    if vital_type not in thresholds:
        return None

    critical_low, warning_low, warning_high, critical_high = thresholds[vital_type]
    vital_name = vital_type.replace("_", " ").title()

    # Check critical conditions first
    if value <= critical_low or value >= critical_high:
        condition = "critically low" if value <= critical_low else "critically high"
        message = f"{patient_name}: {vital_name} is {condition} at {value}"
        return manager.trigger_alert(AlertSeverity.CRITICAL, message)

    # Check warning conditions
    if value <= warning_low or value >= warning_high:
        condition = "below normal" if value <= warning_low else "above normal"
        message = f"{patient_name}: {vital_name} is {condition} at {value}"
        return manager.trigger_alert(AlertSeverity.WARNING, message)

    return None


def create_default_contact_list(manager: EmergencyContactManager) -> None:
    """Add placeholder contacts for demonstration purposes.

    Adds a set of example contacts that can be replaced with real
    contact information. Useful for testing and initial setup.

    Args:
        manager: The EmergencyContactManager to populate.
    """
    manager.add_contact(
        name="Primary Physician",
        phone="555-DOCTOR",
        email="doctor@example.com",
        relationship="Primary Care Physician",
        priority=1,
        is_medical_professional=True,
        preferred_method=ContactMethod.PHONE_CALL,
        notes="Call for any medical emergency",
    )

    manager.add_contact(
        name="Emergency Contact 1",
        phone="555-FAMILY",
        email="family@example.com",
        relationship="Spouse",
        priority=2,
        preferred_method=ContactMethod.SMS,
        notes="Primary family contact",
    )

    manager.add_contact(
        name="Emergency Contact 2",
        phone="555-BACKUP",
        relationship="Adult Child",
        priority=3,
        preferred_method=ContactMethod.PHONE_CALL,
        notes="Backup contact if spouse unavailable",
    )

    manager.add_contact(
        name="Specialist",
        phone="555-CARDIO",
        email="cardio@hospital.org",
        relationship="Cardiologist",
        priority=2,
        is_medical_professional=True,
        preferred_method=ContactMethod.PHONE_CALL,
        notes="Contact for heart-related emergencies",
    )
