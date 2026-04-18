/**
 * @fileoverview Health Metrics Calculation and Analysis Utilities
 * @module utils/health-metrics
 *
 * Provides functions for calculating health metrics, risk assessments,
 * and generating health insights for patient monitoring.
 *
 * @example
 * ```typescript
 * import { calculateBMI, assessHealthRisk, getHealthInsights } from './health-metrics';
 *
 * const bmi = calculateBMI(70, 175); // weight in kg, height in cm
 * const risk = assessHealthRisk({ age: 45, bmi, systolicBP: 130 });
 * ```
 */

/**
 * Vital signs measurement
 */
export interface VitalSigns {
  /** Heart rate in beats per minute */
  heartRate?: number;
  /** Systolic blood pressure in mmHg */
  systolicBP?: number;
  /** Diastolic blood pressure in mmHg */
  diastolicBP?: number;
  /** Body temperature in Celsius */
  temperature?: number;
  /** Respiratory rate in breaths per minute */
  respiratoryRate?: number;
  /** Oxygen saturation percentage */
  oxygenSaturation?: number;
}

/**
 * Patient health profile
 */
export interface HealthProfile {
  /** Patient age in years */
  age: number;
  /** Weight in kilograms */
  weight?: number;
  /** Height in centimeters */
  height?: number;
  /** Body Mass Index */
  bmi?: number;
  /** Current vital signs */
  vitals?: VitalSigns;
  /** Known conditions */
  conditions?: string[];
  /** Current medications */
  medications?: string[];
  /** Lifestyle factors */
  lifestyle?: {
    smoker?: boolean;
    alcoholUse?: "none" | "moderate" | "heavy";
    exerciseFrequency?: "none" | "light" | "moderate" | "active";
    dietQuality?: "poor" | "fair" | "good" | "excellent";
  };
}

/**
 * Health risk assessment result
 */
export interface RiskAssessment {
  /** Overall risk level */
  overallRisk: "low" | "moderate" | "high" | "critical";
  /** Risk score (0-100) */
  riskScore: number;
  /** Individual risk factors identified */
  riskFactors: RiskFactor[];
  /** Recommended actions */
  recommendations: string[];
}

/**
 * Individual risk factor
 */
export interface RiskFactor {
  /** Risk factor name */
  name: string;
  /** Risk level for this factor */
  level: "low" | "moderate" | "high";
  /** Description of the risk */
  description: string;
  /** Contributing value if applicable */
  value?: number | string;
}

/**
 * Health insight for patient education
 */
export interface HealthInsight {
  /** Category of insight */
  category: "vitals" | "lifestyle" | "prevention" | "medication";
  /** Priority level */
  priority: "info" | "warning" | "alert";
  /** Main message */
  title: string;
  /** Detailed explanation */
  description: string;
  /** Suggested action if any */
  action?: string;
}

// Normal ranges for vital signs
const VITAL_RANGES = {
  heartRate: { min: 60, max: 100, criticalMin: 40, criticalMax: 150 },
  systolicBP: { min: 90, max: 120, elevated: 130, high: 140, crisis: 180 },
  diastolicBP: { min: 60, max: 80, elevated: 80, high: 90, crisis: 120 },
  temperature: { min: 36.1, max: 37.2, fever: 38, highFever: 39.4 },
  respiratoryRate: { min: 12, max: 20, criticalMin: 8, criticalMax: 30 },
  oxygenSaturation: { normal: 95, low: 90, critical: 85 },
};

/**
 * Calculate Body Mass Index (BMI)
 *
 * @param weightKg - Weight in kilograms
 * @param heightCm - Height in centimeters
 * @returns BMI value
 *
 * @example
 * ```typescript
 * const bmi = calculateBMI(70, 175);
 * console.log(`BMI: ${bmi.toFixed(1)}`); // BMI: 22.9
 * ```
 */
export function calculateBMI(weightKg: number, heightCm: number): number {
  if (weightKg <= 0 || heightCm <= 0) return 0;
  const heightM = heightCm / 100;
  return weightKg / (heightM * heightM);
}

/**
 * Get BMI category based on WHO classification
 *
 * @param bmi - Body Mass Index value
 * @returns BMI category string
 */
export function getBMICategory(
  bmi: number
): "underweight" | "normal" | "overweight" | "obese" | "severely_obese" {
  if (bmi < 18.5) return "underweight";
  if (bmi < 25) return "normal";
  if (bmi < 30) return "overweight";
  if (bmi < 35) return "obese";
  return "severely_obese";
}

/**
 * Calculate Mean Arterial Pressure (MAP)
 *
 * @param systolic - Systolic blood pressure
 * @param diastolic - Diastolic blood pressure
 * @returns Mean arterial pressure
 */
