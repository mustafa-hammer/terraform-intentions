"""Tests for the run-task webhook endpoint."""

import asyncio
import hashlib
import hmac
import json
from collections.abc import AsyncIterator, Iterator
from typing import Any

import pytest
import respx
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient, Response

from terraform_intentions import app as app_module
from terraform_intentions.app import _redact, app
from terraform_intentions.config import get_settings

KEY = "test-secret"
TEAM_TOKEN = "test-team-token"


@pytest.fixture(autouse=True)
def _configure(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("TFI_TFC_HMAC_KEY", KEY)
    monkeypatch.setenv("TFI_TFC_TEAM_TOKEN", TEAM_TOKEN)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
async def async_client() -> AsyncIterator[AsyncClient]:
    """Provide an async client that properly cleans up."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    # Give background tasks time to complete before test cleanup
    await asyncio.sleep(0.2)


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


def test_redact_masks_access_token() -> None:
    redacted = _redact({"access_token": "tok-secret", "run_id": "run-1"})
    assert redacted == {"access_token": "***redacted***", "run_id": "run-1"}


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


@pytest.mark.asyncio
@respx.mock
async def test_non_pr_run_passes_with_note(
    async_client: AsyncClient, captured_calls: list[dict[str, Any]]
) -> None:
    """Test that non-PR runs pass with a note."""
    cv_id = "cv-abc123"
    payload = {
        "access_token": "tok-123",
        "task_result_callback_url": "https://app.terraform.io/callback/abc",
        "configuration_version_id": cv_id,
        "is_speculative": False,
    }

    # Mock ingress attributes response (non-PR)
    ingress_url = (
        f"https://app.terraform.io/api/v2/configuration-versions/{cv_id}/ingress-attributes"
    )
    ingress_response = {
        "data": {
            "type": "ingress-attributes",
            "attributes": {
                "is-pull-request": False,
                "identifier": "org/repo",
                "branch": "main",
            },
        }
    }
    respx.get(ingress_url).mock(return_value=Response(200, json=ingress_response))

    body = json.dumps(payload).encode()
    headers = {"X-Tfc-Task-Signature": _sign(body)}
    response = await async_client.post("/run-task", content=body, headers=headers)
    assert response.status_code == 200

    # Wait for background task to complete
    await asyncio.sleep(0.15)

    # Should have called back with "passed" and a note about no PR
    assert len(captured_calls) == 1
    assert captured_calls[0]["args"][0] == "passed"
    assert "No PR associated" in captured_calls[0]["args"][1]


@pytest.mark.asyncio
@respx.mock
async def test_missing_configuration_version_id_passes_with_note(
    async_client: AsyncClient, captured_calls: list[dict[str, Any]]
) -> None:
    """Test that missing configuration_version_id passes with a note."""
    payload = {
        "access_token": "tok-123",
        "task_result_callback_url": "https://app.terraform.io/callback/abc",
        "configuration_version_id": None,
    }

    body = json.dumps(payload).encode()
    headers = {"X-Tfc-Task-Signature": _sign(body)}
    response = await async_client.post("/run-task", content=body, headers=headers)
    assert response.status_code == 200

    # Wait for background task to complete
    await asyncio.sleep(0.15)

    # Should have called back with "passed" and a note
    assert len(captured_calls) == 1
    assert captured_calls[0]["args"][0] == "passed"
    assert "No PR associated" in captured_calls[0]["args"][1]


@pytest.mark.asyncio
@respx.mock
async def test_pr_run_with_changes_posts_summary(
    async_client: AsyncClient, captured_calls: list[dict[str, Any]]
) -> None:
    """Test that PR run with changes posts a summary."""
    cv_id = "cv-abc123"
    plan_url = "https://app.terraform.io/api/v2/plans/plan-123/json-output"
    payload = {
        "access_token": "tok-123",
        "task_result_callback_url": "https://app.terraform.io/callback/abc",
        "configuration_version_id": cv_id,
        "plan_json_api_url": plan_url,
        "is_speculative": False,
    }

    # Mock ingress attributes response (PR)
    ingress_url = (
        f"https://app.terraform.io/api/v2/configuration-versions/{cv_id}/ingress-attributes"
    )
    ingress_response = {
        "data": {
            "type": "ingress-attributes",
            "attributes": {
                "is-pull-request": True,
                "pull-request-number": 42,
                "pull-request-body": "Add S3 bucket for logs",
                "identifier": "org/repo",
                "branch": "feature/add-bucket",
            },
        }
    }
    respx.get(ingress_url).mock(return_value=Response(200, json=ingress_response))

    # Mock plan JSON response
    plan_response = {
        "format_version": "1.0",
        "resource_changes": [
            {
                "address": "aws_s3_bucket.logs",
                "type": "aws_s3_bucket",
                "change": {"actions": ["create"]},
            },
            {
                "address": "aws_s3_bucket_versioning.logs",
                "type": "aws_s3_bucket_versioning",
                "change": {"actions": ["create"]},
            },
        ],
    }
    respx.get(plan_url).mock(return_value=Response(200, json=plan_response))

    body = json.dumps(payload).encode()
    headers = {"X-Tfc-Task-Signature": _sign(body)}
    response = await async_client.post("/run-task", content=body, headers=headers)
    assert response.status_code == 200

    # Wait for background task to complete
    await asyncio.sleep(0.15)

    # Should have called back with "passed" and a summary
    assert len(captured_calls) == 1
    assert captured_calls[0]["args"][0] == "passed"
    message = captured_calls[0]["args"][1]
    assert "Slice 2 data gathering complete" in message
    assert "PR #42" in message
    assert "2 resources" in message
    assert "Creates: 2" in message


@pytest.mark.asyncio
@respx.mock
async def test_pr_run_with_empty_plan_skips_check(
    async_client: AsyncClient, captured_calls: list[dict[str, Any]]
) -> None:
    """Test that PR run with no changes skips the check."""
    cv_id = "cv-abc123"
    plan_url = "https://app.terraform.io/api/v2/plans/plan-123/json-output"
    payload = {
        "access_token": "tok-123",
        "task_result_callback_url": "https://app.terraform.io/callback/abc",
        "configuration_version_id": cv_id,
        "plan_json_api_url": plan_url,
    }

    # Mock ingress attributes response (PR)
    ingress_url = (
        f"https://app.terraform.io/api/v2/configuration-versions/{cv_id}/ingress-attributes"
    )
    ingress_response = {
        "data": {
            "type": "ingress-attributes",
            "attributes": {
                "is-pull-request": True,
                "pull-request-number": 43,
                "pull-request-body": "Update docs only",
                "identifier": "org/repo",
                "branch": "docs/update",
            },
        }
    }
    respx.get(ingress_url).mock(return_value=Response(200, json=ingress_response))

    # Mock plan JSON response (no changes)
    plan_response = {"format_version": "1.0", "resource_changes": []}
    respx.get(plan_url).mock(return_value=Response(200, json=plan_response))

    body = json.dumps(payload).encode()
    headers = {"X-Tfc-Task-Signature": _sign(body)}
    response = await async_client.post("/run-task", content=body, headers=headers)
    assert response.status_code == 200

    # Wait for background task to complete
    await asyncio.sleep(0.15)

    # Should have called back with "passed" and note about no changes
    assert len(captured_calls) == 1
    assert captured_calls[0]["args"][0] == "passed"
    message = captured_calls[0]["args"][1]
    assert "Plan has no changes" in message


@pytest.mark.asyncio
@respx.mock
async def test_http_error_fetching_data_posts_error(
    async_client: AsyncClient, captured_calls: list[dict[str, Any]]
) -> None:
    """Test that HTTP errors are handled gracefully."""
    cv_id = "cv-abc123"
    payload = {
        "access_token": "tok-123",
        "task_result_callback_url": "https://app.terraform.io/callback/abc",
        "configuration_version_id": cv_id,
    }

    # Mock ingress attributes to return 404
    ingress_url = (
        f"https://app.terraform.io/api/v2/configuration-versions/{cv_id}/ingress-attributes"
    )
    respx.get(ingress_url).mock(return_value=Response(404, json={"errors": ["Not found"]}))

    body = json.dumps(payload).encode()
    headers = {"X-Tfc-Task-Signature": _sign(body)}
    response = await async_client.post("/run-task", content=body, headers=headers)
    assert response.status_code == 200

    # Wait for background task to complete
    await asyncio.sleep(0.15)

    # Should have called back with "passed" and error message
    assert len(captured_calls) == 1
    assert captured_calls[0]["args"][0] == "passed"
    message = captured_calls[0]["args"][1]
    assert "⚠️" in message
    assert "Failed to fetch" in message
