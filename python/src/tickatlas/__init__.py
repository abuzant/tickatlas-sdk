"""Official Python SDK for the TickAtlas market-data API.

Quickstart
----------
>>> from tickatlas import TickAtlas
>>> client = TickAtlas(api_key="tk_...")   # or set TICKATLAS_API_KEY
>>> quote = client.get_quote("EURUSD")
>>> print(quote.bid, quote.ask)

See https://tickatlas.com for full documentation.
"""

from __future__ import annotations

from ._client import AsyncTickAtlas, TickAtlas
from ._constants import (
    INDICATORS,
    INDICATORS_BY_CATEGORY,
    Bias,
    BiasStrength,
    Category,
    HeatmapTimeframe,
    HeatmapType,
    Impact,
    Indicators as IndicatorCatalog,
    Plan,
    SpreadPeriod,
    Timeframe,
)
from ._constants import Indicators  # noqa: F401  (autocompletion namespace)
from ._exceptions import (
    AuthenticationError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    ServerError,
    TickAtlasAPIError,
    TickAtlasConfigError,
    TickAtlasError,
    TickAtlasNetworkError,
    ValidationError,
)
from ._version import __version__

# Typed response models (re-exported for type hints / isinstance checks).
from ._models import (  # noqa: E402
    Account,
    BulkQuoteItem,
    BulkQuotes,
    Calendar,
    CalendarEvent,
    Candle,
    Health,
    Heatmap,
    Indicator,
    IndicatorCatalogue,
    IndicatorHistory,
    IndicatorHistoryPoint,
    Layout,
    LayoutSaveResult,
    MultiIndicators,
    OHLC,
    Pagination,
    Quote,
    QuoteSource,
    Screener,
    ScreenerResult,
    Session,
    Sessions,
    Spread,
    SpreadCompare,
    SpreadCompareItem,
    SpreadStatistics,
    Summary,
    SymbolList,
    SymbolListItem,
    SymbolSpec,
    Tick,
    Ticks,
)
from ._models import Indicators as IndicatorsModel  # noqa: F401,E402

__all__ = [
    "__version__",
    # clients
    "TickAtlas",
    "AsyncTickAtlas",
    # enums / constants
    "Timeframe",
    "HeatmapTimeframe",
    "Category",
    "SpreadPeriod",
    "Impact",
    "HeatmapType",
    "Bias",
    "BiasStrength",
    "Plan",
    "Indicators",
    "IndicatorCatalog",
    "INDICATORS",
    "INDICATORS_BY_CATEGORY",
    # exceptions
    "TickAtlasError",
    "TickAtlasConfigError",
    "TickAtlasNetworkError",
    "TickAtlasAPIError",
    "AuthenticationError",
    "PermissionDeniedError",
    "NotFoundError",
    "ValidationError",
    "RateLimitError",
    "ServerError",
    # models
    "Account",
    "BulkQuoteItem",
    "BulkQuotes",
    "Calendar",
    "CalendarEvent",
    "Candle",
    "Health",
    "Heatmap",
    "Indicator",
    "IndicatorCatalogue",
    "IndicatorHistory",
    "IndicatorHistoryPoint",
    "IndicatorsModel",
    "Layout",
    "LayoutSaveResult",
    "MultiIndicators",
    "OHLC",
    "Pagination",
    "Quote",
    "QuoteSource",
    "Screener",
    "ScreenerResult",
    "Session",
    "Sessions",
    "Spread",
    "SpreadCompare",
    "SpreadCompareItem",
    "SpreadStatistics",
    "Summary",
    "SymbolList",
    "SymbolListItem",
    "SymbolSpec",
    "Tick",
    "Ticks",
]
