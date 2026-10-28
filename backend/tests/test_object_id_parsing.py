import pytest
from bson import ObjectId
from fastapi import HTTPException

from backend.utils.object_ids import parse_object_id


def test_valid_object_id_parses():
    oid = "650d7f3e7b1f8c9d0e1f2a3c"
    assert parse_object_id(oid) == ObjectId(oid)


@pytest.mark.parametrize("bad", ["", "not-an-id", "650d7f3e7b1f8c9d0e1f2a3", "zz" * 12])
def test_malformed_object_id_is_400(bad):
    with pytest.raises(HTTPException) as exc:
        parse_object_id(bad, "patient_id")
    assert exc.value.status_code == 400
    assert "patient_id" in exc.value.detail
