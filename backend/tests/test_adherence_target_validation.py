from datetime import datetime

import pytest

from backend.utils.adherence_analytics import MedicationLog, calculate_adherence_rate


def test_negative_target_doses_rejected():
    log = MedicationLog(medication_id="m", medication_name="M", timestamp=datetime(2024, 1, 1), taken=True)
    with pytest.raises(ValueError):
        calculate_adherence_rate([log], target_doses=-5)
