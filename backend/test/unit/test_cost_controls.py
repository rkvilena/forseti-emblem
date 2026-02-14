import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.routes import chat as chat_routes
from app import rate_limit


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    store: dict[str, int] = {}

    class FakePipeline:
        def __init__(self, store: dict[str, int]):
            self.store = store
            self.ops: list[tuple[str, str | int]] = []

        def __enter__(self) -> "FakePipeline":
            return self

        def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
            return False

        def incr(self, key: str) -> None:
            self.ops.append(("incr", key))

        def expire(self, key: str, ttl: int) -> None:
            self.ops.append(("expire", ttl))

        def execute(self) -> list[int | bool]:
            results: list[int | bool] = []
            for op, arg in self.ops:
                if op == "incr":
                    key = arg  # type: ignore[assignment]
                    current = self.store.get(key, 0) + 1
                    self.store[key] = current
                    results.append(current)
                elif op == "expire":
                    results.append(True)
            return results

    class FakeRedisClient:
        def __init__(self, store: dict[str, int]):
            self.store = store

        def get(self, key: str) -> bytes | None:
            value = self.store.get(key)
            if value is None:
                return None
            return b"1"

        def setex(self, key: str, ttl: int, value: bytes) -> None:
            self.store[key] = 1

        def pipeline(self) -> FakePipeline:
            return FakePipeline(self.store)

    monkeypatch.setattr(rate_limit, "get_redis_client", lambda: FakeRedisClient(store))

    original_turnstile_enabled = settings.turnstile_enabled
    original_long_ip = settings.rate_limit_long_ip_requests
    original_short_ip = settings.rate_limit_short_ip_requests
    original_cooldown_threshold = settings.session_cooldown_threshold
    original_cooldown_window = settings.session_cooldown_window_seconds
    original_cooldown_duration = settings.session_cooldown_duration_seconds
    original_chat_rag = chat_routes.chat_controller.chat_rag
    original_chat_plain = chat_routes.chat_controller.chat_plain

    settings.turnstile_enabled = False
    settings.rate_limit_long_ip_requests = 100
    settings.rate_limit_short_ip_requests = 100
    settings.session_cooldown_threshold = 3
    settings.session_cooldown_window_seconds = 60
    settings.session_cooldown_duration_seconds = 60

    def _fake_chat_rag(*args, **kwargs):  # type: ignore[no-untyped-def]
        return {"response": "ok", "model": "test", "usage": None}

    def _fake_chat_plain(*args, **kwargs):  # type: ignore[no-untyped-def]
        return {"response": "ok", "model": "test", "usage": None}

    chat_routes.chat_controller.chat_rag = _fake_chat_rag  # type: ignore[assignment]
    chat_routes.chat_controller.chat_plain = _fake_chat_plain  # type: ignore[assignment]

    try:
        yield TestClient(app)
    finally:
        settings.turnstile_enabled = original_turnstile_enabled
        settings.rate_limit_long_ip_requests = original_long_ip
        settings.rate_limit_short_ip_requests = original_short_ip
        settings.session_cooldown_threshold = original_cooldown_threshold
        settings.session_cooldown_window_seconds = original_cooldown_window
        settings.session_cooldown_duration_seconds = original_cooldown_duration
        chat_routes.chat_controller.chat_rag = original_chat_rag  # type: ignore[assignment]
        chat_routes.chat_controller.chat_plain = original_chat_plain  # type: ignore[assignment]


def test_message_length_limit_enforced_on_chat(client: TestClient) -> None:
    too_long = "x" * (settings.request_max_chars + 1)

    response = client.post(
        "/chat",
        json={
            "message": too_long,
            "system_prompt": None,
            "context": None,
            "temperature": 0.3,
            "turnstile_token": "dummy",
        },
    )

    assert response.status_code == 400


def test_message_length_limit_enforced_on_chat_rag(client: TestClient) -> None:
    too_long = "x" * (settings.request_max_chars + 1)

    response = client.post(
        "/chat/rag",
        json={
            "message": too_long,
            "top_k": 1,
            "temperature": 0.3,
            "system_prompt": None,
            "turnstile_token": "dummy",
        },
    )

    assert response.status_code == 400


def test_top_k_clamped_to_max(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured = {}

    def _capture_chat_rag(*, db, message, top_k, temperature, system_prompt):  # type: ignore[no-untyped-def]
        captured["top_k"] = top_k
        return {"response": "ok", "model": "test", "usage": None}

    monkeypatch.setattr(chat_routes.chat_controller, "chat_rag", _capture_chat_rag)

    response = client.post(
        "/chat/rag",
        json={
            "message": "Hello",
            "top_k": settings.rag_top_k_max + 5,
            "temperature": 0.3,
            "system_prompt": None,
            "turnstile_token": "dummy",
        },
    )

    assert response.status_code == 200
    assert captured["top_k"] == settings.rag_top_k_max


def test_session_cooldown_kicks_in_after_threshold(client: TestClient) -> None:
    for _ in range(settings.session_cooldown_threshold):
        response = client.post(
            "/chat/rag",
            json={
                "message": "Hello",
                "top_k": 1,
                "temperature": 0.3,
                "system_prompt": None,
                "turnstile_token": "dummy",
            },
        )
        assert response.status_code == 200

    response_block = client.post(
        "/chat/rag",
        json={
            "message": "Hello again",
            "top_k": 1,
            "temperature": 0.3,
            "system_prompt": None,
            "turnstile_token": "dummy",
        },
    )

    assert response_block.status_code == 429
