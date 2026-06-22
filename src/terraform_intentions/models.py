"""Pydantic models for the TFC run-task payload and result callback."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

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
