"""Integration tests against the REAL TickAtlas API.

These tests are **skipped by default**. They run only when BOTH:

* ``RUN_INTEGRATION=1`` is set, and
* ``TICKATLAS_API_KEY`` is set,

are present in the environment. They are strictly **read-only** and never call the
write endpoint (``save_layout`` / ``PUT /monitor/layout``).

Run them explicitly with::

    RUN_INTEGRATION=1 TICKATLAS_API_KEY="tk_..." pytest tests/test_integration.py

Set ``TICKATLAS_BASE_URL`` to target a staging deployment. A test symbol can be
overridden with ``TICKATLAS_TEST_SYMBOL`` (default ``EURUSD``).
"""

from __future__ import annotations

import os

import pytest

import tickatlas
from tickatlas import AsyncTickAtlas, Indicators, TickAtlas, Timeframe

RUN_INTEGRATION = os.environ.get("RUN_INTEGRATION") == "1"
HAS_KEY = bool(os.environ.get("TICKATLAS_API_KEY"))
TEST_SYMBOL = os.environ.get("TICKATLAS_TEST_SYMBOL", "EURUSD")

pytestmark = pytest.mark.skipif(
    not (RUN_INTEGRATION and HAS_KEY),
    reason="integration tests require RUN_INTEGRATION=1 and TICKATLAS_API_KEY",
)


@pytest.fixture(scope="module")
def client():
    # Key/base URL come from the environment (TICKATLAS_API_KEY / _BASE_URL).
    c = TickAtlas()
    yield c
    c.close()


# --------------------------------------------------------------------------
# Read-only smoke tests across the surface.
# --------------------------------------------------------------------------
def test_health(client):
    health = client.health()
    assert health.status is not None


def test_account_identity(client):
    account = client.get_account()
    assert account.plan is not None  # identity endpoint always returns a plan


def test_symbols(client):
    symbols = client.get_symbols(limit=5)
    assert symbols.total >= 0
    assert len(symbols.symbols) <= 5


def test_symbol_spec(client):
    spec = client.get_symbol(TEST_SYMBOL)
    assert spec.symbol.upper() == TEST_SYMBOL.upper()
    assert spec.digits >= 0


def test_quote(client):
    quote = client.get_quote(TEST_SYMBOL)
    assert quote.symbol.upper() == TEST_SYMBOL.upper()


def test_bulk_quotes(client):
    bulk = client.get_quotes([TEST_SYMBOL])
    assert bulk.count >= 0


def test_ohlc(client):
    ohlc = client.get_ohlc(TEST_SYMBOL, timeframe=Timeframe.H1, limit=10)
    assert ohlc.timeframe == "H1"
    assert len(ohlc.candles) <= 10


def test_indicator(client):
    ind = client.get_indicator(TEST_SYMBOL, Indicators.RSI_14, timeframe=Timeframe.H1)
    assert ind.indicator == "RSI_14"


def test_indicators(client):
    ind = client.get_indicators(TEST_SYMBOL, timeframe=Timeframe.H1)
    assert ind.symbol.upper() == TEST_SYMBOL.upper()


def test_indicators_list(client):
    catalogue = client.list_indicators()
    assert "trend" in catalogue.categories or len(catalogue.categories) > 0


def test_summary(client):
    summary = client.get_summary(TEST_SYMBOL, timeframe=Timeframe.H1)
    assert summary.bias in {"bullish", "bearish", "neutral"}


def test_spread(client):
    spread = client.get_spread(TEST_SYMBOL, period="24h")
    assert spread.symbol.upper() == TEST_SYMBOL.upper()


def test_spread_compare(client):
    cmp = client.compare_spread([TEST_SYMBOL], period="24h")
    assert cmp.count >= 0


def test_sessions(client):
    sessions = client.get_sessions()
    assert isinstance(sessions.active_sessions, list)


def test_screener(client):
    screen = client.screen(Indicators.RSI_14, timeframe=Timeframe.H1, limit=5)
    assert screen.indicator == "RSI_14"


def test_layout_read_only(client):
    # Read-only: GET layout is safe; we never call save_layout here.
    layout = client.get_layout()
    assert layout.layout is None or isinstance(layout.layout, list)


# --------------------------------------------------------------------------
# Plan-gated / premium endpoints: tolerate a permission error on lower plans.
# --------------------------------------------------------------------------
def test_heatmap_or_permission(client):
    try:
        heatmap = client.get_heatmap(timeframe="H4")
        assert heatmap.type in {"strength", "correlation"}
    except tickatlas.PermissionDeniedError:
        pytest.skip("heatmap requires a higher plan for this key")


def test_calendar_or_permission(client):
    try:
        calendar = client.get_calendar(limit=5)
        assert calendar.count >= 0
    except tickatlas.PermissionDeniedError:
        pytest.skip("calendar requires a higher plan for this key")


def test_multi_or_permission(client):
    try:
        multi = client.get_multi([TEST_SYMBOL], [Indicators.RSI_14], timeframe="H1")
        assert TEST_SYMBOL.upper() in {k.upper() for k in multi.data} or not multi.data
    except tickatlas.PermissionDeniedError:
        pytest.skip("multi requires a higher plan for this key")


def test_ticks_or_permission(client):
    # Ticks need pro/enterprise; a 1-hour window is the max allowed.
    from datetime import datetime, timedelta, timezone

    end = datetime.now(timezone.utc).replace(microsecond=0)
    start = end - timedelta(minutes=30)
    try:
        ticks = client.get_ticks(
            TEST_SYMBOL, start.isoformat(), end.isoformat()
        )
        assert ticks.count >= 0
    except tickatlas.PermissionDeniedError:
        pytest.skip("ticks require pro/enterprise for this key")


def test_indicator_history_or_permission(client):
    try:
        hist = client.get_indicator_history(
            TEST_SYMBOL, Indicators.RSI_14, timeframe="H1", limit=10
        )
        assert hist.indicator == "RSI_14"
    except tickatlas.PermissionDeniedError:
        pytest.skip("indicator history requires starter+ for this key")


# --------------------------------------------------------------------------
# Async smoke test.
# --------------------------------------------------------------------------
async def test_async_quote():
    async with AsyncTickAtlas() as client:
        quote = await client.get_quote(TEST_SYMBOL)
        assert quote.symbol.upper() == TEST_SYMBOL.upper()
