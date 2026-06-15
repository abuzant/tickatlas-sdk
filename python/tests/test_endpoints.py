"""Success-path tests for all 24 client methods (21 endpoints + health).

Each test asserts (a) the request the client builds (method, path, query/body —
including the documented param mappings like ``start`` -> ``from`` and the
screener ``min_val``), and (b) that the response payload parses into the right
typed model with the right field values.
"""

from __future__ import annotations

import json

import httpx
import pytest

import tickatlas
from tickatlas import Category, Indicators, Timeframe

from conftest import (
    ACCOUNT_DATA,
    BULK_QUOTES_DATA,
    CALENDAR_DATA,
    HEALTH_DATA,
    HEATMAP_CORRELATION_DATA,
    HEATMAP_STRENGTH_DATA,
    INDICATOR_DATA,
    INDICATOR_HISTORY_DATA,
    INDICATORS_DATA,
    INDICATORS_LIST_DATA,
    LAYOUT_DATA,
    LAYOUT_SAVE_DATA,
    MULTI_HISTORICAL_DATA,
    MULTI_REALTIME_DATA,
    OHLC_DATA,
    QUOTE_DATA,
    QUOTE_WITH_SOURCES_DATA,
    SCREENER_DATA,
    SESSIONS_DATA,
    SPREAD_COMPARE_DATA,
    SPREAD_DATA,
    SUMMARY_DATA,
    SYMBOL_SPEC_DATA,
    SYMBOLS_DATA,
    TICKS_DATA,
    envelope,
    make_sync_client,
    single_response,
)


def run(data, call):
    """Wire a one-shot success response, run ``call(client)``, return (result, request)."""
    handler = single_response(200, envelope(data), {"X-Request-ID": "abc123"})
    client = make_sync_client(handler)
    try:
        result = call(client)
    finally:
        client.close()
    return result, handler.recorded["request"]


def qp(request: httpx.Request):
    """Return query params as a plain dict."""
    return dict(request.url.params)


# --------------------------------------------------------------------------
# Auth header is always present and correct.
# --------------------------------------------------------------------------
def test_auth_and_user_agent_headers():
    _, req = run(SYMBOLS_DATA, lambda c: c.get_symbols())
    assert req.headers["X-API-Key"] == "claw_test_key_do_not_use"
    assert req.headers["User-Agent"] == f"tickatlas-python/{tickatlas.__version__}"


# --------------------------------------------------------------------------
# 7.1 / 7.2 symbols
# --------------------------------------------------------------------------
def test_get_symbols():
    res, req = run(
        SYMBOLS_DATA,
        lambda c: c.get_symbols(category=Category.FOREX, search="EUR", offset=0, limit=50),
    )
    assert req.method == "GET"
    assert req.url.path == "/v1/symbols"
    assert qp(req) == {"category": "forex", "search": "EUR", "offset": "0", "limit": "50"}
    assert isinstance(res, tickatlas.SymbolList)
    assert res.total == 149
    assert res.pagination.has_more is True
    item = res.symbols[0]
    assert item.symbol == "EURUSD"
    assert item.name is None
    assert item.base_currency == "EUR"
    assert item.digits == 5
    assert item.tradable is True
    assert item.raw["symbol"] == "EURUSD"


def test_get_symbol():
    res, req = run(SYMBOL_SPEC_DATA, lambda c: c.get_symbol("EURUSD"))
    assert req.url.path == "/v1/symbols/EURUSD"
    assert isinstance(res, tickatlas.SymbolSpec)
    assert res.contract_size == 100000.0
    assert res.min_volume == 0.01
    assert res.trading_hours["friday"] == "00:00-22:00"
    assert res.swap_long == -7.5


# --------------------------------------------------------------------------
# 7.3 / 7.4 quotes
# --------------------------------------------------------------------------
def test_get_quote():
    res, req = run(QUOTE_DATA, lambda c: c.get_quote("EURUSD"))
    assert req.url.path == "/v1/quote"
    assert qp(req) == {"symbol": "EURUSD", "include_sources": "false"}
    assert isinstance(res, tickatlas.Quote)
    assert res.bid == 1.16404
    assert res.ask == 1.16422
    assert res.spread_pips == 1.8
    assert res.source == "Equiti Securities"


def test_get_quote_with_sources():
    res, req = run(
        QUOTE_WITH_SOURCES_DATA,
        lambda c: c.get_quote("EURUSD", include_sources=True, source="IC Markets"),
    )
    assert qp(req) == {
        "symbol": "EURUSD",
        "include_sources": "true",
        "source": "IC Markets",
    }
    assert res.source_count == 2
    assert res.sources is not None
    assert res.sources[0].broker == "Equiti Securities"
    assert res.best_bid == 1.16405


