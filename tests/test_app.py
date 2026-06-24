"""Tests for the run-task webhook endpoint."""

import hashlib
import hmac
import json
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from terraform_intentions import app as app_module
from terraform_intentions.app import _redact, app
from terraform_intentions.config import Settings, get_settings
from terraform_intentions.models import RunTaskPayload

KEY = "test-secret"
TEAM_TOKEN = "tok-team-test"


@pytest.fixture(autouse=True)
def _configure(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("TFI_TFC_HMAC_KEY", KEY)
    monkeypatch.setenv("TFI_TFC_TEAM_TOKEN", TEAM_TOKEN)
    monkeypatch.setenv("TFI_OPENAI_API_KEY", "sk-test")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def captured_background(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    """Stub out _analyze_and_callback so endpoint tests don't make real HTTP calls.

    Records each invocation so tests can assert the right payload was scheduled.
    The deep logic of _analyze_and_callback is covered by test_fetcher.py.
    """
    calls: list[dict[str, Any]] = []

    async def fake_analyze(payload: RunTaskPayload, settings: Settings) -> None:
        calls.append({"payload": payload, "settings": settings})

    monkeypatch.setattr(app_module, "_analyze_and_callback", fake_analyze)
    return calls


def _sign(body: bytes) -> str:
    return hmac.new(KEY.encode(), body, hashlib.sha512).hexdigest()


def _post(client: TestClient, payload: dict[str, Any], *, sign: bool = True) -> Any:
    body = json.dumps(payload).encode()
    headers = {"X-Tfc-Task-Signature": _sign(body) if sign else "deadbeef"}
    return client.post("/run-task", content=body, headers=headers)


def test_redact_masks_access_token() -> None:
    redacted = _redact({"access_token": "tok-secret", "run_id": "run-1"})
    assert redacted == {"access_token": "***redacted***", "run_id": "run-1"}


def test_healthz() -> None:
    assert TestClient(app).get("/healthz").json() == {"status": "ok"}


def test_valid_request_schedules_analysis(captured_background: list[dict[str, Any]]) -> None:
    payload = {
        "access_token": "tok-123",
        "task_result_callback_url": "https://app.terraform.io/callback/abc",
        "run_id": "run-xyz",
    }
    response = _post(TestClient(app), payload)
    assert response.status_code == 200
    assert len(captured_background) == 1
    scheduled = captured_background[0]["payload"]
    assert scheduled.access_token == "tok-123"
    assert scheduled.task_result_callback_url == payload["task_result_callback_url"]
    assert scheduled.run_id == "run-xyz"


def test_bad_signature_returns_401(captured_background: list[dict[str, Any]]) -> None:
    payload = {"access_token": "tok", "task_result_callback_url": "x"}
    response = _post(TestClient(app), payload, sign=False)
    assert response.status_code == 401
    assert captured_background == []


def test_verification_event_acks_without_analysis(
    captured_background: list[dict[str, Any]],
) -> None:
    response = _post(TestClient(app), {"access_token": None, "task_result_callback_url": None})
    assert response.status_code == 200
    assert captured_background == []
