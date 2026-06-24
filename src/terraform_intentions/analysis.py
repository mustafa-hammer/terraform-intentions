"""The LangChain intention-check chain.

Slice 3: one LCEL chain — (PR body + plan summary) → structured ``Verdict`` via
``with_structured_output``. Deliberately simple; the prompt is not optimised yet (that is
Slice 4). This is the "learn LangChain" payoff, though the Anthropic SDK alone would also do it.
"""

from __future__ import annotations

from typing import cast

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from pydantic import SecretStr

from .config import Settings
from .models import PlanSummary, Verdict

# A run task fires post-plan. We judge whether the plan matches the *intent* of the PR — not
# whether every resource is named. Kept short on purpose — Slice 4 refines this.
_SYSTEM_PROMPT = (
    "You review a Terraform Cloud plan against the pull request that triggered it. Judge the "
    "author's INTENT — the spirit of what they set out to build — not a literal, "
    "resource-by-resource match against the wording.\n\n"
    "The PR description states what the author intends to build. The plan summary lists the "
    "resource changes. The plan should do what the description says — NO MORE and NO LESS. Check "
    "BOTH directions:\n\n"
    "1. EXTRA — anything in the plan BEYOND the author's intent. Put genuinely out-of-scope plan "
    "resource addresses (exactly as given in the plan summary) in `unexpected_resources`. But "
    "treat as IN-SCOPE the supporting resources a described resource normally requires, even when "
    "unnamed: an EC2 instance reasonably implies its IAM role, instance profile, policy "
    "attachments, and security groups; an S3 bucket implies its bucket policy and versioning. "
    "'An EC2 with an instance profile' implies the IAM role and role-policy attachments that make "
    "that profile work — those are expected, not surprises. Out-of-scope means a clearly "
    "different purpose (e.g. a database when only compute was described, an unmentioned "
    "public-facing endpoint) or destroying unrelated infrastructure.\n\n"
    "2. MISSING — anything the description EXPLICITLY calls for that the plan does NOT create. "
    "Put a short description of each (e.g. 'an S3 bucket') in `missing_resources`. Only count "
    "resources the author explicitly named; do NOT list implied supporting plumbing as missing.\n\n"
    "Set `matches` to TRUE only when BOTH `unexpected_resources` and `missing_resources` are "
    "empty. If either has entries, set `matches` to FALSE. When genuinely in doubt about an "
    "incidental item, lean towards in-scope — this check targets real mismatches, not nitpicks.\n\n"
    "Explain in `reasoning`. Set `severity` to `none` when it matches, otherwise `low`/`medium`/"
    "`high` by how far the plan strays from the stated intent. Reason ONLY from the changes "
    "given; do not assume actions (such as a replace or delete) that are not present in the "
    "summary.\n\n"
    "Keep `reasoning` to one or two plain sentences. Do NOT enumerate every resource or use "
    "markdown, bullet points, or backticks — a separate UI element already lists the resources "
    "and their actions. `reasoning` should explain the judgement, not restate the plan."
)

_HUMAN_PROMPT = (
    "PR description:\n{pr_body}\n\nPlan changes (JSON; resource addresses):\n{plan_summary}"
)

_PROMPT = ChatPromptTemplate.from_messages([("system", _SYSTEM_PROMPT), ("human", _HUMAN_PROMPT)])


def build_chain(settings: Settings) -> Runnable[dict[str, str], Verdict]:
    """Build the LCEL chain: prompt | ChatAnthropic(structured → Verdict).

    Tests inject their own chain into :func:`analyze_intention` instead of building this one,
    so this stays free of test seams and just wires the real model.
    """
    # ChatAnthropic's pydantic field aliases confuse mypy (it wants the aliases); the field
    # names work at runtime (populate_by_name). Ignore the call-arg noise on this one call.
    model = ChatAnthropic(  # type: ignore[call-arg]
        model=settings.model_id,
        api_key=SecretStr(settings.anthropic_api_key),
        timeout=settings.llm_timeout,
        max_retries=settings.llm_max_retries,
    )
    structured = model.with_structured_output(Verdict)
    return cast("Runnable[dict[str, str], Verdict]", _PROMPT | structured)


async def analyze_intention(
    pr_body: str,
    summary: PlanSummary,
    settings: Settings,
    *,
    chain: Runnable[dict[str, str], Verdict] | None = None,
) -> Verdict:
    """Compare a PR description against a plan summary and return a structured verdict.

    ``chain`` is the test seam: pass a fake ``Runnable`` (e.g. a ``RunnableLambda`` returning a
    canned ``Verdict``) to keep tests offline. In production it is built from ``settings``.
    """
    chain = chain or build_chain(settings)
    result = await chain.ainvoke(
        {"pr_body": pr_body, "plan_summary": summary.model_dump_json(indent=2)}
    )
    return result
