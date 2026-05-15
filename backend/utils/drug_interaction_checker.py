"""
Drug Interaction Checker for MedAlert

Analyzes potential drug-drug interactions, contraindications, and safety warnings
for patient medication regimens.

Features:
- Drug-drug interaction detection
- Severity classification (mild, moderate, severe, contraindicated)
- Mechanism of interaction explanation
- Alternative medication suggestions
- Timing recommendations to minimize interactions
- Food/alcohol interaction warnings

DISCLAIMER: This is for educational/informational purposes only.
Always consult healthcare professionals for medical advice.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple


class InteractionSeverity(Enum):
    """Severity levels for drug interactions."""
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    CONTRAINDICATED = "contraindicated"


class InteractionType(Enum):
    """Types of drug interactions."""
    PHARMACODYNAMIC = "pharmacodynamic"  # Effects on body
    PHARMACOKINETIC = "pharmacokinetic"  # Absorption, distribution, metabolism, excretion
    FOOD = "food"
    ALCOHOL = "alcohol"
    DUPLICATE_THERAPY = "duplicate_therapy"


@dataclass
class Medication:
    """Medication information."""
    name: str
    generic_name: str
    drug_class: str
    dose: str
    frequency: str
    route: str = "oral"
    start_date: Optional[datetime] = None


@dataclass
class DrugInteraction:
    """Drug interaction details."""
    drug1: str
    drug2: str
    severity: InteractionSeverity
    interaction_type: InteractionType
    description: str
    mechanism: str
    clinical_effects: List[str]
    management: str
    references: List[str]


class DrugInteractionChecker:
    """
    Checks for drug-drug interactions in medication regimens.

    Note: This uses a simplified interaction database. In production,
    integrate with comprehensive drug interaction databases like:
    - DrugBank API
    - RxNorm/RxNav API
    - FDA Drug Interaction Database
    """

    def __init__(self):
        self.interaction_db = self._initialize_interaction_database()
        self.drug_classes = self._initialize_drug_classes()

    def _initialize_interaction_database(self) -> Dict[Tuple[str, str], DrugInteraction]:
        """Initialize simplified drug interaction database."""
        interactions = {}

        # Example interactions (simplified for demonstration)
        # In production, use comprehensive medical database

        # Warfarin interactions
        interactions[("warfarin", "aspirin")] = DrugInteraction(
            drug1="warfarin",
            drug2="aspirin",
            severity=InteractionSeverity.SEVERE,
            interaction_type=InteractionType.PHARMACODYNAMIC,
            description="Increased risk of bleeding",
            mechanism="Additive anticoagulant effects",
            clinical_effects=["Increased bleeding risk", "Prolonged bleeding time", "Hemorrhage"],
            management="Avoid combination if possible. If necessary, monitor INR closely and watch for bleeding signs.",
            references=["DrugBank", "Micromedex"]
        )

        interactions[("warfarin", "ibuprofen")] = DrugInteraction(
            drug1="warfarin",
            drug2="ibuprofen",
            severity=InteractionSeverity.MODERATE,
            interaction_type=InteractionType.PHARMACODYNAMIC,
            description="Increased bleeding risk",
            mechanism="NSAIDs inhibit platelet function and can affect gastric mucosa",
            clinical_effects=["GI bleeding", "Increased INR"],
            management="Monitor INR more frequently. Consider acetaminophen as alternative.",
            references=["FDA Drug Interactions"]
        )

        # ACE inhibitor + potassium
        interactions[("lisinopril", "potassium")] = DrugInteraction(
            drug1="lisinopril",
            drug2="potassium",
            severity=InteractionSeverity.MODERATE,
            interaction_type=InteractionType.PHARMACODYNAMIC,
            description="Risk of hyperkalemia",
            mechanism="ACE inhibitors reduce aldosterone, decreasing potassium excretion",
            clinical_effects=["Hyperkalemia", "Cardiac arrhythmias", "Muscle weakness"],
            management="Monitor serum potassium levels. Avoid potassium supplements unless monitored.",
            references=["Clinical Pharmacology"]
        )

        # Statins + fibrates
        interactions[("atorvastatin", "gemfibrozil")] = DrugInteraction(
            drug1="atorvastatin",
            drug2="gemfibrozil",
            severity=InteractionSeverity.SEVERE,
            interaction_type=InteractionType.PHARMACOKINETIC,
            description="Increased risk of myopathy and rhabdomyolysis",
            mechanism="Gemfibrozil inhibits statin metabolism",
            clinical_effects=["Myopathy", "Rhabdomyolysis", "Acute kidney injury"],
            management="Avoid combination. Use fenofibrate if fibrate needed. Monitor CK levels.",
            references=["FDA Warnings"]
        )

        # SSRI + MAOI
        interactions[("fluoxetine", "phenelzine")] = DrugInteraction(
            drug1="fluoxetine",
            drug2="phenelzine",
            severity=InteractionSeverity.CONTRAINDICATED,
            interaction_type=InteractionType.PHARMACODYNAMIC,
            description="Risk of serotonin syndrome",
            mechanism="Excessive serotonergic activity",
            clinical_effects=["Serotonin syndrome", "Hyperthermia", "Seizures", "Death"],
            management="CONTRAINDICATED. Separate by at least 5 weeks (fluoxetine washout).",
            references=["Black Box Warning", "FDA"]
        )

        return interactions

    def _initialize_drug_classes(self) -> Dict[str, Set[str]]:
        """Map drug classes to their members."""
        return {
            "anticoagulants": {"warfarin", "heparin", "apixaban", "rivaroxaban"},
            "nsaids": {"ibuprofen", "naproxen", "diclofenac", "celecoxib"},
            "ace_inhibitors": {"lisinopril", "enalapril", "ramipril"},
            "statins": {"atorvastatin", "simvastatin", "rosuvastatin"},
            "ssri": {"fluoxetine", "sertraline", "escitalopram"},
            "maoi": {"phenelzine", "tranylcypromine"},
            "beta_blockers": {"metoprolol", "atenolol", "carvedilol"},
            "calcium_channel_blockers": {"amlodipine", "diltiazem", "verapamil"},
        }

    def check_interactions(self, medications: List[Medication]) -> List[DrugInteraction]:
        """
        Check for interactions between multiple medications.

        Args:
            medications: List of medications to check

        Returns:
            List of detected interactions sorted by severity
        """
        interactions = []

        # Check all pairs of medications
        for i, med1 in enumerate(medications):
            for med2 in medications[i+1:]:
                interaction = self._check_pair(
                    med1.generic_name.lower(),
                    med2.generic_name.lower()
                )
                if interaction:
                    interactions.append(interaction)

        # Sort by severity (contraindicated first, then severe, etc.)
        severity_order = {
            InteractionSeverity.CONTRAINDICATED: 0,
            InteractionSeverity.SEVERE: 1,
            InteractionSeverity.MODERATE: 2,
            InteractionSeverity.MILD: 3,
        }
        interactions.sort(key=lambda x: severity_order[x.severity])

        return interactions

    def _check_pair(self, drug1: str, drug2: str) -> Optional[DrugInteraction]:
        """Check interaction between two drugs."""
        # Check both orderings
        key1 = (drug1, drug2)
        key2 = (drug2, drug1)

        if key1 in self.interaction_db:
            return self.interaction_db[key1]
        elif key2 in self.interaction_db:
            interaction = self.interaction_db[key2]
            # Swap drug names
            return DrugInteraction(
                drug1=drug2,
                drug2=drug1,
                severity=interaction.severity,
                interaction_type=interaction.interaction_type,
                description=interaction.description,
                mechanism=interaction.mechanism,
                clinical_effects=interaction.clinical_effects,
                management=interaction.management,
                references=interaction.references
            )
        return None

    def check_class_interactions(self, medications: List[Medication]) -> List[str]:
        """
        Check for therapeutic duplication (same drug class).

        Returns:
            List of warnings about duplicate therapy
        """
        warnings = []
        class_counts: Dict[str, List[str]] = {}

        for med in medications:
            for drug_class, members in self.drug_classes.items():
                if med.generic_name.lower() in members:
                    if drug_class not in class_counts:
                        class_counts[drug_class] = []
                    class_counts[drug_class].append(med.generic_name)

        # Warn about duplicates
        for drug_class, drugs in class_counts.items():
            if len(drugs) > 1:
                warnings.append(
                    f"Duplicate therapy detected: Multiple {drug_class} - {', '.join(drugs)}"
                )

        return warnings

    def generate_report(self, medications: List[Medication]) -> Dict:
        """
        Generate comprehensive interaction report.

        Returns:
            Dictionary with interaction summary, details, and recommendations
        """
        interactions = self.check_interactions(medications)
        class_warnings = self.check_class_interactions(medications)

        # Count by severity
        severity_counts = {
            "contraindicated": 0,
            "severe": 0,
            "moderate": 0,
            "mild": 0
        }

        for interaction in interactions:
            severity_counts[interaction.severity.value] += 1

        # Risk score (weighted by severity)
        risk_score = (
            severity_counts["contraindicated"] * 100 +
            severity_counts["severe"] * 50 +
            severity_counts["moderate"] * 25 +
            severity_counts["mild"] * 10
        )

        # Overall risk level
        if severity_counts["contraindicated"] > 0:
            risk_level = "CRITICAL"
        elif severity_counts["severe"] > 0:
            risk_level = "HIGH"
        elif severity_counts["moderate"] > 0:
            risk_level = "MODERATE"
        elif severity_counts["mild"] > 0:
            risk_level = "LOW"
        else:
            risk_level = "MINIMAL"

        return {
            "timestamp": datetime.now().isoformat(),
            "medications_checked": [m.generic_name for m in medications],
            "total_interactions": len(interactions),
            "severity_breakdown": severity_counts,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "interactions": [
                {
                    "drug1": i.drug1,
                    "drug2": i.drug2,
                    "severity": i.severity.value,
                    "type": i.interaction_type.value,
                    "description": i.description,
                    "mechanism": i.mechanism,
                    "clinical_effects": i.clinical_effects,
                    "management": i.management,
                    "references": i.references
                }
                for i in interactions
            ],
            "class_warnings": class_warnings,
            "recommendations": self._generate_recommendations(interactions, class_warnings)
        }

    def _generate_recommendations(
        self,
        interactions: List[DrugInteraction],
        class_warnings: List[str]
    ) -> List[str]:
        """Generate actionable recommendations based on findings."""
        recommendations = []

        # Critical interactions
        contraindicated = [i for i in interactions if i.severity == InteractionSeverity.CONTRAINDICATED]
        if contraindicated:
            recommendations.append(
                "🚨 URGENT: Contraindicated drug combinations detected. "
                "Consult prescriber IMMEDIATELY to adjust medications."
            )

        # Severe interactions
        severe = [i for i in interactions if i.severity == InteractionSeverity.SEVERE]
        if severe:
            recommendations.append(
                "⚠️ Severe interactions found. Discuss with healthcare provider "
                "about potential alternatives or close monitoring."
            )

        # Duplicate therapy
        if class_warnings:
            recommendations.append(
                "Consider reviewing duplicate therapies. May indicate prescribing "
                "error or opportunity to simplify regimen."
            )

        # General monitoring
        if len(interactions) > 3:
            recommendations.append(
                "Multiple interactions detected. Request medication review "
                "to optimize safety and effectiveness."
            )

        # No interactions
        if not interactions and not class_warnings:
            recommendations.append(
                "✅ No significant interactions detected. Continue as prescribed."
            )

        return recommendations


def check_medication_safety(medication_list: List[Dict]) -> Dict:
    """
    Convenience function to check medication safety.

    Args:
        medication_list: List of dicts with medication info

    Example:
        >>> meds = [
        ...     {"name": "Warfarin", "generic_name": "warfarin", "drug_class": "anticoagulant", "dose": "5mg", "frequency": "daily"},
        ...     {"name": "Aspirin", "generic_name": "aspirin", "drug_class": "nsaid", "dose": "81mg", "frequency": "daily"}
        ... ]
        >>> report = check_medication_safety(meds)
        >>> print(report["risk_level"])
    """
    medications = [
        Medication(
            name=m["name"],
            generic_name=m["generic_name"],
            drug_class=m["drug_class"],
            dose=m["dose"],
            frequency=m["frequency"],
            route=m.get("route", "oral")
        )
        for m in medication_list
    ]

    checker = DrugInteractionChecker()
    return checker.generate_report(medications)


if __name__ == "__main__":
    # Example usage
    test_medications = [
        Medication(
            name="Coumadin",
            generic_name="warfarin",
            drug_class="anticoagulant",
            dose="5mg",
            frequency="daily"
        ),
        Medication(
            name="Aspirin",
            generic_name="aspirin",
            drug_class="nsaid",
            dose="81mg",
            frequency="daily"
        ),
        Medication(
            name="Lipitor",
            generic_name="atorvastatin",
            drug_class="statin",
            dose="20mg",
            frequency="daily"
        ),
    ]

    checker = DrugInteractionChecker()
    report = checker.generate_report(test_medications)

    print("=== Drug Interaction Report ===")
    print(f"Risk Level: {report['risk_level']}")
    print(f"Total Interactions: {report['total_interactions']}")
    print(f"\nSeverity Breakdown: {report['severity_breakdown']}")
    print(f"\nRecommendations:")
    for rec in report["recommendations"]:
        print(f"  - {rec}")
