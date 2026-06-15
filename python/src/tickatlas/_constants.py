"""Enums and constants for the TickAtlas API (SPEC section 6).

All values are the exact, case-sensitive identifiers accepted by the API. The
client methods accept either these constants (for editor autocompletion) or
raw strings.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, FrozenSet, Tuple

__all__ = [
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
    "INDICATORS",
    "INDICATORS_BY_CATEGORY",
    "TIMEFRAMES",
    "HEATMAP_TIMEFRAMES",
    "CATEGORIES",
    "SPREAD_PERIODS",
    "IMPACTS",
]


class _StrEnum(str, Enum):
    """A string enum whose members compare/serialize as their string value.

    Subclassing ``str`` means an instance can be passed anywhere a plain string
    is expected (e.g. into ``httpx`` query params) and ``str(member)`` /
    ``f"{member}"`` yield the bare value rather than ``"Timeframe.H1"``.
    """

    def __str__(self) -> str:  # noqa: D105
        return str(self.value)


class Timeframe(_StrEnum):
    """Timeframes for indicator/indicators/summary/ohlc/multi/history/screener.

    Default ``H1``.
    """

    M1 = "M1"
    M5 = "M5"
    M15 = "M15"
    M30 = "M30"
    H1 = "H1"
    H4 = "H4"
    D1 = "D1"


class HeatmapTimeframe(_StrEnum):
    """Timeframes accepted by the heatmap endpoint (default ``H4``)."""

    H1 = "H1"
    H4 = "H4"
    D1 = "D1"
    W1 = "W1"


class Category(_StrEnum):
    """Symbol categories."""

    FOREX = "forex"
    METALS = "metals"
    COMMODITIES = "commodities"
    INDICES = "indices"
    CRYPTO = "crypto"
    STOCKS = "stocks"


class SpreadPeriod(_StrEnum):
    """Spread statistics periods (default ``24h``)."""

    H1 = "1h"
    H24 = "24h"
    D7 = "7d"
    D30 = "30d"


class Impact(_StrEnum):
    """Economic calendar impact levels."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class HeatmapType(_StrEnum):
    """Heatmap modes (default ``strength``)."""

    STRENGTH = "strength"
    CORRELATION = "correlation"


class Bias(_StrEnum):
    """Market-bias values returned by ``/summary``."""

    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class BiasStrength(_StrEnum):
    """Bias strength returned by ``/summary``."""

    NORMAL = "normal"
    STRONG = "strong"


class Plan(_StrEnum):
    """Account plans returned by ``/monitor/account``."""

    FREE = "free"
    TRIAL = "trial"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"
    PAYG = "payg"


class Indicators:
    """Namespace of the 42 case-sensitive indicator identifiers (SPEC section 6).

    Use these constants for editor autocompletion, e.g.::

        client.get_indicator("EURUSD", Indicators.RSI_14)

    Raw strings (``"RSI_14"``) are equally accepted by every method.
    """

    # --- Trend (23) ---
    SMA_10 = "SMA_10"
    SMA_20 = "SMA_20"
    SMA_50 = "SMA_50"
    SMA_100 = "SMA_100"
    SMA_200 = "SMA_200"
    EMA_10 = "EMA_10"
    EMA_20 = "EMA_20"
    EMA_50 = "EMA_50"
    MACD_main = "MACD_main"
    MACD_signal = "MACD_signal"
    MACD_hist = "MACD_hist"
    ADX = "ADX"
    ADX_plusDI = "ADX_plusDI"
    ADX_minusDI = "ADX_minusDI"
    Ichimoku_tenkan = "Ichimoku_tenkan"
    Ichimoku_kijun = "Ichimoku_kijun"
    Ichimoku_senkou_a = "Ichimoku_senkou_a"
    Alligator_jaw = "Alligator_jaw"
    Alligator_teeth = "Alligator_teeth"
    Alligator_lips = "Alligator_lips"
    SAR = "SAR"
    TEMA_20 = "TEMA_20"
    DEMA_20 = "DEMA_20"

    # --- Oscillator (8) ---
    RSI_14 = "RSI_14"
    Stochastic_K = "Stochastic_K"
    Stochastic_D = "Stochastic_D"
    CCI_14 = "CCI_14"
    CCI_20 = "CCI_20"
    WilliamsR_14 = "WilliamsR_14"
    Momentum_14 = "Momentum_14"
    DeMarker_14 = "DeMarker_14"

    # --- Volatility (7) ---
    BB_upper = "BB_upper"
    BB_middle = "BB_middle"
    BB_lower = "BB_lower"
    BB_width = "BB_width"
    ATR_14 = "ATR_14"
    ATR_7 = "ATR_7"
    StdDev_20 = "StdDev_20"

    # --- Volume (4) ---
    OBV = "OBV"
    MFI_14 = "MFI_14"
    AD = "AD"
    Volumes = "Volumes"


INDICATORS_BY_CATEGORY: Dict[str, Tuple[str, ...]] = {
    "trend": (
        "SMA_10", "SMA_20", "SMA_50", "SMA_100", "SMA_200",
        "EMA_10", "EMA_20", "EMA_50",
        "MACD_main", "MACD_signal", "MACD_hist",
        "ADX", "ADX_plusDI", "ADX_minusDI",
        "Ichimoku_tenkan", "Ichimoku_kijun", "Ichimoku_senkou_a",
        "Alligator_jaw", "Alligator_teeth", "Alligator_lips",
        "SAR", "TEMA_20", "DEMA_20",
    ),
    "oscillator": (
        "RSI_14", "Stochastic_K", "Stochastic_D",
        "CCI_14", "CCI_20", "WilliamsR_14", "Momentum_14", "DeMarker_14",
    ),
    "volatility": (
        "BB_upper", "BB_middle", "BB_lower", "BB_width",
        "ATR_14", "ATR_7", "StdDev_20",
    ),
    "volume": ("OBV", "MFI_14", "AD", "Volumes"),
}

#: The full, ordered tuple of all 42 indicator identifiers.
INDICATORS: Tuple[str, ...] = tuple(
    name for names in INDICATORS_BY_CATEGORY.values() for name in names
)

#: Valid timeframes for most endpoints (frozen set of strings).
TIMEFRAMES: FrozenSet[str] = frozenset(tf.value for tf in Timeframe)

#: Valid timeframes for the heatmap endpoint.
HEATMAP_TIMEFRAMES: FrozenSet[str] = frozenset(tf.value for tf in HeatmapTimeframe)

#: Valid symbol categories.
CATEGORIES: FrozenSet[str] = frozenset(c.value for c in Category)

#: Valid spread periods.
SPREAD_PERIODS: FrozenSet[str] = frozenset(p.value for p in SpreadPeriod)

#: Valid calendar impact levels.
IMPACTS: FrozenSet[str] = frozenset(i.value for i in Impact)


# Sanity check kept cheap: the catalogue must have exactly 42 entries.
assert len(INDICATORS) == 42, f"expected 42 indicators, got {len(INDICATORS)}"
