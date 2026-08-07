import httpx
import pytest

from integrations.webhooks import deliver_webhook


class _FakeResponse:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code
        self.is_success = 200 <= status_code < 300


def test_deliver_webhook_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(httpx, "post", lambda url, json, timeout: _FakeResponse(200))
    assert deliver_webhook("https://example.com/hook", {"job_id": "1"}) is True


def test_deliver_webhook_retries_then_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []

    def fake_post(url, json, timeout):
        calls.append(1)
        return _FakeResponse(500)

    monkeypatch.setattr(httpx, "post", fake_post)
    result = deliver_webhook("https://example.com/hook", {"job_id": "1"}, retries=3, backoff_seconds=0)
    assert result is False
    assert len(calls) == 3


def test_deliver_webhook_handles_connection_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_post(url, json, timeout):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(httpx, "post", fake_post)
    result = deliver_webhook("https://example.com/hook", {"job_id": "1"}, retries=2, backoff_seconds=0)
    assert result is False
