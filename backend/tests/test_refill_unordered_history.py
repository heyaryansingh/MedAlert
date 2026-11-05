from datetime import datetime

from backend.utils.refill_predictor import RefillPredictor


def test_unordered_refill_history_gives_same_interval():
    jan, feb, mar = datetime(2024, 1, 1), datetime(2024, 2, 1), datetime(2024, 3, 3)
    p = RefillPredictor()
    ordered = p._calculate_avg_refill_interval([jan, feb, mar])
    assert p._calculate_avg_refill_interval([mar, jan, feb]) == ordered
    assert ordered > 0
