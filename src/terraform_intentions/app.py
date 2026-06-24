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

from .analysis import analyze_intention
from .callback import post_task_result
from .config import Settings, get_settings
from .models import (
    IngressAttributes,
    Outcome,
    PlanSummary,
    RunTaskPayload,
    TaskResultStatus,
    Verdict,
)
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
    """Background task: fetch data, analyze, post verdict.

    The webhook is enforcement-agnostic: it posts an honest ``passed``/``failed`` and TFC's
    operator-set enforcement level (advisory = warn, mandatory = block) decides what a failure
    does. Genuine mismatches and checker errors both post ``failed``; "nothing to check" cases
    post ``passed``.
    """
    try:
        # Surface the operator's enforcement level (we don't change behaviour based on it — TFC
        # decides whether a 'failed' blocks — but it's useful to see which mode a run task is in).
        logger.info("Run task enforcement level: %s", payload.task_result_enforcement_level)

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

        assert payload.task_result_callback_url is not None
        assert payload.access_token is not None

        # Nothing to check if the plan is a no-op or the PR has no description to compare against.
        if summary.is_empty():
            await _post_passed(
                payload, settings, "✅ Plan has no changes. Intention check skipped."
            )
            return
        pr_body = (ingress.pull_request_body or "").strip()
        if not pr_body:
            await _post_passed(
                payload,
                settings,
                "✅ No PR description to compare against. Intention check skipped.",
            )
            return

        # Ask the LLM whether the plan matches the PR's stated intent.
        # Fail closed — if our own check can't run, post 'failed' so the result is inconclusive
        # rather than a false pass (the operator's enforcement level decides if that blocks).
        try:
            verdict = await analyze_intention(pr_body, summary, settings)
        except Exception:
            logger.exception("Intention check failed")
            await _post_error(payload, settings, "the intention check could not run")
            return

        logger.info("Verdict: %s", verdict.model_dump_json(indent=2))
        status: TaskResultStatus = "passed" if verdict.matches else "failed"
        await post_task_result(
            payload.task_result_callback_url,
            payload.access_token,
            status,
            _build_verdict_message(verdict, ingress),
            timeout=settings.request_timeout,
            outcomes=[_build_verdict_outcome(verdict, summary, ingress)],
        )

    except httpx.HTTPError:
        logger.exception("Failed to fetch TFC data")
        await _post_error(payload, settings, "the plan or PR data could not be fetched from TFC")
    except Exception:
        logger.exception("Unexpected error processing run task")
        await _post_error(payload, settings, "an internal error interrupted the intention check")


async def _post_status(
    payload: RunTaskPayload, settings: Settings, status: TaskResultStatus, message: str
) -> None:
    """Post a verdict with a custom status and message."""
    assert payload.task_result_callback_url is not None
    assert payload.access_token is not None
    await post_task_result(
        payload.task_result_callback_url,
        payload.access_token,
        status,
        message,
        timeout=settings.request_timeout,
    )


async def _post_passed(payload: RunTaskPayload, settings: Settings, message: str) -> None:
    """Post a 'passed' verdict (used for the 'nothing to check' cases)."""
    await _post_status(payload, settings, "passed", message)


async def _post_passed_no_pr(payload: RunTaskPayload, settings: Settings) -> None:
    """Post 'passed' verdict for non-PR runs (nothing to compare against)."""
    await _post_passed(
        payload,
        settings,
        "No PR associated with this run (direct push or manual run). Skipping intention check.",
    )


async def _post_error(payload: RunTaskPayload, settings: Settings, reason: str) -> None:
    """Post 'failed' when our own check can't run (fail closed — the result is inconclusive).

    This is distinct from a real mismatch: the message makes clear the check did not complete.
    Whether this blocks is up to the run task's enforcement level, set by the operator in TFC.
    """
    await _post_status(
        payload,
        settings,
        "failed",
        f"⚠️ Intention check could not complete: {reason}. "
        "Marked failed because the result is inconclusive.",
    )


def _build_verdict_message(verdict: Verdict, ingress: IngressAttributes) -> str:
    """The one-line summary shown in the TFC run-task Details column.

    This field is plain text (no markdown, newlines collapsed), so keep it to a single
    sentence. The structured detail lives in the outcome (see ``_build_verdict_outcome``).
    """
    pr = f"PR #{ingress.pull_request_number}" if ingress.pull_request_number else "the PR"
    if verdict.matches:
        return f"✅ The plan matches the intention described in {pr}."

    extra = len(verdict.unexpected_resources)
    missing = len(verdict.missing_resources)
    counts = []
    if extra:
        counts.append(f"{extra} unexpected")
    if missing:
        counts.append(f"{missing} missing")
    detail = " and ".join(counts) or "differences"
    noun = "resource" if extra + missing == 1 else "resources"
    return f"⚠️ The plan doesn't match {pr} — {detail} {noun} (see details)."


# TFC colours/icons an outcome's severity tag off these levels.
_SEVERITY_LEVEL = {"none": "none", "low": "info", "medium": "warning", "high": "error"}


def _outcome_description(verdict: Verdict) -> str:
    """One-line outcome title reflecting which direction(s) the plan diverged."""
    if verdict.matches:
        return "Plan matches the intended changes"
    extra = bool(verdict.unexpected_resources)
    missing = bool(verdict.missing_resources)
    if extra and missing:
        return "Plan does not match the PR's stated intent"
    if missing:
        return "Plan is missing resources the PR describes"
    return "Plan provisions more than the PR describes"


def _build_verdict_outcome(
    verdict: Verdict, summary: PlanSummary, ingress: IngressAttributes
) -> Outcome:
    """Render the verdict as a structured TFC outcome with a Markdown body.

    Unlike the flat message, the outcome ``body`` is rendered as Markdown, so the resource
    breakdown is laid out deterministically here (rather than relying on the model's prose).
    """
    changes = (
        [(addr, "create") for addr in summary.creates]
        + [(addr, "update") for addr in summary.updates]
        + [(addr, "replace") for addr in summary.replaces]
        + [(addr, "delete") for addr in summary.deletes]
    )

    lines = ["**Plan changes**", ""]
    lines += [f"- `{addr}` — {action}" for addr, action in changes]
    if verdict.unexpected_resources:
        lines += ["", "**Beyond the PR description** (in the plan, not described)", ""]
        lines += [f"- `{addr}`" for addr in verdict.unexpected_resources]
    if verdict.missing_resources:
        lines += ["", "**Described but not in the plan**", ""]
        lines += [f"- {item}" for item in verdict.missing_resources]
    lines += ["", "**Assessment**", "", verdict.reasoning]

    status_label = "Passed" if verdict.matches else "Failed"
    description = _outcome_description(verdict)
    return Outcome(
        outcome_id=f"intention-check-pr-{ingress.pull_request_number or 'unknown'}",
        description=description,
        body="\n".join(lines),
        tags={
            "status": [{"label": status_label, "level": "info" if verdict.matches else "error"}],
            "severity": [{"label": verdict.severity, "level": _SEVERITY_LEVEL[verdict.severity]}],
        },
    )
