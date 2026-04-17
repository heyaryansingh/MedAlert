"""Symptom checker and triage utilities.

This module provides symptom assessment and preliminary triage functionality
for patient self-reporting, including urgency scoring and care recommendations.

Features:
- Symptom severity assessment
- Red flag detection for emergency symptoms
- Preliminary triage scoring
- Related symptom suggestions
- Care level recommendations

Example:
    >>> from backend.utils.symptom_checker import SymptomChecker
    >>> checker = SymptomChecker()
    >>> result = checker.assess_symptoms(["chest pain", "shortness of breath"])
    >>> print(f"Urgency: {result.urgency_level}")
    >>> print(f"Recommendation: {result.recommendation}")
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple


class UrgencyLevel(Enum):
    """Urgency levels for symptom assessment."""

    EMERGENCY = "emergency"  # Call 911 / Go to ER immediately
    URGENT = "urgent"  # Seek care within hours
    SEMI_URGENT = "semi_urgent"  # Seek care within 24 hours
    ROUTINE = "routine"  # Schedule appointment
    SELF_CARE = "self_care"  # Can manage at home


class CareLevel(Enum):
    """Recommended care level."""

    EMERGENCY_ROOM = "emergency_room"
    URGENT_CARE = "urgent_care"
    PRIMARY_CARE = "primary_care"
    TELEHEALTH = "telehealth"
    SELF_CARE = "self_care"
    PHARMACY = "pharmacy"


@dataclass
class Symptom:
    """Represents a reported symptom."""

    name: str
    severity: int  # 1-10 scale
    duration_hours: Optional[float] = None
    is_new: bool = True
    is_worsening: bool = False
    associated_symptoms: List[str] = field(default_factory=list)


@dataclass
class AssessmentResult:
    """Result of symptom assessment."""

    urgency_level: UrgencyLevel
    care_level: CareLevel
    urgency_score: int  # 0-100, higher = more urgent
    red_flags: List[str]
    recommendation: str
    related_conditions: List[str]
    questions_to_ask: List[str]
    self_care_tips: List[str]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# Red flag symptoms requiring immediate attention
RED_FLAG_SYMPTOMS: Dict[str, UrgencyLevel] = {
    "chest pain": UrgencyLevel.EMERGENCY,
    "chest tightness": UrgencyLevel.EMERGENCY,
    "crushing chest pressure": UrgencyLevel.EMERGENCY,
    "difficulty breathing": UrgencyLevel.EMERGENCY,
    "shortness of breath": UrgencyLevel.URGENT,
    "severe shortness of breath": UrgencyLevel.EMERGENCY,
    "sudden severe headache": UrgencyLevel.EMERGENCY,
    "worst headache of life": UrgencyLevel.EMERGENCY,
    "sudden confusion": UrgencyLevel.EMERGENCY,
    "sudden numbness": UrgencyLevel.EMERGENCY,
    "facial drooping": UrgencyLevel.EMERGENCY,
    "arm weakness": UrgencyLevel.EMERGENCY,
    "speech difficulty": UrgencyLevel.EMERGENCY,
    "slurred speech": UrgencyLevel.EMERGENCY,
    "severe abdominal pain": UrgencyLevel.URGENT,
    "vomiting blood": UrgencyLevel.EMERGENCY,
    "blood in stool": UrgencyLevel.URGENT,
    "severe bleeding": UrgencyLevel.EMERGENCY,
    "uncontrolled bleeding": UrgencyLevel.EMERGENCY,
    "loss of consciousness": UrgencyLevel.EMERGENCY,
    "fainting": UrgencyLevel.URGENT,
    "seizure": UrgencyLevel.EMERGENCY,
    "severe allergic reaction": UrgencyLevel.EMERGENCY,
    "swelling of throat": UrgencyLevel.EMERGENCY,
    "difficulty swallowing": UrgencyLevel.URGENT,
    "high fever": UrgencyLevel.URGENT,
    "fever over 103": UrgencyLevel.URGENT,
    "stiff neck with fever": UrgencyLevel.EMERGENCY,
    "suicidal thoughts": UrgencyLevel.EMERGENCY,
    "thoughts of self-harm": UrgencyLevel.EMERGENCY,
}

# Symptom severity modifiers
SEVERITY_MODIFIERS: Dict[str, float] = {
    "severe": 1.5,
    "mild": 0.6,
    "moderate": 1.0,
    "sudden": 1.3,
    "persistent": 1.2,
    "recurring": 1.1,
    "worsening": 1.4,
    "chronic": 0.9,
}

# Related symptom clusters
SYMPTOM_CLUSTERS: Dict[str, Set[str]] = {
    "respiratory": {
        "cough", "shortness of breath", "wheezing", "chest congestion",
        "runny nose", "sore throat", "sneezing", "nasal congestion"
    },
    "cardiac": {
        "chest pain", "palpitations", "shortness of breath", "fatigue",
        "dizziness", "swelling in legs", "irregular heartbeat"
    },
    "gastrointestinal": {
        "nausea", "vomiting", "diarrhea", "constipation", "abdominal pain",
        "bloating", "heartburn", "loss of appetite"
    },
    "neurological": {
        "headache", "dizziness", "confusion", "numbness", "tingling",
        "vision changes", "memory problems", "difficulty concentrating"
    },
    "musculoskeletal": {
        "back pain", "joint pain", "muscle pain", "stiffness",
        "weakness", "swelling", "limited mobility"
    },
    "infectious": {
        "fever", "chills", "fatigue", "body aches", "headache",
        "sore throat", "cough", "swollen lymph nodes"
    },
    "mental_health": {
        "anxiety", "depression", "insomnia", "fatigue", "difficulty concentrating",
        "mood changes", "irritability", "loss of interest"
    },
}

# Possible conditions by symptom combination
CONDITION_SUGGESTIONS: Dict[Tuple[str, ...], List[str]] = {
    ("fever", "cough", "body aches"): ["Influenza", "COVID-19", "Common cold"],
    ("headache", "fever", "stiff neck"): ["Meningitis (seek immediate care)", "Migraine", "Tension headache"],
    ("chest pain", "shortness of breath"): ["Heart attack (seek immediate care)", "Anxiety", "Pulmonary embolism"],
    ("nausea", "vomiting", "diarrhea"): ["Gastroenteritis", "Food poisoning", "Viral infection"],
    ("fatigue", "weight gain", "cold intolerance"): ["Hypothyroidism", "Depression", "Anemia"],
    ("frequent urination", "thirst", "fatigue"): ["Diabetes", "Urinary tract infection", "Dehydration"],
    ("joint pain", "fatigue", "rash"): ["Lupus", "Rheumatoid arthritis", "Lyme disease"],
    ("anxiety", "palpitations", "sweating"): ["Panic attack", "Hyperthyroidism", "Anxiety disorder"],
}


class SymptomChecker:
    """Symptom assessment and triage utility.

    Analyzes reported symptoms to provide preliminary urgency assessment,
    care recommendations, and related health information.

    Note: This is NOT a diagnostic tool and should not replace
    professional medical advice.

    Example:
        >>> checker = SymptomChecker()
        >>> symptoms = [
        ...     Symptom(name="headache", severity=6, duration_hours=24),
        ...     Symptom(name="fever", severity=4)
        ... ]
        >>> result = checker.assess(symptoms)
        >>> print(result.urgency_level)
    """

    def __init__(self) -> None:
        """Initialize the symptom checker."""
        self._red_flags = RED_FLAG_SYMPTOMS
        self._clusters = SYMPTOM_CLUSTERS
        self._conditions = CONDITION_SUGGESTIONS

    def assess_symptoms(
        self,
        symptom_names: List[str],
        patient_age: Optional[int] = None,
        has_chronic_conditions: bool = False,
    ) -> AssessmentResult:
        """Assess symptoms from a list of symptom names.

        Args:
            symptom_names: List of symptom descriptions.
            patient_age: Patient age for age-specific adjustments.
            has_chronic_conditions: Whether patient has chronic conditions.

        Returns:
            Assessment result with urgency level and recommendations.
        """
        symptoms = [Symptom(name=name.lower().strip(), severity=5) for name in symptom_names]
        return self.assess(symptoms, patient_age, has_chronic_conditions)

    def assess(
        self,
        symptoms: List[Symptom],
        patient_age: Optional[int] = None,
        has_chronic_conditions: bool = False,
    ) -> AssessmentResult:
        """Perform comprehensive symptom assessment.

        Args:
            symptoms: List of Symptom objects with details.
            patient_age: Patient age for age-specific adjustments.
            has_chronic_conditions: Whether patient has chronic conditions.

        Returns:
            Assessment result with urgency level and recommendations.
        """
        red_flags: List[str] = []
        max_urgency = UrgencyLevel.SELF_CARE
        urgency_score = 0

        # Check for red flag symptoms
        for symptom in symptoms:
            symptom_lower = symptom.name.lower()

            # Direct red flag check
            if symptom_lower in self._red_flags:
                flag_urgency = self._red_flags[symptom_lower]
                red_flags.append(symptom.name)
                if flag_urgency.value < max_urgency.value or (
                    flag_urgency == UrgencyLevel.EMERGENCY
                ):
                    max_urgency = flag_urgency

            # Partial match for red flags
            for flag, flag_urgency in self._red_flags.items():
                if flag in symptom_lower and symptom_lower not in red_flags:
                    red_flags.append(symptom.name)
                    if flag_urgency == UrgencyLevel.EMERGENCY:
                        max_urgency = flag_urgency
                    elif flag_urgency.value < max_urgency.value:
                        max_urgency = flag_urgency

        # Calculate base urgency score
        for symptom in symptoms:
            base_score = symptom.severity * 5  # 5-50 range per symptom

            # Apply modifiers
            for modifier, factor in SEVERITY_MODIFIERS.items():
                if modifier in symptom.name.lower():
                    base_score *= factor

            if symptom.is_worsening:
                base_score *= 1.3
            if symptom.duration_hours and symptom.duration_hours > 72:
                base_score *= 1.2

            urgency_score += base_score

        # Cap and normalize score
        urgency_score = min(100, int(urgency_score))

        # Age adjustments
        if patient_age:
            if patient_age < 2 or patient_age > 65:
                urgency_score = min(100, int(urgency_score * 1.2))

        # Chronic condition adjustment
        if has_chronic_conditions:
            urgency_score = min(100, int(urgency_score * 1.15))

        # Determine urgency level from score if no red flags
        if max_urgency == UrgencyLevel.SELF_CARE:
            if urgency_score >= 80:
                max_urgency = UrgencyLevel.URGENT
            elif urgency_score >= 60:
                max_urgency = UrgencyLevel.SEMI_URGENT
            elif urgency_score >= 40:
                max_urgency = UrgencyLevel.ROUTINE

        # Determine care level
        care_level = self._get_care_level(max_urgency)

        # Get recommendation
        recommendation = self._get_recommendation(max_urgency, red_flags)

        # Find related conditions
        related_conditions = self._find_related_conditions(symptoms)

        # Generate follow-up questions
        questions = self._generate_questions(symptoms)

        # Generate self-care tips
        self_care = self._get_self_care_tips(symptoms, max_urgency)

        return AssessmentResult(
            urgency_level=max_urgency,
            care_level=care_level,
            urgency_score=urgency_score,
            red_flags=red_flags,
            recommendation=recommendation,
            related_conditions=related_conditions,
            questions_to_ask=questions,
            self_care_tips=self_care,
        )

    def get_related_symptoms(self, symptom: str) -> List[str]:
        """Get symptoms commonly associated with a given symptom.

        Args:
            symptom: The primary symptom to check.

        Returns:
            List of related symptoms.
        """
        symptom_lower = symptom.lower()
        related: Set[str] = set()

        for cluster_name, cluster_symptoms in self._clusters.items():
            if symptom_lower in cluster_symptoms or any(
                symptom_lower in s for s in cluster_symptoms
            ):
                related.update(cluster_symptoms)

        related.discard(symptom_lower)
        return sorted(list(related))

    def _get_care_level(self, urgency: UrgencyLevel) -> CareLevel:
        """Map urgency level to recommended care level."""
        mapping = {
            UrgencyLevel.EMERGENCY: CareLevel.EMERGENCY_ROOM,
            UrgencyLevel.URGENT: CareLevel.URGENT_CARE,
            UrgencyLevel.SEMI_URGENT: CareLevel.PRIMARY_CARE,
            UrgencyLevel.ROUTINE: CareLevel.TELEHEALTH,
            UrgencyLevel.SELF_CARE: CareLevel.SELF_CARE,
        }
        return mapping.get(urgency, CareLevel.PRIMARY_CARE)

    def _get_recommendation(
        self, urgency: UrgencyLevel, red_flags: List[str]
    ) -> str:
        """Generate recommendation text based on assessment."""
        if urgency == UrgencyLevel.EMERGENCY:
            if red_flags:
                return (
                    f"EMERGENCY: You reported {', '.join(red_flags)}. "
                    "Call 911 or go to the nearest emergency room immediately. "
                    "Do not drive yourself."
                )
            return "EMERGENCY: Seek immediate emergency care. Call 911."

        if urgency == UrgencyLevel.URGENT:
            return (
                "Your symptoms require prompt medical attention. "
                "Visit an urgent care center or contact your doctor within the next few hours."
            )

        if urgency == UrgencyLevel.SEMI_URGENT:
            return (
                "Your symptoms should be evaluated by a healthcare provider "
                "within the next 24 hours. Consider scheduling an appointment "
                "or visiting an urgent care if symptoms worsen."
            )

        if urgency == UrgencyLevel.ROUTINE:
            return (
                "Your symptoms appear manageable but should be discussed with "
                "your healthcare provider. Schedule a routine appointment or "
                "consider a telehealth visit."
            )

        return (
            "Your symptoms appear mild and may be managed at home with self-care. "
            "Monitor your symptoms and seek care if they worsen or persist."
        )

    def _find_related_conditions(self, symptoms: List[Symptom]) -> List[str]:
        """Find possible conditions based on symptom combinations."""
        symptom_names = frozenset(s.name.lower() for s in symptoms)
        conditions: List[str] = []

        for combo, possible_conditions in self._conditions.items():
            combo_set = frozenset(combo)
            overlap = len(combo_set.intersection(symptom_names))
            if overlap >= 2 or (overlap >= 1 and len(combo_set) <= 2):
                conditions.extend(possible_conditions)

        # Deduplicate while preserving order
        seen: Set[str] = set()
        unique_conditions: List[str] = []
        for condition in conditions:
            if condition not in seen:
                seen.add(condition)
                unique_conditions.append(condition)

        return unique_conditions[:5]  # Limit to top 5

    def _generate_questions(self, symptoms: List[Symptom]) -> List[str]:
        """Generate relevant follow-up questions based on symptoms."""
        questions: List[str] = []
        symptom_names = {s.name.lower() for s in symptoms}

        # General questions
        questions.append("When did your symptoms first start?")
        questions.append("Have your symptoms gotten better or worse over time?")

        # Symptom-specific questions
        if any("pain" in s for s in symptom_names):
            questions.append("On a scale of 1-10, how would you rate your pain?")
            questions.append("Is the pain constant or does it come and go?")

        if any(s in symptom_names for s in ["fever", "chills"]):
            questions.append("What is your temperature?")
            questions.append("Are you experiencing any night sweats?")

        if any(s in symptom_names for s in ["cough", "shortness of breath"]):
            questions.append("Are you coughing up any mucus or blood?")
            questions.append("Do you have any chest pain when breathing?")

        if any(s in symptom_names for s in ["nausea", "vomiting"]):
            questions.append("When did you last eat and what did you eat?")
            questions.append("Are you able to keep fluids down?")

        questions.append("Are you currently taking any medications?")
        questions.append("Do you have any known allergies?")

        return questions[:8]  # Limit to 8 questions

    def _get_self_care_tips(
        self, symptoms: List[Symptom], urgency: UrgencyLevel
    ) -> List[str]:
        """Generate self-care tips based on symptoms."""
        if urgency in [UrgencyLevel.EMERGENCY, UrgencyLevel.URGENT]:
            return ["Seek professional medical care immediately."]

        tips: List[str] = []
        symptom_names = {s.name.lower() for s in symptoms}

        # General tips
        tips.append("Stay hydrated by drinking plenty of water and clear fluids.")
        tips.append("Get adequate rest to help your body recover.")

        # Symptom-specific tips
        if any("fever" in s for s in symptom_names):
            tips.append(
                "For fever: Take over-the-counter fever reducers as directed. "
                "Use cool compresses. Stay hydrated."
            )

        if any("headache" in s for s in symptom_names):
            tips.append(
                "For headache: Rest in a quiet, dark room. "
                "Consider over-the-counter pain relievers. Stay hydrated."
            )

        if any(s in symptom_names for s in ["cough", "sore throat", "congestion"]):
            tips.append(
                "For respiratory symptoms: Use a humidifier, try honey for cough, "
                "gargle with salt water, and consider saline nasal spray."
            )

        if any(s in symptom_names for s in ["nausea", "vomiting", "diarrhea"]):
            tips.append(
                "For GI symptoms: Follow the BRAT diet (bananas, rice, applesauce, toast). "
                "Avoid dairy, fatty, and spicy foods. Stay hydrated with small sips."
            )

        if any("pain" in s for s in symptom_names):
            tips.append(
                "For pain: Rest the affected area, apply ice/heat as appropriate, "
                "and consider over-the-counter pain relief."
            )

        tips.append(
            "Monitor your symptoms and seek medical care if they worsen or don't improve."
        )

        return tips[:6]


def quick_assess(symptoms: List[str]) -> AssessmentResult:
    """Quick symptom assessment utility function.

    Args:
        symptoms: List of symptom descriptions.

    Returns:
        Assessment result.

    Example:
        >>> result = quick_assess(["headache", "fever", "cough"])
        >>> print(result.urgency_level)
    """
    checker = SymptomChecker()
    return checker.assess_symptoms(symptoms)


def check_emergency(symptoms: List[str]) -> Tuple[bool, List[str]]:
    """Check if any symptoms indicate an emergency.

    Args:
        symptoms: List of symptom descriptions.

    Returns:
        Tuple of (is_emergency, list_of_red_flags).

    Example:
        >>> is_emergency, flags = check_emergency(["chest pain", "headache"])
        >>> if is_emergency:
        ...     print(f"Emergency! Red flags: {flags}")
    """
    result = quick_assess(symptoms)
    is_emergency = result.urgency_level == UrgencyLevel.EMERGENCY
    return is_emergency, result.red_flags
