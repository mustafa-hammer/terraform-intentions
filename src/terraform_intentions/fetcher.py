"""Fetch Terraform Cloud data needed to evaluate a run-task: plan JSON and PR metadata.

Two calls are made using *different* credentials:

* ``fetch_plan_json``    — uses the short-lived ``access_token`` from the run-task payload
                          (scoped to the current run only).
* ``fetch_ingress_attrs`` — uses the long-lived ``tfc_team_token`` from settings
                          (needed because ingress-attributes is not accessible via the
                          run-scoped access_token).

Both are thin async wrappers around httpx. Errors are raised as ``FetchError`` so the
caller can decide whether to fail the run task or skip analysis gracefully.
"""

from __future__ import annotations

import logging

import httpx

from .models import IngressAttributes, PlanSummary

logger = logging.getLogger(__name__)

TFC_API_BASE = "https://app.terraform.io/api/v2"


class FetchError(Exception):
    """Raised when a TFC API call fails in a way that prevents plan analysis."""


async def fetch_plan_json(
    plan_json_api_url: str,
    access_token: str,
    *,
    timeout: float,
) -> dict[str, object]:
    """Download the plan JSON for this run.

    Uses the run-scoped ``access_token`` from the run-task payload — no team token needed.

    Args:
        plan_json_api_url: The ``plan_json_api_url`` field from the run-task payload.
        access_token: The short-lived bearer token included in the run-task POST.
        timeout: HTTP request timeout in seconds.

    Returns:
        The raw plan JSON as a dict.

    Raises:
        FetchError: On any HTTP or network failure.
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(plan_json_api_url, headers=headers)
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]
    except httpx.HTTPError as exc:
        raise FetchError(f"Failed to fetch plan JSON from {plan_json_api_url}: {exc}") from exc


async def fetch_ingress_attrs(
    configuration_version_id: str,
    team_token: str,
    *,
    timeout: float,
) -> IngressAttributes:
    """Fetch ingress-attributes for a configuration version to get PR metadata.

    Ingress-attributes contain the PR number, PR body, repository identifier, and whether
    this is a pull-request run.  The run-scoped access_token *cannot* read this endpoint —
    a TFC team token with workspace read access is required.

    Args:
        configuration_version_id: The ``configuration_version_id`` from the run-task payload.
        team_token: A TFC team token with at least read access to the workspace.
        timeout: HTTP request timeout in seconds.

    Returns:
        Parsed ``IngressAttributes``.

    Raises:
        FetchError: On any HTTP or network failure, or if the response is malformed.
    """
    url = f"{TFC_API_BASE}/configuration-versions/{configuration_version_id}/ingress-attributes"
    headers = {
        "Authorization": f"Bearer {team_token}",
        "Content-Type": "application/vnd.api+json",
    }
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise FetchError(
            f"Failed to fetch ingress-attributes for {configuration_version_id}: {exc}"
        ) from exc

    body = response.json()
    try:
        attrs_raw: dict[str, object] = body["data"]["attributes"]
    except (KeyError, TypeError) as exc:
        raise FetchError(
            f"Unexpected ingress-attributes shape for {configuration_version_id}: {exc}"
        ) from exc

    return IngressAttributes.model_validate(attrs_raw)


def reduce_plan(plan_json: dict[str, object]) -> PlanSummary:
    """Reduce a raw Terraform plan JSON to only the actionable resource changes.

    Drops no-op and read-only changes so the LLM only sees what actually changes.

    Args:
        plan_json: The raw dict from ``fetch_plan_json``.

    Returns:
        A ``PlanSummary`` containing only create/update/delete/replace entries.
    """
    summary = PlanSummary.from_plan_json(plan_json)
    logger.info(
        "Plan reduced to %d actionable change(s): %s",
        len(summary.changes),
        [c.address for c in summary.changes],
    )
    return summary