export function calculateMAP(systolic: number, diastolic: number): number {
  return diastolic + (systolic - diastolic) / 3;
}

/**
 * Assess blood pressure category
 *
 * @param systolic - Systolic blood pressure in mmHg
 * @param diastolic - Diastolic blood pressure in mmHg
 * @returns Blood pressure category
 */
export function assessBloodPressure(
  systolic: number,
  diastolic: number
): "normal" | "elevated" | "high_stage1" | "high_stage2" | "crisis" {
  if (systolic >= 180 || diastolic >= 120) return "crisis";
  if (systolic >= 140 || diastolic >= 90) return "high_stage2";
  if (systolic >= 130 || diastolic >= 80) return "high_stage1";
  if (systolic >= 120 && diastolic < 80) return "elevated";
  return "normal";
}

/**
 * Check if vital sign is within normal range
 *
 * @param vital - Vital sign type
 * @param value - Measured value
 * @returns Status of the vital sign
 */
export function checkVitalStatus(
  vital: keyof typeof VITAL_RANGES,
  value: number
): "normal" | "low" | "high" | "critical" {
  const range = VITAL_RANGES[vital];

  if (vital === "oxygenSaturation") {
    if (value < range.critical) return "critical";
    if (value < range.low) return "low";
    if (value >= range.normal) return "normal";
    return "low";
  }

  if ("criticalMin" in range && value < range.criticalMin) return "critical";
  if ("criticalMax" in range && value > range.criticalMax) return "critical";
  if (value < range.min) return "low";
  if (value > range.max) return "high";
  return "normal";
}

/**
 * Assess overall health risk based on profile
 *
 * @param profile - Patient health profile
 * @returns Risk assessment with score and recommendations
 *
 * @example
 * ```typescript
 * const risk = assessHealthRisk({
 *   age: 55,
 *   bmi: 28,
 *   vitals: { systolicBP: 145, diastolicBP: 92 },
 *   lifestyle: { smoker: true }
 * });
 * console.log(`Risk: ${risk.overallRisk}, Score: ${risk.riskScore}`);
 * ```
 */
