import pytest
from utils.dosage_adjustment import calculate_weight_based_dose


@pytest.mark.parametrize("args", [(-5, 70), (5, -70), (5, 0), (float("nan"), 70), (5, 70, -1)])
def test_invalid_weight_dose_rejected(args):
    with pytest.raises(ValueError):
        calculate_weight_based_dose(*args)
