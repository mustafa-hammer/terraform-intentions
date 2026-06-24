"""Tests for the LangChain verdict chain (verdicts.py).

All LLM calls are mocked so no real OpenAI key is needed.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from terraform_intentions.models import PlanSummary, ResourceChange, Verdict
from terraform_intentions.verdicts import (
    build_verdict_chain,
    plan_summary_to_text,
    verdict_to_tfc_outcome,
)


# ---------------------------------------------------------------------------
# plan_summary_to_text
# ---------------------------------------------------------------------------


def _make_summary(*entries: tuple[str, str, list[str]]) -> PlanSummary:
    """Build a PlanSummary from (address, type, actions) tuples."""
    changes = [
        ResourceChange(address=addr, type=rtype, actions=actions)
        for addr, rtype, actions in entries
    ]
    return PlanSummary(changes=changes)


def test_plan_summary_to_text_empty() -> None:
    summary = PlanSummary(changes=[])
    assert plan_summary_to_text(summary) == "(no actionable changes)"


def test_plan_summary_to_text_single_change() -> None:
    summary = _make_summary(("aws_instance.web", "aws_instance", ["create"]))
    text = plan_summary_to_text(summary)
    assert "create" in text
    assert "aws_instance.web" in text
    assert "aws_instance" in text


def test_plan_summary_to_text_multiple_changes() -> None:
    summary = _make_summary(
        ("aws_s3_bucket.data", "aws_s3_bucket", ["create"]),
        ("aws_iam_role.old", "aws_iam_role", ["delete"]),
        ("aws_instance.app", "aws_instance", ["update"]),
    )
    text = plan_summary_to_text(summary)
    lines = text.splitlines()
    assert len(lines) == 3
    assert any("aws_s3_bucket.data" in line for line in lines)
    assert any("delete" in line for line in lines)


def test_plan_summary_to_text_replace_action() -> None:
    summary = _make_summary(("module.vpc.aws_subnet.public", "aws_subnet", ["delete", "create"]))
    text = plan_summary_to_text(summary)
    assert "delete/create" in text
    assert "module.vpc.aws_subnet.public" in text


def test_plan_summary_to_text_no_type() -> None:
    changes = [ResourceChange(address="null_resource.wait", actions=["create"])]
    summary = PlanSummary(changes=changes)
    text = plan_summary_to_text(summary)
    assert "null_resource.wait" in text
    # No type annotation when type is None
    assert "()" not in text


# ---------------------------------------------------------------------------
# build_verdict_chain + ainvoke (mocked LLM)
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_verdict() -> Verdict:
    return Verdict(
        matches=True,
        unexpected_resources=[],
        reasoning="The plan creates the EC2 instance mentioned in the PR.",
        severity="none",
    )


@pytest.fixture
def mock_chain(mock_verdict: Verdict) -> MagicMock:
    """Return a mock LCEL chain whose ainvoke returns the canned verdict."""
    chain = MagicMock()
    chain.ainvoke = AsyncMock(return_value=mock_verdict)
    return chain


async def test_chain_ainvoke_returns_verdict(mock_chain: MagicMock, mock_verdict: Verdict) -> None:
    """Verify the chain contract: ainvoke(inputs) -> Verdict."""
    result = await mock_chain.ainvoke(
        {"pr_body": "Add an EC2 instance for the web tier.", "plan_summary": "create  aws_instance.web  (aws_instance)"}
    )
    assert isinstance(result, Verdict)
    assert result.matches is True
    assert result.severity == "none"
    assert result.unexpected_resources == []


async def test_chain_mismatch_verdict() -> None:
    """build_verdict_chain wires prompt → llm.with_structured_output; mock the whole chain."""
    bad_verdict = Verdict(
        matches=False,
        unexpected_resources=["aws_rds_instance.prod"],
        reasoning="The PR only mentions S3 but the plan creates an RDS instance.",
        severity="critical",
    )
    chain = MagicMock()
    chain.ainvoke = AsyncMock(return_value=bad_verdict)

    result: Verdict = await chain.ainvoke(
        {"pr_body": "Add an S3 bucket.", "plan_summary": "create  aws_rds_instance.prod  (aws_rds_instance)"}
    )
    assert result.matches is False
    assert result.severity == "critical"
    assert "aws_rds_instance.prod" in result.unexpected_resources


def test_build_verdict_chain_returns_runnable() -> None:
    """build_verdict_chain should return a LangChain Runnable without making any API calls."""
    with patch("terraform_intentions.verdicts.ChatOpenAI") as mock_llm_cls:
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = MagicMock()
        mock_llm_cls.return_value = mock_llm

        chain = build_verdict_chain(api_key="sk-test", model="gpt-4o-mini")

        mock_llm_cls.assert_called_once_with(
            model="gpt-4o-mini", api_key="sk-test", temperature=0
        )
        mock_llm.with_structured_output.assert_called_once_with(Verdict)
        assert chain is not None


# ---------------------------------------------------------------------------
# Verdict model validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "severity",
    ["none", "warning", "critical"],
)
def test_verdict_accepts_valid_severities(severity: str) -> None:
    v = Verdict(matches=True, unexpected_resources=[], reasoning="ok", severity=severity)  # type: ignore[arg-type]
    assert v.severity == severity


def test_verdict_rejects_invalid_severity() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Verdict(
            matches=True,
            unexpected_resources=[],
            reasoning="ok",
            severity="high",  # type: ignore[arg-type]
        )


def test_verdict_unexpected_resources_defaults_to_empty() -> None:
    v = Verdict(matches=True, reasoning="ok", severity="none")
    assert v.unexpected_resources == []


# ---------------------------------------------------------------------------
# verdict_to_tfc_outcome
# ---------------------------------------------------------------------------


def _passing_verdict() -> Verdict:
    return Verdict(
        matches=True,
        unexpected_resources=[],
        reasoning="The plan creates the S3 bucket mentioned in the PR.",
        severity="none",
    )


def _failing_verdict() -> Verdict:
    return Verdict(
        matches=False,
        unexpected_resources=["aws_rds_instance.prod", "aws_db_subnet_group.main"],
        reasoning="The PR only mentions S3 but the plan creates an RDS instance and subnet group.",
        severity="critical",
    )


def test_outcome_passing_verdict_has_one_row() -> None:
    outcomes = verdict_to_tfc_outcome(_passing_verdict(), run_id="run-abc")
    assert len(outcomes) == 1
    primary = outcomes[0]
    assert primary.outcome_id == "run-abc:intention-check"
    assert "matches" in primary.description.lower() or "✅" in primary.description


def test_outcome_passing_verdict_result_tag_is_passed() -> None:
    outcomes = verdict_to_tfc_outcome(_passing_verdict())
    assert outcomes[0].tags == {"result": [{"label": "result:passed"}]}


def test_outcome_failing_verdict_has_extra_rows_per_resource() -> None:
    verdict = _failing_verdict()
    outcomes = verdict_to_tfc_outcome(verdict, run_id="run-xyz")
    # 1 primary + 1 per unexpected resource
    assert len(outcomes) == 1 + len(verdict.unexpected_resources)


def test_outcome_failing_resource_rows_have_unique_ids() -> None:
    outcomes = verdict_to_tfc_outcome(_failing_verdict(), run_id="run-1")
    ids = [o.outcome_id for o in outcomes]
    assert len(ids) == len(set(ids)), "outcome_id values must be unique"


def test_outcome_failing_resource_rows_contain_address() -> None:
    outcomes = verdict_to_tfc_outcome(_failing_verdict(), run_id="run-1")
    resource_rows = outcomes[1:]
    addresses = [o.description for o in resource_rows]
    assert any("aws_rds_instance.prod" in d for d in addresses)
    assert any("aws_db_subnet_group.main" in d for d in addresses)


def test_outcome_failing_verdict_result_tag_is_failed() -> None:
    outcomes = verdict_to_tfc_outcome(_failing_verdict())
    assert outcomes[0].tags == {"result": [{"label": "result:failed"}]}


def test_outcome_warning_verdict_result_tag_is_warning() -> None:
    v = Verdict(
        matches=False,
        unexpected_resources=["aws_cloudwatch_metric_alarm.cpu"],
        reasoning="Minor discrepancy.",
        severity="warning",
    )
    outcomes = verdict_to_tfc_outcome(v)
    assert outcomes[0].tags == {"result": [{"label": "result:warning"}]}


def test_outcome_body_contains_reasoning() -> None:
    verdict = _passing_verdict()
    outcomes = verdict_to_tfc_outcome(verdict)
    assert verdict.reasoning in (outcomes[0].body or "")


def test_outcome_body_lists_unexpected_resources() -> None:
    verdict = _failing_verdict()
    outcomes = verdict_to_tfc_outcome(verdict)
    body = outcomes[0].body or ""
    assert "aws_rds_instance.prod" in body
    assert "aws_db_subnet_group.main" in body


def test_outcome_fallback_run_id_when_none() -> None:
    outcomes = verdict_to_tfc_outcome(_passing_verdict(), run_id=None)
    assert outcomes[0].outcome_id.startswith("run:")


def test_outcome_serialises_with_wire_names() -> None:
    """model_dump(by_alias=True) must produce 'outcome-id', not 'outcome_id'."""
    outcomes = verdict_to_tfc_outcome(_passing_verdict(), run_id="run-1")
    serialised = outcomes[0].model_dump(by_alias=True, exclude_none=True)
    assert "outcome-id" in serialised
    assert "outcome_id" not in serialised
