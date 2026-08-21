"""Tests for dose time generation in the medication scheduler."""

import pytest

from backend.utils.medication_scheduler import (
    MealTiming,
    calculate_dose_times,
    format_time,
    parse_time,
)


def _minutes(hhmm: str) -> int:
    hours, mins = hhmm.split(":")
    return int(hours) * 60 + int(mins)


class TestCalculateDoseTimes:
    def test_once_daily_is_taken_at_wake(self):
        assert calculate_dose_times(1, "07:00", "22:00") == ["07:00"]

    def test_first_dose_does_not_move_when_frequency_rises(self):
        # Adding a dose should add one, not delay the first.
        for frequency in range(1, 7):
            assert calculate_dose_times(frequency, "07:00", "22:00")[0] == "07:00"

    def test_doses_are_evenly_spaced(self):
        times = calculate_dose_times(3, "07:00", "22:00")

        gaps = [
            _minutes(later) - _minutes(earlier)
            for earlier, later in zip(times, times[1:])
        ]
        assert len(set(gaps)) == 1
        assert gaps[0] == 300  # 15 waking hours split three ways

    def test_all_doses_fall_inside_the_waking_window(self):
        times = calculate_dose_times(6, "07:00", "22:00")

        assert all(_minutes("07:00") <= _minutes(t) < _minutes("22:00") for t in times)

    def test_overnight_waking_window_wraps_past_midnight(self):
        times = calculate_dose_times(3, "20:00", "06:00")

        assert times[0] == "20:00"
        # A night-shift schedule has to roll into the next calendar day.
        assert times[-1] < times[0]
        assert all(len(t) == 5 and t[2] == ":" for t in times)

    def test_frequency_is_bounded(self):
        with pytest.raises(ValueError):
            calculate_dose_times(0)
        with pytest.raises(ValueError):
            calculate_dose_times(7)

    def test_returns_one_time_per_dose(self):
        for frequency in range(1, 7):
            assert len(calculate_dose_times(frequency)) == frequency


class TestMealTiming:
    def test_twice_daily_with_food_uses_the_two_furthest_meals(self):
        # Breakfast and lunch are 4.5 hours apart, leaving a 19.5 hour gap.
        assert calculate_dose_times(2, meal_timing=MealTiming.WITH_FOOD) == [
            "08:00",
            "18:30",
        ]

    def test_once_daily_with_food_is_breakfast(self):
        assert calculate_dose_times(1, meal_timing=MealTiming.WITH_FOOD) == ["08:00"]

    def test_three_times_daily_with_food_is_every_meal(self):
        assert calculate_dose_times(3, meal_timing=MealTiming.WITH_FOOD) == [
            "08:00",
            "12:30",
            "18:30",
        ]

    def test_more_than_three_doses_falls_back_to_even_spacing(self):
        with_food = calculate_dose_times(4, meal_timing=MealTiming.WITH_FOOD)

        assert with_food == calculate_dose_times(4)

    def test_other_meal_timings_do_not_override_the_spacing(self):
        baseline = calculate_dose_times(3)

        for timing in (
            MealTiming.BEFORE_FOOD,
            MealTiming.AFTER_FOOD,
            MealTiming.EMPTY_STOMACH,
            MealTiming.NO_RESTRICTION,
        ):
            assert calculate_dose_times(3, meal_timing=timing) == baseline


class TestTimeHelpers:
    def test_round_trip(self):
        assert format_time(parse_time("09:05")) == "09:05"

    def test_rejects_an_impossible_time(self):
        with pytest.raises(ValueError):
            parse_time("25:00")
