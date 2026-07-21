"""Tests for refill prediction edge cases and urgency classification."""

from datetime import datetime, timedelta

import pytest

from utils.refill_predictor import (
    MedicationSupply,
    RefillPredictor,
    RefillUrgency,
)


def make_supply(**overrides):
    defaults = dict(
        medication_id="med1",
        medication_name="Lisinopril",
        current_quantity=30,
        daily_dose=1.0,
        days_supply=30,
        last_refill_date=datetime.now() - timedelta(days=10),
        refill_history=[
            datetime.now() - timedelta(days=70),
            datetime.now() - timedelta(days=40),
            datetime.now() - timedelta(days=10),
        ],
        adherence_rate=1.0,
    )
    defaults.update(overrides)
    return MedicationSupply(**defaults)


class TestPredictRefill:
    def test_basic_prediction(self):
        pred = RefillPredictor(buffer_days=5).predict_refill(make_supply())
        assert pred.medication_id == "med1"
        assert pred.days_until_refill >= 0
        assert isinstance(pred.urgency, RefillUrgency)
        assert 0 < pred.confidence <= 1.0

    def test_zero_adherence_does_not_crash(self):
        # Regression: adherence_rate=0 previously produced inf days_remaining
        # and OverflowError in timedelta arithmetic
        pred = RefillPredictor().predict_refill(
            make_supply(adherence_rate=0.0)
        )
        assert pred.urgency == RefillUrgency.NOT_NEEDED
        assert pred.days_until_refill > 30

    def test_empty_refill_history_does_not_crash(self):
        # Regression: _calculate_confidence indexed refill_history[0]
        pred = RefillPredictor().predict_refill(
            make_supply(refill_history=[])
        )
        assert 0 < pred.confidence <= 1.0

    def test_low_supply_is_immediate(self):
        pred = RefillPredictor(buffer_days=0).predict_refill(
            make_supply(current_quantity=2, refill_history=[])
        )
        assert pred.urgency == RefillUrgency.IMMEDIATE


class TestPredictBatch:
    def test_sorted_by_urgency(self):
        predictor = RefillPredictor(buffer_days=0)
        supplies = [
            make_supply(medication_id="plenty", current_quantity=200,
                        refill_history=[]),
            make_supply(medication_id="low", current_quantity=2,
                        refill_history=[]),
        ]
        preds = predictor.predict_batch(supplies)
        assert preds[0].medication_id == "low"


class TestAdherenceIssues:
    def test_below_threshold_flagged(self):
        issue = RefillPredictor().detect_adherence_issues(
            make_supply(adherence_rate=0.4)
        )
        assert issue is not None
        assert issue["concern_level"] == "high"

    def test_good_adherence_not_flagged(self):
        issue = RefillPredictor().detect_adherence_issues(
            make_supply(adherence_rate=0.95)
        )
        assert issue is None
