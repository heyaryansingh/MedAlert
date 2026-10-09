from datetime import datetime, timedelta

from utils.health_insights import HealthInsightsGenerator, VitalSignReading


def _readings(vals, kind="weight_change"):
    now = datetime.now()
    return [VitalSignReading(kind, v, "kg", now - timedelta(days=len(vals) - i)) for i, v in enumerate(vals)]


def test_zero_baseline_does_not_crash():
    HealthInsightsGenerator().analyze_vital_trends("p", _readings([0, 0, 0, 5, 5, 5]))


def test_negative_baseline_flat_values_no_trend():
    assert HealthInsightsGenerator().analyze_vital_trends("p", _readings([-5, -5, -5, -5, -5, -5])) == []