def test_get_quotes_post_body():
    res, req = run(
        BULK_QUOTES_DATA,
        lambda c: c.get_quotes(["EURUSD", "GBPUSD"], fields=["bid", "ask"]),
    )
    assert req.method == "POST"
    assert req.url.path == "/v1/quotes"
    body = json.loads(req.content)
    assert body == {"symbols": ["EURUSD", "GBPUSD"], "fields": ["bid", "ask"]}
    assert isinstance(res, tickatlas.BulkQuotes)
    assert res.count == 2
    assert res.not_found == ["NOPE"]
    assert res.quotes[0].symbol == "EURUSD"
    assert res.quotes[0].bid == 1.16404


def test_get_quotes_accepts_csv_string():
    _, req = run(BULK_QUOTES_DATA, lambda c: c.get_quotes("EURUSD, GBPUSD"))
    body = json.loads(req.content)
    assert body == {"symbols": ["EURUSD", "GBPUSD"]}


# --------------------------------------------------------------------------
# 7.5 / 7.6 ohlc + ticks
# --------------------------------------------------------------------------
def test_get_ohlc_maps_start_end_to_from_to():
    res, req = run(
        OHLC_DATA,
        lambda c: c.get_ohlc(
            "EURUSD", timeframe=Timeframe.H1,
            start="2026-05-25T00:00:00Z", end="2026-05-26T00:00:00Z", limit=500,
        ),
    )
    assert req.url.path == "/v1/ohlc"
    params = qp(req)
    assert params["from"] == "2026-05-25T00:00:00Z"
    assert params["to"] == "2026-05-26T00:00:00Z"
    assert "start" not in params and "end" not in params
    assert params["timeframe"] == "H1"
    assert params["limit"] == "500"
    assert isinstance(res, tickatlas.OHLC)
    assert res.retention == "90d"
    candle = res.candles[0]
    assert candle.close == 1.16404
    assert candle.volume == 1523
    assert isinstance(candle.volume, int)


def test_get_ticks():
    res, req = run(
        TICKS_DATA,
        lambda c: c.get_ticks("EURUSD", "2026-05-25T13:00:00Z", "2026-05-25T13:30:00Z"),
    )
    assert req.url.path == "/v1/ticks"
    params = qp(req)
    assert params == {
        "symbol": "EURUSD",
        "from": "2026-05-25T13:00:00Z",
        "to": "2026-05-25T13:30:00Z",
    }
    assert isinstance(res, tickatlas.Ticks)
    assert res.count == 1
    assert res.ticks[0].flags == 6


# --------------------------------------------------------------------------
# 7.7 - 7.13 indicators
# --------------------------------------------------------------------------
def test_get_indicator():
    res, req = run(
        INDICATOR_DATA,
        lambda c: c.get_indicator("EURUSD", Indicators.RSI_14, timeframe="H1"),
    )
    assert req.url.path == "/v1/indicator"
    assert qp(req) == {"symbol": "EURUSD", "indicator": "RSI_14", "timeframe": "H1"}
    assert isinstance(res, tickatlas.Indicator)
    assert res.value == 58.34
    assert res.updated_at == 1711548000
    assert res.server_time == "2026-03-27T14:00:00"


def test_get_indicators():
    res, req = run(
        INDICATORS_DATA,
        lambda c: c.get_indicators("EURUSD", timeframe="H1", category="oscillator"),
    )
    assert req.url.path == "/v1/indicators"
    assert qp(req)["category"] == "oscillator"
    assert isinstance(res, tickatlas.IndicatorsModel)
    assert res.indicators["RSI_14"] == 58.34
    assert res.indicators["ATR_14"] is None
    assert res.count == 3
    assert res.ohlcv is not None and res.ohlcv["close"] == 1.16404
    assert res.bid == 1.16404


def test_list_indicators():
    res, req = run(INDICATORS_LIST_DATA, lambda c: c.list_indicators())
    assert req.url.path == "/v1/indicators/list"
    assert isinstance(res, tickatlas.IndicatorCatalogue)
    assert res.categories == ["trend", "oscillator", "volatility", "volume"]
    assert res.indicators["trend"]["SAR"] == "Parabolic SAR"


def test_get_indicator_history():
    res, req = run(
        INDICATOR_HISTORY_DATA,
        lambda c: c.get_indicator_history(
            "EURUSD", "RSI_14", timeframe="H1",
            start="2026-05-24T00:00:00Z", end="2026-05-25T00:00:00Z", limit=500,
        ),
    )
    assert req.url.path == "/v1/indicator/history"
    params = qp(req)
    assert params["from"] == "2026-05-24T00:00:00Z"
    assert params["to"] == "2026-05-25T00:00:00Z"
    assert isinstance(res, tickatlas.IndicatorHistory)
    assert res.max_window_hours == 720
    assert res.from_ == "2026-05-24T00:00:00Z"
    assert res.series[1].value is None


