"""FastAPI app exposing the TFC run-task webhook.

Slice 3: verify signature, ack 200 immediately, then asynchronously fetch plan JSON
and PR metadata from TFC, run the LangChain verdict chain, and post an advisory
verdict back to TFC.
"""

import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import BackgroundTasks, FastAPI, Request, Response
from langchain_core.runnables import Runnable

from .callback import post_task_result
from .config import Settings, get_settings
from .fetcher import FetchError, fetch_ingress_attrs, fetch_plan_json, reduce_plan
from .models import RunTaskPayload, Verdict
from .security import verify_signature
from .verdicts import build_verdict_chain, plan_summary_to_text, verdict_to_tfc_outcome

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

# Module-level chain cache — built once per process with the live settings.
_verdict_chain: Runnable | None = None


def _get_verdict_chain(settings: Settings) -> Runnable:
    """Return (or lazily create) the module-level verdict chain."""
    global _verdict_chain
    if _verdict_chain is None:
        _verdict_chain = build_verdict_chain(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
        )
    return _verdict_chain


def _redact(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a shallow copy of ``payload`` with sensitive values masked."""
    return {k: ("***redacted***" if k in _SENSITIVE_KEYS else v) for k, v in payload.items()}


async def _analyze_and_callback(payload: RunTaskPayload, settings: Settings) -> None:
    """Fetch plan + PR data, run the LangChain verdict chain, and post result to TFC.

    Runs in a background task so the initial 200 ack is not delayed.
    Any failure posts an advisory ``passed`` rather than leaving the run task hanging —
    run tasks that never callback are retried and eventually time out, which is worse than
    an explicit (advisory) pass.
    """
    # These are guaranteed non-None before this function is called (checked in run_task).
    assert payload.access_token is not None
    assert payload.task_result_callback_url is not None

    # ------------------------------------------------------------------ #
    # Speculative runs: nothing to compare against a PR; pass and skip.   #
    # ------------------------------------------------------------------ #
    if payload.is_speculative:
        logger.info("Skipping analysis for speculative run %s", payload.run_id)
        await post_task_result(
            payload.task_result_callback_url,
            payload.access_token,
            "passed",
            "Speculative run — no intention check performed.",
            timeout=settings.request_timeout,
        )
        return

    # ------------------------------------------------------------------ #
    # Fetch plan JSON and reduce to actionable changes.                   #
    # ------------------------------------------------------------------ #
    plan_text = "(no actionable changes)"
    pr_body = ""
    try:
        if payload.plan_json_api_url:
            plan_json = await fetch_plan_json(
                payload.plan_json_api_url,
                payload.access_token,
                timeout=settings.request_timeout,
            )
            summary = reduce_plan(plan_json)
            plan_text = plan_summary_to_text(summary)
            logger.info(
                "Plan summary for run %s: %d change(s)",
                payload.run_id,
                len(summary.changes),
            )
        else:
            logger.warning("No plan_json_api_url in payload for run %s", payload.run_id)

        # ------------------------------------------------------------------ #
        # Fetch ingress-attributes to get the PR body.                        #
        # ------------------------------------------------------------------ #
        if payload.configuration_version_id:
            ingress = await fetch_ingress_attrs(
                payload.configuration_version_id,
                settings.tfc_team_token,
                timeout=settings.request_timeout,
            )
            if not ingress.is_pull_request:
                logger.info(
                    "Run %s is not a PR run — skipping intention check.", payload.run_id
                )
                await post_task_result(
                    payload.task_result_callback_url,
                    payload.access_token,
                    "passed",
                    "No pull request associated with this run — intention check skipped.",
                    timeout=settings.request_timeout,
                )
                return

            pr_body = ingress.pull_request_body or ""
            logger.info(
                "PR #%s body (%d chars) for run %s:\n%s",
                ingress.pull_request_number,
                len(pr_body),
                payload.run_id,
                pr_body[:500],  # truncate for readability in logs
            )
        else:
            logger.warning(
                "No configuration_version_id in payload for run %s", payload.run_id
            )

    except FetchError:
        logger.exception("Fetch failed for run %s — posting advisory passed", payload.run_id)
        await post_task_result(
            payload.task_result_callback_url,
            payload.access_token,
            "passed",
            "Advisory check skipped — could not fetch plan or PR data.",
            timeout=settings.request_timeout,
        )
        return

    # ------------------------------------------------------------------ #
    # Run the LangChain verdict chain.                                    #
    # ------------------------------------------------------------------ #
    try:
        chain = _get_verdict_chain(settings)
        verdict: Verdict = await chain.ainvoke(  # type: ignore[assignment]
            {"pr_body": pr_body, "plan_summary": plan_text}
        )
        logger.info(
            "Verdict for run %s: matches=%s severity=%s unexpected=%s",
            payload.run_id,
            verdict.matches,
            verdict.severity,
            verdict.unexpected_resources,
        )
    except Exception:
        logger.exception("Verdict chain failed for run %s — posting advisory passed", payload.run_id)
        await post_task_result(
            payload.task_result_callback_url,
            payload.access_token,
            "passed",
            "Advisory check skipped — LLM verdict generation failed.",
            timeout=settings.request_timeout,
        )
        return

    # ------------------------------------------------------------------ #
    # Map verdict → TFC callback status + outcomes.                       #
    # ------------------------------------------------------------------ #
    # Run tasks are advisory-only — we always post "passed" to avoid blocking applies.
    # The flat message is a concise summary; the structured outcomes array gives TFC
    # a rich, per-resource breakdown rendered in the run-task UI panel.
    outcomes = verdict_to_tfc_outcome(verdict, run_id=payload.run_id)

    if verdict.matches:
        message = f"[{verdict.severity.upper()}] Plan aligns with PR intention."
    else:
        n = len(verdict.unexpected_resources)
        message = (
            f"[{verdict.severity.upper()}] {n} unexpected resource(s) detected. "
            f"See outcomes for details."
        )

    await post_task_result(
        payload.task_result_callback_url,
        payload.access_token,
        "passed",
        message,
        timeout=settings.request_timeout,
        outcomes=outcomes,
    )


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

    # access_token / callback_url are guaranteed non-None before _analyze_and_callback.
    if payload.access_token is None or payload.task_result_callback_url is None:
        logger.error("Unexpected: non-verification event missing access_token or callback URL")
        return Response(status_code=400)

    background_tasks.add_task(_analyze_and_callback, payload, settings)
    return Response(status_code=200)
