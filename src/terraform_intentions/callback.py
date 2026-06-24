"""Post a run-task result back to TFC's callback URL."""

import logging

import httpx

from .models import Outcome, TaskResultStatus

logger = logging.getLogger(__name__)

# TFC's run-task callback speaks JSON:API.
_JSON_API_CONTENT_TYPE = "application/vnd.api+json"


def _outcome_resource(outcome: Outcome) -> dict[str, object]:
    """Serialize an Outcome to its inline JSON:API resource (kebab-case keys, drop None)."""
    attributes: dict[str, object] = {
        "outcome-id": outcome.outcome_id,
        "description": outcome.description,
    }
    if outcome.body is not None:
        attributes["body"] = outcome.body
    if outcome.url is not None:
        attributes["url"] = outcome.url
    if outcome.tags is not None:
        attributes["tags"] = outcome.tags
    return {"type": "task-result-outcomes", "attributes": attributes}


def _build_payload(
    status: TaskResultStatus,
    message: str,
    url: str | None,
    outcomes: list[Outcome] | None,
) -> dict[str, object]:
    attributes: dict[str, object] = {"status": status, "message": message}
    if url is not None:
        attributes["url"] = url
    data: dict[str, object] = {"type": "task-results", "attributes": attributes}
    if outcomes:
        data["relationships"] = {"outcomes": {"data": [_outcome_resource(o) for o in outcomes]}}
    return {"data": data}


async def post_task_result(
    callback_url: str,
    access_token: str,
    status: TaskResultStatus,
    message: str,
    *,
    timeout: float,
    url: str | None = None,
    outcomes: list[Outcome] | None = None,
) -> None:
    """PATCH the run-task result to ``callback_url``, authenticated with ``access_token``.

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
        logger.info("Posted run-task result status=%s", status)
    except httpx.HTTPError:
        logger.exception("Failed to post run-task result to %s", callback_url)
