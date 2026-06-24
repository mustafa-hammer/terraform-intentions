"""Tests for the TFC data fetcher (plan JSON + ingress-attributes + plan reduction)."""

import json

import httpx
import pytest
import respx

from terraform_intentions.fetcher import (
    FetchError,
    TFC_API_BASE,
    fetch_ingress_attrs,
    fetch_plan_json,
    reduce_plan,
)
from terraform_intentions.models import PlanSummary

PLAN_URL = "https://app.terraform.io/api/v2/plans/plan-abc/json"
CV_ID = "cv-abc123"
INGRESS_URL = f"{TFC_API_BASE}/configuration-versions/{CV_ID}/ingress-attributes"

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MINIMAL_PLAN: dict[str, object] = {
    "format_version": "1.2",
    "resource_changes": [
        {
            "address": "aws_s3_bucket.example",
            "type": "aws_s3_bucket",
            "name": "example",
            "provider_name": "registry.terraform.io/hashicorp/aws",
            "change": {"actions": ["create"], "before": None, "after": {}},
        },
        {
            "address": "data.aws_caller_identity.current",
            "type": "aws_caller_identity",
            "name": "current",
            "change": {"actions": ["read"]},
        },
        {
            "address": "aws_iam_role.lambda",
            "type": "aws_iam_role",
            "name": "lambda",
            "change": {"actions": ["no-op"]},
        },
    ],
}

INGRESS_BODY: dict[str, object] = {
    "data": {
        "type": "ingress-attributes",
        "attributes": {
            "is-pull-request": True,
            "pull-request-number": 42,
            "pull-request-body": "Add an S3 bucket for static assets.",
            "pull-request-url": "https://github.com/org/repo/pull/42",
            "identifier": "org/repo",
            "branch": "feature/add-s3",
            "commit-sha": "abc123",
        },
    }
}

NON_PR_INGRESS_BODY: dict[str, object] = {
    "data": {
        "type": "ingress-attributes",
        "attributes": {
            "is-pull-request": False,
        },
    }
}


# ---------------------------------------------------------------------------
# fetch_plan_json
# ---------------------------------------------------------------------------


@respx.mock
async def test_fetch_plan_json_returns_parsed_body() -> None:
    respx.get(PLAN_URL).mock(return_value=httpx.Response(200, json=MINIMAL_PLAN))

    result = await fetch_plan_json(PLAN_URL, "tok-run", timeout=5.0)

    assert result["format_version"] == "1.2"
    assert "resource_changes" in result


@respx.mock
async def test_fetch_plan_json_raises_fetch_error_on_http_error() -> None:
    respx.get(PLAN_URL).mock(return_value=httpx.Response(403))

    with pytest.raises(FetchError, match="Failed to fetch plan JSON"):
        await fetch_plan_json(PLAN_URL, "tok-run", timeout=5.0)


@respx.mock
async def test_fetch_plan_json_raises_fetch_error_on_network_error() -> None:
    respx.get(PLAN_URL).mock(side_effect=httpx.ConnectError("timeout"))

    with pytest.raises(FetchError):
        await fetch_plan_json(PLAN_URL, "tok-run", timeout=5.0)


# ---------------------------------------------------------------------------
# fetch_ingress_attrs
# ---------------------------------------------------------------------------


@respx.mock
async def test_fetch_ingress_attrs_parses_pr_fields() -> None:
    respx.get(INGRESS_URL).mock(return_value=httpx.Response(200, json=INGRESS_BODY))

    attrs = await fetch_ingress_attrs(CV_ID, "tok-team", timeout=5.0)

    assert attrs.is_pull_request is True
    assert attrs.pull_request_number == 42
    assert attrs.pull_request_body == "Add an S3 bucket for static assets."
    assert attrs.identifier == "org/repo"
    assert attrs.branch == "feature/add-s3"
    assert attrs.commit_sha == "abc123"


@respx.mock
async def test_fetch_ingress_attrs_handles_non_pr_run() -> None:
    respx.get(INGRESS_URL).mock(return_value=httpx.Response(200, json=NON_PR_INGRESS_BODY))

    attrs = await fetch_ingress_attrs(CV_ID, "tok-team", timeout=5.0)

    assert attrs.is_pull_request is False
    assert attrs.pull_request_body is None


@respx.mock
async def test_fetch_ingress_attrs_raises_on_http_error() -> None:
    respx.get(INGRESS_URL).mock(return_value=httpx.Response(404))

    with pytest.raises(FetchError, match="Failed to fetch ingress-attributes"):
        await fetch_ingress_attrs(CV_ID, "tok-team", timeout=5.0)


@respx.mock
async def test_fetch_ingress_attrs_raises_on_malformed_body() -> None:
    respx.get(INGRESS_URL).mock(return_value=httpx.Response(200, json={"unexpected": "shape"}))

    with pytest.raises(FetchError, match="Unexpected ingress-attributes shape"):
        await fetch_ingress_attrs(CV_ID, "tok-team", timeout=5.0)


# ---------------------------------------------------------------------------
# reduce_plan / PlanSummary.from_plan_json
# ---------------------------------------------------------------------------


def test_reduce_plan_keeps_only_actionable_changes() -> None:
    summary = reduce_plan(MINIMAL_PLAN)

    # Only the create should survive; read and no-op are dropped.
    assert len(summary.changes) == 1
    assert summary.changes[0].address == "aws_s3_bucket.example"
    assert summary.changes[0].actions == ["create"]
    assert summary.changes[0].type == "aws_s3_bucket"


def test_reduce_plan_handles_empty_resource_changes() -> None:
    summary = reduce_plan({"resource_changes": []})
    assert summary.changes == []


def test_reduce_plan_handles_missing_resource_changes() -> None:
    summary = reduce_plan({})
    assert summary.changes == []


def test_reduce_plan_handles_multiple_actions() -> None:
    plan: dict[str, object] = {
        "resource_changes": [
            {
                "address": "aws_instance.web",
                "type": "aws_instance",
                "name": "web",
                "change": {"actions": ["delete", "create"]},  # replace
            },
        ]
    }
    summary = reduce_plan(plan)
    assert len(summary.changes) == 1
    assert set(summary.changes[0].actions) == {"delete", "create"}


def test_reduce_plan_handles_update() -> None:
    plan: dict[str, object] = {
        "resource_changes": [
            {
                "address": "aws_security_group.web",
                "type": "aws_security_group",
                "name": "web",
                "change": {"actions": ["update"]},
            },
        ]
    }
    summary = reduce_plan(plan)
    assert len(summary.changes) == 1
    assert summary.changes[0].actions == ["update"]


def test_plan_summary_from_plan_json_is_idempotent() -> None:
    """Calling from_plan_json twice produces the same result."""
    raw = json.dumps(MINIMAL_PLAN)
    a = PlanSummary.from_plan_json(json.loads(raw))
    b = PlanSummary.from_plan_json(json.loads(raw))
    assert a == b
