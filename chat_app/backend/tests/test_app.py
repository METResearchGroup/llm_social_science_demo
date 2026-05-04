from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import chat_app.backend.app as backend_app
from chat_app.backend.app import app


@pytest.fixture(autouse=True)
def reset_singleton() -> None:
    backend_app._conversation_id = None
    yield
    backend_app._conversation_id = None


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as c:
        yield c


def test_health(client: TestClient) -> None:
    r = client.get("/api/health")
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is True
    assert j["conversation_id"] is None
    assert j["model"] == "gpt-4o-mini"


def test_chat(client: TestClient) -> None:
    with (
        patch.object(
            backend_app.client.conversations,
            "create",
            return_value=SimpleNamespace(id="conv_test_1"),
        ),
        patch.object(
            backend_app.client.responses,
            "create",
            return_value=SimpleNamespace(output_text="hello back"),
        ),
    ):
        r = client.post("/api/chat", json={"user_message": "hi"})
    assert r.status_code == 200
    j = r.json()
    assert j["assistant_message"] == "hello back"
    assert j["conversation_id"] == "conv_test_1"


def test_reset(client: TestClient) -> None:
    with (
        patch.object(
            backend_app.client.conversations,
            "create",
            side_effect=[
                SimpleNamespace(id="conv_test_1"),
                SimpleNamespace(id="conv_test_2"),
            ],
        ),
        patch.object(
            backend_app.client.responses,
            "create",
            return_value=SimpleNamespace(output_text="ok"),
        ),
        patch.object(backend_app.client.conversations, "delete", return_value=None),
    ):
        r1 = client.post("/api/chat", json={"user_message": "first"})
        assert r1.json()["conversation_id"] == "conv_test_1"
        r2 = client.post("/api/reset")
    assert r2.status_code == 200
    assert r2.json()["conversation_id"] == "conv_test_2"
