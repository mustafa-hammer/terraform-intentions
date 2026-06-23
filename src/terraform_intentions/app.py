"""FastAPI app exposing the TFC run-task webhook.

Slice 2: fetch plan JSON and ingress attributes, log all data, post summary verdict.
"""

import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastapi import BackgroundTasks, FastAPI, Request, Response

from .callback import post_task_result
from .config import Settings, get_settings
from .models import IngressAttributes, PlanSummary, RunTaskPayload
from .security import verify_signature
from .tfc_client import TFCClient

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
        process_run_task,
        payload,
        settings,
    )
    return Response(status_code=200)


async def process_run_task(payload: RunTaskPayload, settings: Settings) -> None:
    """Background task: fetch data, analyze, post verdict."""
    try:
        client = TFCClient(
            settings.tfc_api_base_url,
            settings.tfc_team_token,
            timeout=settings.request_timeout,
        )

        # Fetch ingress attributes
        if not payload.configuration_version_id:
            logger.warning(
                "No configuration_version_id in payload, cannot fetch ingress attributes"
            )
            await _post_passed_no_pr(payload, settings)
            return

        ingress = await client.fetch_ingress_attributes(payload.configuration_version_id)
        logger.info("Fetched ingress attributes: %s", ingress.model_dump_json(indent=2))

        # Handle non-PR runs
        if not ingress.is_pull_request:
            logger.info(
                "Run is not associated with a PR (is_speculative=%s)", payload.is_speculative
            )
            await _post_passed_no_pr(payload, settings)
            return

        # Fetch plan JSON
        if not payload.plan_json_api_url:
            logger.warning("No plan_json_api_url in payload")
            await _post_passed_no_pr(payload, settings)
            return

        plan_json = await client.fetch_plan_json(payload.plan_json_api_url)
        summary = client.summarize_plan(plan_json)
        logger.info("Plan summary: %s", summary.model_dump_json(indent=2))

        # Log PR context
        logger.info(
            "PR context: repo=%s, PR#%s, branch=%s",
            ingress.identifier,
            ingress.pull_request_number,
            ingress.branch,
        )
        logger.info("PR body:\n%s", ingress.pull_request_body or "(empty)")

        # For Slice 2, still post "passed" but with richer message
        assert payload.task_result_callback_url is not None
        assert payload.access_token is not None
        message = _build_slice2_message(summary, ingress)
        await post_task_result(
            payload.task_result_callback_url,
            payload.access_token,
            "passed",
            message,
            timeout=settings.request_timeout,
        )

    except httpx.HTTPError:
        logger.exception("Failed to fetch TFC data")
        await _post_error(payload, settings, "Failed to fetch plan or PR data from TFC")
    except Exception:
        logger.exception("Unexpected error processing run task")
        await _post_error(payload, settings, "Internal error processing run task")


async def _post_passed_no_pr(payload: RunTaskPayload, settings: Settings) -> None:
    """Post 'passed' verdict for non-PR runs."""
    assert payload.task_result_callback_url is not None
    assert payload.access_token is not None
    message = (
        "No PR associated with this run (direct push or manual run). Skipping intention check."
    )
    await post_task_result(
        payload.task_result_callback_url,
        payload.access_token,
        "passed",
        message,
        timeout=settings.request_timeout,
    )


async def _post_error(payload: RunTaskPayload, settings: Settings, message: str) -> None:
    """Post 'passed' verdict with error message (advisory, so don't fail)."""
    assert payload.task_result_callback_url is not None
    assert payload.access_token is not None
    await post_task_result(
        payload.task_result_callback_url,
        payload.access_token,
        "passed",
        f"⚠️ {message}",
        timeout=settings.request_timeout,
    )


def _build_slice2_message(summary: PlanSummary, ingress: IngressAttributes) -> str:
    """Build human-readable message for Slice 2 (data gathering complete)."""
    if summary.is_empty():
        return "✅ Plan has no changes. Intention check skipped."

    parts = [
        f"✅ Slice 2 data gathering complete for PR #{ingress.pull_request_number}.",
        f"Plan changes: {summary.total_changes} resources",
    ]

    if summary.creates:
        parts.append(f"  • Creates: {len(summary.creates)}")
    if summary.updates:
        parts.append(f"  • Updates: {len(summary.updates)}")
    if summary.deletes:
        parts.append(f"  • Deletes: {len(summary.deletes)}")
    if summary.replaces:
        parts.append(f"  • Replaces: {len(summary.replaces)}")

    parts.append("(LLM analysis coming in Slice 3)")

    return "\n".join(parts)
