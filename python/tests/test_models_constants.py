"""Model parsing edge cases and the constants/enum catalogue (SPEC section 6)."""

from __future__ import annotations

import tickatlas
from tickatlas import (
    INDICATORS,
    INDICATORS_BY_CATEGORY,
    Category,
    HeatmapTimeframe,
    Indicators,
    SpreadPeriod,
    Timeframe,
)
from tickatlas import _models as m


# --------------------------------------------------------------------------
# Indicator catalogue (must be exactly the 42 case-sensitive names).
# --------------------------------------------------------------------------
def test_indicator_count_is_42():
    assert len(INDICATORS) == 42
    assert len(set(INDICATORS)) == 42


def test_indicator_category_totals():
    assert len(INDICATORS_BY_CATEGORY["trend"]) == 23
    assert len(INDICATORS_BY_CATEGORY["oscillator"]) == 8
    assert len(INDICATORS_BY_CATEGORY["volatility"]) == 7
    assert len(INDICATORS_BY_CATEGORY["volume"]) == 4


def test_indicator_naming_gotchas():
    # SPEC section 6 "naming gotchas" — these exact spellings, not the doc typos.
    assert Indicators.SAR == "SAR"
    assert Indicators.Volumes == "Volumes"
    assert Indicators.WilliamsR_14 == "WilliamsR_14"
    assert Indicators.ADX_plusDI == "ADX_plusDI"
    assert Indicators.ADX_minusDI == "ADX_minusDI"
    # Things that must NOT exist:
    assert not hasattr(Indicators, "Parabolic_SAR")
    assert not hasattr(Indicators, "Tick_Volume")
    assert not hasattr(Indicators, "RSI_9")
    assert not hasattr(Indicators, "EMA_200")
    assert "EMA_200" not in INDICATORS
    assert "RSI_9" not in INDICATORS
    # EMA stops at 50, SMA goes to 200.
    assert "EMA_50" in INDICATORS and "EMA_200" not in INDICATORS
    assert "SMA_200" in INDICATORS
    # Only three Ichimoku keys.
    ichimoku = [i for i in INDICATORS if i.startswith("Ichimoku")]
    assert sorted(ichimoku) == [
        "Ichimoku_kijun",
        "Ichimoku_senkou_a",
        "Ichimoku_tenkan",
    ]


def test_timeframe_enum():
    assert [t.value for t in Timeframe] == ["M1", "M5", "M15", "M30", "H1", "H4", "D1"]
    assert str(Timeframe.H4) == "H4"
    # Subclasses str so it can be used directly as a string.
    assert Timeframe.H1 == "H1"


def test_heatmap_timeframe_has_w1_no_m15():
    values = {t.value for t in HeatmapTimeframe}
    assert values == {"H1", "H4", "D1", "W1"}
    assert "M15" not in values


def test_spread_period_and_category_values():
    assert {p.value for p in SpreadPeriod} == {"1h", "24h", "7d", "30d"}
    assert {c.value for c in Category} == {
        "forex", "metals", "commodities", "indices", "crypto", "stocks",
    }
    assert str(SpreadPeriod.H24) == "24h"


# --------------------------------------------------------------------------
# Models: frozen, forward-compatible, tolerant of unknown fields.
# --------------------------------------------------------------------------
def test_models_are_frozen():
    q = m.Quote.from_dict({"symbol": "EURUSD", "bid": 1.0, "ask": 1.1})
    try:
        q.bid = 2.0  # type: ignore[misc]
    except Exception as exc:  # FrozenInstanceError
        assert "frozen" in str(exc).lower() or exc.__class__.__name__ == "FrozenInstanceError"
    else:
        raise AssertionError("expected frozen dataclass to reject mutation")


def test_unknown_fields_are_tolerated_and_kept_in_raw():
    payload = {
        "symbol": "EURUSD",
        "bid": 1.16,
        "ask": 1.17,
        "spread": 1,
        "spread_pips": 0.1,
        "timestamp": "2026-01-01T00:00:00Z",
        "brand_new_field": {"nested": 123},  # field added by a future API version
    }
    q = m.Quote.from_dict(payload)
    assert q.bid == 1.16
    # Unknown field is preserved on .raw for forward-compatibility.
    assert q.raw["brand_new_field"] == {"nested": 123}


def test_null_numbers_become_none():
    ind = m.Indicator.from_dict(
        {"symbol": "X", "timeframe": "H1", "indicator": "RSI_14", "value": None,
         "bid": None, "ask": None, "updated_at": None}
    )
    assert ind.value is None
    assert ind.bid is None
    assert ind.updated_at is None


def test_volume_coerced_to_int():
    c = m.Candle.from_dict(
        {"time": "t", "open": 1, "high": 2, "low": 0, "close": 1, "volume": 1523.0}
    )
    assert c.volume == 1523
    assert isinstance(c.volume, int)


def test_heatmap_correlation_matrix_null_cell_becomes_none():
    # A null correlation cell must coerce to None, not raise TypeError (FIX 1).
    hm = m.Heatmap.from_dict(
        {
            "type": "correlation",
            "timeframe": "H4",
            "correlation_matrix": {
                "USD": {"USD": 1.0, "EUR": None},
                "EUR": {"USD": None, "EUR": 1.0},
            },
            "available": True,
        }
    )
    assert hm.correlation_matrix is not None
    assert hm.correlation_matrix["USD"]["USD"] == 1.0
    assert hm.correlation_matrix["USD"]["EUR"] is None
    assert hm.correlation_matrix["EUR"]["USD"] is None


def test_multi_is_historical_property():
    rt = m.MultiIndicators.from_dict({"timeframe": "H1", "data": {}, "not_found": None})
    assert rt.is_historical is False
    hist = m.MultiIndicators.from_dict(
        {"timeframe": "H1", "mode": "historical", "data": {}, "not_found": None}
    )
    assert hist.is_historical is True


def test_public_exports_present():
    # Spot-check that the public namespace exposes clients, enums, models, errors.
    for name in [
        "TickAtlas", "AsyncTickAtlas", "Timeframe", "Indicators", "Quote",
        "OHLC", "Screener", "RateLimitError", "NotFoundError", "TickAtlasError",
        "__version__",
    ]:
        assert hasattr(tickatlas, name), name
