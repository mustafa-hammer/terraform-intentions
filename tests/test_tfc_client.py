"""Tests for the TFC API client."""

from typing import Any

import pytest
import respx
from httpx import Response

from terraform_intentions.models import IngressAttributes
from terraform_intentions.tfc_client import TFCClient

BASE_URL = "https://app.terraform.io/api/v2"
TEAM_TOKEN = "test-token"


@pytest.fixture
def client() -> TFCClient:
    """Create a TFC client for testing."""
    return TFCClient(BASE_URL, TEAM_TOKEN, timeout=5.0)


@respx.mock
async def test_fetch_plan_json(client: TFCClient) -> None:
    """Test fetching plan JSON from TFC."""
    plan_url = "https://app.terraform.io/api/v2/plans/plan-123/json-output"
    expected_plan = {"format_version": "1.0", "resource_changes": []}

    respx.get(plan_url).mock(return_value=Response(200, json=expected_plan))

    result = await client.fetch_plan_json(plan_url)

    assert result == expected_plan


@respx.mock
async def test_fetch_ingress_attributes(client: TFCClient) -> None:
    """Test fetching ingress attributes from TFC."""
    cv_id = "cv-abc123"
    expected_url = f"{BASE_URL}/configuration-versions/{cv_id}/ingress-attributes"

    response_data = {
        "data": {
            "type": "ingress-attributes",
            "attributes": {
                "is-pull-request": True,
                "pull-request-number": 42,
                "pull-request-body": "Add S3 bucket",
                "identifier": "org/repo",
                "branch": "feature/add-bucket",
            },
        }
    }

    respx.get(expected_url).mock(return_value=Response(200, json=response_data))

    result = await client.fetch_ingress_attributes(cv_id)

    assert isinstance(result, IngressAttributes)
    assert result.is_pull_request is True
    assert result.pull_request_number == 42
    assert result.pull_request_body == "Add S3 bucket"
    assert result.identifier == "org/repo"
    assert result.branch == "feature/add-bucket"


@respx.mock
async def test_fetch_ingress_attributes_non_pr(client: TFCClient) -> None:
    """Test fetching ingress attributes for non-PR run."""
    cv_id = "cv-xyz789"
    expected_url = f"{BASE_URL}/configuration-versions/{cv_id}/ingress-attributes"

    response_data = {
        "data": {
            "type": "ingress-attributes",
            "attributes": {
                "is-pull-request": False,
                "identifier": "org/repo",
                "branch": "main",
            },
        }
    }

    respx.get(expected_url).mock(return_value=Response(200, json=response_data))

    result = await client.fetch_ingress_attributes(cv_id)

    assert result.is_pull_request is False
    assert result.pull_request_number is None
    assert result.pull_request_body is None


def test_summarize_plan_creates(client: TFCClient) -> None:
    """Test plan summary correctly categorizes creates."""
    plan_json: dict[str, Any] = {
        "resource_changes": [
            {
                "address": "aws_s3_bucket.example",
                "type": "aws_s3_bucket",
                "change": {"actions": ["create"]},
            },
            {
                "address": "aws_s3_bucket.another",
                "type": "aws_s3_bucket",
                "change": {"actions": ["create"]},
            },
        ]
    }

    summary = client.summarize_plan(plan_json)

    assert summary.creates == ["aws_s3_bucket.example", "aws_s3_bucket.another"]
    assert summary.updates == []
    assert summary.deletes == []
    assert summary.replaces == []
    assert summary.total_changes == 2
    assert not summary.is_empty()


def test_summarize_plan_updates(client: TFCClient) -> None:
    """Test plan summary correctly categorizes updates."""
    plan_json: dict[str, Any] = {
        "resource_changes": [
            {
                "address": "aws_s3_bucket.existing",
                "type": "aws_s3_bucket",
                "change": {"actions": ["update"]},
            }
        ]
    }

    summary = client.summarize_plan(plan_json)

    assert summary.creates == []
    assert summary.updates == ["aws_s3_bucket.existing"]
    assert summary.deletes == []
    assert summary.replaces == []
    assert summary.total_changes == 1


