"""Endpoint definitions shared by the sync and async clients.

Each endpoint is described once as a function that turns the user-facing
arguments into a :class:`RequestSpec` plus the model parser to apply to the
returned ``data``. The sync/async clients then only differ in *how* they execute
the spec (blocking vs awaitable), not in *what* they send or parse.

This keeps the 24 method signatures, parameter mapping (e.g. ``start`` -> ``from``),
and response typing in a single place.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, TypeVar, Union

from . import _models as m
from ._constants import HeatmapType, SpreadPeriod, Timeframe
from ._transport import RequestSpec

T = TypeVar("T")

# A "plan" is the request to send plus the function that parses ``data`` into a model.
Plan = Tuple[RequestSpec, Callable[[Any], T]]

# Accept enums or raw strings everywhere.
StrLike = Union[str, Any]


def _s(value: Optional[StrLike]) -> Optional[str]:
    """Stringify an enum/str value, preserving ``None``."""
    return None if value is None else str(value)


def _csv(values: Union[str, Iterable[Any]]) -> str:
    """Join a list of symbols/indicators into the comma-separated form the API wants.

    A bare string is re-split on commas so empty items (e.g. a trailing comma in
    ``"EURUSD,"``) are dropped just like the iterable form.
    """
    items: Iterable[Any] = values.split(",") if isinstance(values, str) else values
    return ",".join(s for s in (str(v).strip() for v in items) if s)


# --------------------------------------------------------------------------
# Symbols
# --------------------------------------------------------------------------
def get_symbols(
    category: Optional[StrLike] = None,
    search: Optional[str] = None,
    offset: int = 0,
    limit: int = 100,
) -> Plan[m.SymbolList]:
    spec = RequestSpec(
        "GET",
        "/symbols",
        params={
            "category": _s(category),
            "search": search,
            "offset": offset,
            "limit": limit,
        },
    )
    return spec, m.SymbolList.from_dict


def get_symbol(symbol: str) -> Plan[m.SymbolSpec]:
    spec = RequestSpec("GET", f"/symbols/{symbol}")
    return spec, m.SymbolSpec.from_dict


# --------------------------------------------------------------------------
# Quotes
# --------------------------------------------------------------------------
def get_quote(
    symbol: str,
    include_sources: bool = False,
    source: Optional[str] = None,
) -> Plan[m.Quote]:
    spec = RequestSpec(
        "GET",
        "/quote",
        params={
            "symbol": symbol,
            "include_sources": include_sources,
            "source": source,
        },
    )
    return spec, m.Quote.from_dict


def get_quotes(
    symbols: Union[str, Iterable[str]],
    fields: Optional[Iterable[str]] = None,
) -> Plan[m.BulkQuotes]:
    raw_syms: Iterable[str] = symbols.split(",") if isinstance(symbols, str) else symbols
    sym_list: List[str] = [s for s in (str(x).strip() for x in raw_syms) if s]
    body: Dict[str, Any] = {"symbols": sym_list}
    if fields is not None:
        body["fields"] = list(fields)
    spec = RequestSpec("POST", "/quotes", json=body)
    return spec, m.BulkQuotes.from_dict


# --------------------------------------------------------------------------
# OHLC / ticks
# --------------------------------------------------------------------------
def get_ohlc(
    symbol: str,
    timeframe: StrLike = Timeframe.H1,
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: int = 100,
) -> Plan[m.OHLC]:
    spec = RequestSpec(
        "GET",
        "/ohlc",
        params={
            "symbol": symbol,
            "timeframe": _s(timeframe),
            "from": start,
            "to": end,
            "limit": limit,
        },
    )
    return spec, m.OHLC.from_dict


def get_ticks(symbol: str, start: str, end: str) -> Plan[m.Ticks]:
    spec = RequestSpec(
        "GET",
        "/ticks",
        params={"symbol": symbol, "from": start, "to": end},
    )
    return spec, m.Ticks.from_dict


# --------------------------------------------------------------------------
# Indicators
# --------------------------------------------------------------------------
def get_indicator(
    symbol: str,
    indicator: StrLike,
    timeframe: StrLike = Timeframe.H1,
    source: Optional[str] = None,
) -> Plan[m.Indicator]:
    spec = RequestSpec(
        "GET",
        "/indicator",
        params={
            "symbol": symbol,
            "indicator": _s(indicator),
            "timeframe": _s(timeframe),
            "source": source,
        },
    )
    return spec, m.Indicator.from_dict


def get_indicators(
    symbol: str,
    timeframe: StrLike = Timeframe.H1,
    category: Optional[str] = None,
) -> Plan[m.Indicators]:
    spec = RequestSpec(
        "GET",
        "/indicators",
        params={
            "symbol": symbol,
            "timeframe": _s(timeframe),
            "category": category,
        },
    )
    return spec, m.Indicators.from_dict


def list_indicators() -> Plan[m.IndicatorCatalogue]:
    spec = RequestSpec("GET", "/indicators/list")
    return spec, m.IndicatorCatalogue.from_dict


def get_indicator_history(
    symbol: str,
    indicator: StrLike,
    timeframe: StrLike = Timeframe.H1,
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: int = 500,
) -> Plan[m.IndicatorHistory]:
    spec = RequestSpec(
        "GET",
        "/indicator/history",
        params={
            "symbol": symbol,
            "indicator": _s(indicator),
            "timeframe": _s(timeframe),
            "from": start,
            "to": end,
            "limit": limit,
        },
    )
    return spec, m.IndicatorHistory.from_dict


def get_multi(
    symbols: Union[str, Iterable[str]],
    indicators: Union[str, Iterable[str]],
    timeframe: StrLike = Timeframe.H1,
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> Plan[m.MultiIndicators]:
    spec = RequestSpec(
        "GET",
        "/multi",
        params={
            "symbols": _csv(symbols),
            "indicators": _csv(indicators),
            "timeframe": _s(timeframe),
            "from": start,
            "to": end,
        },
    )
    return spec, m.MultiIndicators.from_dict


def screen(
    indicator: StrLike,
    timeframe: StrLike = Timeframe.H1,
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
    sort: str = "asc",
    offset: int = 0,
    limit: int = 50,
) -> Plan[m.Screener]:
    spec = RequestSpec(
        "GET",
        "/screener",
        params={
            "indicator": _s(indicator),
            "timeframe": _s(timeframe),
            "min_val": min_val,
            "max_val": max_val,
            "sort": sort,
            "offset": offset,
            "limit": limit,
        },
    )
    return spec, m.Screener.from_dict


def get_summary(symbol: str, timeframe: StrLike = Timeframe.H1) -> Plan[m.Summary]:
    spec = RequestSpec(
        "GET",
        "/summary",
        params={"symbol": symbol, "timeframe": _s(timeframe)},
    )
    return spec, m.Summary.from_dict


# --------------------------------------------------------------------------
# Spread
# --------------------------------------------------------------------------
def get_spread(symbol: str, period: StrLike = SpreadPeriod.H24) -> Plan[m.Spread]:
    spec = RequestSpec(
        "GET",
        "/spread",
        params={"symbol": symbol, "period": _s(period)},
    )
    return spec, m.Spread.from_dict


def compare_spread(
    symbols: Union[str, Iterable[str]],
    period: StrLike = SpreadPeriod.H24,
) -> Plan[m.SpreadCompare]:
    spec = RequestSpec(
        "GET",
        "/spread/compare",
        params={"symbols": _csv(symbols), "period": _s(period)},
    )
    return spec, m.SpreadCompare.from_dict


# --------------------------------------------------------------------------
# Sessions / heatmap / calendar
# --------------------------------------------------------------------------
def get_sessions() -> Plan[m.Sessions]:
    spec = RequestSpec("GET", "/sessions")
    return spec, m.Sessions.from_dict


def get_heatmap(
    type: StrLike = HeatmapType.STRENGTH,
    timeframe: StrLike = "H4",
    correlations: Optional[bool] = None,
) -> Plan[m.Heatmap]:
    spec = RequestSpec(
        "GET",
        "/heatmap",
        params={
            "type": _s(type),
            "timeframe": _s(timeframe),
            "correlations": correlations,
        },
    )
    return spec, m.Heatmap.from_dict


def get_calendar(
    start: Optional[str] = None,
    end: Optional[str] = None,
    currencies: Optional[Union[str, Iterable[str]]] = None,
    country: Optional[Union[str, Iterable[str]]] = None,
    impact: Optional[StrLike] = None,
    q: Optional[str] = None,
    next_hours: Optional[int] = None,
    offset: int = 0,
    limit: int = 100,
) -> Plan[m.Calendar]:
    spec = RequestSpec(
        "GET",
        "/calendar",
        params={
            "from": start,
            "to": end,
            "currencies": _csv(currencies) if currencies is not None else None,
            "country": _csv(country) if country is not None else None,
            "impact": _s(impact),
            "q": q,
            "next_hours": next_hours,
            "offset": offset,
            "limit": limit,
        },
    )
    return spec, m.Calendar.from_dict


# --------------------------------------------------------------------------
# Monitor
# --------------------------------------------------------------------------
def get_account() -> Plan[m.Account]:
    spec = RequestSpec("GET", "/monitor/account")
    return spec, m.Account.from_dict


def get_layout() -> Plan[m.Layout]:
    spec = RequestSpec("GET", "/monitor/layout")
    return spec, m.Layout.from_dict


def save_layout(layout: List[Any]) -> Plan[m.LayoutSaveResult]:
    spec = RequestSpec("PUT", "/monitor/layout", json={"layout": list(layout)})
    return spec, m.LayoutSaveResult.from_dict


# --------------------------------------------------------------------------
# Infra
# --------------------------------------------------------------------------
def health() -> Plan[m.Health]:
    spec = RequestSpec("GET", "/health", root=True, raw=True)
    return spec, m.Health.from_dict