export function assessHealthRisk(profile: HealthProfile): RiskAssessment {
  const riskFactors: RiskFactor[] = [];
  let riskScore = 0;

  // Age risk
  if (profile.age >= 65) {
    riskFactors.push({
      name: "Age",
      level: "moderate",
      description: "Advanced age increases health risks",
      value: profile.age,
    });
    riskScore += 15;
  } else if (profile.age >= 45) {
    riskFactors.push({
      name: "Age",
      level: "low",
      description: "Middle age - regular screenings recommended",
      value: profile.age,
    });
    riskScore += 5;
  }

  // BMI risk
  if (profile.bmi) {
    const bmiCategory = getBMICategory(profile.bmi);
    if (bmiCategory === "severely_obese") {
      riskFactors.push({
        name: "BMI",
        level: "high",
        description: "Severe obesity significantly increases health risks",
        value: profile.bmi.toFixed(1),
      });
      riskScore += 25;
    } else if (bmiCategory === "obese") {
      riskFactors.push({
        name: "BMI",
        level: "high",
        description: "Obesity increases risk of chronic diseases",
        value: profile.bmi.toFixed(1),
      });
      riskScore += 18;
    } else if (bmiCategory === "overweight") {
      riskFactors.push({
        name: "BMI",
        level: "moderate",
        description: "Overweight - consider lifestyle modifications",
        value: profile.bmi.toFixed(1),
      });
      riskScore += 8;
    } else if (bmiCategory === "underweight") {
      riskFactors.push({
        name: "BMI",
        level: "moderate",
        description: "Underweight may indicate nutritional issues",
        value: profile.bmi.toFixed(1),
      });
      riskScore += 10;
    }
  }

  // Blood pressure risk
  if (profile.vitals?.systolicBP && profile.vitals?.diastolicBP) {
    const bpCategory = assessBloodPressure(
      profile.vitals.systolicBP,
      profile.vitals.diastolicBP
    );

    if (bpCategory === "crisis") {
      riskFactors.push({
        name: "Blood Pressure",
        level: "high",
        description: "Hypertensive crisis - immediate medical attention needed",
        value: `${profile.vitals.systolicBP}/${profile.vitals.diastolicBP}`,
      });
      riskScore += 35;
    } else if (bpCategory === "high_stage2") {
      riskFactors.push({
        name: "Blood Pressure",
        level: "high",
        description: "Stage 2 hypertension - medication likely needed",
        value: `${profile.vitals.systolicBP}/${profile.vitals.diastolicBP}`,
      });
      riskScore += 20;
    } else if (bpCategory === "high_stage1") {
      riskFactors.push({
        name: "Blood Pressure",
        level: "moderate",
        description: "Stage 1 hypertension - lifestyle changes recommended",
        value: `${profile.vitals.systolicBP}/${profile.vitals.diastolicBP}`,
      });
      riskScore += 12;
    }
  }

  // Heart rate risk
  if (profile.vitals?.heartRate) {
    const hrStatus = checkVitalStatus("heartRate", profile.vitals.heartRate);
    if (hrStatus === "critical") {
      riskFactors.push({
        name: "Heart Rate",
        level: "high",
        description: "Abnormal heart rate requires evaluation",
        value: profile.vitals.heartRate,
      });
      riskScore += 20;
    } else if (hrStatus !== "normal") {
      riskFactors.push({
        name: "Heart Rate",
        level: "moderate",
        description: `Heart rate is ${hrStatus} - monitor closely`,
        value: profile.vitals.heartRate,
      });
      riskScore += 8;
    }
  }

  // Oxygen saturation risk
  if (profile.vitals?.oxygenSaturation) {
    const o2Status = checkVitalStatus(
      "oxygenSaturation",
      profile.vitals.oxygenSaturation
    );
    if (o2Status === "critical") {
      riskFactors.push({
        name: "Oxygen Saturation",
        level: "high",
        description: "Critically low oxygen - immediate attention required",
        value: `${profile.vitals.oxygenSaturation}%`,
      });
      riskScore += 30;
    } else if (o2Status === "low") {
      riskFactors.push({
        name: "Oxygen Saturation",
        level: "moderate",
        description: "Low oxygen saturation - evaluation recommended",
        value: `${profile.vitals.oxygenSaturation}%`,
      });
      riskScore += 15;
    }
  }

  // Lifestyle risks
  if (profile.lifestyle?.smoker) {
    riskFactors.push({
      name: "Smoking",
      level: "high",
      description: "Smoking significantly increases cardiovascular risk",
    });
    riskScore += 20;
  }

  if (profile.lifestyle?.alcoholUse === "heavy") {
    riskFactors.push({
      name: "Alcohol",
      level: "moderate",
      description: "Heavy alcohol use impacts multiple organ systems",
    });
    riskScore += 12;
  }

  if (profile.lifestyle?.exerciseFrequency === "none") {
    riskFactors.push({
      name: "Physical Activity",
      level: "moderate",
      description: "Sedentary lifestyle increases health risks",
    });
    riskScore += 10;
  }

  // Cap score at 100
  riskScore = Math.min(100, riskScore);

  // Determine overall risk level
  let overallRisk: "low" | "moderate" | "high" | "critical";
  if (riskScore >= 70) {
    overallRisk = "critical";
  } else if (riskScore >= 45) {
    overallRisk = "high";
  } else if (riskScore >= 20) {
    overallRisk = "moderate";
  } else {
    overallRisk = "low";
  }

  // Generate recommendations
  const recommendations = generateRecommendations(riskFactors, profile);

  return {
    overallRisk,
    riskScore,
    riskFactors,
    recommendations,
  };
}

/**
 * Generate health insights based on profile
 *
 * @param profile - Patient health profile
 * @returns Array of health insights
 */
