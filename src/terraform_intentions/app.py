"""FastAPI app exposing the TFC run-task webhook.

Slice 1: verify the signature, ack 200 immediately, and asynchronously post a hardcoded
``passed`` verdict back to TFC. No plan/PR analysis yet.
"""

import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import BackgroundTasks, FastAPI, Request, Response

from .callback import post_task_result
from .config import get_settings
from .models import RunTaskPayload
from .security import verify_signature

logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    """Make our package's INFO logs visible.

    Python drops INFO from a logger with no handler, so under uvicorn our messages would
    otherwise vanish. Reuse uvicorn's handler (consistent formatting) when present; fall
    back to basicConfig when run standalone (e.g. tests).
    """
    pkg_logger = logging.getLogger("terraform_intentions")
    pkg_logger.setLevel(logging.INFO)
    if pkg_logger.handlers:
        return
    uvicorn_logger = logging.getLogger("uvicorn.error")
    if uvicorn_logger.handlers:
        for handler in uvicorn_logger.handlers:
            pkg_logger.addHandler(handler)
        pkg_logger.propagate = False
    else:
        logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    _configure_logging()
    yield


app = FastAPI(title="terraform-intentions", version="0.1.0", lifespan=lifespan)

_STUB_MESSAGE = "Advisory check passed (Slice 1 round-trip stub)."

# Payload keys to mask before logging — short-lived credentials, not for logs.
_SENSITIVE_KEYS = frozenset({"access_token"})


def _redact(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a shallow copy of ``payload`` with sensitive values masked."""
    return {k: ("***redacted***" if k in _SENSITIVE_KEYS else v) for k, v in payload.items()}


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

    # Log the full payload (redacted) so we can see exactly what TFC sends and code
    # against fields we don't model yet. Body is trusted here (signature verified).
    raw_dict: dict[str, Any] = json.loads(raw)
    logger.info("Received run-task payload:\n%s", json.dumps(_redact(raw_dict), indent=2))
    payload = RunTaskPayload.model_validate(raw_dict)

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
