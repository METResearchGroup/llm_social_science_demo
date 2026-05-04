import json
from types import SimpleNamespace
from unittest.mock import patch

import httpx
import pytest

import chat_app.backend.app as backend_app
from chat_app.backend.app import app


@pytest.fixture(autouse=True)
def reset_singleton() -> None:
    backend_app._conversation_id = None
    yield
    backend_app._conversation_id = None


class FakeAsyncStreamCM:
    def __init__(self, deltas: list[str]) -> None:
        self._events = [
            SimpleNamespace(type="response.output_text.delta", delta=d) for d in deltas
        ]
        self._idx = 0

    async def __aenter__(self) -> "FakeAsyncStreamCM":
        return self

    async def __aexit__(self, *args: object) -> bool:
        return False

    def __aiter__(self) -> "FakeAsyncStreamCM":
        return self

    async def __anext__(self) -> SimpleNamespace:
        if self._idx >= len(self._events):
            raise StopAsyncIteration
        e = self._events[self._idx]
        self._idx += 1
        return e


@pytest.mark.asyncio
async def test_chat_stream_sse() -> None:
    def fake_stream(**kwargs: object) -> FakeAsyncStreamCM:
        return FakeAsyncStreamCM(["hello", " ", "world"])

    with (
        patch.object(
            backend_app.client.conversations,
            "create",
            return_value=SimpleNamespace(id="conv_test_stream"),
        ),
        patch.object(backend_app.aclient.responses, "stream", side_effect=fake_stream),
    ):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            async with client.stream(
                "POST",
                "/api/chat/stream",
                json={"user_message": "hi"},
            ) as resp:
                assert resp.status_code == 200
                body = "".join([chunk async for chunk in resp.aiter_text()])

    frames = [f for f in body.split("\n\n") if f.strip()]
    deltas: list[str] = []
    last_obj: dict | None = None
    for frame in frames:
        line = next((ln for ln in frame.split("\n") if ln.startswith("data:")), None)
        assert line is not None
        obj = json.loads(line[5:].strip())
        if obj["type"] == "delta":
            deltas.append(obj["text"])
        else:
            last_obj = obj

    assert "".join(deltas) == "hello world"
    assert last_obj == {
        "type": "done",
        "conversation_id": "conv_test_stream",
        "assistant_message": "hello world",
    }
