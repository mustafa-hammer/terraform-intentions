"""LangChain LCEL chain that compares a Terraform plan to a PR's stated intention.

The chain receives two text inputs — a PR description and a compact plan summary — and
returns a structured ``Verdict`` using ``with_structured_output``.  The LLM is only
ever used for advisory analysis; the webhook always posts a non-blocking result to TFC.

Usage::

    chain = build_verdict_chain(api_key="sk-...", model="gpt-4o-mini")
    verdict = await chain.ainvoke({"pr_body": "...", "plan_summary": "..."})
"""

from __future__ import annotations

import logging

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI

from .models import PlanSummary, TaskOutcome, Verdict

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are an expert Terraform code reviewer.
Your job is to decide whether the infrastructure changes in a Terraform plan are \
consistent with the intention stated in the associated pull-request description.

Rules:
- Data sources, null_resource, and local-only resources (terraform_data, random_*) are \
  almost never unexpected — treat them as consistent unless the PR description explicitly \
  excludes them.
- Tag-only attribute updates are cosmetic; treat them as consistent.
- Focus on resource *type* and *action* (create/update/delete/replace). A plan that \
  creates an aws_instance when the PR says "add EC2 instance" is consistent.
- If the PR description is empty or very short, be lenient — insufficient context is not \
  grounds for a warning; only flag genuinely surprising changes.
- Be concise.  One short paragraph for reasoning is enough.
"""

_HUMAN_PROMPT = """\
## Pull-request description

{pr_body}

## Terraform plan changes (compact)

{plan_summary}

Evaluate whether the plan aligns with the PR intention and return a structured verdict.
"""

_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", _SYSTEM_PROMPT),
        ("human", _HUMAN_PROMPT),
    ]
)


# ---------------------------------------------------------------------------
# Chain factory
# ---------------------------------------------------------------------------


def build_verdict_chain(
    *,
    api_key: str,
    model: str = "gpt-4o-mini",
) -> Runnable:
    """Return an LCEL runnable that accepts ``pr_body`` + ``plan_summary`` and yields a Verdict.

    The chain is ``_PROMPT | llm.with_structured_output(Verdict)`` — a minimal, explicit
    LCEL pipeline.  We keep it as a factory so tests can inject different models or mocks.

    Args:
        api_key: OpenAI API key.
        model: OpenAI chat model name (default: ``gpt-4o-mini``).

    Returns:
        A LangChain ``Runnable`` whose ``ainvoke`` accepts
        ``{"pr_body": str, "plan_summary": str}`` and returns a ``Verdict``.
    """
    llm = ChatOpenAI(model=model, api_key=api_key, temperature=0)  # type: ignore[arg-type]
    return _PROMPT | llm.with_structured_output(Verdict)


# ---------------------------------------------------------------------------
# Helper: render plan summary as text for the prompt
# ---------------------------------------------------------------------------


def plan_summary_to_text(summary: PlanSummary) -> str:
    """Render a ``PlanSummary`` as a short human-readable list for the LLM prompt.

    Each line is:  ``<action(s)>  <address>  (<type>)``

    Example::

        create  aws_instance.web  (aws_instance)
        delete  aws_security_group.old  (aws_security_group)
    """
    if not summary.changes:
        return "(no actionable changes)"
    lines = []
    for change in summary.changes:
        actions = "/".join(change.actions) if change.actions else "unknown"
        resource_type = f"  ({change.type})" if change.type else ""
        lines.append(f"{actions}  {change.address}{resource_type}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Verdict → TFC outcomes mapper
# ---------------------------------------------------------------------------

# Maps our severity levels to TFC's outcome result tags.
# TFC recognises "result:passed", "result:warning", and "result:failed" as tag values.
_SEVERITY_TO_RESULT_TAG: dict[str, str] = {
    "none": "result:passed",
    "warning": "result:warning",
    "critical": "result:failed",
}


def verdict_to_tfc_outcome(verdict: Verdict, run_id: str | None = None) -> list[TaskOutcome]:
    """Map a ``Verdict`` to a list of TFC ``TaskOutcome`` objects.

    TFC renders each outcome as a collapsible row in the run-task UI panel.
    We produce one primary outcome row (the overall verdict) and one additional
    row per unexpected resource, so engineers can see exactly what was flagged
    without reading a long message string.

    Args:
        verdict: The structured verdict from the LangChain chain.
        run_id: Optional TFC run ID used to make ``outcome_id`` values stable and unique.

    Returns:
        A non-empty list of ``TaskOutcome`` objects ready to be serialised into the
        TFC callback PATCH body's ``outcomes`` array.
    """
    prefix = run_id or "run"
    result_tag = _SEVERITY_TO_RESULT_TAG.get(verdict.severity, "result:passed")

    # Build the markdown body for the primary outcome detail panel.
    body_lines = [f"**Severity:** {verdict.severity.upper()}", "", verdict.reasoning]
    if verdict.unexpected_resources:
        body_lines += [
            "",
            "**Unexpected resources:**",
            *[f"- `{addr}`" for addr in verdict.unexpected_resources],
        ]
    body_md = "\n".join(body_lines)

    primary_description = (
        "✅ Plan matches PR intention"
        if verdict.matches
        else f"⚠️ {len(verdict.unexpected_resources)} unexpected resource(s) detected"
    )

    outcomes: list[TaskOutcome] = [
        TaskOutcome(
            outcome_id=f"{prefix}:intention-check",
            description=primary_description,
            tags={"result": [{"label": result_tag}]},
            body=body_md,
        )
    ]

    # One row per unexpected resource — makes the TFC UI scannable at a glance.
    for i, addr in enumerate(verdict.unexpected_resources):
        outcomes.append(
            TaskOutcome(
                outcome_id=f"{prefix}:unexpected:{i}",
                description=f"Unexpected: {addr}",
                tags={"result": [{"label": "result:failed"}]},
            )
        )

    return outcomes
