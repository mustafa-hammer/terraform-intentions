"""Tests for the TFC result callback POST."""

import json

import httpx
import respx

from terraform_intentions.callback import post_task_result
from terraform_intentions.models import Outcome

CALLBACK_URL = "https://app.terraform.io/api/v2/task-results/abc/callback"


@respx.mock
async def test_post_task_result_sends_jsonapi_patch() -> None:
    route = respx.patch(CALLBACK_URL).mock(return_value=httpx.Response(200))

    await post_task_result(CALLBACK_URL, "tok-123", "passed", "all good", timeout=5.0)

    assert route.called
    request = route.calls.last.request
    assert request.headers["Authorization"] == "Bearer tok-123"
    assert request.headers["Content-Type"] == "application/vnd.api+json"

    body = json.loads(request.content)
    assert body == {
        "data": {"type": "task-results", "attributes": {"status": "passed", "message": "all good"}}
    }


@respx.mock
async def test_post_task_result_serializes_outcomes() -> None:
    route = respx.patch(CALLBACK_URL).mock(return_value=httpx.Response(200))
    outcome = Outcome(
        outcome_id="intention-check-pr-1",
        description="Plan provisions more than the PR describes",
        body="**Plan changes**\n\n- `aws_db_instance.main` — create",
        tags={"severity": [{"label": "high", "level": "error"}]},
    )

    await post_task_result(
        CALLBACK_URL, "tok", "failed", "summary", timeout=5.0, outcomes=[outcome]
    )

    body = json.loads(route.calls.last.request.content)
    assert body["data"]["relationships"]["outcomes"]["data"] == [
        {
            "type": "task-result-outcomes",
            "attributes": {
                "outcome-id": "intention-check-pr-1",
                "description": "Plan provisions more than the PR describes",
                "body": "**Plan changes**\n\n- `aws_db_instance.main` — create",
                "tags": {"severity": [{"label": "high", "level": "error"}]},
            },
        }
    ]


@respx.mock
async def test_post_task_result_swallows_http_errors() -> None:
    # A failing callback must not raise out of the background task.
    respx.patch(CALLBACK_URL).mock(return_value=httpx.Response(500))
    await post_task_result(CALLBACK_URL, "tok", "passed", "msg", timeout=5.0)
