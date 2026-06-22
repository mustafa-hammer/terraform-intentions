"""Tests for the run-task webhook endpoint."""

import hashlib
import hmac
import json
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from terraform_intentions import app as app_module
from terraform_intentions.app import app
from terraform_intentions.config import get_settings

KEY = "test-secret"


@pytest.fixture(autouse=True)
def _configure(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("TFI_TFC_HMAC_KEY", KEY)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def captured_calls(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    """Replace the outbound callback with a recorder so no network is hit."""
    calls: list[dict[str, Any]] = []

    async def fake_post_task_result(
        callback_url: str, access_token: str, *args: Any, **kw: Any
    ) -> None:
        calls.append({"callback_url": callback_url, "access_token": access_token, "args": args})

    monkeypatch.setattr(app_module, "post_task_result", fake_post_task_result)
    return calls


def _sign(body: bytes) -> str:
    return hmac.new(KEY.encode(), body, hashlib.sha512).hexdigest()


def _post(client: TestClient, payload: dict[str, Any], *, sign: bool = True) -> Any:
    body = json.dumps(payload).encode()
    headers = {"X-Tfc-Task-Signature": _sign(body) if sign else "deadbeef"}
    return client.post("/run-task", content=body, headers=headers)


def test_healthz() -> None:
    assert TestClient(app).get("/healthz").json() == {"status": "ok"}


def test_valid_request_schedules_callback(captured_calls: list[dict[str, Any]]) -> None:
    payload = {
        "access_token": "tok-123",
        "task_result_callback_url": "https://app.terraform.io/callback/abc",
        "run_id": "run-xyz",
    }
    response = _post(TestClient(app), payload)
    assert response.status_code == 200
    assert len(captured_calls) == 1
    assert captured_calls[0]["callback_url"] == payload["task_result_callback_url"]
    assert captured_calls[0]["access_token"] == "tok-123"
    assert "passed" in captured_calls[0]["args"]


def test_bad_signature_returns_401(captured_calls: list[dict[str, Any]]) -> None:
    payload = {"access_token": "tok", "task_result_callback_url": "x"}
    response = _post(TestClient(app), payload, sign=False)
    assert response.status_code == 401
    assert captured_calls == []


def test_verification_event_acks_without_callback(captured_calls: list[dict[str, Any]]) -> None:
    response = _post(TestClient(app), {"access_token": None, "task_result_callback_url": None})
    assert response.status_code == 200
    assert captured_calls == []
