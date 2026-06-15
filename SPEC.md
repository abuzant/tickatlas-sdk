# TickAtlas API — Client SDK Contract

> **This is the authoritative contract every TickAtlas SDK in this repo is built
> against.** It was produced by reading the live API reference docs **and** the
> running server's source code, then cross-checking against a full live endpoint
> test (90/90 cases) performed on the production stack. Where the published docs
> and the implementation disagreed, the **implementation/live behaviour wins** and
> the disagreement is recorded in [§12 Findings](#12-findings--published-docs-vs-live-api).

| | |
|---|---|
| **Built against** | TickAtlas API `v1`, app version `1.0.0` |
| **Contract date** | 2026-06-15 |
| **Base URL** | `https://tickatlas.com/v1` |
| **Auth** | `X-API-Key: <key>` request header |
| **Transport** | HTTPS only, JSON request/response |
| **Public endpoints** | 21 (the `/v1` API-key surface) + 3 infra probes |

---

## 1. Base URL & versioning

All API endpoints live under the versioned prefix:

```
https://tickatlas.com/v1
```

Every path in this document is relative to that base (e.g. `GET /quote` means
`GET https://tickatlas.com/v1/quote`). The base URL must be configurable in each
SDK (constructor option / env var `TICKATLAS_BASE_URL`) to support self-hosted or
staging deployments, defaulting to the production URL above.

---

## 2. Authentication

Authenticate **every** request with an API key in the `X-API-Key` header:

```
X-API-Key: tk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

- Keys are opaque strings. New keys are prefixed `tk_`; pre-rebrand `claw_` keys
  remain valid (legacy) and are also accepted. SDKs MUST treat the key as an opaque string — never parse
  or validate its format client-side.
- The key is read, in priority order, from: (1) an explicit constructor argument,
  then (2) the environment variable **`TICKATLAS_API_KEY`**.
- **Never** hardcode, log, or serialize the key. Redact it from any debug output.

Auth failures:

| HTTP | `error.code` | Meaning |
|------|--------------|---------|
| 401 | `MISSING_API_KEY` | No `X-API-Key` header sent |
| 401 | `INVALID_API_KEY` | Key not recognised |
| 403 | `API_KEY_DISABLED` | Key was revoked/disabled |
| 403 | `API_KEY_EXPIRED` | Key past its `expires_at` |
| 403 | `IP_NOT_ALLOWED` | Caller IP not in the key's IP whitelist |
| 403 | `ACCOUNT_INACTIVE` / `ACCOUNT_SUSPENDED` / `ACCOUNT_EXPIRED` | Account-level block |

---

## 3. Response envelope

### Success

Every successful (`2xx`) response is:

```json
{ "success": true, "data": <object or array> }
```

SDKs should unwrap `data` and return strongly-typed models from it. The `success`
flag is always `true` on 2xx.

### Error

Every non-2xx response — including framework-level `404` (no route), `405` (bad
method), and `422` (validation) — is normalised by global handlers into:

```json
{ "success": false, "error": { "code": "STRING_CODE", "message": "Human readable", "...": "extra fields" } }
```

- `error.code` — stable, machine-branchable string (see [§4](#4-error-codes)).
- `error.message` — human-readable description.
- Additional context keys may appear alongside `code`/`message` depending on the
  error: e.g. `valid_timeframes`, `valid_periods`, `valid_types`, `valid_values`,
  `available_symbols`, `available_indicators`, `current_plan`, `required_plan`,
  `requested_range`, `max_range`, `max_window_hours`, `earliest_available`,
  `retention_period`, `details` (for `VALIDATION_ERROR`), and the rate-limit
  fields `limit` / `remaining` / `reset_in_seconds` / `upgrade`.

SDKs MUST tolerate unknown extra keys (forward-compatibility) and expose the raw
`error` object so callers can read context fields.

> Normalisation rules (from the server's global exception handlers):
> - Handler-raised errors with a structured detail pass through verbatim (their
>   specific `code`).
> - Handler-raised errors with a plain-string detail become
>   `{"code": "HTTP_<status>", "message": "<string>"}`.
> - FastAPI request validation → `{"code": "VALIDATION_ERROR", "message": "...",
>   "details": [ {type, loc, msg, ...}, ... ]}` with HTTP `422`.
> - Any unhandled exception → `{"code": "INTERNAL_ERROR"}` with HTTP `500`.

---

## 4. Error codes

Map HTTP status + `error.code` to typed SDK exceptions as follows. This hierarchy
must be mirrored (idiomatically) in all four SDKs.

```
TickAtlasError                     (base for everything)
├── TickAtlasAPIError              (the server returned a structured error)
│   │   .status_code .code .message .details .request_id .raw
│   ├── AuthenticationError        HTTP 401  (MISSING_API_KEY, INVALID_API_KEY)
│   ├── PermissionDeniedError      HTTP 403  (API_KEY_DISABLED, API_KEY_EXPIRED,
│   │                                         IP_NOT_ALLOWED, ACCOUNT_*,
│   │                                         PERMISSION_DENIED, PLAN_UPGRADE_REQUIRED)
│   ├── NotFoundError              HTTP 404  (SYMBOL_NOT_FOUND, DATA_NOT_FOUND,
│   │                                         INDICATOR_NOT_FOUND)
│   ├── ValidationError            HTTP 400 & 422 (all INVALID_*, RANGE_TOO_LARGE,
│   │                                         OUTSIDE_RETENTION, TOO_MANY_SYMBOLS,
│   │                                         NO_SYMBOLS, VALIDATION_ERROR, HTTP_400, …)
│   ├── RateLimitError             HTTP 429  (RATE_LIMIT_EXCEEDED, QUOTA_EXCEEDED,
│   │                                         RATE_LIMITED) — carries retry_after
│   └── ServerError                HTTP 5xx  (INTERNAL_ERROR, SERVICE_UNAVAILABLE)
└── TickAtlasNetworkError          no HTTP response (connection/timeout/DNS)
```

Complete observed `error.code` values by status:

| HTTP | Codes |
|------|-------|
| 400 | `INVALID_TIMEFRAME`, `INVALID_CATEGORY`, `INVALID_DATETIME`, `INVALID_TIME_RANGE`, `INVALID_RANGE`, `RANGE_TOO_LARGE`, `OUTSIDE_RETENTION`, `DATA_OUTSIDE_RETENTION`, `INVALID_REQUEST`, `TOO_MANY_SYMBOLS`, `NO_SYMBOLS`, `INVALID_SORT`, `INVALID_PERIOD`, `INVALID_SYMBOL`, `INVALID_TYPE`, `INVALID_DATE`, `INVALID_IMPACT`, `HTTP_400` |
| 401 | `MISSING_API_KEY`, `INVALID_API_KEY` |
| 403 | `API_KEY_DISABLED`, `API_KEY_EXPIRED`, `IP_NOT_ALLOWED`, `ACCOUNT_INACTIVE`, `ACCOUNT_SUSPENDED`, `ACCOUNT_EXPIRED`, `PERMISSION_DENIED`, `PLAN_UPGRADE_REQUIRED` |
| 404 | `SYMBOL_NOT_FOUND`, `DATA_NOT_FOUND`, `INDICATOR_NOT_FOUND`, `HTTP_404` |
| 405 | `HTTP_405` |
| 422 | `VALIDATION_ERROR` (with `details`) |
| 429 | `RATE_LIMIT_EXCEEDED`, `QUOTA_EXCEEDED`, `RATE_LIMITED` |
| 500 | `INTERNAL_ERROR` |
| 503 | `SERVICE_UNAVAILABLE`, `HTTP_503` |

---

## 5. Rate limiting, quota & retries

Every `/v1` response carries:

| Header | Meaning |
|--------|---------|
| `X-RateLimit-Limit` | Requests/minute allowed for this key's plan |
| `X-RateLimit-Remaining` | Remaining in the current window |
| `X-RateLimit-Reset` | Seconds until the window resets |
| `X-Request-ID` | 32-char correlation id (echo in support requests) |

On `429`, the response also includes a **`Retry-After`** header (seconds) and the
JSON carries `reset_in_seconds`. Quota exhaustion (`QUOTA_EXCEEDED`) uses
`Retry-After: 3600`.

**Required SDK retry policy** (configurable; sensible defaults):

- Retry on **`429`**, **`5xx`**, and **network/timeout** errors only.
- Default **max 3 retries** (4 total attempts).
- Exponential backoff with full jitter: `delay = min(cap, base * 2^attempt) * rand`
  with `base ≈ 0.5s`, `cap ≈ 30s`.
- On `429`, honour `Retry-After` (fallback `X-RateLimit-Reset`) **instead of** the
  computed backoff when present.
- All endpoints are read-only/idempotent (the only write is the deliberately
  out-of-scope `PUT /v1/monitor/layout`), so retries are always safe.
- Expose `max_retries`, `backoff_base`, `timeout` as client options.

Plan rate limits (informational; enforced server-side): trial/free are limited
(trial = 1,000 requests/day); paid tiers raise both per-minute and daily quotas
(Enterprise ≈ 6,000 req/min). SDKs should not assume specific numbers — read the
headers.

---

## 6. Common enums & constants

```
Timeframes (indicator/indicators/summary/ohlc/multi/history/screener):
    M1, M5, M15, M30, H1, H4, D1            (default: H1)
Timeframes (heatmap):
    H1, H4, D1, W1                          (default: H4)
Symbol categories:
    forex, metals, commodities, indices, crypto, stocks
Spread periods:
    1h, 24h, 7d, 30d                        (default: 24h)
Calendar impact:
    high, medium, low
Summary bias values:
    bullish, bearish, neutral
Summary bias_strength:
    normal, strong
Heatmap type:
    strength (default), correlation
Account plans:
    free, trial, starter, pro, enterprise, payg
```

### Indicator catalogue (42)

Exact, **case-sensitive** identifiers accepted by the API (source of truth:
`INDICATOR_COLUMN_MAP`). Use these verbatim for any enum/constant set.

**Trend (23):** `SMA_10` `SMA_20` `SMA_50` `SMA_100` `SMA_200` `EMA_10` `EMA_20`
`EMA_50` `MACD_main` `MACD_signal` `MACD_hist` `ADX` `ADX_plusDI` `ADX_minusDI`
`Ichimoku_tenkan` `Ichimoku_kijun` `Ichimoku_senkou_a` `Alligator_jaw`
`Alligator_teeth` `Alligator_lips` `SAR` `TEMA_20` `DEMA_20`

**Oscillator (8):** `RSI_14` `Stochastic_K` `Stochastic_D` `CCI_14` `CCI_20`
`WilliamsR_14` `Momentum_14` `DeMarker_14`

**Volatility (7):** `BB_upper` `BB_middle` `BB_lower` `BB_width` `ATR_14` `ATR_7`
`StdDev_20`

**Volume (4):** `OBV` `MFI_14` `AD` `Volumes`

> Naming gotchas (the docs occasionally use wrong names — these are 404s): it is
> `SAR` (not `Parabolic_SAR`), `Volumes` (not `Tick_Volume`), `WilliamsR_14` (no
> underscore before `R`), `ADX_plusDI`/`ADX_minusDI` (camel `DI`). `EMA` stops at
> `EMA_50`; `SMA` goes to `SMA_200`. No `RSI_9`, no `EMA_200`. Only three Ichimoku
> keys (no `senkou_b`/`chikou`).

---

## 7. Endpoint reference (the 21 `/v1` endpoints)

> **Permission scopes**: each endpoint declares the API-key *permission scope* it
> needs. A key with `{"all": true}` (the default for most accounts) satisfies every
> scope. Some endpoints additionally enforce a **plan gate** (noted inline). Scope
> failure → `403 PERMISSION_DENIED`; plan-gate failure → `403 PLAN_UPGRADE_REQUIRED`.
> All endpoints also surface the shared auth/rate/quota errors from §4.

### 7.1 `GET /symbols` — list symbols (paginated) · scope: none

| Param | Type | Req | Default | Notes |
|-------|------|-----|---------|-------|
| `category` | string | no | — | one of the categories in §6 (unknown → empty list, no error) |
| `search` | string | no | — | substring match on symbol or name |
| `offset` | int | no | `0` | `≥ 0` |
| `limit` | int | no | `100` | `1..500` |

`data`: `{ symbols: SymbolListItem[], total: int, pagination: Pagination }`
`SymbolListItem`: `{ symbol: str, name: str|null, category: str, base_currency: str|null, quote_currency: str|null, digits: int, tradable: bool }`
`Pagination`: `{ offset: int, limit: int, total: int, has_more: bool }`

```json
{"success":true,"data":{"symbols":[{"symbol":"EURUSD","name":null,"category":"forex","base_currency":"EUR","quote_currency":"USD","digits":5,"tradable":true}],"total":149,"pagination":{"offset":0,"limit":100,"total":149,"has_more":true}}}
```

### 7.2 `GET /symbols/{symbol}` — symbol contract spec · scope: none

Path param `symbol` (1–20 chars, `^[A-Z0-9.]+$`; bad → `400 INVALID_SYMBOL`,
unknown → `404 SYMBOL_NOT_FOUND`).

`data`: `{ symbol: str, name: str|null, category: str, description: str|null,
base_currency: str|null, quote_currency: str|null, digits: int, point: number,
contract_size: number, min_volume: number, max_volume: number, volume_step: number,
swap_long: number|null, swap_short: number|null, margin_currency: str|null,
trading_hours: { sunday..saturday: str } }`

### 7.3 `GET /quote` — single real-time quote · scope: `quotes`

| Param | Type | Req | Default | Notes |
|-------|------|-----|---------|-------|
| `symbol` | string | **yes** | — | trading symbol |
| `include_sources` | bool | no | `false` | include per-broker `sources[]` |
| `source` | string | no | — | force a broker source (debug) |

`data` (`QuoteData`): `{ symbol: str, bid: number|null, ask: number|null,
spread: number, spread_pips: number|null, timestamp: str(ISO8601), source?: str,
best_bid?: number|null, best_ask?: number|null, best_spread?: number|null,
source_count?: int, sources?: {broker,bid,ask,spread,updated}[] }`
Errors: `404 SYMBOL_NOT_FOUND`.

```json
{"success":true,"data":{"symbol":"EURUSD","bid":1.16404,"ask":1.16422,"spread":18,"spread_pips":1.8,"timestamp":"2026-05-25T13:56:15.819519+00:00","source":"Equiti Securities"}}
```

### 7.4 `POST /quotes` — batch quotes · scope: `quotes`

JSON body: `{ "symbols": string[]  (required, 1..100), "fields"?: string[] }`
`fields` ⊆ `["bid","ask","spread","spread_pips","timestamp"]` (default: all five).

`data` (`BulkQuotesData`): `{ quotes: BulkQuoteItem[], count: int,
not_found: string[]|null, timestamp: str }`
`BulkQuoteItem`: `{ symbol: str, bid?: number|null, ask?: number|null,
spread?: number|null, spread_pips?: number|null, timestamp?: str }` (only the
requested `fields` are present).
Errors: `400 INVALID_REQUEST` (empty), `400 TOO_MANY_SYMBOLS` (>100).
**Note:** this endpoint is **POST only**; `GET /quotes` → `405`.

### 7.5 `GET /ohlc` — OHLC candles · scope: `historical`

| Param | Type | Req | Default | Notes |
|-------|------|-----|---------|-------|
| `symbol` | string | **yes** | — | |
| `timeframe` | string | no | `H1` | §6 set |
| `from` | string | no | retention start | ISO 8601 |
| `to` | string | no | now | ISO 8601 |
| `limit` | int | no | `100` | `1..1000` |

`data` (`OHLCData`): `{ symbol: str, timeframe: str, candles: Candle[],
count: int, retention: str|null }`
`Candle`: `{ time: str(ISO8601 "…Z"), open: number, high: number, low: number,
close: number, volume: int }`
Errors: `400 INVALID_TIMEFRAME`, `400 INVALID_DATETIME`,
`400 DATA_OUTSIDE_RETENTION`, `404 SYMBOL_NOT_FOUND`. Empty-but-valid → `200`,
`candles: []`.

### 7.6 `GET /ticks` — tick data · scope: `historical` · **plan: pro/enterprise**

| Param | Type | Req | Default | Notes |
|-------|------|-----|---------|-------|
| `symbol` | string | **yes** | — | |
| `from` | string | **yes** | — | ISO 8601 |
| `to` | string | **yes** | — | ISO 8601; `to ≥ from`; `to − from ≤ 1 hour` |

`data` (`TicksData`): `{ symbol: str, ticks: Tick[], count: int }`
`Tick`: `{ time: str(ISO8601), bid: number, ask: number, flags: int }`
Errors: `403 PLAN_UPGRADE_REQUIRED`, `400 INVALID_RANGE` (inverted),
`400 RANGE_TOO_LARGE` (>1h), `400 INVALID_DATETIME`. No `limit` param (server caps
at 50,000). Empty-but-valid → `200`, `ticks: []`.

### 7.7 `GET /indicator` — single indicator value · scope: `indicators`

| Param | Type | Req | Default | Notes |
|-------|------|-----|---------|-------|
| `symbol` | string | **yes** | — | |
| `indicator` | string | **yes** | — | from §6 catalogue |
| `timeframe` | string | no | `H1` | §6 set |
| `source` | string | no | — | force broker source |

`data`: `{ symbol: str, timeframe: str, indicator: str, value: number|null,
bid: number|null, ask: number|null, updated_at: int(epoch), server_time: str|null }`
Errors: `400 INVALID_TIMEFRAME`, `404 DATA_NOT_FOUND`, `404 INDICATOR_NOT_FOUND`.

```json
{"success":true,"data":{"symbol":"EURUSD","timeframe":"H1","indicator":"RSI_14","value":58.34,"bid":1.0831,"ask":1.0832,"updated_at":1711548000,"server_time":"2026-03-27T14:00:00"}}
```

### 7.8 `GET /indicators` — all indicators for a symbol · scope: `indicators`

| Param | Type | Req | Default | Notes |
|-------|------|-----|---------|-------|
| `symbol` | string | **yes** | — | |
| `timeframe` | string | no | `H1` | §6 set |
| `category` | string | no | — | `trend`/`oscillator`/`volatility`/`volume` |

`data`: `{ symbol: str, timeframe: str, ohlcv: {open,high,low,close,volume}|null,
bid: number|null, ask: number|null, indicators: { <name>: number|null },
count: int, updated_at: int }`
Errors: `400 INVALID_TIMEFRAME`, `400 INVALID_CATEGORY`, `404 DATA_NOT_FOUND`.

### 7.9 `GET /indicators/list` — indicator catalogue · scope: `indicators`

No params. `data`: `{ indicators: { <category>: { <name>: <description> } },
timeframes: string[], categories: string[] }`.

### 7.10 `GET /indicator/history` — indicator series · scope: `historical` · **plan: starter+**

| Param | Type | Req | Default | Notes |
|-------|------|-----|---------|-------|
| `symbol` | string | **yes** | — | |
| `indicator` | string | **yes** | — | must be in §6 catalogue |
| `timeframe` | string | no | `H1` | §6 set |
| `from` | string | no | `to − maxwindow` | ISO 8601 |
| `to` | string | no | now | ISO 8601 |
| `limit` | int | no | `500` | `1..5000` (also capped per-timeframe) |

`data`: `{ symbol, indicator, timeframe, from: str|null, to: str|null, count: int,
max_window_hours: int|null, series: { time: str, value: number|null }[] }`
Errors: `403 PLAN_UPGRADE_REQUIRED`, `400 INVALID_TIMEFRAME`, `400 INVALID_DATETIME`,
`400 INVALID_TIME_RANGE`, `400 OUTSIDE_RETENTION`, `400 RANGE_TOO_LARGE`,
`404 SYMBOL_NOT_FOUND`, `404 INDICATOR_NOT_FOUND`.

### 7.11 `GET /multi` — batch indicators across symbols · scope: `premium` · (historical mode **plan: starter+**)

| Param | Type | Req | Default | Notes |
|-------|------|-----|---------|-------|
| `symbols` | string | **yes** | — | comma-separated; ≤50 real-time, ≤10 historical |
| `indicators` | string | **yes** | — | comma-separated |
| `timeframe` | string | no | `H1` | §6 set |
| `from` | string | no | — | presence ⇒ historical mode |
| `to` | string | no | — | historical mode |

Real-time `data`: `{ timeframe, data: { <symbol>: { <indicator>: number|null } },
not_found: string[]|null, updated_at: int }`
Historical `data`: `{ timeframe, mode: "historical", from, to,
data: { <symbol>: [ { time, <indicator>: number|null } ] }, not_found }`
Errors: `400 INVALID_REQUEST`, `400 INVALID_TIMEFRAME`, `400 TOO_MANY_SYMBOLS`, plus
historical: `403 PLAN_UPGRADE_REQUIRED`, `404 INDICATOR_NOT_FOUND`, the date errors.

### 7.12 `GET /screener` — scan symbols by indicator · scope: `premium`

| Param | Type | Req | Default | Notes |
|-------|------|-----|---------|-------|
| `indicator` | string | **yes** | — | |
| `timeframe` | string | no | `H1` | validated; bad value → `400 INVALID_TIMEFRAME` |
| `min_val` | number | no | — | inclusive lower bound (**not** `min`) |
| `max_val` | number | no | — | inclusive upper bound (**not** `max`) |
| `sort` | string | no | `asc` | `asc` or `desc` |
| `offset` | int | no | `0` | `≥ 0` |
| `limit` | int | no | `50` | `1..200` |

`data`: `{ indicator, timeframe, filter: { min: number|null, max: number|null },
results: { symbol: str, value: number|null, bid: number|null }[],
total_matches: int, pagination: { offset, limit, total, has_more }, updated_at: int }`
Errors: `400 INVALID_SORT`, `400 INVALID_TIMEFRAME` (timeframe now validated, consistent with the other indicator endpoints).

### 7.13 `GET /summary` — market-bias summary · scope: `indicators`

| Param | Type | Req | Default | Notes |
|-------|------|-----|---------|-------|
| `symbol` | string | **yes** | — | |
| `timeframe` | string | no | `H1` | §6 set |

`data`: `{ symbol, timeframe, bias: "bullish"|"bearish"|"neutral",
bias_strength: "normal"|"strong", confidence: number(0..1), trend_score: number,
momentum_score: number, volatility_score: number, signals: {trend,momentum,
volatility,volume}, key_levels: { resistance: number[], support: number[] },
bullish_signals: str[], bearish_signals: str[], neutral_signals: str[],
volatility_info: str[], volume_info: str[], summary: str, recommendations: str[],
key_values: { bid, ask, rsi_14, macd_hist, adx, atr_14, sma_20, sma_50, sma_200,
bb_upper, bb_lower, stochastic_k, mfi_14 }, updated_at: int }`
Errors: `400 INVALID_TIMEFRAME`, `404 DATA_NOT_FOUND`.

### 7.14 `GET /spread` — spread statistics · scope: none

| Param | Type | Req | Default | Notes |
|-------|------|-----|---------|-------|
| `symbol` | string | **yes** | — | |
| `period` | string | no | `24h` | `1h`/`24h`/`7d`/`30d` |

`data`: `{ symbol, current: { spread_pips: number, spread_points: int },
statistics: { period, avg_spread, min_spread, max_spread, std_deviation },
by_session: { asian: number|null, london: number|null, new_york: number|null } }`
Errors: `400 INVALID_SYMBOL`, `400 INVALID_PERIOD`, `404 SYMBOL_NOT_FOUND`.

### 7.15 `GET /spread/compare` — compare spread across symbols · scope: none

| Param | Type | Req | Default | Notes |
|-------|------|-----|---------|-------|
| `symbols` | string | **yes** | — | comma-separated, ≤20 |
| `period` | string | no | `24h` | `1h`/`24h`/`7d`/`30d` |

`data`: `{ period, symbols: { symbol, current_pips: number|null, avg_pips: number|null,
min_pips: number|null, max_pips: number|null, has_live_data: bool }[], count: int }`
(sorted by `avg_pips` asc). Errors: `400 INVALID_PERIOD`, `400 INVALID_SYMBOL`,
`400 NO_SYMBOLS`, `400 TOO_MANY_SYMBOLS`. (Never 404 — missing symbols come back
with null stats + `has_live_data: false`.)

### 7.16 `GET /sessions` — market session clock · scope: none

No params. `data`: `{ current_time: str(ISO8601), active_sessions: str[],
sessions: { sydney|tokyo|london|new_york: { status: "open"|"closed", closes_in?: str,
opens_in?: str, weekend?: bool } }, overlaps: str[], next_major_event: { event: str,
in: str } | null }`.

### 7.17 `GET /heatmap` — currency strength / correlation · scope: `premium`

| Param | Type | Req | Default | Notes |
|-------|------|-----|---------|-------|
| `type` | string | no | `strength` | `strength` or `correlation` |
| `timeframe` | string | no | `H4` | `H1`/`H4`/`D1`/`W1` |
| `correlations` | bool | no | — | `true` forces correlation mode; **takes precedence over `type`** |

Strength `data`: `{ type:"strength", timeframe, currencies: { <CCY>: { strength:
number(0..10), trend: "bullish"|"bearish"|"neutral", change: number,
pairs_analyzed: int } }, strongest: str|null, weakest: str|null, range: number,
timestamp: str }` (8 majors: USD EUR GBP JPY CHF AUD CAD NZD).
Correlation `data`: `{ type:"correlation", timeframe, correlation_matrix:
{ <CCY>: { <CCY>: number } }, available: bool, message?: str, timestamp: str }`
(when `available:false`, matrix is `{}` and `message` explains why — still HTTP 200).
Errors: `400 INVALID_TYPE`, `400 INVALID_TIMEFRAME`.

### 7.18 `GET /calendar` — economic calendar · scope: `premium`

| Param | Type | Req | Default | Notes |
|-------|------|-----|---------|-------|
| `from` | string | no | today 00:00 UTC | date/ISO |
| `to` | string | no | from+7d | range ≤ 30 days |
| `currencies` | string | no | — | comma-separated (e.g. `USD,EUR`) |
| `country` | string | no | — | alias of `currencies` |
| `impact` | string | no | — | `high`/`medium`/`low` |
| `q` | string | no | — | title search, ≤100 chars |
| `next_hours` | int | no | — | `1..168`; overrides from/to |
| `offset` | int | no | `0` | `≥ 0` |
| `limit` | int | no | `100` | `1..500` |

`data`: `{ events: { id: str, datetime: str(ISO 8601, `+00:00` UTC offset),
currency: str, event: str, impact: str, forecast: str|null, previous: str|null,
actual: str|null }[], count: int, pagination: { offset, limit, total, has_more },
range: { from: str, to: str } }`
Errors: `400 INVALID_DATE`, `400 RANGE_TOO_LARGE`, `400 INVALID_IMPACT`,
`422 VALIDATION_ERROR` (out-of-range `next_hours`/`limit`/`offset`/`q`).

### 7.19 `GET /monitor/account` — account identity & quota · scope: none

No params. `data`: `{ name: str, plan: str, prepaid_credits: number,
daily_quota: int|null  (null = unlimited), daily_used: int }`. This is the de-facto
identity endpoint (there is no `/me`).

### 7.20 `GET /monitor/layout` — saved dashboard layout · scope: none

No params. `data`: `{ layout: array|null }` (per-key, server-side; returns whatever
was stored, or `null`).

### 7.21 `PUT /monitor/layout` — save dashboard layout · scope: none · **write**

JSON body `{ "layout": array }` (≤60 elements). `data`: `{ saved: true }`.
Errors via envelope: `HTTP_400` ("layout must be an array" / "Too many widgets
(max 60)" / "Invalid JSON body"), `HTTP_503` (cache unavailable).
**SDKs SHOULD expose this but document it as advanced/optional** (it mutates the
user's dashboard). It is excluded from the automated integration write-path tests.

### Infrastructure probes (no API key) — served at the API **origin**, not under `/v1`

These live at the host root (e.g. `https://tickatlas.com/health`), need no key, and
are **not** wrapped in the `{success, data}` envelope — SDKs resolve them against the
origin (scheme+host) and return the body verbatim.

`GET /health` → `{ "status": "ok", "components": { "redis": { "status": "ok" }, "postgres": { "status": "ok" } } }`
(each component is a nested status **object**, not a string) · `GET /status` ·
`GET /ready` (proxied at the edge after a 2026-06-15 fix).

---

## 8. Coverage statement

All **21** `/v1` API-key endpoints above are implemented in every SDK (Python,
JS/TS, PHP, Go) and exposed as MCP tools / skill capabilities in `tickatlas-skills`.
The only deliberately-gated surface is the **write** half of `PUT /monitor/layout`,
which is implemented as a callable method but excluded from automated write-path
integration testing (it would overwrite a real user's saved layout). The `/health`
probe is exposed as a convenience method (`health()` / `get_health`); `/status` and
`/ready` live at the same origin and are documented but not wrapped (point the
client's base URL at the origin to reach them if needed).

No public `/v1` endpoint is omitted.

---

## 9. WebSocket (out of scope for v0.1.0)

The platform also exposes a WebSocket quote stream (`/v1/stream` family, see the
server's `ws_quotes` module and `docs/api/websocket.md`). It is **not** part of the
`0.1.0` REST SDK surface and is tracked as a future addition. The SDK READMEs note
this explicitly.

---

## 10. SDK conventions (all languages)

- Config precedence: explicit arg → `TICKATLAS_API_KEY` env. Base URL overridable
  via arg → `TICKATLAS_BASE_URL` env → production default.
- A descriptive `User-Agent` per SDK, e.g. `tickatlas-python/0.1.0`.
- Typed models for every response; typed exception hierarchy from §4.
- Sensible client options: `timeout`, `max_retries`, `backoff_base`, `base_url`.
- Read-only by default; the one write method is clearly named & documented.
- No secret ever written to disk/logs by the SDK.

## 11. Versioning

SDKs start at **0.1.0** (SemVer). The API itself is `v1`. Breaking changes to the
API surface bump the SDK minor version pre-1.0.

---

## 12. Findings — published docs vs live API

Recorded during contract extraction; **the SDKs follow the live/implementation
column.** These are also useful pre-launch fixes for the TickAtlas docs team.

> **Status — RESOLVED 2026-06-15.** The published docs (`docs/api/*`) and the Astro
> site (`public-folder/`) have been reconciled to match the live API for every row
> below (F1–F20); a live guard (`tests/docs-reconciliation/`) now enforces it. F18
> was additionally corrected here: calendar timestamps are ISO 8601 with a
> **`+00:00`** offset (verified live), not naive/no-suffix. Two contract items were
> also actioned on the API side: screener now validates `timeframe` (§7.12) and new
> keys mint `tk_` with `claw_` kept valid (§2). SDKs unchanged — they already
> followed the live column.

| # | Area | Published docs say | Live API actually does | SDK follows |
|---|------|--------------------|------------------------|-------------|
| F1 | Error envelope (`error-codes.md`) | flat `{error, code, details}`, code `RATE_LIMITED` | nested `{success,error:{code,message,…}}`, code `RATE_LIMIT_EXCEEDED` | nested |
| F2 | Screener params (README/some docs) | `min=` / `max=` | `min_val=` / `max_val=` (others silently ignored) | `min_val`/`max_val` |
| F3 | OHLC response (`ohlc.md`) | array `bars`, `first_time`/`last_time`, float volume | array `candles`, `retention`, int volume | `candles`/int |
| F4 | Bulk quotes (`quotes.md`) | examples use `GET /v1/quotes` w/ query params, include a `volume` field | `POST /v1/quotes` JSON body; no `volume` field | POST/no-volume |
| F5 | Ticks (`ticks.md`) | `limit` param, `spread_pips` field, 422 on over-range, "Starter+" | no `limit`, no `spread_pips`, `400 RANGE_TOO_LARGE`/`INVALID_RANGE`, **pro/enterprise** | live |
| F6 | Indicator names (`indicators.md`) | `Parabolic_SAR`, `Tick_Volume`, `RSI_9`, `EMA_200` | `SAR`, `Volumes`; no RSI_9/EMA_200 | live catalogue |
| F7 | `/indicator` & `/indicators` fields | `timestamp` ISO field | `updated_at` (epoch) + `server_time`; `/indicators` adds `ohlcv,bid,ask,count` | live |
| F8 | `/indicators/list` shape | array of `{name,display_name,…}` + `total` | dict keyed by category → {name: description} + `timeframes` | live |
| F9 | `/multi` payload key | `results` + `timestamp` | `data` + `not_found` + `updated_at` (+`mode/from/to` historical) | live |
| F10 | Screener result fields | `count`, no `bid` | `total_matches`, includes `bid`, always `filter:{min,max}` | live |
| F11 | Screener `sort` default | `desc` | `asc` | `asc` |
| F12 | `timeframe` required? (`indicators.md`) | marked required | optional, default `H1` everywhere | optional |
| F13 | Heatmap timeframes | mentions `M15` | valid set is `H1,H4,D1,W1` (no M15) | live |
| F14 | Spread response (`spread.md`) | `optimal_times`, `cost_analysis`, `percentiles`, alt field names | only `current`,`statistics`,`by_session` (field names per §7.14) | live |
| F15 | `/spread/compare` | undocumented | exists; params/shape per §7.15 | implemented |
| F16 | `/monitor/*` | (was) undocumented | `account`,`layout` (GET/PUT) exist; shapes per §7.19–21 | implemented |
| F17 | `monitor/account` fields | (task brief expected email/rate_limit/monthly) | only `name, plan, prepaid_credits, daily_quota, daily_used` | live |
| F18 | Calendar timestamps | trailing `Z` | ISO 8601 with **`+00:00`** UTC offset (verified live 2026-06-15) | live |
| F19 | Datetime error codes (`indicator-history.md`) | `INVALID_FROM_TIME`/`FROM_TIME_TOO_OLD` | `INVALID_DATETIME` / `OUTSIDE_RETENTION` | live |
| F20 | `/health` (verified live 2026-06-15) | implied `/v1/health`, `components` as `{redis, postgres}` strings | served at **origin** `/health` (not `/v1`), **no** envelope, `components` are nested `{status}` objects | origin + nested + envelope-bypass |

> All of the above were **functionally healthy** in the live test (no 5xx; every
> happy path returned `200` with the correct envelope). The findings are docs
> drift + a couple of validation niceties, not outages.
