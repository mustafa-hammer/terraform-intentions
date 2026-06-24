"""Tests for the LangChain intention-check chain and verdict-message rendering."""

from typing import Any

import pytest
from langchain_core.runnables import Runnable, RunnableLambda

from terraform_intentions.analysis import analyze_intention
from terraform_intentions.app import _build_verdict_message, _build_verdict_outcome
from terraform_intentions.config import Settings
from terraform_intentions.models import IngressAttributes, PlanSummary, Verdict


def _settings() -> Settings:
    return Settings(
        tfc_hmac_key="k",
        tfc_team_token="t",
        anthropic_api_key="a",
    )


def _fake_chain(verdict: Verdict, seen: dict[str, Any]) -> Runnable[dict[str, str], Verdict]:
    """A stand-in for prompt | structured-model that records its input and returns a verdict."""

    def _run(inputs: dict[str, str]) -> Verdict:
        seen.update(inputs)
        return verdict

    return RunnableLambda(_run)


@pytest.mark.asyncio
async def test_analyze_intention_uses_injected_chain() -> None:
    verdict = Verdict(
        matches=False,
        unexpected_resources=["aws_db_instance.main"],
        missing_resources=[],
        reasoning="Plan also creates an RDS instance.",
        severity="high",
    )
    seen: dict[str, Any] = {}
    summary = PlanSummary(creates=["aws_s3_bucket.logs", "aws_db_instance.main"], total_changes=2)

    result = await analyze_intention(
        "Add an S3 bucket", summary, _settings(), chain=_fake_chain(verdict, seen)
    )

    assert result is verdict
    # The chain receives the PR body and the serialized plan summary.
    assert seen["pr_body"] == "Add an S3 bucket"
    assert "aws_db_instance.main" in seen["plan_summary"]


def _ingress() -> IngressAttributes:
    return IngressAttributes.model_validate({"is-pull-request": True, "pull-request-number": 42})


def test_verdict_message_matches() -> None:
    """The summary message is a single plain sentence (detail lives in the outcome)."""
    verdict = Verdict(
        matches=True,
        unexpected_resources=[],
        missing_resources=[],
        reasoning="All good.",
        severity="none",
    )
    msg = _build_verdict_message(verdict, _ingress())
    assert "✅" in msg
    assert "PR #42" in msg
    assert "matches" in msg.lower()
    # No markdown / backticks leak into the flat field.
    assert "**" not in msg and "`" not in msg


def test_verdict_message_counts_extra_and_missing() -> None:
    verdict = Verdict(
        matches=False,
        unexpected_resources=["aws_db_instance.main"],
        missing_resources=["an S3 bucket"],
        reasoning="Extra database and a missing bucket.",
        severity="high",
    )
    msg = _build_verdict_message(verdict, _ingress())
    assert "⚠️" in msg
    assert "1 unexpected" in msg
    assert "1 missing" in msg
    assert "**" not in msg and "`" not in msg


def test_verdict_outcome_matches_lists_all_changes() -> None:
    verdict = Verdict(
        matches=True,
        unexpected_resources=[],
        missing_resources=[],
        reasoning="All in scope.",
        severity="none",
    )
    summary = PlanSummary(
        creates=["aws_instance.example"],
        updates=["aws_iam_instance_profile.ec2"],
        total_changes=2,
    )
    outcome = _build_verdict_outcome(verdict, summary, _ingress())

    assert outcome.body is not None
    assert "aws_instance.example` — create" in outcome.body
    assert "aws_iam_instance_profile.ec2` — update" in outcome.body
    assert "All in scope." in outcome.body
    # No divergence sections when it matches.
    assert "Beyond the PR description" not in outcome.body
    assert "Described but not in the plan" not in outcome.body
    assert outcome.tags is not None
    assert outcome.tags["status"] == [{"label": "Passed", "level": "info"}]
    assert outcome.tags["severity"] == [{"label": "none", "level": "none"}]


def test_verdict_outcome_flags_extra_with_error_severity() -> None:
    verdict = Verdict(
        matches=False,
        unexpected_resources=["aws_db_instance.main"],
        missing_resources=[],
        reasoning="Adds a database.",
        severity="high",
    )
    summary = PlanSummary(creates=["aws_s3_bucket.logs", "aws_db_instance.main"], total_changes=2)
    outcome = _build_verdict_outcome(verdict, summary, _ingress())

    assert outcome.body is not None
    assert "**Beyond the PR description**" in outcome.body
    assert "aws_db_instance.main" in outcome.body
    assert "Described but not in the plan" not in outcome.body
    assert outcome.description == "Plan provisions more than the PR describes"
    assert outcome.tags is not None
    assert outcome.tags["status"] == [{"label": "Failed", "level": "error"}]
    assert outcome.tags["severity"] == [{"label": "high", "level": "error"}]


def test_verdict_outcome_flags_missing_resource() -> None:
    """PR describes an S3 bucket the plan never creates → 'missing', failed."""
    verdict = Verdict(
        matches=False,
        unexpected_resources=[],
        missing_resources=["an S3 bucket"],
        reasoning="The described S3 bucket is not in the plan.",
        severity="medium",
    )
    summary = PlanSummary(creates=["aws_instance.example"], total_changes=1)
    outcome = _build_verdict_outcome(verdict, summary, _ingress())

    assert outcome.body is not None
    assert "**Described but not in the plan**" in outcome.body
    assert "an S3 bucket" in outcome.body
    assert "Beyond the PR description" not in outcome.body
    assert outcome.description == "Plan is missing resources the PR describes"
