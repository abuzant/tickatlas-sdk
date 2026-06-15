"""Async client tests: success parsing, error mapping, retry + Retry-After.

``asyncio_mode = "auto"`` (set in pyproject) means plain ``async def test_*``
functions are collected and run without an explicit marker.
"""

from __future__ import annotations

import json

import httpx
import pytest

import tickatlas
from tickatlas import NotFoundError, RateLimitError

from conftest import (
    BULK_QUOTES_DATA,
    CALENDAR_DATA,
    HEATMAP_STRENGTH_DATA,
    QUOTE_DATA,
    SYMBOLS_DATA,
    envelope,
    error_envelope,
    make_async_client,
    sequence_handler,
    single_response,
)


async def test_async_get_quote_success():
    handler = single_response(200, envelope(QUOTE_DATA), {"X-Request-ID": "a1"})
    client = make_async_client(handler)
    quote = await client.get_quote("EURUSD")
    await client.aclose()
    assert isinstance(quote, tickatlas.Quote)
    assert quote.bid == 1.16404
    assert quote.ask == 1.16422


async def test_async_context_manager():
    handler = single_response(200, envelope(SYMBOLS_DATA))
    async with make_async_client(handler) as client:
        symbols = await client.get_symbols(category="forex")
    assert symbols.total == 149
    assert symbols.symbols[0].symbol == "EURUSD"


async def test_async_post_quotes_body():
    handler = single_response(200, envelope(BULK_QUOTES_DATA))
    client = make_async_client(handler)
    res = await client.get_quotes(["EURUSD", "GBPUSD"], fields=["bid"])
    await client.aclose()
    req = handler.recorded["request"]
    assert req.method == "POST"
    assert json.loads(req.content) == {"symbols": ["EURUSD", "GBPUSD"], "fields": ["bid"]}
    assert res.count == 2


async def test_async_get_heatmap():
    handler = single_response(200, envelope(HEATMAP_STRENGTH_DATA))
    client = make_async_client(handler)
    res = await client.get_heatmap(type="strength", timeframe="H4")
    await client.aclose()
    assert res.strongest == "USD"


async def test_async_calendar_param_mapping():
    handler = single_response(200, envelope(CALENDAR_DATA))
    client = make_async_client(handler)
    await client.get_calendar(start="2026-06-01", end="2026-06-07", currencies="USD")
    await client.aclose()
    params = dict(handler.recorded["request"].url.params)
    assert params["from"] == "2026-06-01"
    assert params["to"] == "2026-06-07"
    assert params["currencies"] == "USD"


async def test_async_error_mapping():
    handler = single_response(404, error_envelope("SYMBOL_NOT_FOUND", "no such"))
    client = make_async_client(handler, max_retries=0)
    with pytest.raises(NotFoundError) as exc:
        await client.get_quote("NOPE")
    await client.aclose()
    assert exc.value.code == "SYMBOL_NOT_FOUND"
    assert exc.value.status_code == 404


async def test_async_retry_on_429_honours_retry_after():
    slept = []

    async def fake_sleep(d):
        slept.append(d)

    handler = sequence_handler(
        [
            (429, error_envelope("RATE_LIMIT_EXCEEDED", "slow"), {"Retry-After": "5"}),
            (200, envelope(QUOTE_DATA), {}),
        ]
    )
    client = make_async_client(handler, max_retries=3)
    client._sleep = fake_sleep  # inject deterministic async sleep
    res = await client.get_quote("EURUSD")
    await client.aclose()
    assert res.bid == 1.16404
    assert slept == [5.0]
    assert handler.state["i"] == 2


async def test_async_retry_exhausted_raises_rate_limit():
    async def fake_sleep(d):
        return None

    handler = single_response(
        429, error_envelope("RATE_LIMIT_EXCEEDED", "no"), {"Retry-After": "2"}
    )
    client = make_async_client(handler, max_retries=1)
    client._sleep = fake_sleep
    with pytest.raises(RateLimitError) as exc:
        await client.get_quote("EURUSD")
    await client.aclose()
    assert exc.value.retry_after == 2.0


async def test_async_network_error_wrapped():
    async def fake_sleep(d):
        return None

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom")

    client = make_async_client(handler, max_retries=1)
    client._sleep = fake_sleep
    with pytest.raises(tickatlas.TickAtlasNetworkError):
        await client.get_quote("EURUSD")
    await client.aclose()
