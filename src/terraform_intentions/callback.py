"""Post a run-task result back to TFC's callback URL."""

import logging

import httpx

from .models import TaskResultStatus

logger = logging.getLogger(__name__)

# TFC's run-task callback speaks JSON:API.
_JSON_API_CONTENT_TYPE = "application/vnd.api+json"


def _build_payload(status: TaskResultStatus, message: str, url: str | None) -> dict[str, object]:
    attributes: dict[str, object] = {"status": status, "message": message}
    if url is not None:
        attributes["url"] = url
    return {"data": {"type": "task-results", "attributes": attributes}}


async def post_task_result(
    callback_url: str,
    access_token: str,
    status: TaskResultStatus,
    message: str,
    *,
    timeout: float,
    url: str | None = None,
) -> None:
    """PATCH the run-task result to ``callback_url``, authenticated with ``access_token``.

    Errors are logged rather than raised: this runs in a background task after the 200
    response, so there is no caller to surface an exception to.
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": _JSON_API_CONTENT_TYPE,
    }
    body = _build_payload(status, message, url)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.patch(callback_url, json=body, headers=headers)
            response.raise_for_status()
        logger.info("Posted run-task result status=%s", status)
    except httpx.HTTPError:
        logger.exception("Failed to post run-task result to %s", callback_url)
