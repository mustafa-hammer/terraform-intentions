"""Post a run-task result back to TFC's callback URL."""

import logging

import httpx

from .models import TaskOutcome, TaskResultStatus

logger = logging.getLogger(__name__)

# TFC's run-task callback speaks JSON:API.
_JSON_API_CONTENT_TYPE = "application/vnd.api+json"


def _build_payload(
    status: TaskResultStatus,
    message: str,
    url: str | None,
    outcomes: list[TaskOutcome] | None,
) -> dict[str, object]:
    attributes: dict[str, object] = {"status": status, "message": message}
    if url is not None:
        attributes["url"] = url
    if outcomes:
        # Serialise each TaskOutcome using by_alias=True so Python snake_case fields
        # (outcome_id) are sent as their TFC wire names (outcome-id).
        attributes["outcomes"] = [
            o.model_dump(by_alias=True, exclude_none=True) for o in outcomes
        ]
    return {"data": {"type": "task-results", "attributes": attributes}}


async def post_task_result(
    callback_url: str,
    access_token: str,
    status: TaskResultStatus,
    message: str,
    *,
    timeout: float,
    url: str | None = None,
    outcomes: list[TaskOutcome] | None = None,
) -> None:
    """PATCH the run-task result to ``callback_url``, authenticated with ``access_token``.

    Args:
        callback_url: The ``task_result_callback_url`` from the run-task payload.
        access_token: The short-lived bearer token from the run-task payload.
        status: TFC result status — ``"passed"``, ``"failed"``, or ``"running"``.
        message: Short summary shown in the TFC UI (plain text, max ~500 chars).
        timeout: HTTP request timeout in seconds.
        url: Optional URL linked from the result row in the TFC UI.
        outcomes: Optional list of structured outcome rows rendered in the TFC UI panel.

    Errors are logged rather than raised: this runs in a background task after the 200
    response, so there is no caller to surface an exception to.
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": _JSON_API_CONTENT_TYPE,
    }
    body = _build_payload(status, message, url, outcomes)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.patch(callback_url, json=body, headers=headers)
            response.raise_for_status()
        logger.info("Posted run-task result status=%s outcomes=%d", status, len(outcomes or []))
    except httpx.HTTPError:
        logger.exception("Failed to post run-task result to %s", callback_url)
