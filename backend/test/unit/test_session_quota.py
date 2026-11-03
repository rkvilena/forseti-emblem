import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.application.chat import service
from app.application.chat.results import ChatResult
from app.config import settings
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

        def pipeline(self) -> FakePipeline:
            return FakePipeline(self.store)

    monkeypatch.setattr(rate_limit, "get_redis_client", lambda: FakeRedisClient(store))

    original_long_ip = settings.rate_limit_long_ip_requests
    original_session_long = settings.session_rate_limit_long_ip_requests
    original_turnstile_enabled = settings.turnstile_enabled

    settings.rate_limit_long_ip_requests = 100
    settings.session_rate_limit_long_ip_requests = 3
    settings.turnstile_enabled = False

    def _fake_execute(*args, **kwargs):  # type: ignore[no-untyped-def]
        return ChatResult(
            response="ok",
            model="test-model",
            usage=None,
        )

    monkeypatch.setattr(service.RagChatService, "execute", _fake_execute)

    try:
        yield TestClient(app)
    finally:
        settings.rate_limit_long_ip_requests = original_long_ip
        settings.session_rate_limit_long_ip_requests = original_session_long
        settings.turnstile_enabled = original_turnstile_enabled


def test_session_quota_sets_cookie_and_limits(client: TestClient) -> None:
    response1 = client.post(
        "/chat/rag",
        json={
            "message": "Hello",
            "top_k": 1,
            "temperature": 0.3,
            "system_prompt": None,
            "turnstile_token": "dummy",
        },
    )
    assert response1.status_code == 200
    cookies = response1.cookies
    assert settings.session_cookie_name in cookies

    for _ in range(2):
        response = client.post(
            "/chat/rag",
            json={
                "message": "Hello again",
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
            "message": "One more",
            "top_k": 1,
            "temperature": 0.3,
            "system_prompt": None,
            "turnstile_token": "dummy",
        },
    )

    assert response_block.status_code == 429
