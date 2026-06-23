"""Client for fetching data from Terraform Cloud API."""

import logging
from typing import Any

import httpx

from .models import IngressAttributes, PlanSummary, ResourceChange

logger = logging.getLogger(__name__)


class TFCClient:
    """Client for TFC API operations."""

    def __init__(self, base_url: str, team_token: str, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.team_token = team_token
        self.timeout = timeout

    async def fetch_plan_json(self, plan_json_api_url: str) -> dict[str, Any]:
        """Fetch plan JSON from TFC.

        Args:
            plan_json_api_url: Full URL to the plan JSON endpoint.

        Returns:
            The plan JSON as a dictionary.

        Raises:
            httpx.HTTPError: If the request fails.
        """
        headers = {"Authorization": f"Bearer {self.team_token}"}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(plan_json_api_url, headers=headers)
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            return data

    async def fetch_ingress_attributes(self, configuration_version_id: str) -> IngressAttributes:
        """Fetch ingress attributes for a configuration version.

        Args:
            configuration_version_id: The TFC configuration version ID.

        Returns:
            Parsed ingress attributes.

        Raises:
            httpx.HTTPError: If the request fails.
        """
        url = (
            f"{self.base_url}/configuration-versions/{configuration_version_id}/ingress-attributes"
        )
        headers = {"Authorization": f"Bearer {self.team_token}"}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            # TFC returns JSON:API format: {"data": {"attributes": {...}}}
            attributes = data.get("data", {}).get("attributes", {})
            return IngressAttributes.model_validate(attributes)

    def summarize_plan(self, plan_json: dict[str, Any]) -> PlanSummary:
        """Reduce plan JSON to compact change summary.

        Args:
            plan_json: The full plan JSON from TFC.

        Returns:
            A compact summary of resource changes.
        """
        summary = PlanSummary()

        resource_changes = plan_json.get("resource_changes", [])

        for change_data in resource_changes:
            change = ResourceChange.model_validate(change_data)
            actions = change.actions

            # Skip no-ops
            if actions == ["no-op"]:
                continue

            address = change.address

            # Categorize by action type
            if "create" in actions and "delete" in actions:
                summary.replaces.append(address)
            elif "create" in actions:
                summary.creates.append(address)
            elif "update" in actions:
                summary.updates.append(address)
            elif "delete" in actions:
                summary.deletes.append(address)

        summary.total_changes = (
            len(summary.creates)
            + len(summary.updates)
            + len(summary.deletes)
            + len(summary.replaces)
        )

        return summary


# Made with Bob