def test_get_multi_realtime():
    res, req = run(
        MULTI_REALTIME_DATA,
        lambda c: c.get_multi(["EURUSD", "GBPUSD"], ["RSI_14", "MACD_hist"], timeframe="H1"),
    )
    assert req.url.path == "/v1/multi"
    params = qp(req)
    assert params["symbols"] == "EURUSD,GBPUSD"
    assert params["indicators"] == "RSI_14,MACD_hist"
    assert isinstance(res, tickatlas.MultiIndicators)
    assert res.is_historical is False
    assert res.data["EURUSD"]["RSI_14"] == 58.34
    assert res.not_found is None


def test_get_multi_historical():
    res, req = run(
        MULTI_HISTORICAL_DATA,
        lambda c: c.get_multi(
            "EURUSD", "RSI_14", timeframe="H1",
            start="2026-05-24T00:00:00Z", end="2026-05-25T00:00:00Z",
        ),
    )
    params = qp(req)
    assert params["from"] == "2026-05-24T00:00:00Z"
    assert res.is_historical is True
    assert res.mode == "historical"
    assert isinstance(res.data["EURUSD"], list)
    assert res.data["EURUSD"][0]["RSI_14"] == 55.1


def test_screen_uses_min_val_max_val_and_asc_default():
    res, req = run(
        SCREENER_DATA,
        lambda c: c.screen("RSI_14", timeframe="H1", min_val=70, sort="desc", limit=50),
    )
    assert req.url.path == "/v1/screener"
    params = qp(req)
    # F2: must be min_val / max_val, never min / max.
    assert params["min_val"] == "70"
    assert "min" not in params and "max" not in params
    assert params["sort"] == "desc"
    assert isinstance(res, tickatlas.Screener)
    assert res.total_matches == 2
    assert res.filter == {"min": 70.0, "max": None}
    assert res.results[0].symbol == "GBPUSD"
    assert res.results[0].bid == 1.27001


def test_screen_default_sort_is_asc():
    _, req = run(SCREENER_DATA, lambda c: c.screen("RSI_14"))
    assert qp(req)["sort"] == "asc"


def test_get_summary():
    res, req = run(SUMMARY_DATA, lambda c: c.get_summary("EURUSD", timeframe="H1"))
    assert req.url.path == "/v1/summary"
    assert isinstance(res, tickatlas.Summary)
    assert res.bias == "bullish"
    assert res.bias_strength == "strong"
    assert res.confidence == 0.82
    assert res.key_levels["resistance"] == [1.165, 1.17]
    assert res.key_values["rsi_14"] == 58.34


# --------------------------------------------------------------------------
# 7.14 / 7.15 spread
# --------------------------------------------------------------------------
def test_get_spread():
    res, req = run(SPREAD_DATA, lambda c: c.get_spread("EURUSD", period="24h"))
    assert req.url.path == "/v1/spread"
    assert qp(req) == {"symbol": "EURUSD", "period": "24h"}
    assert isinstance(res, tickatlas.Spread)
    assert res.current["spread_pips"] == 1.8
    assert res.statistics.avg_spread == 1.9
    assert res.by_session["london"] == 1.6


def test_compare_spread():
    res, req = run(
        SPREAD_COMPARE_DATA,
        lambda c: c.compare_spread(["EURUSD", "NOPE"], period="7d"),
    )
    assert req.url.path == "/v1/spread/compare"
    params = qp(req)
    assert params["symbols"] == "EURUSD,NOPE"
    assert params["period"] == "7d"
    assert isinstance(res, tickatlas.SpreadCompare)
    assert res.count == 2
    assert res.symbols[1].has_live_data is False
    assert res.symbols[1].avg_pips is None


# --------------------------------------------------------------------------
# 7.16 - 7.18 sessions, heatmap, calendar
# --------------------------------------------------------------------------
def test_get_sessions():
    res, req = run(SESSIONS_DATA, lambda c: c.get_sessions())
    assert req.url.path == "/v1/sessions"
    assert isinstance(res, tickatlas.Sessions)
    assert res.active_sessions == ["london", "new_york"]
    assert res.sessions["london"].status == "open"
    assert res.sessions["london"].closes_in == "3h"
    assert res.next_major_event == {"event": "London close", "in": "3h"}


def test_get_heatmap_strength():
    res, req = run(
        HEATMAP_STRENGTH_DATA,
        lambda c: c.get_heatmap(type="strength", timeframe="H4"),
    )
    assert req.url.path == "/v1/heatmap"
    assert qp(req) == {"type": "strength", "timeframe": "H4"}
    assert isinstance(res, tickatlas.Heatmap)
    assert res.strongest == "USD"
    assert res.weakest == "EUR"
    assert res.currencies is not None
    assert res.currencies["USD"]["strength"] == 7.2


