"""Tests for the run-task webhook endpoint."""

import asyncio
import hashlib
import hmac
import json
from collections.abc import AsyncIterator, Callable, Iterator
from typing import Any

import pytest
import respx
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient, Response

from terraform_intentions import app as app_module
from terraform_intentions.app import _redact, app
from terraform_intentions.config import get_settings
from terraform_intentions.models import Verdict

KEY = "test-secret"
TEAM_TOKEN = "test-team-token"


@pytest.fixture(autouse=True)
def _configure(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("TFI_TFC_HMAC_KEY", KEY)
    monkeypatch.setenv("TFI_TFC_TEAM_TOKEN", TEAM_TOKEN)
    monkeypatch.setenv("TFI_ANTHROPIC_API_KEY", "test-anthropic-key")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def set_verdict(monkeypatch: pytest.MonkeyPatch) -> Callable[..., None]:
    """Patch app.analyze_intention to return a canned verdict (or raise), keeping tests offline."""

    def _set(verdict: Verdict | None = None, *, raises: Exception | None = None) -> None:
        async def fake_analyze(pr_body: str, summary: Any, settings: Any, **kw: Any) -> Verdict:
            if raises is not None:
                raise raises
            assert verdict is not None
            return verdict

        monkeypatch.setattr(app_module, "analyze_intention", fake_analyze)

    return _set


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
        calls.append(
            {
                "callback_url": callback_url,
                "access_token": access_token,
                "args": args,
                "kwargs": kw,
            }
        )

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


def _mock_pr_run(
    cv_id: str, plan_url: str, *, pr_body: str, resource_changes: list[dict[str, Any]]
) -> None:
    """Register respx mocks for a PR-associated run with the given plan changes."""
    ingress_url = (
        f"https://app.terraform.io/api/v2/configuration-versions/{cv_id}/ingress-attributes"
    )
    respx.get(ingress_url).mock(
        return_value=Response(
            200,
            json={
                "data": {
                    "type": "ingress-attributes",
                    "attributes": {
                        "is-pull-request": True,
                        "pull-request-number": 42,
                        "pull-request-body": pr_body,
                        "identifier": "org/repo",
                        "branch": "feature/x",
                    },
                }
            },
        )
    )
    respx.get(plan_url).mock(
        return_value=Response(
            200, json={"format_version": "1.0", "resource_changes": resource_changes}
        )
    )


@pytest.mark.asyncio
@respx.mock
async def test_pr_run_matching_verdict_passes(
    async_client: AsyncClient,
    captured_calls: list[dict[str, Any]],
    set_verdict: Callable[..., None],
) -> None:
    """A verdict with matches=True posts 'passed'."""
    cv_id = "cv-abc123"
    plan_url = "https://app.terraform.io/api/v2/plans/plan-123/json-output"
    _mock_pr_run(
        cv_id,
        plan_url,
        pr_body="Add S3 bucket for logs",
        resource_changes=[
            {
                "address": "aws_s3_bucket.logs",
                "type": "aws_s3_bucket",
                "change": {"actions": ["create"]},
            },
        ],
    )
    set_verdict(
        Verdict(
            matches=True,
            unexpected_resources=[],
            missing_resources=[],
            reasoning="Plan only adds the bucket.",
            severity="none",
        )
    )

    payload = {
        "access_token": "tok-123",
        "task_result_callback_url": "https://app.terraform.io/callback/abc",
        "configuration_version_id": cv_id,
        "plan_json_api_url": plan_url,
    }
    body = json.dumps(payload).encode()
    response = await async_client.post(
        "/run-task", content=body, headers={"X-Tfc-Task-Signature": _sign(body)}
    )
    assert response.status_code == 200
    await asyncio.sleep(0.15)

    assert len(captured_calls) == 1
    assert captured_calls[0]["args"][0] == "passed"
    assert "matches" in captured_calls[0]["args"][1].lower()


@pytest.mark.asyncio
@respx.mock
async def test_pr_run_mismatch_verdict_fails_and_names_resource(
    async_client: AsyncClient,
    captured_calls: list[dict[str, Any]],
    set_verdict: Callable[..., None],
) -> None:
    """The done-when: S3-only description but plan also creates RDS → 'failed' naming the RDS."""
    cv_id = "cv-abc123"
    plan_url = "https://app.terraform.io/api/v2/plans/plan-123/json-output"
    _mock_pr_run(
        cv_id,
        plan_url,
        pr_body="Add an S3 bucket",
        resource_changes=[
            {
                "address": "aws_s3_bucket.logs",
                "type": "aws_s3_bucket",
                "change": {"actions": ["create"]},
            },
            {
                "address": "aws_db_instance.main",
                "type": "aws_db_instance",
                "change": {"actions": ["create"]},
            },
        ],
    )
    set_verdict(
        Verdict(
            matches=False,
            unexpected_resources=["aws_db_instance.main"],
            missing_resources=[],
            reasoning="The PR mentions only an S3 bucket but the plan also creates RDS.",
            severity="high",
        )
    )

    payload = {
        "access_token": "tok-123",
        "task_result_callback_url": "https://app.terraform.io/callback/abc",
        "configuration_version_id": cv_id,
        "plan_json_api_url": plan_url,
    }
    body = json.dumps(payload).encode()
    response = await async_client.post(
        "/run-task", content=body, headers={"X-Tfc-Task-Signature": _sign(body)}
    )
    assert response.status_code == 200
    await asyncio.sleep(0.15)

    assert len(captured_calls) == 1
    assert captured_calls[0]["args"][0] == "failed"
    # The flat message is a one-line summary; the resource is named in the structured outcome.
    outcomes = captured_calls[0]["kwargs"]["outcomes"]
    assert len(outcomes) == 1
    assert "aws_db_instance.main" in outcomes[0].body
    assert outcomes[0].tags["status"] == [{"label": "Failed", "level": "error"}]


@pytest.mark.asyncio
@respx.mock
async def test_pr_run_missing_resource_fails(
    async_client: AsyncClient,
    captured_calls: list[dict[str, Any]],
    set_verdict: Callable[..., None],
) -> None:
    """PR describes an S3 bucket the plan never creates → 'failed' with a 'missing' note."""
    cv_id = "cv-abc123"
    plan_url = "https://app.terraform.io/api/v2/plans/plan-123/json-output"
    _mock_pr_run(
        cv_id,
        plan_url,
        pr_body="Add an EC2 instance and an S3 bucket",
        resource_changes=[
            {
                "address": "aws_instance.example",
                "type": "aws_instance",
                "change": {"actions": ["create"]},
            },
        ],
    )
    set_verdict(
        Verdict(
            matches=False,
            unexpected_resources=[],
            missing_resources=["an S3 bucket"],
            reasoning="The PR describes an S3 bucket that the plan does not create.",
            severity="medium",
        )
    )

    payload = {
        "access_token": "tok-123",
        "task_result_callback_url": "https://app.terraform.io/callback/abc",
        "configuration_version_id": cv_id,
        "plan_json_api_url": plan_url,
    }
    body = json.dumps(payload).encode()
    response = await async_client.post(
        "/run-task", content=body, headers={"X-Tfc-Task-Signature": _sign(body)}
    )
    assert response.status_code == 200
    await asyncio.sleep(0.15)

    assert len(captured_calls) == 1
    assert captured_calls[0]["args"][0] == "failed"
    outcomes = captured_calls[0]["kwargs"]["outcomes"]
    assert "Described but not in the plan" in outcomes[0].body
    assert "an S3 bucket" in outcomes[0].body


@pytest.mark.asyncio
@respx.mock
async def test_pr_run_empty_body_skips_llm(
    async_client: AsyncClient,
    captured_calls: list[dict[str, Any]],
    set_verdict: Callable[..., None],
) -> None:
    """An empty PR body short-circuits to 'passed' without invoking the chain."""
    cv_id = "cv-abc123"
    plan_url = "https://app.terraform.io/api/v2/plans/plan-123/json-output"
    _mock_pr_run(
        cv_id,
        plan_url,
        pr_body="   ",
        resource_changes=[
            {
                "address": "aws_s3_bucket.logs",
                "type": "aws_s3_bucket",
                "change": {"actions": ["create"]},
            },
        ],
    )
    # If the chain were called, this would raise and fail the test.
    set_verdict(raises=AssertionError("chain should not be invoked for empty PR body"))

    payload = {
        "access_token": "tok-123",
        "task_result_callback_url": "https://app.terraform.io/callback/abc",
        "configuration_version_id": cv_id,
        "plan_json_api_url": plan_url,
    }
    body = json.dumps(payload).encode()
    response = await async_client.post(
        "/run-task", content=body, headers={"X-Tfc-Task-Signature": _sign(body)}
    )
    assert response.status_code == 200
    await asyncio.sleep(0.15)

    assert len(captured_calls) == 1
    assert captured_calls[0]["args"][0] == "passed"
    assert "No PR description" in captured_calls[0]["args"][1]


@pytest.mark.asyncio
@respx.mock
async def test_pr_run_llm_failure_fails_closed(
    async_client: AsyncClient,
    captured_calls: list[dict[str, Any]],
    set_verdict: Callable[..., None],
) -> None:
    """If the LLM call raises, the check is inconclusive → post 'failed' (fail closed)."""
    cv_id = "cv-abc123"
    plan_url = "https://app.terraform.io/api/v2/plans/plan-123/json-output"
    _mock_pr_run(
        cv_id,
        plan_url,
        pr_body="Add an S3 bucket",
        resource_changes=[
            {
                "address": "aws_s3_bucket.logs",
                "type": "aws_s3_bucket",
                "change": {"actions": ["create"]},
            },
        ],
    )
    set_verdict(raises=RuntimeError("anthropic timeout"))

    payload = {
        "access_token": "tok-123",
        "task_result_callback_url": "https://app.terraform.io/callback/abc",
        "configuration_version_id": cv_id,
        "plan_json_api_url": plan_url,
    }
    body = json.dumps(payload).encode()
    response = await async_client.post(
        "/run-task", content=body, headers={"X-Tfc-Task-Signature": _sign(body)}
    )
    assert response.status_code == 200
    await asyncio.sleep(0.15)

    assert len(captured_calls) == 1
    assert captured_calls[0]["args"][0] == "failed"
    message = captured_calls[0]["args"][1]
    assert "⚠️" in message
    assert "could not complete" in message


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
async def test_http_error_fetching_data_fails_closed(
    async_client: AsyncClient, captured_calls: list[dict[str, Any]]
) -> None:
    """A TFC fetch error is inconclusive → post 'failed' (fail closed), not a false pass."""
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

    # Should have called back with "failed" and an inconclusive-check message
    assert len(captured_calls) == 1
    assert captured_calls[0]["args"][0] == "failed"
    message = captured_calls[0]["args"][1]
    assert "⚠️" in message
    assert "could not complete" in message
    assert "inconclusive" in message
