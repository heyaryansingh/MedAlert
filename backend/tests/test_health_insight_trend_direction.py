from datetime import datetime, timedelta

from utils.health_insights import HealthInsightsGenerator, InsightType, VitalSignReading


def _trend(vals, kind):
    now = datetime.now()
    readings = [VitalSignReading(kind, v, "", now - timedelta(days=len(vals) - i)) for i, v in enumerate(vals)]
    out = HealthInsightsGenerator().analyze_vital_trends("p", readings)
    return [i.insight_type for i in out if "_trend_" in i.insight_id]


def test_falling_below_minimum_is_negative():
    assert _trend([98, 98, 98, 85, 85, 85], "oxygen_saturation") == [InsightType.NEGATIVE_TREND]


def test_recovering_from_low_is_positive():
    assert _trend([45, 45, 45, 70, 70, 70], "heart_rate") == [InsightType.POSITIVE_TREND]


def test_existing_high_side_behavior_kept():
    assert _trend([110, 110, 110, 150, 150, 150], "systolic_bp") == [InsightType.NEGATIVE_TREND]
    assert _trend([150, 150, 150, 115, 115, 115], "systolic_bp") == [InsightType.POSITIVE_TREND]
    assert _trend([70, 70, 70, 90, 90, 90], "heart_rate") == [InsightType.PATTERN_DETECTED]
