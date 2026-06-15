# TickAtlas Go SDK

[![Go Reference](https://pkg.go.dev/badge/github.com/tickatlas/tickatlas-sdk/go.svg)](https://pkg.go.dev/github.com/tickatlas/tickatlas-sdk/go)
[![Go 1.21+](https://img.shields.io/badge/go-1.21%2B-00ADD8.svg)](https://go.dev/dl/)

Official Go SDK for the [TickAtlas](https://tickatlas.com) market-data API —
real-time quotes, OHLC candles, ticks, 42 technical indicators, currency
strength/correlation heatmaps, spread analytics, market sessions, and an economic
calendar across forex, metals, commodities, indices, crypto, and stocks.

- Idiomatic Go: functional options, `context.Context` on every call, typed
  results and typed errors.
- **Zero external dependencies** — standard library only (`net/http`,
  `encoding/json`, `context`).
- Automatic retries with exponential backoff + full jitter; `Retry-After` aware.
- Forward-compatible models that tolerate unknown fields.

> **Scope:** This is the REST SDK. The TickAtlas WebSocket quote stream is **out
> of scope for `0.1.0`** and is planned for a future release.

---

## Installation

```bash
go get github.com/tickatlas/tickatlas-sdk/go
```

Requires Go 1.21+. The import path is the module path; the package name is
`tickatlas`:

```go
import tickatlas "github.com/tickatlas/tickatlas-sdk/go"
```

## Authentication

Authenticate with your API key (the `X-API-Key` header is set for you). The key
is resolved in this order:

1. the [`WithAPIKey`] option, then
2. the `TICKATLAS_API_KEY` environment variable.

If neither is present, `NewClient` returns an error.

```go
// Explicit:
client, err := tickatlas.NewClient(
    tickatlas.WithAPIKey("claw_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"),
)

// Or from the environment (recommended — never hardcode keys):
//   export TICKATLAS_API_KEY="claw_..."
client, err := tickatlas.NewClient()
```

The SDK **never** logs, prints, or serializes your key.

### Base URL

The base URL defaults to `https://tickatlas.com/v1` and can be overridden for
self-hosted/staging deployments via `WithBaseURL(...)` or the
`TICKATLAS_BASE_URL` environment variable.

### Client options

| Option | Default | Meaning |
|--------|---------|---------|
| `WithAPIKey(string)` | env `TICKATLAS_API_KEY` | API key (opaque string) |
| `WithBaseURL(string)` | env `TICKATLAS_BASE_URL`, then production | API base URL |
| `WithHTTPClient(*http.Client)` | `&http.Client{Timeout: 30s}` | custom transport/proxy/TLS |
| `WithTimeout(time.Duration)` | `30s` | per-request timeout on the HTTP client |
| `WithMaxRetries(int)` | `3` | max retries for 429/5xx/network failures |
| `WithUserAgent(string)` | `tickatlas-go/0.1.0` | override the User-Agent |

```go
client, err := tickatlas.NewClient(
    tickatlas.WithAPIKey("claw_..."),
    tickatlas.WithBaseURL("https://staging.tickatlas.com/v1"),
    tickatlas.WithTimeout(15*time.Second),
    tickatlas.WithMaxRetries(5),
)
```

## Quickstart

```go
package main

import (
    "context"
    "fmt"
    "log"

    tickatlas "github.com/tickatlas/tickatlas-sdk/go"
)

func main() {
    client, err := tickatlas.NewClient() // reads TICKATLAS_API_KEY
    if err != nil {
        log.Fatal(err)
    }

    ctx := context.Background()
    quote, err := client.Quote(ctx, "EURUSD", nil)
    if err != nil {
        log.Fatal(err)
    }

    if quote.Bid != nil {
        fmt.Printf("%s bid=%.5f ask=%.5f spread=%.1f pips\n",
            quote.Symbol, *quote.Bid, *quote.Ask, *quote.SpreadPips)
    }
}
```

Every method takes a `context.Context` as its first argument and returns a typed
result pointer and an `error`. Endpoints with many optional parameters take an
option struct (a nil pointer means "all defaults").

Nullable numeric fields are modelled as pointers (for example `Bid *float64`), so
a JSON `null` is distinguishable from a real `0`.

## Endpoint examples

All 21 `/v1` endpoints are covered, plus the `/health` infra probe.

### Symbols

```go
syms, _ := client.Symbols(ctx, &tickatlas.SymbolsParams{
    Category: tickatlas.CategoryForex,
    Search:   "EUR",
    Limit:    ptr(50),
})
fmt.Println(syms.Total, len(syms.Symbols))

spec, _ := client.Symbol(ctx, "EURUSD")
fmt.Println(spec.Digits, spec.ContractSize)
```

### Quotes

```go
q, _ := client.Quote(ctx, "EURUSD", &tickatlas.QuoteParams{IncludeSources: true})

batch, _ := client.Quotes(ctx,
    []string{"EURUSD", "GBPUSD", "XAUUSD"},
    []string{"bid", "ask"}, // nil for all fields
)
fmt.Println(batch.Count, batch.NotFound)
```

### OHLC & ticks

```go
ohlc, _ := client.OHLC(ctx, "EURUSD", &tickatlas.OHLCParams{
    Timeframe: tickatlas.TimeframeH1,
    Limit:     ptr(200),
})

// Ticks require a pro/enterprise plan; range must be <= 1 hour.
ticks, _ := client.Ticks(ctx, "EURUSD",
    "2026-05-25T13:00:00Z", "2026-05-25T13:30:00Z")
_ = ticks
```

### Indicators

```go
// Single indicator. Use the exported constants for the 42-indicator catalogue.
rsi, _ := client.Indicator(ctx, "EURUSD", tickatlas.RSI14,
    &tickatlas.IndicatorParams{Timeframe: tickatlas.TimeframeH4})
if rsi.Value != nil {
    fmt.Printf("RSI(14) = %.2f\n", *rsi.Value)
}

// All indicators for a symbol.
all, _ := client.Indicators(ctx, "EURUSD", nil)
fmt.Println(all.Count, all.Indicators["MACD_hist"])

// Catalogue (categories -> {name: description}).
cat, _ := client.ListIndicators(ctx)
_ = cat

// History (starter+ plan).
hist, _ := client.IndicatorHistory(ctx, "EURUSD", tickatlas.RSI14,
    &tickatlas.HistoryParams{Limit: ptr(500)})
_ = hist
```

### Multi (batch indicators across symbols)

```go
multi, _ := client.Multi(ctx,
    []string{"EURUSD", "GBPUSD"},
    []string{tickatlas.RSI14, tickatlas.SMA20},
    nil, // pass &MultiParams{From: ...} for historical mode (starter+)
)

rt, _ := multi.RealTime() // map[symbol]map[indicator]*float64
fmt.Println(rt["EURUSD"][tickatlas.RSI14])

// In historical mode, use multi.Historical() instead.
```

### Screener

```go
// NOTE: bounds are min_val / max_val (the MinVal/MaxVal fields), not min/max.
hits, _ := client.Screen(ctx, tickatlas.RSI14, &tickatlas.ScreenParams{
    MinVal: ptr(70.0), // overbought
    Sort:   "desc",
    Limit:  ptr(25),
})
fmt.Println(hits.TotalMatches)
```

### Summary, spread, sessions

```go
sum, _ := client.Summary(ctx, "EURUSD", tickatlas.TimeframeH1)
fmt.Println(sum.Bias, sum.Confidence)

sp, _ := client.Spread(ctx, "EURUSD", tickatlas.SpreadPeriod24h)
fmt.Println(sp.Current.SpreadPips)

cmp, _ := client.CompareSpread(ctx,
    []string{"EURUSD", "GBPUSD"}, tickatlas.SpreadPeriod24h)
_ = cmp

sess, _ := client.Sessions(ctx)
fmt.Println(sess.ActiveSessions)
```

### Heatmap & calendar

```go
hm, _ := client.Heatmap(ctx, &tickatlas.HeatmapParams{
    Type:      tickatlas.HeatmapTypeStrength,
    Timeframe: tickatlas.HeatmapTimeframeH4,
})
if hm.Strongest != nil {
    fmt.Println("strongest:", *hm.Strongest)
}

cal, _ := client.Calendar(ctx, &tickatlas.CalendarParams{
    Currencies: "USD,EUR",
    Impact:     tickatlas.ImpactHigh,
    NextHours:  ptr(24),
})
fmt.Println(cal.Count)
// Note: event datetimes are naive UTC (no "Z" suffix); treat them as UTC.
```

### Account & layout

```go
acct, _ := client.Account(ctx) // the de-facto identity endpoint (no /me)
fmt.Println(acct.Plan, acct.DailyUsed)

layout, _ := client.Layout(ctx) // layout.Layout is raw JSON (nil if unset)
_ = layout
```

### Health (no API key)

```go
h, _ := client.Health(ctx)
fmt.Println(h.Status, h.Components.Redis, h.Components.Postgres)
```

### Write: SaveLayout (advanced)

`SaveLayout` is the **only** write method. It mutates the user's saved dashboard
layout (max 60 widgets), so most callers will not need it.

```go
widgets := []map[string]any{
    {"widget": "chart", "symbol": "EURUSD"},
}
res, err := client.SaveLayout(ctx, widgets)
if err == nil {
    fmt.Println(res.Saved)
}
```

A small helper used in the examples above:

```go
func ptr[T any](v T) *T { return &v }
```

## Error handling

All API errors are typed. The server's structured errors are reported as
`*APIError` (or one of its subtypes); transport failures (connection, timeout,
DNS, context cancellation) as `*NetworkError`.

You can branch with the predicate helpers, or with `errors.As` against a concrete
type — both are supported on the same error value.

```go
quote, err := client.Quote(ctx, "NOPE", nil)
if err != nil {
    switch {
    case tickatlas.IsNotFound(err):
        // 404: SYMBOL_NOT_FOUND, DATA_NOT_FOUND, INDICATOR_NOT_FOUND
    case tickatlas.IsAuth(err):
        // 401: MISSING_API_KEY, INVALID_API_KEY
    case tickatlas.IsPermissionDenied(err):
        // 403: API_KEY_DISABLED, PLAN_UPGRADE_REQUIRED, ...
    case tickatlas.IsValidation(err):
        // 400/422: INVALID_*, RANGE_TOO_LARGE, VALIDATION_ERROR, ...
    case tickatlas.IsRateLimit(err):
        // 429 (see RetryAfter below)
    case tickatlas.IsServer(err):
        // 5xx
    case tickatlas.IsNetwork(err):
        // no HTTP response
    }
}
```

Read the machine-branchable code and the forward-compatible context fields via
`*APIError`:

```go
var apiErr *tickatlas.APIError
if errors.As(err, &apiErr) {
    fmt.Println(apiErr.StatusCode, apiErr.Code, apiErr.Message)
    fmt.Println(apiErr.RequestID)                 // X-Request-ID, echo in support tickets
    fmt.Println(apiErr.Details["required_plan"])  // any extra server context
    fmt.Println(string(apiErr.Raw()))             // verbatim error JSON
}
```

`*RateLimitError` exposes the server-advised delay:

```go
var rle *tickatlas.RateLimitError
if errors.As(err, &rle) {
    time.Sleep(rle.RetryAfter) // from Retry-After (falls back to reset_in_seconds)
}
```

`*NetworkError` unwraps the underlying transport error, so it composes with
`errors.Is`:

```go
if errors.Is(err, context.DeadlineExceeded) {
    // request timed out
}
```

### Error type hierarchy

| Type | HTTP | Predicate |
|------|------|-----------|
| `*AuthenticationError` | 401 | `IsAuth` |
| `*PermissionDeniedError` | 403 | `IsPermissionDenied` |
| `*NotFoundError` | 404 | `IsNotFound` |
| `*ValidationError` | 400, 422 | `IsValidation` |
| `*RateLimitError` | 429 | `IsRateLimit` |
| `*ServerError` | 5xx | `IsServer` |
| `*APIError` | any structured error (base of the above) | `IsAPIError` |
| `*NetworkError` | none (transport failure) | `IsNetwork` |

## Retries & rate limiting

The client automatically retries **only** transient failures: HTTP `429`, HTTP
`5xx`, and network/timeout errors. All `/v1` endpoints are read-only/idempotent
(the sole write, `SaveLayout`, is also safe to retry), so retries are always safe.

- Default **max 3 retries** (4 attempts total); configure with `WithMaxRetries`.
- Exponential backoff with full jitter: `min(cap, base * 2^attempt) * rand`, with
  `base = 500ms` and `cap = 30s`.
- On `429`, the SDK honours the `Retry-After` header (falling back to the JSON
  `reset_in_seconds`, then `X-RateLimit-Reset`) instead of the computed backoff.
- Backoff sleeps respect context cancellation: a cancelled/expired `ctx` aborts
  the wait and surfaces a `*NetworkError`.

Every `/v1` response carries `X-RateLimit-Limit`, `X-RateLimit-Remaining`,
`X-RateLimit-Reset` and `X-Request-ID`. Read these from your own `*http.Client`
transport if you need them; the SDK surfaces `X-Request-ID` on errors via
`APIError.RequestID`.

## Constants

Exported constants are provided for timeframes (`TimeframeH1`, …), heatmap
timeframes (`HeatmapTimeframeW1`, …), categories, spread periods, calendar impact,
bias values, heatmap types, plans, and the full **42-indicator** catalogue
(`RSI14`, `MACDHist`, `SAR`, `Volumes`, …). `AllIndicators()` returns the complete
list. Raw strings are accepted everywhere too.

## Testing

```bash
go test ./...                # unit tests (no network, httptest-based)
go vet ./...
gofmt -l .                   # should print nothing
```

Integration tests run against the live API and are gated behind a build tag **and**
environment variables, so they never run by accident:

```bash
RUN_INTEGRATION=1 TICKATLAS_API_KEY=claw_... go test -tags integration ./...
```

They are read-only and skip (rather than fail) when the gate is not set. The write
path (`SaveLayout`) is intentionally not exercised.

## Contributing

1. `go test ./...`, `go vet ./...` and `gofmt -l .` must all be clean.
2. Keep the SDK dependency-free (standard library only).
3. The authoritative API contract lives in the repository's top-level `SPEC.md`;
   match it exactly (the live/implementation behaviour wins on any conflict).
4. Never commit, log, or hardcode an API key.

## License

MIT — see [LICENSE](../LICENSE).
