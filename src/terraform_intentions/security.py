"""HMAC verification for incoming TFC run-task requests."""

import hashlib
import hmac


def verify_signature(raw_body: bytes, signature: str | None, key: str) -> bool:
    """Return True iff ``signature`` is the HMAC-SHA512 of ``raw_body`` under ``key``.

    TFC sends the hex digest in the ``X-Tfc-Task-Signature`` header, computed over the
    exact raw request body. Comparison is constant-time to avoid timing leaks.
    """
    if not signature:
        return False
    expected = hmac.new(key.encode(), raw_body, hashlib.sha512).hexdigest()
    return hmac.compare_digest(expected, signature)
