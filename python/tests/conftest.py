"""Shared pytest fixtures: example payloads (from SPEC section 7) and helpers.

No test in this suite touches the network: every test drives the client through
an ``httpx.MockTransport`` so the request/retry/parse pipeline is exercised end
to end against canned responses.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple

import httpx
import pytest

from tickatlas import AsyncTickAtlas, TickAtlas

API_KEY = "claw_test_key_do_not_use"
BASE_URL = "https://api.test.tickatlas.local/v1"


# --------------------------------------------------------------------------
# Example success payloads (data objects), mostly verbatim from SPEC section 7.
# --------------------------------------------------------------------------
SYMBOLS_DATA: Dict[str, Any] = {
    "symbols": [
        {
            "symbol": "EURUSD",
            "name": None,
            "category": "forex",
            "base_currency": "EUR",
            "quote_currency": "USD",
            "digits": 5,
            "tradable": True,
        }
    ],
    "total": 149,
    "pagination": {"offset": 0, "limit": 100, "total": 149, "has_more": True},
}

SYMBOL_SPEC_DATA: Dict[str, Any] = {
    "symbol": "EURUSD",
    "name": "Euro vs US Dollar",
    "category": "forex",
    "description": "Euro vs US Dollar",
    "base_currency": "EUR",
    "quote_currency": "USD",
    "digits": 5,
    "point": 0.00001,
    "contract_size": 100000,
    "min_volume": 0.01,
    "max_volume": 500,
    "volume_step": 0.01,
    "swap_long": -7.5,
    "swap_short": 2.1,
    "margin_currency": "USD",
    "trading_hours": {
        "sunday": "22:00-24:00",
        "monday": "00:00-24:00",
        "tuesday": "00:00-24:00",
        "wednesday": "00:00-24:00",
        "thursday": "00:00-24:00",
        "friday": "00:00-22:00",
        "saturday": "closed",
    },
}

QUOTE_DATA: Dict[str, Any] = {
    "symbol": "EURUSD",
    "bid": 1.16404,
    "ask": 1.16422,
    "spread": 18,
    "spread_pips": 1.8,
    "timestamp": "2026-05-25T13:56:15.819519+00:00",
    "source": "Equiti Securities",
}

QUOTE_WITH_SOURCES_DATA: Dict[str, Any] = {
    "symbol": "EURUSD",
    "bid": 1.16404,
    "ask": 1.16422,
    "spread": 18,
    "spread_pips": 1.8,
    "timestamp": "2026-05-25T13:56:15.819519+00:00",
    "best_bid": 1.16405,
    "best_ask": 1.16421,
    "best_spread": 16,
    "source_count": 2,
    "sources": [
        {
            "broker": "Equiti Securities",
            "bid": 1.16404,
            "ask": 1.16422,
            "spread": 18,
            "updated": "2026-05-25T13:56:15+00:00",
        },
        {
            "broker": "IC Markets",
            "bid": 1.16405,
            "ask": 1.16421,
            "spread": 16,
            "updated": "2026-05-25T13:56:14+00:00",
        },
    ],
}

BULK_QUOTES_DATA: Dict[str, Any] = {
    "quotes": [
        {"symbol": "EURUSD", "bid": 1.16404, "ask": 1.16422},
        {"symbol": "GBPUSD", "bid": 1.27001, "ask": 1.27025},
    ],
    "count": 2,
    "not_found": ["NOPE"],
    "timestamp": "2026-05-25T13:56:15+00:00",
}

OHLC_DATA: Dict[str, Any] = {
    "symbol": "EURUSD",
    "timeframe": "H1",
    "candles": [
        {
            "time": "2026-05-25T13:00:00Z",
            "open": 1.16380,
            "high": 1.16450,
            "low": 1.16370,
            "close": 1.16404,
            "volume": 1523,
        }
    ],
    "count": 1,
    "retention": "90d",
}

TICKS_DATA: Dict[str, Any] = {
    "symbol": "EURUSD",
    "ticks": [
        {"time": "2026-05-25T13:00:00.123Z", "bid": 1.16404, "ask": 1.16422, "flags": 6}
    ],
    "count": 1,
}

INDICATOR_DATA: Dict[str, Any] = {
    "symbol": "EURUSD",
    "timeframe": "H1",
    "indicator": "RSI_14",
    "value": 58.34,
    "bid": 1.0831,
    "ask": 1.0832,
    "updated_at": 1711548000,
    "server_time": "2026-03-27T14:00:00",
}

INDICATORS_DATA: Dict[str, Any] = {
    "symbol": "EURUSD",
    "timeframe": "H1",
    "ohlcv": {
        "open": 1.16380,
        "high": 1.16450,
        "low": 1.16370,
        "close": 1.16404,
        "volume": 1523,
    },
    "bid": 1.16404,
    "ask": 1.16422,
    "indicators": {"RSI_14": 58.34, "MACD_hist": 0.00012, "ATR_14": None},
    "count": 3,
    "updated_at": 1711548000,
}

INDICATORS_LIST_DATA: Dict[str, Any] = {
    "indicators": {
        "trend": {"SMA_10": "Simple Moving Average (10)", "SAR": "Parabolic SAR"},
        "oscillator": {"RSI_14": "Relative Strength Index (14)"},
        "volatility": {"ATR_14": "Average True Range (14)"},
        "volume": {"Volumes": "Tick volume"},
    },
    "timeframes": ["M1", "M5", "M15", "M30", "H1", "H4", "D1"],
    "categories": ["trend", "oscillator", "volatility", "volume"],
}

INDICATOR_HISTORY_DATA: Dict[str, Any] = {
    "symbol": "EURUSD",
    "indicator": "RSI_14",
    "timeframe": "H1",
    "from": "2026-05-24T00:00:00Z",
    "to": "2026-05-25T00:00:00Z",
    "count": 2,
    "max_window_hours": 720,
    "series": [
        {"time": "2026-05-24T00:00:00Z", "value": 55.1},
        {"time": "2026-05-24T01:00:00Z", "value": None},
    ],
}

MULTI_REALTIME_DATA: Dict[str, Any] = {
    "timeframe": "H1",
    "data": {
        "EURUSD": {"RSI_14": 58.34, "MACD_hist": 0.00012},
        "GBPUSD": {"RSI_14": 61.2, "MACD_hist": -0.0003},
    },
    "not_found": None,
    "updated_at": 1711548000,
}

MULTI_HISTORICAL_DATA: Dict[str, Any] = {
    "timeframe": "H1",
    "mode": "historical",
    "from": "2026-05-24T00:00:00Z",
    "to": "2026-05-25T00:00:00Z",
    "data": {
        "EURUSD": [
            {"time": "2026-05-24T00:00:00Z", "RSI_14": 55.1},
            {"time": "2026-05-24T01:00:00Z", "RSI_14": 56.0},
        ]
    },
    "not_found": None,
}

SCREENER_DATA: Dict[str, Any] = {
    "indicator": "RSI_14",
    "timeframe": "H1",
    "filter": {"min": 70.0, "max": None},
    "results": [
        {"symbol": "GBPUSD", "value": 72.3, "bid": 1.27001},
        {"symbol": "EURUSD", "value": 71.1, "bid": 1.16404},
    ],
    "total_matches": 2,
    "pagination": {"offset": 0, "limit": 50, "total": 2, "has_more": False},
    "updated_at": 1711548000,
}

SUMMARY_DATA: Dict[str, Any] = {
    "symbol": "EURUSD",
    "timeframe": "H1",
    "bias": "bullish",
    "bias_strength": "strong",
    "confidence": 0.82,
    "trend_score": 3.5,
    "momentum_score": 1.2,
    "volatility_score": 0.4,
    "signals": {"trend": "up", "momentum": "up", "volatility": "normal", "volume": "high"},
    "key_levels": {"resistance": [1.165, 1.17], "support": [1.16, 1.158]},
    "bullish_signals": ["Price above SMA_200"],
    "bearish_signals": [],
    "neutral_signals": [],
    "volatility_info": ["ATR normal"],
    "volume_info": ["Above average"],
    "summary": "EURUSD shows a strong bullish bias.",
    "recommendations": ["Consider long positions"],
    "key_values": {
        "bid": 1.16404,
        "ask": 1.16422,
        "rsi_14": 58.34,
        "macd_hist": 0.00012,
        "adx": 27.5,
        "atr_14": 0.0008,
        "sma_20": 1.163,
        "sma_50": 1.161,
        "sma_200": 1.155,
        "bb_upper": 1.166,
        "bb_lower": 1.160,
        "stochastic_k": 65.0,
        "mfi_14": 58.0,
    },
    "updated_at": 1711548000,
}

SPREAD_DATA: Dict[str, Any] = {
    "symbol": "EURUSD",
    "current": {"spread_pips": 1.8, "spread_points": 18},
    "statistics": {
        "period": "24h",
        "avg_spread": 1.9,
        "min_spread": 1.2,
        "max_spread": 3.4,
        "std_deviation": 0.4,
    },
    "by_session": {"asian": 2.1, "london": 1.6, "new_york": 1.8},
}

SPREAD_COMPARE_DATA: Dict[str, Any] = {
    "period": "24h",
    "symbols": [
        {
            "symbol": "EURUSD",
            "current_pips": 1.8,
            "avg_pips": 1.9,
            "min_pips": 1.2,
            "max_pips": 3.4,
            "has_live_data": True,
        },
        {
            "symbol": "NOPE",
            "current_pips": None,
            "avg_pips": None,
            "min_pips": None,
            "max_pips": None,
            "has_live_data": False,
        },
    ],
    "count": 2,
}

SESSIONS_DATA: Dict[str, Any] = {
    "current_time": "2026-05-25T13:56:15+00:00",
    "active_sessions": ["london", "new_york"],
    "sessions": {
        "sydney": {"status": "closed", "opens_in": "5h"},
        "tokyo": {"status": "closed", "opens_in": "6h"},
        "london": {"status": "open", "closes_in": "3h"},
        "new_york": {"status": "open", "closes_in": "6h"},
    },
    "overlaps": ["london/new_york"],
    "next_major_event": {"event": "London close", "in": "3h"},
}

HEATMAP_STRENGTH_DATA: Dict[str, Any] = {
    "type": "strength",
    "timeframe": "H4",
    "currencies": {
        "USD": {"strength": 7.2, "trend": "bullish", "change": 0.3, "pairs_analyzed": 7},
        "EUR": {"strength": 4.1, "trend": "bearish", "change": -0.2, "pairs_analyzed": 7},
    },
    "strongest": "USD",
    "weakest": "EUR",
    "range": 3.1,
    "timestamp": "2026-05-25T13:56:15+00:00",
}

HEATMAP_CORRELATION_DATA: Dict[str, Any] = {
    "type": "correlation",
    "timeframe": "H4",
    "correlation_matrix": {"USD": {"USD": 1.0, "EUR": -0.85}, "EUR": {"USD": -0.85, "EUR": 1.0}},
    "available": True,
    "timestamp": "2026-05-25T13:56:15+00:00",
}

CALENDAR_DATA: Dict[str, Any] = {
    "events": [
        {
            "id": "evt_123",
            "datetime": "2026-06-01T12:30:00",
            "currency": "USD",
            "event": "Non-Farm Payrolls",
            "impact": "high",
            "forecast": "180K",
            "previous": "175K",
            "actual": None,
        }
    ],
    "count": 1,
    "pagination": {"offset": 0, "limit": 100, "total": 1, "has_more": False},
    "range": {"from": "2026-06-01", "to": "2026-06-08"},
}

ACCOUNT_DATA: Dict[str, Any] = {
    "name": "Acme Trading",
    "plan": "pro",
    "prepaid_credits": 12.5,
    "daily_quota": 100000,
    "daily_used": 4213,
}

LAYOUT_DATA: Dict[str, Any] = {"layout": [{"widget": "quote", "symbol": "EURUSD"}]}

LAYOUT_SAVE_DATA: Dict[str, Any] = {"saved": True}

HEALTH_DATA: Dict[str, Any] = {
    "status": "ok",
    "components": {"redis": "ok", "postgres": "ok"},
}


def envelope(data: Any) -> Dict[str, Any]:
    """Wrap a data payload in the success envelope."""
    return {"success": True, "data": data}


def error_envelope(code: str, message: str, **extra: Any) -> Dict[str, Any]:
    """Build an error envelope with optional extra context fields."""
    err: Dict[str, Any] = {"code": code, "message": message}
    err.update(extra)
    return {"success": False, "error": err}


# --------------------------------------------------------------------------
# Transport helpers
# --------------------------------------------------------------------------
Handler = Callable[[httpx.Request], httpx.Response]


def make_sync_client(
    handler: Handler,
    **kwargs: Any,
) -> TickAtlas:
    """A sync client wired to a MockTransport, jitter off, instant retries."""
    kwargs.setdefault("jitter", False)
    kwargs.setdefault("backoff_base", 0.0001)
    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport, base_url=BASE_URL)
    return TickAtlas(
        api_key=API_KEY,
        base_url=BASE_URL,
        http_client=http_client,
        **kwargs,
    )


def make_async_client(
    handler: Handler,
    **kwargs: Any,
) -> AsyncTickAtlas:
    """An async client wired to a MockTransport, jitter off, instant retries."""
    kwargs.setdefault("jitter", False)
    kwargs.setdefault("backoff_base", 0.0001)
    transport = httpx.MockTransport(handler)
    http_client = httpx.AsyncClient(transport=transport, base_url=BASE_URL)
    return AsyncTickAtlas(
        api_key=API_KEY,
        base_url=BASE_URL,
        http_client=http_client,
        **kwargs,
    )


def single_response(
    status: int,
    json_body: Any,
    headers: Optional[Dict[str, str]] = None,
) -> Handler:
    """A handler that records the request and always returns the same response."""

    def handler(request: httpx.Request) -> httpx.Response:
        recorded["request"] = request
        return httpx.Response(status, json=json_body, headers=headers or {})

    recorded: Dict[str, Any] = {}
    handler.recorded = recorded  # type: ignore[attr-defined]
    return handler


def sequence_handler(
    responses: List[Tuple[int, Any, Optional[Dict[str, str]]]],
) -> Handler:
    """A handler that returns each response in order, recording every request."""
    state = {"i": 0, "requests": []}  # type: Dict[str, Any]

    def handler(request: httpx.Request) -> httpx.Response:
        state["requests"].append(request)
        idx = min(state["i"], len(responses) - 1)
        status, body, headers = responses[idx]
        state["i"] += 1
        return httpx.Response(status, json=body, headers=headers or {})

    handler.state = state  # type: ignore[attr-defined]
    return handler


@pytest.fixture
def api_key() -> str:
    return API_KEY


@pytest.fixture
def base_url() -> str:
    return BASE_URL