def test_summarize_plan_deletes(client: TFCClient) -> None:
    """Test plan summary correctly categorizes deletes."""
    plan_json: dict[str, Any] = {
        "resource_changes": [
            {
                "address": "aws_s3_bucket.old",
                "type": "aws_s3_bucket",
                "change": {"actions": ["delete"]},
            }
        ]
    }

    summary = client.summarize_plan(plan_json)

    assert summary.creates == []
    assert summary.updates == []
    assert summary.deletes == ["aws_s3_bucket.old"]
    assert summary.replaces == []
    assert summary.total_changes == 1


def test_summarize_plan_replaces(client: TFCClient) -> None:
    """Test plan summary correctly identifies replace actions."""
    plan_json: dict[str, Any] = {
        "resource_changes": [
            {
                "address": "aws_instance.web",
                "type": "aws_instance",
                "change": {"actions": ["delete", "create"]},
            }
        ]
    }

    summary = client.summarize_plan(plan_json)

    assert summary.creates == []
    assert summary.updates == []
    assert summary.deletes == []
    assert summary.replaces == ["aws_instance.web"]
    assert summary.total_changes == 1


def test_summarize_plan_skips_noops(client: TFCClient) -> None:
    """Test plan summary ignores no-op changes."""
    plan_json: dict[str, Any] = {
        "resource_changes": [
            {
                "address": "aws_s3_bucket.unchanged",
                "type": "aws_s3_bucket",
                "change": {"actions": ["no-op"]},
            },
            {
                "address": "aws_s3_bucket.created",
                "type": "aws_s3_bucket",
                "change": {"actions": ["create"]},
            },
        ]
    }

    summary = client.summarize_plan(plan_json)

    assert summary.creates == ["aws_s3_bucket.created"]
    assert summary.total_changes == 1


def test_summarize_plan_mixed_changes(client: TFCClient) -> None:
    """Test plan summary with multiple change types."""
    plan_json: dict[str, Any] = {
        "resource_changes": [
            {
                "address": "aws_s3_bucket.new",
                "type": "aws_s3_bucket",
                "change": {"actions": ["create"]},
            },
            {
                "address": "aws_s3_bucket.existing",
                "type": "aws_s3_bucket",
                "change": {"actions": ["update"]},
            },
            {
                "address": "aws_s3_bucket.old",
                "type": "aws_s3_bucket",
                "change": {"actions": ["delete"]},
            },
            {
                "address": "aws_instance.web",
                "type": "aws_instance",
                "change": {"actions": ["delete", "create"]},
            },
            {
                "address": "data.aws_ami.ubuntu",
                "type": "aws_ami",
                "change": {"actions": ["no-op"]},
            },
        ]
    }

    summary = client.summarize_plan(plan_json)

    assert summary.creates == ["aws_s3_bucket.new"]
    assert summary.updates == ["aws_s3_bucket.existing"]
    assert summary.deletes == ["aws_s3_bucket.old"]
    assert summary.replaces == ["aws_instance.web"]
    assert summary.total_changes == 4


def test_summarize_plan_empty(client: TFCClient) -> None:
    """Test plan summary with no changes."""
    plan_json: dict[str, Any] = {"resource_changes": []}

    summary = client.summarize_plan(plan_json)

    assert summary.creates == []
    assert summary.updates == []
    assert summary.deletes == []
    assert summary.replaces == []
    assert summary.total_changes == 0
    assert summary.is_empty()


def test_summarize_plan_only_noops(client: TFCClient) -> None:
    """Test plan summary with only no-op changes."""
    plan_json: dict[str, Any] = {
        "resource_changes": [
            {
                "address": "aws_s3_bucket.unchanged1",
                "type": "aws_s3_bucket",
                "change": {"actions": ["no-op"]},
            },
            {
                "address": "aws_s3_bucket.unchanged2",
                "type": "aws_s3_bucket",
                "change": {"actions": ["no-op"]},
            },
        ]
    }

    summary = client.summarize_plan(plan_json)

    assert summary.total_changes == 0
    assert summary.is_empty()


# Made with Bob