export function getHealthInsights(profile: HealthProfile): HealthInsight[] {
  const insights: HealthInsight[] = [];

  // BMI insights
  if (profile.bmi) {
    const category = getBMICategory(profile.bmi);
    if (category === "normal") {
      insights.push({
        category: "vitals",
        priority: "info",
        title: "Healthy Weight",
        description: `Your BMI of ${profile.bmi.toFixed(1)} is within the healthy range. Maintain your current lifestyle habits.`,
      });
    } else if (category === "overweight" || category === "obese") {
      insights.push({
        category: "vitals",
        priority: "warning",
        title: "Weight Management",
        description: `Your BMI of ${profile.bmi.toFixed(1)} indicates ${category === "obese" ? "obesity" : "overweight"}. Even a 5-10% weight loss can significantly improve health outcomes.`,
        action: "Consider consulting a nutritionist for a personalized plan",
      });
    }
  }

  // Blood pressure insights
  if (profile.vitals?.systolicBP && profile.vitals?.diastolicBP) {
    const bpCategory = assessBloodPressure(
      profile.vitals.systolicBP,
      profile.vitals.diastolicBP
    );

    if (bpCategory === "normal") {
      insights.push({
        category: "vitals",
        priority: "info",
        title: "Healthy Blood Pressure",
        description: "Your blood pressure is in the normal range. Continue with heart-healthy habits.",
      });
    } else if (bpCategory !== "normal") {
      insights.push({
        category: "vitals",
        priority: bpCategory === "crisis" ? "alert" : "warning",
        title: "Blood Pressure Attention",
        description: `Blood pressure reading of ${profile.vitals.systolicBP}/${profile.vitals.diastolicBP} mmHg requires attention.`,
        action:
          bpCategory === "crisis"
            ? "Seek immediate medical attention"
            : "Monitor regularly and consult your doctor",
      });
    }
  }

  // Lifestyle insights
  if (profile.lifestyle) {
    if (profile.lifestyle.smoker) {
      insights.push({
        category: "lifestyle",
        priority: "warning",
        title: "Smoking Cessation",
        description: "Quitting smoking is the single most important step to improve your health. Benefits begin within 20 minutes of your last cigarette.",
        action: "Talk to your doctor about smoking cessation programs",
      });
    }

    if (profile.lifestyle.exerciseFrequency === "none") {
      insights.push({
        category: "lifestyle",
        priority: "warning",
        title: "Physical Activity",
        description: "Regular physical activity reduces risk of heart disease, diabetes, and many cancers. Aim for 150 minutes of moderate activity per week.",
        action: "Start with short walks and gradually increase duration",
      });
    }
  }

  // Age-appropriate screening reminders
  if (profile.age >= 50) {
    insights.push({
      category: "prevention",
      priority: "info",
      title: "Preventive Screenings",
      description: "At your age, regular screenings for colorectal cancer, diabetes, and cardiovascular disease are recommended.",
      action: "Discuss screening schedule with your healthcare provider",
    });
  }

  if (profile.age >= 65) {
    insights.push({
      category: "prevention",
      priority: "info",
      title: "Immunizations",
      description: "Stay current with flu shots, pneumococcal vaccine, and shingles vaccine to prevent serious illnesses.",
    });
  }

  return insights;
}

/**
 * Calculate medication adherence rate
 *
 * @param dosesTaken - Number of doses taken
 * @param dosesScheduled - Number of doses scheduled
 * @returns Adherence percentage
 */
export function calculateAdherence(
  dosesTaken: number,
  dosesScheduled: number
): number {
  if (dosesScheduled <= 0) return 100;
  return Math.round((dosesTaken / dosesScheduled) * 100);
}

/**
 * Get adherence status based on percentage
 *
 * @param adherence - Adherence percentage
 * @returns Status and recommendation
 */
export function getAdherenceStatus(adherence: number): {
  status: "excellent" | "good" | "fair" | "poor";
  message: string;
} {
  if (adherence >= 90) {
    return {
      status: "excellent",
      message: "Great job! You're taking your medications as prescribed.",
    };
  }
  if (adherence >= 80) {
    return {
      status: "good",
      message: "Good adherence, but try to be more consistent for best results.",
    };
  }
  if (adherence >= 50) {
    return {
      status: "fair",
      message: "Medication adherence needs improvement. Consider setting reminders.",
    };
  }
  return {
    status: "poor",
    message: "Low adherence may reduce medication effectiveness. Please consult your doctor.",
  };
}

// Helper function to generate recommendations
function generateRecommendations(
  riskFactors: RiskFactor[],
  profile: HealthProfile
): string[] {
  const recommendations: string[] = [];

  const hasHighBP = riskFactors.some(
    (f) => f.name === "Blood Pressure" && f.level === "high"
  );
  const hasBMIIssue = riskFactors.some((f) => f.name === "BMI");
  const isSmoker = profile.lifestyle?.smoker;
  const isInactive = profile.lifestyle?.exerciseFrequency === "none";

  if (hasHighBP) {
    recommendations.push("Monitor blood pressure daily and keep a log");
    recommendations.push("Reduce sodium intake to less than 2,300mg per day");
  }

  if (hasBMIIssue && profile.bmi && profile.bmi > 25) {
    recommendations.push("Aim for gradual weight loss of 1-2 pounds per week");
    recommendations.push("Focus on whole foods and reduce processed food intake");
  }

  if (isSmoker) {
    recommendations.push("Consider nicotine replacement therapy or cessation programs");
    recommendations.push("Identify triggers and develop coping strategies");
  }

  if (isInactive) {
    recommendations.push("Start with 10-minute walks and gradually increase");
    recommendations.push("Find physical activities you enjoy to stay motivated");
  }

  if (recommendations.length === 0) {
    recommendations.push("Continue with your current healthy habits");
    recommendations.push("Schedule regular check-ups to maintain good health");
  }

  return recommendations;
}
