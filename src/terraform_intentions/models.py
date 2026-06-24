"""Pydantic models for the TFC run-task payload and result callback."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

TaskResultStatus = Literal["passed", "failed", "running"]


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


class IngressAttributes(BaseModel):
    """Ingress attributes from TFC configuration-version endpoint."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    is_pull_request: bool = Field(default=False, alias="is-pull-request")
    pull_request_number: int | None = Field(default=None, alias="pull-request-number")
    pull_request_body: str | None = Field(default=None, alias="pull-request-body")
    identifier: str | None = None  # e.g., "org/repo"
    branch: str | None = None


class ResourceChange(BaseModel):
    """A single resource change from the plan JSON."""

    address: str  # e.g., "aws_s3_bucket.example"
    type: str  # e.g., "aws_s3_bucket"
    change: dict[str, Any]  # Contains "actions" list

    @property
    def actions(self) -> list[str]:
        """Extract actions list (e.g., ["create"], ["update"], ["delete", "create"])."""
        actions: list[str] = self.change.get("actions", [])
        return actions


class PlanSummary(BaseModel):
    """Compact summary of plan changes."""

    creates: list[str] = []  # Resource addresses being created
    updates: list[str] = []  # Resource addresses being updated
    deletes: list[str] = []  # Resource addresses being deleted
    replaces: list[str] = []  # Resource addresses being replaced
    total_changes: int = 0

    def is_empty(self) -> bool:
        """True if plan has no actual changes."""
        return self.total_changes == 0


class Verdict(BaseModel):
    """The LLM's structured judgement of plan-vs-PR-intention.

    This is the schema the LangChain chain fills via ``with_structured_output``.
    """

    matches: bool  # True only if the plan does no more AND no less than the description implies
    unexpected_resources: list[str]  # Plan resources beyond the intent (extra/out-of-scope)
    missing_resources: list[str]  # Resources the PR described but the plan does not create
    reasoning: str  # Short explanation of the judgement
    severity: Literal["none", "low", "medium", "high"]  # "none" when matches is True


class Outcome(BaseModel):
    """A structured TFC run-task result outcome.

    Rendered by TFC as an enriched card: ``body`` supports Markdown (lists, line breaks), and
    ``tags`` named ``severity``/``status`` get colour + icon treatment keyed off ``level``.
    """

    outcome_id: str
    description: str  # One-line summary shown as the outcome title
    body: str | None = None  # Markdown detail
    url: str | None = None
    # {tag_name: [{"label": str, "level": "none"|"info"|"warning"|"error"}]}
    tags: dict[str, list[dict[str, str]]] | None = None
