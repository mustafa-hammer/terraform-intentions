"""FastAPI app exposing the TFC run-task webhook.

Slice 1: verify the signature, ack 200 immediately, and asynchronously post a hardcoded
``passed`` verdict back to TFC. No plan/PR analysis yet.
"""

import logging

from fastapi import BackgroundTasks, FastAPI, Request, Response

from .callback import post_task_result
from .config import get_settings
from .models import RunTaskPayload
from .security import verify_signature

logger = logging.getLogger(__name__)

app = FastAPI(title="terraform-intentions", version="0.1.0")

_STUB_MESSAGE = "Advisory check passed (Slice 1 round-trip stub)."


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/run-task")
async def run_task(request: Request, background_tasks: BackgroundTasks) -> Response:
    settings = get_settings()
    raw = await request.body()

    signature = request.headers.get("X-Tfc-Task-Signature")
    if not verify_signature(raw, signature, settings.tfc_hmac_key):
        logger.warning("Rejected run-task request with invalid signature")
        return Response(status_code=401)

    payload = RunTaskPayload.model_validate_json(raw)

    # The endpoint-verification ping has nothing to call back to — just ack it.
    if payload.is_verification_event:
        logger.info("Acknowledged run-task verification event")
        return Response(status_code=200)

    # access_token / callback_url are guaranteed non-None here (not a verification event).
    assert payload.access_token is not None
    assert payload.task_result_callback_url is not None
    background_tasks.add_task(
        post_task_result,
        payload.task_result_callback_url,
        payload.access_token,
        "passed",
        _STUB_MESSAGE,
        timeout=settings.request_timeout,
    )
    return Response(status_code=200)
