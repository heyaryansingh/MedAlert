"""Tests for health summary trend and alert aggregation."""

import asyncio
from datetime import datetime, timezone

from utils.health_summary import VITAL_RANGES, HealthSummaryGenerator, TrendDirection


gen = HealthSummaryGenerator()


def test_falling_oxygen_saturation_is_worsening():
    spo2 = VITAL_RANGES["oxygen_saturation"]
    assert gen._calculate_trend([98, 98, 97, 93, 90, 88], spo2) == TrendDirection.WORSENING
    assert gen._calculate_trend([88, 90, 92, 96, 97, 98], spo2) == TrendDirection.IMPROVING


def test_fever_resolving_is_improving():
    temp = VITAL_RANGES["temperature"]
    assert gen._calculate_trend([39.5, 39.2, 38.8, 37.4, 37.0, 36.8], temp) == TrendDirection.IMPROVING


def test_unknown_vital_keeps_higher_is_worse():
    assert gen._calculate_trend([10, 10, 10, 20, 20, 20]) == TrendDirection.WORSENING
    assert gen._calculate_trend([10, 10]) == TrendDirection.INSUFFICIENT_DATA


def test_unknown_alert_severity_does_not_crash():
    now = datetime.now(timezone.utc)

    async def alerts(*_):
        return [
            {"alert_type": "bp", "severity": "moderate", "timestamp": now},
            {"alert_type": "bp", "severity": "high", "timestamp": now},
        ]

    g = HealthSummaryGenerator()
    g._get_alerts_data = alerts
    [summary] = asyncio.run(g._summarize_alerts("p1", now, now))
    assert summary.highest_severity == "high"
    assert summary.unresolved_count == 2
