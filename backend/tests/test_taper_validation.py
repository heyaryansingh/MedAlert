"""Taper inputs that used to hang or build nonsense schedules are rejected."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from backend.utils.taper_schedule import (
    estimate_taper_duration,
    generate_custom_taper,
    generate_linear_taper,
    generate_percentage_taper,
)


def test_estimate_zero_pct_rejected_not_infinite_loop():
    with pytest.raises(ValueError):
        estimate_taper_duration(40, 0, reduction_pct=0, days_per_step=7)


@pytest.mark.parametrize("days", [0, -7, 2.5])
def test_bad_days_per_step(days):
    with pytest.raises(ValueError):
        generate_linear_taper(40, 0, 5, days_per_step=days)
    with pytest.raises(ValueError):
        generate_percentage_taper(40, 0, 10, days_per_step=days)


def test_percentage_to_zero_needs_floor():
    with pytest.raises(ValueError):
        generate_percentage_taper(40, 0, 10, min_dose_mg=0)
    # tapering to a positive target needs no floor
    assert generate_percentage_taper(40, 10, 10, min_dose_mg=0).steps[-1].dose_mg == 10


def test_custom_rejects_negative_dose_and_zero_days():
    with pytest.raises(ValueError):
        generate_custom_taper("prednisone", [(20, 7), (-5, 7)])
    with pytest.raises(ValueError):
        generate_custom_taper("prednisone", [(20, 7), (10, 0)])
    assert generate_custom_taper("prednisone", [(20, 7), (0, 7)]).total_duration_days == 14
