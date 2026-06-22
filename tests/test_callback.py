"""Tests for the TFC result callback POST."""

import httpx
import respx

from terraform_intentions.callback import post_task_result

CALLBACK_URL = "https://app.terraform.io/api/v2/task-results/abc/callback"


@respx.mock
async def test_post_task_result_sends_jsonapi_patch() -> None:
    route = respx.patch(CALLBACK_URL).mock(return_value=httpx.Response(200))

    await post_task_result(CALLBACK_URL, "tok-123", "passed", "all good", timeout=5.0)

    assert route.called
    request = route.calls.last.request
    assert request.headers["Authorization"] == "Bearer tok-123"
    assert request.headers["Content-Type"] == "application/vnd.api+json"

    import json

    body = json.loads(request.content)
    assert body == {
        "data": {"type": "task-results", "attributes": {"status": "passed", "message": "all good"}}
    }


@respx.mock
async def test_post_task_result_swallows_http_errors() -> None:
    # A failing callback must not raise out of the background task.
    respx.patch(CALLBACK_URL).mock(return_value=httpx.Response(500))
    await post_task_result(CALLBACK_URL, "tok", "passed", "msg", timeout=5.0)
