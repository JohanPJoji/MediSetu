"""
Unit tests for app.core.security — password hashing and JWT handling.

Per ARCHITECTURE.md §76 (TESTING STRATEGY), unit tests should cover
services/business rules directly, not just through the API layer. These
tests import app.core.security functions directly (no HTTP, no database).
"""

import time

import jwt
import pytest

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_password_produces_a_different_string_than_the_input() -> None:
    hashed = hash_password("my-secret-password")
    assert hashed != "my-secret-password"
    assert hashed.startswith("$2b$")  # bcrypt hash prefix


def test_verify_password_accepts_correct_password() -> None:
    hashed = hash_password("my-secret-password")
    assert verify_password("my-secret-password", hashed) is True


def test_verify_password_rejects_incorrect_password() -> None:
    hashed = hash_password("my-secret-password")
    assert verify_password("wrong-password", hashed) is False


def test_verify_password_rejects_malformed_hash_without_raising() -> None:
    # Should return False, not raise — a malformed hash must never become
    # an authentication bypass or an unhandled exception.
    assert verify_password("anything", "not-a-real-bcrypt-hash") is False


def test_create_and_decode_access_token_round_trip() -> None:
    token = create_access_token(subject="user-123", role="PATIENT")
    payload = decode_access_token(token)

    assert payload["sub"] == "user-123"
    assert payload["role"] == "PATIENT"
    assert "exp" in payload
    assert "iat" in payload


def test_decode_access_token_rejects_tampered_token() -> None:
    token = create_access_token(subject="user-123", role="PATIENT")
    tampered = token[:-4] + "abcd"  # corrupt the signature

    with pytest.raises(jwt.PyJWTError):
        decode_access_token(tampered)


def test_decode_access_token_rejects_garbage_string() -> None:
    with pytest.raises(jwt.PyJWTError):
        decode_access_token("not.a.jwt")


def test_decode_access_token_rejects_expired_token() -> None:
    # expires_minutes accepts a float internally via timedelta, but the
    # public signature types it as int | None — pass 0 and sleep past
    # issuance to guarantee expiry deterministically.
    token = create_access_token(subject="user-123", role="PATIENT", expires_minutes=0)
    time.sleep(1)

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)
