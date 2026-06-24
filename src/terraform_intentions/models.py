"""Pydantic models for the TFC run-task payload, result callback, and fetched plan data."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

TaskResultStatus = Literal["passed", "failed", "running"]

# ---------------------------------------------------------------------------
# TFC run-task outcomes (richer structured result items shown in the TFC UI)
# ---------------------------------------------------------------------------


class TaskOutcome(BaseModel):
    """One item in the ``outcomes`` array of a TFC run-task result PATCH.

    TFC renders each outcome as a collapsible row in the run-task UI panel.
    All fields except ``outcome_id`` and ``description`` are optional.

    See: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/run-tasks/run-tasks-integration
    """

    model_config = ConfigDict(populate_by_name=True)

    # Required: stable identifier used for de-duplication across re-deliveries.
    outcome_id: str = Field(serialization_alias="outcome-id")
    # Human-readable label shown in the TFC UI row.
    description: str
    # Optional severity tag: "result:passed" | "result:failed" | "result:warning"
    tags: dict[str, list[dict[str, str]]] | None = None
    # Optional markdown body rendered in the expandable detail panel.
    body: str | None = None
    # Optional URL linked from the outcome row (e.g. deep-link to a dashboard).
    url: str | None = None


# ---------------------------------------------------------------------------
# Ingress-attributes (PR metadata from TFC configuration version)
# ---------------------------------------------------------------------------


class IngressAttributes(BaseModel):
    """Relevant fields from GET /configuration-versions/{cv}/ingress-attributes.

    TFC returns a JSON:API document; we parse the ``attributes`` object only.
    All fields are optional — non-VCS workspaces omit most of them.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    is_pull_request: bool = Field(False, alias="is-pull-request")
    pull_request_number: int | None = Field(None, alias="pull-request-number")
    pull_request_body: str | None = Field(None, alias="pull-request-body")
    pull_request_url: str | None = Field(None, alias="pull-request-url")
    # repository identifier, e.g. "org/repo"
    identifier: str | None = None
    branch: str | None = None
    commit_sha: str | None = Field(None, alias="commit-sha")


# ---------------------------------------------------------------------------
# Plan JSON reduction
# ---------------------------------------------------------------------------

ChangeAction = Literal["create", "read", "update", "delete", "replace", "no-op", "forget"]


class ResourceChange(BaseModel):
    """One entry from ``resource_changes`` in a Terraform plan JSON.

    We capture only the fields useful for comparing the plan to the PR intent.
    Unknown fields are ignored so we stay stable against different plan schema versions.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    address: str
    type: str | None = None
    name: str | None = None
    provider_name: str | None = None
    actions: list[ChangeAction] = Field(default_factory=list, alias="change_actions")

    @property
    def is_actionable(self) -> bool:
        """True when this change is not a pure no-op or read (i.e. something changes)."""
        return bool(self.actions) and not all(a in ("no-op", "read") for a in self.actions)


class PlanSummary(BaseModel):
    """Compact representation of a plan's meaningful changes, ready for LLM consumption."""

    changes: list[ResourceChange]

    @classmethod
    def from_plan_json(cls, plan: dict[str, object]) -> "PlanSummary":
        """Build a ``PlanSummary`` from a raw Terraform plan JSON dict.

        Parses ``resource_changes``, drops no-ops/reads, and returns only what matters.
        """
        raw_changes = plan.get("resource_changes", [])
        if not isinstance(raw_changes, list):
            return cls(changes=[])

        changes: list[ResourceChange] = []
        for raw in raw_changes:
            if not isinstance(raw, dict):
                continue
            # Flatten: TFC plan JSON nests actions under change.actions
            change_block = raw.get("change", {})
            actions: list[str] = []
            if isinstance(change_block, dict):
                raw_actions = change_block.get("actions")
                if isinstance(raw_actions, list):
                    actions = [str(a) for a in raw_actions]
            entry = ResourceChange.model_validate(
                {
                    "address": raw.get("address", ""),
                    "type": raw.get("type"),
                    "name": raw.get("name"),
                    "provider_name": raw.get("provider_name"),
                    "change_actions": actions,
                }
            )
            if entry.is_actionable:
                changes.append(entry)

        return cls(changes=changes)


class RunTaskPayload(BaseModel):
    """The subset of the TFC post-plan run-task payload we care about.

    Unknown fields are ignored so TFC can add payload fields without breaking parsing.
    The initial verification request TFC sends when a run task is created has a null
    ``access_token`` and no real callback — hence those two fields are optional.
    """

    model_config = ConfigDict(extra="ignore")

    access_token: str | None = None
    task_result_callback_url: str | None = None
    plan_json_api_url: str | None = None
    configuration_version_id: str | None = None
    task_result_enforcement_level: str | None = None
    run_id: str | None = None
    vcs_branch: str | None = None
    is_speculative: bool | None = None
    organization_name: str | None = None
    workspace_name: str | None = None

    @property
    def is_verification_event(self) -> bool:
        """True for TFC's endpoint-verification ping (no token / nothing to call back)."""
        return not (self.access_token and self.task_result_callback_url)


# ---------------------------------------------------------------------------
# LLM verdict
# ---------------------------------------------------------------------------

VerdictSeverity = Literal["none", "warning", "critical"]


class Verdict(BaseModel):
    """Structured output from the LangChain intention-check chain.

    Fields
    ------
    matches:
        ``True`` when the plan's resource changes appear consistent with the PR intention.
    unexpected_resources:
        List of resource addresses (e.g. ``aws_s3_bucket.logs``) that were not anticipated
        by the PR description.  Empty when ``matches`` is ``True``.
    reasoning:
        One-paragraph human-readable explanation of the verdict, written for the engineer
        who opened the PR.  Cite specific resource addresses when flagging mismatches.
    severity:
        ``"none"``     — plan aligns with the PR intent; no action required.
        ``"warning"``  — minor or ambiguous discrepancies; worth reviewing.
        ``"critical"`` — significant unexpected changes detected.
    """

    matches: bool
    unexpected_resources: Annotated[list[str], Field(default_factory=list)]
    reasoning: str
    severity: VerdictSeverity
