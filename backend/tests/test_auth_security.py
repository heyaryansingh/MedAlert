"""Tests for password hashing and JWT token handling."""

import importlib
from datetime import timedelta

import pytest

from utils import auth_security
from utils.auth_security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_is_not_the_plaintext(self):
        hashed = hash_password("correct horse battery staple")
        assert hashed != "correct horse battery staple"
        assert hashed.startswith("$2")

    def test_correct_password_verifies(self):
        assert verify_password("s3cret", hash_password("s3cret"))

    def test_wrong_password_rejected(self):
        assert not verify_password("wrong", hash_password("s3cret"))

    def test_hashes_are_salted(self):
        assert hash_password("same") != hash_password("same")


class TestAccessTokens:
    def test_round_trip_preserves_claims(self):
        token = create_access_token({"sub": "user123", "role": "patient"})
        payload = decode_access_token(token)
        assert payload["sub"] == "user123"
        assert payload["role"] == "patient"

    def test_expired_token_is_rejected(self):
        token = create_access_token(
            {"sub": "user123"}, expires_delta=timedelta(seconds=-1)
        )
        assert decode_access_token(token) is None

    def test_garbage_token_is_rejected(self):
        assert decode_access_token("not.a.jwt") is None

    def test_token_signed_with_another_key_is_rejected(self):
        from jose import jwt

        forged = jwt.encode(
            {"sub": "attacker", "role": "doctor"}, "some-other-key", algorithm="HS256"
        )
        assert decode_access_token(forged) is None


class TestJWTSecretConfiguration:
    def test_configured_secret_is_used(self, monkeypatch):
        monkeypatch.setenv("MEDALERT_JWT_SECRET", "an-explicitly-configured-secret")
        reloaded = importlib.reload(auth_security)
        try:
            assert reloaded.JWT_SECRET_KEY == "an-explicitly-configured-secret"
        finally:
            monkeypatch.delenv("MEDALERT_JWT_SECRET", raising=False)
            importlib.reload(auth_security)

    def test_unset_secret_is_random_not_a_known_constant(self, monkeypatch):
        """An unset secret must never fall back to a value in the source tree."""
        monkeypatch.delenv("MEDALERT_JWT_SECRET", raising=False)
        first = importlib.reload(auth_security).JWT_SECRET_KEY
        second = importlib.reload(auth_security).JWT_SECRET_KEY
        try:
            assert first != "dev-secret-change-in-production"
            assert first != second, "fallback secret must be generated per process"
            assert len(first) >= 32
        finally:
            importlib.reload(auth_security)

    def test_token_forged_with_the_old_default_secret_is_rejected(self, monkeypatch):
        """The previously hardcoded secret must not validate anything."""
        from jose import jwt

        monkeypatch.delenv("MEDALERT_JWT_SECRET", raising=False)
        reloaded = importlib.reload(auth_security)
        try:
            forged = jwt.encode(
                {"sub": "attacker", "role": "doctor"},
                "dev-secret-change-in-production",
                algorithm="HS256",
            )
            assert reloaded.decode_access_token(forged) is None
        finally:
            importlib.reload(auth_security)
