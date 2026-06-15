"""Typed response models for every TickAtlas endpoint (SPEC section 7).

Conventions
-----------
* Every model is a **frozen** :func:`dataclasses.dataclass`.
* Each model parses from the unwrapped ``data`` dict via ``from_dict``.
* Every model keeps the original payload in ``.raw`` for forward-compatibility,
  so callers can read fields added by the API after this SDK was released.
* Unknown fields are tolerated (ignored at the typed level, preserved in ``.raw``).
* Numbers that may be ``null`` are typed ``Optional[float]``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

__all__ = [
    "Pagination",
    "SymbolListItem",
    "SymbolList",
    "SymbolSpec",
    "QuoteSource",
    "Quote",
    "BulkQuoteItem",
    "BulkQuotes",
    "Candle",
    "OHLC",
    "Tick",
    "Ticks",
    "Indicator",
    "Indicators",
    "IndicatorCatalogue",
    "IndicatorHistoryPoint",
    "IndicatorHistory",
    "MultiIndicators",
    "ScreenerResult",
    "Screener",
    "Summary",
    "SpreadStatistics",
    "Spread",
    "SpreadCompareItem",
    "SpreadCompare",
    "Session",
    "Sessions",
    "Heatmap",
    "CalendarEvent",
    "Calendar",
    "Account",
    "Layout",
    "LayoutSaveResult",
    "Health",
]


def _f(value: Any) -> Optional[float]:
    """Coerce to ``float`` while preserving ``None``."""
    if value is None:
        return None
    if isinstance(value, bool):  # guard: bool is an int subclass
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _i(value: Any) -> Optional[int]:
    """Coerce to ``int`` while preserving ``None``."""
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------------------
# Shared
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Pagination:
    """Pagination block shared by paginated list responses."""

    offset: int
    limit: int
    total: int
    has_more: bool

    @classmethod
    def from_dict(cls, d: Optional[Dict[str, Any]]) -> "Pagination":
        d = d or {}
        return cls(
            offset=_i(d.get("offset")) or 0,
            limit=_i(d.get("limit")) or 0,
            total=_i(d.get("total")) or 0,
            has_more=bool(d.get("has_more", False)),
        )


# --------------------------------------------------------------------------
# 7.1 / 7.2  Symbols
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class SymbolListItem:
    symbol: str
    category: str
    digits: int
    tradable: bool
    name: Optional[str] = None
    base_currency: Optional[str] = None
    quote_currency: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SymbolListItem":
        return cls(
            symbol=str(d.get("symbol", "")),
            category=str(d.get("category", "")),
            digits=_i(d.get("digits")) or 0,
            tradable=bool(d.get("tradable", False)),
            name=d.get("name"),
            base_currency=d.get("base_currency"),
            quote_currency=d.get("quote_currency"),
            raw=dict(d),
        )


@dataclass(frozen=True)
class SymbolList:
    symbols: List[SymbolListItem]
    total: int
    pagination: Pagination
    raw: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SymbolList":
        return cls(
            symbols=[SymbolListItem.from_dict(s) for s in d.get("symbols", []) or []],
            total=_i(d.get("total")) or 0,
            pagination=Pagination.from_dict(d.get("pagination")),
            raw=dict(d),
        )


@dataclass(frozen=True)
class SymbolSpec:
    """Symbol contract specification (``GET /symbols/{symbol}``)."""

    symbol: str
    category: str
    digits: int
    point: Optional[float]
    contract_size: Optional[float]
    min_volume: Optional[float]
    max_volume: Optional[float]
    volume_step: Optional[float]
    name: Optional[str] = None
    description: Optional[str] = None
    base_currency: Optional[str] = None
    quote_currency: Optional[str] = None
    swap_long: Optional[float] = None
    swap_short: Optional[float] = None
    margin_currency: Optional[str] = None
    trading_hours: Dict[str, Any] = field(default_factory=dict)
    raw: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SymbolSpec":
        return cls(
            symbol=str(d.get("symbol", "")),
            category=str(d.get("category", "")),
            digits=_i(d.get("digits")) or 0,
            point=_f(d.get("point")),
            contract_size=_f(d.get("contract_size")),
            min_volume=_f(d.get("min_volume")),
            max_volume=_f(d.get("max_volume")),
            volume_step=_f(d.get("volume_step")),
            name=d.get("name"),
            description=d.get("description"),
            base_currency=d.get("base_currency"),
            quote_currency=d.get("quote_currency"),
            swap_long=_f(d.get("swap_long")),
            swap_short=_f(d.get("swap_short")),
            margin_currency=d.get("margin_currency"),
            trading_hours=dict(d.get("trading_hours") or {}),
            raw=dict(d),
        )


# --------------------------------------------------------------------------
# 7.3 / 7.4  Quotes
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class QuoteSource:
    broker: Optional[str]
    bid: Optional[float]
    ask: Optional[float]
    spread: Optional[float]
    updated: Optional[str]
    raw: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "QuoteSource":
        return cls(
            broker=d.get("broker"),
            bid=_f(d.get("bid")),
            ask=_f(d.get("ask")),
            spread=_f(d.get("spread")),
            updated=d.get("updated"),
            raw=dict(d),
        )


@dataclass(frozen=True)
class Quote:
    """Single real-time quote (``GET /quote``)."""

    symbol: str
    bid: Optional[float]
    ask: Optional[float]
    spread: Optional[float]
    spread_pips: Optional[float]
    timestamp: Optional[str]
    source: Optional[str] = None
    best_bid: Optional[float] = None
    best_ask: Optional[float] = None
    best_spread: Optional[float] = None
    source_count: Optional[int] = None
    sources: Optional[List[QuoteSource]] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Quote":
        sources_raw = d.get("sources")
        sources = (
            [QuoteSource.from_dict(s) for s in sources_raw]
            if isinstance(sources_raw, list)
            else None
        )
        return cls(
            symbol=str(d.get("symbol", "")),
            bid=_f(d.get("bid")),
            ask=_f(d.get("ask")),
            spread=_f(d.get("spread")),
            spread_pips=_f(d.get("spread_pips")),
            timestamp=d.get("timestamp"),
            source=d.get("source"),
            best_bid=_f(d.get("best_bid")),
            best_ask=_f(d.get("best_ask")),
            best_spread=_f(d.get("best_spread")),
            source_count=_i(d.get("source_count")),
            sources=sources,
            raw=dict(d),
        )


@dataclass(frozen=True)
class BulkQuoteItem:
    symbol: str
    bid: Optional[float] = None
    ask: Optional[float] = None
    spread: Optional[float] = None
    spread_pips: Optional[float] = None
    timestamp: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "BulkQuoteItem":
        return cls(
            symbol=str(d.get("symbol", "")),
            bid=_f(d.get("bid")) if "bid" in d else None,
            ask=_f(d.get("ask")) if "ask" in d else None,
            spread=_f(d.get("spread")) if "spread" in d else None,
            spread_pips=_f(d.get("spread_pips")) if "spread_pips" in d else None,
            timestamp=d.get("timestamp"),
            raw=dict(d),
        )


@dataclass(frozen=True)
class BulkQuotes:
    """Batch quotes (``POST /quotes``)."""

    quotes: List[BulkQuoteItem]
    count: int
    not_found: Optional[List[str]]
    timestamp: Optional[str]
    raw: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "BulkQuotes":
        return cls(
            quotes=[BulkQuoteItem.from_dict(q) for q in d.get("quotes", []) or []],
            count=_i(d.get("count")) or 0,
            not_found=list(d["not_found"]) if d.get("not_found") else None,
            timestamp=d.get("timestamp"),
            raw=dict(d),
        )


# --------------------------------------------------------------------------
# 7.5  OHLC
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Candle:
    time: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    raw: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Candle":
        return cls(
            time=str(d.get("time", "")),
            open=_f(d.get("open")) or 0.0,
            high=_f(d.get("high")) or 0.0,
            low=_f(d.get("low")) or 0.0,
            close=_f(d.get("close")) or 0.0,
            volume=_i(d.get("volume")) or 0,
            raw=dict(d),
        )


@dataclass(frozen=True)
class OHLC:
    """OHLC candles (``GET /ohlc``)."""

    symbol: str
    timeframe: str
    candles: List[Candle]
    count: int
    retention: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "OHLC":
        return cls(
            symbol=str(d.get("symbol", "")),
            timeframe=str(d.get("timeframe", "")),
            candles=[Candle.from_dict(c) for c in d.get("candles", []) or []],
            count=_i(d.get("count")) or 0,
            retention=d.get("retention"),
            raw=dict(d),
        )


# --------------------------------------------------------------------------
# 7.6  Ticks
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Tick:
    time: str
    bid: Optional[float]
    ask: Optional[float]
    flags: Optional[int]
    raw: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Tick":
        return cls(
            time=str(d.get("time", "")),
            bid=_f(d.get("bid")),
            ask=_f(d.get("ask")),
            flags=_i(d.get("flags")),
            raw=dict(d),
        )


@dataclass(frozen=True)
class Ticks:
    """Tick data (``GET /ticks``)."""

    symbol: str
    ticks: List[Tick]
    count: int
    raw: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Ticks":
        return cls(
            symbol=str(d.get("symbol", "")),
            ticks=[Tick.from_dict(t) for t in d.get("ticks", []) or []],
            count=_i(d.get("count")) or 0,
            raw=dict(d),
        )


# --------------------------------------------------------------------------
# 7.7  Single indicator
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Indicator:
    """Single indicator value (``GET /indicator``)."""

    symbol: str
    timeframe: str
    indicator: str
    value: Optional[float]
    bid: Optional[float]
    ask: Optional[float]
    updated_at: Optional[int]
    server_time: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Indicator":
        return cls(
            symbol=str(d.get("symbol", "")),
            timeframe=str(d.get("timeframe", "")),
            indicator=str(d.get("indicator", "")),
            value=_f(d.get("value")),
            bid=_f(d.get("bid")),
            ask=_f(d.get("ask")),
            updated_at=_i(d.get("updated_at")),
            server_time=d.get("server_time"),
            raw=dict(d),
        )


# --------------------------------------------------------------------------
# 7.8  All indicators for a symbol
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Indicators:
    """All indicators for a symbol (``GET /indicators``)."""

    symbol: str
    timeframe: str
    indicators: Dict[str, Optional[float]]
    count: int
    updated_at: Optional[int]
    ohlcv: Optional[Dict[str, Any]] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Indicators":
        ind_raw = d.get("indicators") or {}
        indicators = {k: _f(v) for k, v in ind_raw.items()}
        ohlcv = d.get("ohlcv")
        return cls(
            symbol=str(d.get("symbol", "")),
            timeframe=str(d.get("timeframe", "")),
            indicators=indicators,
            count=_i(d.get("count")) or 0,
            updated_at=_i(d.get("updated_at")),
            ohlcv=dict(ohlcv) if isinstance(ohlcv, dict) else None,
            bid=_f(d.get("bid")),
            ask=_f(d.get("ask")),
            raw=dict(d),
        )


# --------------------------------------------------------------------------
# 7.9  Indicator catalogue
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class IndicatorCatalogue:
    """Indicator catalogue (``GET /indicators/list``)."""

    indicators: Dict[str, Dict[str, str]]
    timeframes: List[str]
    categories: List[str]
    raw: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "IndicatorCatalogue":
        return cls(
            indicators=dict(d.get("indicators") or {}),
            timeframes=list(d.get("timeframes") or []),
            categories=list(d.get("categories") or []),
            raw=dict(d),
        )


# --------------------------------------------------------------------------
# 7.10  Indicator history
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class IndicatorHistoryPoint:
    time: str
    value: Optional[float]
    raw: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "IndicatorHistoryPoint":
        return cls(
            time=str(d.get("time", "")),
            value=_f(d.get("value")),
            raw=dict(d),
        )


@dataclass(frozen=True)
class IndicatorHistory:
    """Indicator series (``GET /indicator/history``)."""

    symbol: str
    indicator: str
    timeframe: str
    count: int
    series: List[IndicatorHistoryPoint]
    from_: Optional[str] = None
    to: Optional[str] = None
    max_window_hours: Optional[int] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "IndicatorHistory":
        return cls(
            symbol=str(d.get("symbol", "")),
            indicator=str(d.get("indicator", "")),
            timeframe=str(d.get("timeframe", "")),
            count=_i(d.get("count")) or 0,
            series=[
                IndicatorHistoryPoint.from_dict(p) for p in d.get("series", []) or []
            ],
            from_=d.get("from"),
            to=d.get("to"),
            max_window_hours=_i(d.get("max_window_hours")),
            raw=dict(d),
        )


# --------------------------------------------------------------------------
# 7.11  Multi
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class MultiIndicators:
    """Batch indicators across symbols (``GET /multi``).

    Works for both real-time and historical mode. In real-time mode ``data`` maps
    ``symbol -> {indicator: value}``; in historical mode ``data`` maps
    ``symbol -> [{time, indicator: value}, ...]`` and ``mode == "historical"``.
    """

    timeframe: str
    data: Dict[str, Any]
    not_found: Optional[List[str]]
    updated_at: Optional[int] = None
    mode: Optional[str] = None
    from_: Optional[str] = None
    to: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @property
    def is_historical(self) -> bool:
        return self.mode == "historical"

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "MultiIndicators":
        return cls(
            timeframe=str(d.get("timeframe", "")),
            data=dict(d.get("data") or {}),
            not_found=list(d["not_found"]) if d.get("not_found") else None,
            updated_at=_i(d.get("updated_at")),
            mode=d.get("mode"),
            from_=d.get("from"),
            to=d.get("to"),
            raw=dict(d),
        )


# --------------------------------------------------------------------------
# 7.12  Screener
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class ScreenerResult:
    symbol: str
    value: Optional[float]
    bid: Optional[float]
    raw: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ScreenerResult":
        return cls(
            symbol=str(d.get("symbol", "")),
            value=_f(d.get("value")),
            bid=_f(d.get("bid")),
            raw=dict(d),
        )


@dataclass(frozen=True)
class Screener:
    """Symbol scan by indicator (``GET /screener``)."""

    indicator: str
    timeframe: str
    filter: Dict[str, Optional[float]]
    results: List[ScreenerResult]
    total_matches: int
    pagination: Pagination
    updated_at: Optional[int] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Screener":
        flt_raw = d.get("filter") or {}
        return cls(
            indicator=str(d.get("indicator", "")),
            timeframe=str(d.get("timeframe", "")),
            filter={"min": _f(flt_raw.get("min")), "max": _f(flt_raw.get("max"))},
            results=[ScreenerResult.from_dict(r) for r in d.get("results", []) or []],
            total_matches=_i(d.get("total_matches")) or 0,
            pagination=Pagination.from_dict(d.get("pagination")),
            updated_at=_i(d.get("updated_at")),
            raw=dict(d),
        )


# --------------------------------------------------------------------------
# 7.13  Summary
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Summary:
    """Market-bias summary (``GET /summary``)."""

    symbol: str
    timeframe: str
    bias: str
    bias_strength: str
    confidence: Optional[float]
    trend_score: Optional[float]
    momentum_score: Optional[float]
    volatility_score: Optional[float]
    signals: Dict[str, Any] = field(default_factory=dict)
    key_levels: Dict[str, Any] = field(default_factory=dict)
    bullish_signals: List[str] = field(default_factory=list)
    bearish_signals: List[str] = field(default_factory=list)
    neutral_signals: List[str] = field(default_factory=list)
    volatility_info: List[str] = field(default_factory=list)
    volume_info: List[str] = field(default_factory=list)
    summary: Optional[str] = None
    recommendations: List[str] = field(default_factory=list)
    key_values: Dict[str, Any] = field(default_factory=dict)
    updated_at: Optional[int] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Summary":
        return cls(
            symbol=str(d.get("symbol", "")),
            timeframe=str(d.get("timeframe", "")),
            bias=str(d.get("bias", "")),
            bias_strength=str(d.get("bias_strength", "")),
            confidence=_f(d.get("confidence")),
            trend_score=_f(d.get("trend_score")),
            momentum_score=_f(d.get("momentum_score")),
            volatility_score=_f(d.get("volatility_score")),
            signals=dict(d.get("signals") or {}),
            key_levels=dict(d.get("key_levels") or {}),
            bullish_signals=list(d.get("bullish_signals") or []),
            bearish_signals=list(d.get("bearish_signals") or []),
            neutral_signals=list(d.get("neutral_signals") or []),
            volatility_info=list(d.get("volatility_info") or []),
            volume_info=list(d.get("volume_info") or []),
            summary=d.get("summary"),
            recommendations=list(d.get("recommendations") or []),
            key_values=dict(d.get("key_values") or {}),
            updated_at=_i(d.get("updated_at")),
            raw=dict(d),
        )


# --------------------------------------------------------------------------
# 7.14  Spread
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class SpreadStatistics:
    period: Optional[str]
    avg_spread: Optional[float]
    min_spread: Optional[float]
    max_spread: Optional[float]
    std_deviation: Optional[float]
    raw: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, d: Optional[Dict[str, Any]]) -> "SpreadStatistics":
        d = d or {}
        return cls(
            period=d.get("period"),
            avg_spread=_f(d.get("avg_spread")),
            min_spread=_f(d.get("min_spread")),
            max_spread=_f(d.get("max_spread")),
            std_deviation=_f(d.get("std_deviation")),
            raw=dict(d),
        )


@dataclass(frozen=True)
class Spread:
    """Spread statistics (``GET /spread``)."""

    symbol: str
    current: Dict[str, Any]
    statistics: SpreadStatistics
    by_session: Dict[str, Optional[float]]
    raw: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Spread":
        sess_raw = d.get("by_session") or {}
        return cls(
            symbol=str(d.get("symbol", "")),
            current=dict(d.get("current") or {}),
            statistics=SpreadStatistics.from_dict(d.get("statistics")),
            by_session={k: _f(v) for k, v in sess_raw.items()},
            raw=dict(d),
        )


@dataclass(frozen=True)
class SpreadCompareItem:
    symbol: str
    current_pips: Optional[float]
    avg_pips: Optional[float]
    min_pips: Optional[float]
    max_pips: Optional[float]
    has_live_data: bool
    raw: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SpreadCompareItem":
        return cls(
            symbol=str(d.get("symbol", "")),
            current_pips=_f(d.get("current_pips")),
            avg_pips=_f(d.get("avg_pips")),
            min_pips=_f(d.get("min_pips")),
            max_pips=_f(d.get("max_pips")),
            has_live_data=bool(d.get("has_live_data", False)),
            raw=dict(d),
        )


@dataclass(frozen=True)
class SpreadCompare:
    """Spread comparison across symbols (``GET /spread/compare``)."""

    period: str
    symbols: List[SpreadCompareItem]
    count: int
    raw: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SpreadCompare":
        return cls(
            period=str(d.get("period", "")),
            symbols=[
                SpreadCompareItem.from_dict(s) for s in d.get("symbols", []) or []
            ],
            count=_i(d.get("count")) or 0,
            raw=dict(d),
        )


# --------------------------------------------------------------------------
# 7.16  Sessions
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Session:
    status: str
    closes_in: Optional[str] = None
    opens_in: Optional[str] = None
    weekend: Optional[bool] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Session":
        return cls(
            status=str(d.get("status", "")),
            closes_in=d.get("closes_in"),
            opens_in=d.get("opens_in"),
            weekend=d.get("weekend"),
            raw=dict(d),
        )


@dataclass(frozen=True)
class Sessions:
    """Market session clock (``GET /sessions``)."""

    current_time: Optional[str]
    active_sessions: List[str]
    sessions: Dict[str, Session]
    overlaps: List[str]
    next_major_event: Optional[Dict[str, Any]] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Sessions":
        sess_raw = d.get("sessions") or {}
        return cls(
            current_time=d.get("current_time"),
            active_sessions=list(d.get("active_sessions") or []),
            sessions={k: Session.from_dict(v) for k, v in sess_raw.items()},
            overlaps=list(d.get("overlaps") or []),
            next_major_event=(
                dict(d["next_major_event"])
                if isinstance(d.get("next_major_event"), dict)
                else None
            ),
            raw=dict(d),
        )


# --------------------------------------------------------------------------
# 7.17  Heatmap
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Heatmap:
    """Currency strength / correlation heatmap (``GET /heatmap``).

    Strength mode populates ``currencies``/``strongest``/``weakest``/``range``;
    correlation mode populates ``correlation_matrix``/``available``/``message``.
    """

    type: str
    timeframe: str
    timestamp: Optional[str] = None
    # strength mode
    currencies: Optional[Dict[str, Any]] = None
    strongest: Optional[str] = None
    weakest: Optional[str] = None
    range: Optional[float] = None
    # correlation mode
    correlation_matrix: Optional[Dict[str, Dict[str, float]]] = None
    available: Optional[bool] = None
    message: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Heatmap":
        matrix_raw = d.get("correlation_matrix")
        matrix: Optional[Dict[str, Dict[str, float]]] = None
        if isinstance(matrix_raw, dict):
            matrix = {
                k: {kk: float(vv) for kk, vv in (v or {}).items()}
                for k, v in matrix_raw.items()
            }
        return cls(
            type=str(d.get("type", "")),
            timeframe=str(d.get("timeframe", "")),
            timestamp=d.get("timestamp"),
            currencies=(
                dict(d["currencies"]) if isinstance(d.get("currencies"), dict) else None
            ),
            strongest=d.get("strongest"),
            weakest=d.get("weakest"),
            range=_f(d.get("range")),
            correlation_matrix=matrix,
            available=d.get("available"),
            message=d.get("message"),
            raw=dict(d),
        )


# --------------------------------------------------------------------------
# 7.18  Calendar
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class CalendarEvent:
    id: str
    datetime: str
    currency: str
    event: str
    impact: str
    forecast: Optional[str] = None
    previous: Optional[str] = None
    actual: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CalendarEvent":
        return cls(
            id=str(d.get("id", "")),
            datetime=str(d.get("datetime", "")),
            currency=str(d.get("currency", "")),
            event=str(d.get("event", "")),
            impact=str(d.get("impact", "")),
            forecast=d.get("forecast"),
            previous=d.get("previous"),
            actual=d.get("actual"),
            raw=dict(d),
        )


@dataclass(frozen=True)
class Calendar:
    """Economic calendar (``GET /calendar``)."""

    events: List[CalendarEvent]
    count: int
    pagination: Pagination
    range: Dict[str, Any] = field(default_factory=dict)
    raw: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Calendar":
        return cls(
            events=[CalendarEvent.from_dict(e) for e in d.get("events", []) or []],
            count=_i(d.get("count")) or 0,
            pagination=Pagination.from_dict(d.get("pagination")),
            range=dict(d.get("range") or {}),
            raw=dict(d),
        )


# --------------------------------------------------------------------------
# 7.19 / 7.20 / 7.21  Monitor
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Account:
    """Account identity & quota (``GET /monitor/account``)."""

    name: Optional[str]
    plan: Optional[str]
    prepaid_credits: Optional[float]
    daily_quota: Optional[int]
    daily_used: Optional[int]
    raw: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Account":
        return cls(
            name=d.get("name"),
            plan=d.get("plan"),
            prepaid_credits=_f(d.get("prepaid_credits")),
            daily_quota=_i(d.get("daily_quota")),
            daily_used=_i(d.get("daily_used")),
            raw=dict(d),
        )


@dataclass(frozen=True)
class Layout:
    """Saved dashboard layout (``GET /monitor/layout``)."""

    layout: Optional[List[Any]]
    raw: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Layout":
        lay = d.get("layout")
        return cls(
            layout=list(lay) if isinstance(lay, list) else None,
            raw=dict(d),
        )


@dataclass(frozen=True)
class LayoutSaveResult:
    """Result of saving a layout (``PUT /monitor/layout``)."""

    saved: bool
    raw: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "LayoutSaveResult":
        return cls(saved=bool(d.get("saved", False)), raw=dict(d))


# --------------------------------------------------------------------------
# Infra probe
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Health:
    """Health probe (``GET /health``)."""

    status: Optional[str]
    components: Dict[str, Any] = field(default_factory=dict)
    raw: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Health":
        return cls(
            status=d.get("status"),
            components=dict(d.get("components") or {}),
            raw=dict(d),
        )
