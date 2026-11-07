import pytest

from backend.utils.dosage_adjustment import suggest_adjustment


@pytest.mark.parametrize("score", [-3, 0, 4, 16])
def test_out_of_range_child_pugh_rejected(score):
    with pytest.raises(ValueError):
        suggest_adjustment("lithium", 300, child_pugh_score=score)
