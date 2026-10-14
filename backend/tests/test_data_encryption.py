"""Tests for backend.utils.data_encryption."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from backend.utils.data_encryption import (
    HealthDataEncryption,
    decrypt_patient_data,
    encrypt_patient_data,
)


def test_round_trip_sensitive_fields():
    key = HealthDataEncryption().key.decode()
    patient = {"name": "Pat", "diagnosis": "T2 diabetes", "ssn": "123-45-6789"}
    encrypted = encrypt_patient_data(patient, key)
    assert encrypted["name"] == "Pat"
    assert encrypted["diagnosis"] != "T2 diabetes"
    assert decrypt_patient_data(encrypted, key) == patient


def test_wrong_key_raises_instead_of_returning_ciphertext():
    encrypted = encrypt_patient_data({"diagnosis": "asthma"}, HealthDataEncryption().key.decode())
    with pytest.raises(ValueError):
        decrypt_patient_data(encrypted, HealthDataEncryption().key.decode())


def test_plaintext_field_left_untouched():
    key = HealthDataEncryption().key.decode()
    assert decrypt_patient_data({"diagnosis": "asthma"}, key) == {"diagnosis": "asthma"}


def test_password_key_is_reproducible_with_stored_salt():
    salt = os.urandom(16)
    k1 = HealthDataEncryption.generate_key_from_password("hunter2", salt)
    k2 = HealthDataEncryption.generate_key_from_password("hunter2", salt)
    assert k1 == k2
    token = HealthDataEncryption(k1.decode()).encrypt("lab: A1c 7.1")
    assert HealthDataEncryption(k2.decode()).decrypt(token) == "lab: A1c 7.1"


@pytest.mark.parametrize("salt", [None, b"short"])
def test_password_key_requires_real_salt(salt):
    with pytest.raises(ValueError):
        HealthDataEncryption.generate_key_from_password("hunter2", salt)
