"""QTc checks fail closed on NaN / non-positive input instead of reading NORMAL."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from backend.utils.qt_prolongation_checker import (
    QtcClassification,
    assess_qt_risk,
    calculate_qtc,
    classify_qtc_risk,
)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), 0, -5])
def test_classify_rejects_bad_qtc(bad):
    with pytest.raises(ValueError):
        classify_qtc_risk(bad)
    with pytest.raises(ValueError):
        assess_qt_risk(["sotalol"], qtc_ms=bad)


@pytest.mark.parametrize("kwargs", [
    {"qt_ms": float("nan"), "heart_rate_bpm": 60},
    {"qt_ms": 400, "heart_rate_bpm": float("nan")},
    {"qt_ms": 400, "rr_interval_sec": float("nan")},
])
def test_calculate_rejects_nan(kwargs):
    with pytest.raises(ValueError):
        calculate_qtc(**kwargs)


def test_valid_still_classifies():
    assert classify_qtc_risk(400) == QtcClassification.NORMAL
    assert calculate_qtc(400, heart_rate_bpm=60) == 400.0
