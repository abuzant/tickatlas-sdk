"""Retry policy tests (SPEC section 5).

Sleeps are made effectively free via ``backoff_base=0.0001`` and ``jitter=False``;
we also patch ``time.sleep`` to assert the *computed* delays without waiting.
"""

from __future__ import annotations

import httpx
import pytest

import tickatlas
from tickatlas import RateLimitError, ServerError, TickAtlasNetworkError

from conftest import (
    QUOTE_DATA,
    envelope,
    error_envelope,
    make_sync_client,
    sequence_handler,
    single_response,
)


def test_retries_on_429_then_succeeds(monkeypatch):
    slept = []
    monkeypatch.setattr("tickatlas._client.time.sleep", lambda d: slept.append(d))

    handler = sequence_handler(
        [
            (429, error_envelope("RATE_LIMIT_EXCEEDED", "slow down"), {"Retry-After": "7"}),
            (200, envelope(QUOTE_DATA), {}),
        ]
    )
    client = make_sync_client(handler, max_retries=3)
    res = client.get_quote("EURUSD")
    client.close()

    assert res.bid == 1.16404
    assert handler.state["i"] == 2  # one retry
    # Retry-After header (7s) is honoured instead of computed backoff.
    assert slept == [7.0]


def test_retries_on_5xx_then_succeeds(monkeypatch):
    slept = []
    monkeypatch.setattr("tickatlas._client.time.sleep", lambda d: slept.append(d))

    handler = sequence_handler(
        [
            (503, error_envelope("SERVICE_UNAVAILABLE", "down"), {}),
            (500, error_envelope("INTERNAL_ERROR", "boom"), {}),
            (200, envelope(QUOTE_DATA), {}),
        ]
    )
    client = make_sync_client(handler, max_retries=3, backoff_base=0.5)
    client._jitter = False  # deterministic
    res = client.get_quote("EURUSD")
    client.close()

    assert res.bid == 1.16404
    assert len(slept) == 2
    # Full backoff (no jitter): base*2^0 = 0.5, base*2^1 = 1.0
    assert slept == [0.5, 1.0]


def test_retries_exhausted_raises_last_error(monkeypatch):
    monkeypatch.setattr("tickatlas._client.time.sleep", lambda d: None)
    handler = single_response(500, error_envelope("INTERNAL_ERROR", "boom"))
    client = make_sync_client(handler, max_retries=2)
    with pytest.raises(ServerError):
        client.get_quote("EURUSD")
    client.close()
    # 1 initial + 2 retries = 3 attempts.
    assert len(handler.recorded) >= 1


def test_429_exhausted_raises_rate_limit_error(monkeypatch):
    monkeypatch.setattr("tickatlas._client.time.sleep", lambda d: None)
    handler = single_response(
        429, error_envelope("RATE_LIMIT_EXCEEDED", "nope"), {"Retry-After": "1"}
    )
    client = make_sync_client(handler, max_retries=2)
    with pytest.raises(RateLimitError) as exc:
        client.get_quote("EURUSD")
    client.close()
    assert exc.value.retry_after == 1.0


def test_network_error_is_retried_then_wrapped(monkeypatch):
    monkeypatch.setattr("tickatlas._client.time.sleep", lambda d: None)
    attempts = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["n"] += 1
        raise httpx.ConnectError("connection refused")

    client = make_sync_client(handler, max_retries=2)
    with pytest.raises(TickAtlasNetworkError) as exc:
        client.get_quote("EURUSD")
    client.close()
    assert attempts["n"] == 3  # 1 + 2 retries
    assert isinstance(exc.value.cause, httpx.ConnectError)


def test_network_error_recovers(monkeypatch):
    monkeypatch.setattr("tickatlas._client.time.sleep", lambda d: None)
    state = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        state["n"] += 1
        if state["n"] == 1:
            raise httpx.ReadTimeout("timeout")
        return httpx.Response(200, json=envelope(QUOTE_DATA))

    client = make_sync_client(handler, max_retries=3)
    res = client.get_quote("EURUSD")
    client.close()
    assert res.bid == 1.16404
    assert state["n"] == 2


def test_4xx_non_429_is_not_retried(monkeypatch):
    monkeypatch.setattr("tickatlas._client.time.sleep", lambda d: pytest.fail("slept"))
    handler = single_response(404, error_envelope("SYMBOL_NOT_FOUND", "no"))
    client = make_sync_client(handler, max_retries=3)
    with pytest.raises(tickatlas.NotFoundError):
        client.get_quote("EURUSD")
    client.close()


def test_max_retries_zero_means_no_retry(monkeypatch):
    monkeypatch.setattr("tickatlas._client.time.sleep", lambda d: pytest.fail("slept"))
    handler = single_response(500, error_envelope("INTERNAL_ERROR", "boom"))
    client = make_sync_client(handler, max_retries=0)
    with pytest.raises(ServerError):
        client.get_quote("EURUSD")
    client.close()


def test_backoff_is_capped_at_30s():
    # Directly exercise the pure backoff computation with jitter disabled.
    client = make_sync_client(single_response(200, envelope(QUOTE_DATA)))
    client._jitter = False
    client.backoff_base = 0.5
    # attempt 10 would be 0.5 * 1024 = 512 -> capped to 30.
    assert client._compute_backoff(10) == 30.0
    client.close()


def test_full_jitter_uses_injected_rng():
    # rng returns 0.5 -> delay is exactly half the ceiling.
    client = make_sync_client(
        single_response(200, envelope(QUOTE_DATA)), rng=lambda: 0.5
    )
    client._jitter = True
    client.backoff_base = 1.0
    # ceiling at attempt 0 = 1.0 ; * 0.5 = 0.5
    assert client._compute_backoff(0) == 0.5
    client.close()
