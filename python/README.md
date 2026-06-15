# TickAtlas Python SDK

[![PyPI](https://img.shields.io/pypi/v/tickatlas.svg)](https://pypi.org/project/tickatlas/)
[![Python](https://img.shields.io/pypi/pyversions/tickatlas.svg)](https://pypi.org/project/tickatlas/)

Official Python SDK for the [TickAtlas](https://tickatlas.com) market-data API —
real-time quotes, OHLC candles, ticks, 42 technical indicators, currency
strength/correlation heatmaps, spread analytics, market sessions, and an
economic calendar across forex, metals, commodities, indices, crypto, and stocks.

- Sync **and** async clients with an identical surface.
- Fully typed (ships `py.typed`), single runtime dependency (`httpx`).
- Typed exceptions, automatic retries with backoff + jitter, and forward-compatible
  response models.

> **Scope:** This is the REST SDK. The TickAtlas WebSocket quote stream is **out
> of scope for `0.1.0`** and is planned for a future release.

---

## Installation

```bash
pip install tickatlas
```

Requires Python 3.9+.

## Authentication

Authenticate with your API key (the `X-API-Key` header is set for you). The key is
resolved in this order:

1. the explicit `api_key=` constructor argument, then
2. the `TICKATLAS_API_KEY` environment variable.

If neither is present, the client raises `TickAtlasConfigError`.

```python
from tickatlas import TickAtlas

# Explicit:
client = TickAtlas(api_key="claw_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")

# Or from the environment (recommended — never hardcode keys):
#   export TICKATLAS_API_KEY="claw_..."
client = TickAtlas()
```

The SDK **never** logs, prints, or serializes your key.

### Base URL

The base URL defaults to `https://tickatlas.com/v1` and can be overridden for
self-hosted/staging deployments via the `base_url=` argument or the
`TICKATLAS_BASE_URL` environment variable.

### Client options

| Option         | Default | Meaning |
|----------------|---------|---------|
| `api_key`      | env     | Your API key. |
| `base_url`     | prod    | API base URL. |
| `timeout`      | `30`    | Per-request timeout (seconds). |
| `max_retries`  | `3`     | Retries for 429/5xx/network errors (4 attempts total). |
| `backoff_base` | `0.5`   | Base for exponential backoff (seconds). |
| `jitter`       | `True`  | Apply full jitter to backoff (set `False` for deterministic delays). |
| `http_client`  | `None`  | Bring your own `httpx.Client` / `httpx.AsyncClient`. |

## Quickstart

```python
from tickatlas import TickAtlas

with TickAtlas() as client:
    quote = client.get_quote("EURUSD")
    print(quote.symbol, quote.bid, quote.ask, quote.spread_pips)

    candles = client.get_ohlc("EURUSD", timeframe="H1", limit=10)
    for c in candles.candles:
        print(c.time, c.open, c.high, c.low, c.close, c.volume)
```

Every response is a typed, frozen dataclass. The original JSON payload is always
available on `.raw` so you can read fields added by the API after this SDK was
released.

## Enums and constants

Use the provided enums/namespaces for autocompletion, or pass raw strings — both
work everywhere.

```python
from tickatlas import TickAtlas, Timeframe, Indicators, Category

client = TickAtlas()
client.get_indicator("EURUSD", Indicators.RSI_14, timeframe=Timeframe.H4)
client.get_indicator("EURUSD", "RSI_14", timeframe="H4")  # equivalent
client.get_symbols(category=Category.FOREX)
```

- `Timeframe`: `M1 M5 M15 M30 H1 H4 D1` (default `H1`).
- `HeatmapTimeframe`: `H1 H4 D1 W1` (default `H4`).
- `Indicators`: all 42 case-sensitive identifiers (e.g. `SAR`, `Volumes`,
  `WilliamsR_14`, `ADX_plusDI`). `INDICATORS` is the full tuple and
  `INDICATORS_BY_CATEGORY` groups them by `trend`/`oscillator`/`volatility`/`volume`.
- `Category`, `SpreadPeriod`, `Impact`, `HeatmapType`, `Bias`, `BiasStrength`, `Plan`.

## Endpoint reference

All 21 `/v1` endpoints plus the `/health` probe are available as snake_case
methods. `start`/`end` map to the API's `from`/`to` query params.

### Symbols

```python
symbols = client.get_symbols(category="forex", search="EUR", offset=0, limit=100)
print(symbols.total, symbols.pagination.has_more)
for s in symbols.symbols:
    print(s.symbol, s.category, s.digits, s.tradable)

spec = client.get_symbol("EURUSD")
print(spec.contract_size, spec.min_volume, spec.trading_hours)
```

### Quotes

```python
quote = client.get_quote("EURUSD", include_sources=True)
print(quote.bid, quote.ask, quote.spread_pips)
if quote.sources:
    for src in quote.sources:
        print(src.broker, src.bid, src.ask)

# Batch (POST). `fields` is a subset of bid/ask/spread/spread_pips/timestamp.
bulk = client.get_quotes(["EURUSD", "GBPUSD", "USDJPY"], fields=["bid", "ask"])
print(bulk.count, bulk.not_found)
for q in bulk.quotes:
    print(q.symbol, q.bid, q.ask)
```

### OHLC and ticks

```python
ohlc = client.get_ohlc(
    "EURUSD", timeframe="H1",
    start="2026-05-01T00:00:00Z", end="2026-05-02T00:00:00Z", limit=500,
)
print(ohlc.count, ohlc.retention)

# Ticks require a pro/enterprise plan and a window <= 1 hour.
ticks = client.get_ticks(
    "EURUSD", start="2026-05-01T00:00:00Z", end="2026-05-01T00:30:00Z",
)
print(ticks.count)
```

### Indicators

```python
ind = client.get_indicator("EURUSD", "RSI_14", timeframe="H1")
print(ind.value, ind.updated_at)

all_ind = client.get_indicators("EURUSD", timeframe="H1", category="oscillator")
print(all_ind.indicators["RSI_14"])

catalogue = client.list_indicators()
print(catalogue.categories, catalogue.timeframes)

# Indicator history (starter+).
hist = client.get_indicator_history(
    "EURUSD", "RSI_14", timeframe="H1",
    start="2026-05-01T00:00:00Z", end="2026-05-02T00:00:00Z", limit=500,
)
for point in hist.series:
    print(point.time, point.value)

# Batch indicators across symbols (premium; historical mode is starter+).
multi = client.get_multi(["EURUSD", "GBPUSD"], ["RSI_14", "MACD_hist"], timeframe="H4")
print(multi.is_historical, multi.data["EURUSD"]["RSI_14"])

# Screener (premium). NOTE: bounds are min_val / max_val, default sort is "asc".
screen = client.screen("RSI_14", timeframe="H1", min_val=70, sort="desc", limit=50)
for r in screen.results:
    print(r.symbol, r.value)

# Market-bias summary.
summary = client.get_summary("EURUSD", timeframe="H4")
print(summary.bias, summary.bias_strength, summary.confidence)
```

### Spread

```python
spread = client.get_spread("EURUSD", period="24h")
print(spread.current, spread.statistics.avg_spread, spread.by_session)

cmp = client.compare_spread(["EURUSD", "GBPUSD", "USDJPY"], period="7d")
for item in cmp.symbols:  # sorted by avg_pips ascending
    print(item.symbol, item.avg_pips, item.has_live_data)
```

### Sessions, heatmap, calendar

```python
sessions = client.get_sessions()
print(sessions.active_sessions, sessions.overlaps)

strength = client.get_heatmap(type="strength", timeframe="H4")
print(strength.strongest, strength.weakest)

corr = client.get_heatmap(type="correlation", timeframe="D1")
print(corr.available, corr.correlation_matrix)

calendar = client.get_calendar(
    start="2026-06-01", end="2026-06-07",
    currencies="USD,EUR", impact="high", limit=100,
)
for ev in calendar.events:
    print(ev.datetime, ev.currency, ev.event, ev.impact)
```

> Calendar `datetime` values are naive UTC (no `Z` suffix); treat them as UTC.

### Account and dashboard layout

```python
account = client.get_account()
print(account.name, account.plan, account.daily_used, account.daily_quota)

layout = client.get_layout()
print(layout.layout)
```

#### `save_layout` (advanced / write)

`save_layout` is the **only write method** in the SDK. It overwrites the
server-side dashboard layout stored against your API key (max 60 widgets). Use it
deliberately.

```python
result = client.save_layout([{"widget": "quote", "symbol": "EURUSD"}])
print(result.saved)  # True
```

### Health probe

```python
print(client.health().status)
```

## Error handling

All errors derive from `TickAtlasError`. Server-returned errors are
`TickAtlasAPIError` subclasses carrying `.status_code`, `.code`, `.message`,
`.details`, `.request_id`, and the raw error object as `.raw` (so you can read
context fields like `valid_timeframes` or `current_plan`).

```python
from tickatlas import (
    TickAtlas,
    TickAtlasError,
    AuthenticationError,
    PermissionDeniedError,
    NotFoundError,
    ValidationError,
    RateLimitError,
    ServerError,
    TickAtlasNetworkError,
)

client = TickAtlas()
try:
    client.get_quote("NOPE")
except NotFoundError as e:
    print(e.status_code, e.code, e.message)   # 404 SYMBOL_NOT_FOUND ...
    print(e.raw.get("available_symbols"))
except RateLimitError as e:
    print("retry after", e.retry_after, "seconds")
except ValidationError as e:
    print(e.details)                          # 422 VALIDATION_ERROR detail list
except AuthenticationError:
    ...   # 401 MISSING_API_KEY / INVALID_API_KEY
except PermissionDeniedError:
    ...   # 403 plan gate / disabled key / IP block
except ServerError:
    ...   # 5xx
except TickAtlasNetworkError as e:
    print("transport failure:", e.cause)
except TickAtlasError:
    ...   # catch-all
```

Mapping (HTTP status -> exception): `401 -> AuthenticationError`,
`403 -> PermissionDeniedError`, `404 -> NotFoundError`,
`400/422 -> ValidationError`, `429 -> RateLimitError`, `5xx -> ServerError`.
Network/timeout/DNS failures (no HTTP response) raise `TickAtlasNetworkError`.

## Rate limiting & retries

Every `/v1` response carries `X-RateLimit-Limit`, `X-RateLimit-Remaining`,
`X-RateLimit-Reset`, and `X-Request-ID`. The client automatically retries on:

- HTTP `429` (rate limit / quota),
- HTTP `5xx`,
- network/timeout errors.

Retries use exponential backoff with full jitter
(`delay = min(30, backoff_base * 2**attempt) * random()`), capped at 30s. On
`429`, the client honours the `Retry-After` header (falling back to
`X-RateLimit-Reset`) instead of the computed backoff. All endpoints are read-only
except `save_layout`, so retries are safe.

Tune via `max_retries`, `backoff_base`, and `timeout`. Set `jitter=False` (and
optionally inject `rng=`) for deterministic delays in tests.

```python
client = TickAtlas(max_retries=5, backoff_base=0.25, timeout=10)
```

## Async usage

`AsyncTickAtlas` mirrors `TickAtlas` exactly; every method is a coroutine.

```python
import asyncio
from tickatlas import AsyncTickAtlas

async def main():
    async with AsyncTickAtlas() as client:
        quote, summary = await asyncio.gather(
            client.get_quote("EURUSD"),
            client.get_summary("EURUSD", timeframe="H4"),
        )
        print(quote.bid, summary.bias)

asyncio.run(main())
```

## Bring your own httpx client

```python
import httpx
from tickatlas import TickAtlas

http = httpx.Client(proxies="http://localhost:8080", verify=False)
client = TickAtlas(http_client=http)  # the SDK will not close a client you pass in
```

## Contributing / development

```bash
git clone https://github.com/tickatlas/tickatlas-sdk
cd tickatlas-sdk/python

python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

pytest          # unit tests (no network)
mypy            # type-check (strict)
```

### Integration tests

`tests/test_integration.py` hits the **real** API and is skipped unless both
`RUN_INTEGRATION=1` and `TICKATLAS_API_KEY` are set. It is read-only and never
calls write endpoints.

```bash
RUN_INTEGRATION=1 TICKATLAS_API_KEY="claw_..." pytest tests/test_integration.py
```

## License

MIT — see [LICENSE](../LICENSE).
