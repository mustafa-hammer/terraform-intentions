"""Tests for HMAC signature verification."""

import hashlib
import hmac

from terraform_intentions.security import verify_signature

KEY = "test-secret"
BODY = b'{"payload_version":1,"run_id":"run-abc"}'


def _sign(body: bytes, key: str) -> str:
    return hmac.new(key.encode(), body, hashlib.sha512).hexdigest()


def test_valid_signature_passes() -> None:
    assert verify_signature(BODY, _sign(BODY, KEY), KEY) is True


def test_tampered_body_fails() -> None:
    assert verify_signature(BODY + b" ", _sign(BODY, KEY), KEY) is False


def test_wrong_key_fails() -> None:
    assert verify_signature(BODY, _sign(BODY, "other-key"), KEY) is False


def test_missing_signature_fails() -> None:
    assert verify_signature(BODY, None, KEY) is False
    assert verify_signature(BODY, "", KEY) is False