def test_get_heatmap_correlation():
    res, req = run(
        HEATMAP_CORRELATION_DATA,
        lambda c: c.get_heatmap(type="correlation", timeframe="H4", correlations=True),
    )
    assert qp(req)["correlations"] == "true"
    assert res.available is True
    assert res.correlation_matrix is not None
    assert res.correlation_matrix["USD"]["EUR"] == -0.85


def test_get_calendar():
    res, req = run(
        CALENDAR_DATA,
        lambda c: c.get_calendar(
            start="2026-06-01", end="2026-06-07",
            currencies="USD,EUR", impact="high", q="payroll",
            next_hours=24, offset=0, limit=100,
        ),
    )
    assert req.url.path == "/v1/calendar"
    params = qp(req)
    assert params["from"] == "2026-06-01"
    assert params["to"] == "2026-06-07"
    assert params["currencies"] == "USD,EUR"
    assert params["impact"] == "high"
    assert params["q"] == "payroll"
    assert params["next_hours"] == "24"
    assert isinstance(res, tickatlas.Calendar)
    assert res.count == 1
    ev = res.events[0]
    assert ev.event == "Non-Farm Payrolls"
    assert ev.actual is None
    # F18: calendar datetimes are naive UTC (no trailing Z).
    assert ev.datetime == "2026-06-01T12:30:00"


def test_get_calendar_currencies_list():
    _, req = run(CALENDAR_DATA, lambda c: c.get_calendar(currencies=["USD", "EUR"]))
    assert qp(req)["currencies"] == "USD,EUR"


# --------------------------------------------------------------------------
# 7.19 - 7.21 monitor
# --------------------------------------------------------------------------
def test_get_account():
    res, req = run(ACCOUNT_DATA, lambda c: c.get_account())
    assert req.url.path == "/v1/monitor/account"
    assert isinstance(res, tickatlas.Account)
    assert res.name == "Acme Trading"
    assert res.plan == "pro"
    assert res.daily_quota == 100000
    assert res.daily_used == 4213


def test_get_layout():
    res, req = run(LAYOUT_DATA, lambda c: c.get_layout())
    assert req.url.path == "/v1/monitor/layout"
    assert isinstance(res, tickatlas.Layout)
    assert res.layout == [{"widget": "quote", "symbol": "EURUSD"}]


def test_save_layout_put_body():
    layout = [{"widget": "quote", "symbol": "EURUSD"}]
    res, req = run(LAYOUT_SAVE_DATA, lambda c: c.save_layout(layout))
    assert req.method == "PUT"
    assert req.url.path == "/v1/monitor/layout"
    assert json.loads(req.content) == {"layout": layout}
    assert isinstance(res, tickatlas.LayoutSaveResult)
    assert res.saved is True


def test_get_layout_null():
    res, _ = run({"layout": None}, lambda c: c.get_layout())
    assert res.layout is None


# --------------------------------------------------------------------------
# infra probe
# --------------------------------------------------------------------------
def test_health():
    res, req = run(HEALTH_DATA, lambda c: c.health())
    assert req.url.path == "/v1/health"
    assert isinstance(res, tickatlas.Health)
    assert res.status == "ok"
    assert res.components == {"redis": "ok", "postgres": "ok"}


# --------------------------------------------------------------------------
# request_id is captured on the success path too (via .raw on errors); here we
# confirm empty/None query params are dropped.
# --------------------------------------------------------------------------
def test_none_params_are_dropped():
    _, req = run(QUOTE_DATA, lambda c: c.get_quote("EURUSD"))
    # `source` was None -> must not appear.
    assert "source" not in qp(req)


# --------------------------------------------------------------------------
# empty-but-valid responses parse to empty collections (SPEC 7.5/7.6).
# --------------------------------------------------------------------------
def test_empty_ohlc():
    data = {"symbol": "EURUSD", "timeframe": "H1", "candles": [], "count": 0, "retention": None}
    res, _ = run(data, lambda c: c.get_ohlc("EURUSD"))
    assert res.candles == []
    assert res.count == 0


@pytest.mark.parametrize(
    "method_name",
    [
        "get_symbols", "get_symbol", "get_quote", "get_quotes", "get_ohlc",
        "get_ticks", "get_indicator", "get_indicators", "list_indicators",
        "get_indicator_history", "get_multi", "screen", "get_summary",
        "get_spread", "compare_spread", "get_sessions", "get_heatmap",
        "get_calendar", "get_account", "get_layout", "save_layout", "health",
    ],
)
def test_method_exists_on_both_clients(method_name):
    """Coverage guard: every documented method exists on sync and async clients."""
    assert callable(getattr(tickatlas.TickAtlas, method_name))
    assert callable(getattr(tickatlas.AsyncTickAtlas, method_name))
