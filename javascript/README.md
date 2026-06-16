# tickatlas

Official JavaScript / TypeScript SDK for the [TickAtlas](https://tickatlas.com) market-data API.

Real-time quotes, OHLC candles, tick data, **42 technical indicators**, a market screener, currency-strength heatmaps, an economic calendar, and account/quota info — for forex, metals, commodities, indices, crypto, and stocks.

- **Zero runtime dependencies.** Uses the platform `fetch` — works in **Node 18+** and modern **browsers**.
- **Dual package:** ships **ESM**, **CommonJS**, and full **TypeScript declarations**.
- **Fully typed:** every request parameter and response model, plus a typed exception hierarchy.
- **Resilient:** automatic retries with exponential backoff + jitter, honouring `Retry-After` on rate limits.

> Covers all **21** `/v1` endpoints plus the `/health` probe. The WebSocket quote stream is out of scope for `0.1.0` (tracked for a future release).

---

## Installation

```bash
npm install tickatlas
```

Requires Node.js **18 or newer** (for the built-in `fetch`/`AbortController`), or any modern browser.

---

## Authentication

Authenticate with your API key (sent as the `X-API-Key` header). The key is resolved in this order:

1. The explicit `apiKey` constructor option.
2. The `TICKATLAS_API_KEY` environment variable (Node only).

If neither is present, the constructor throws a `TickAtlasConfigError`.

```ts
import { TickAtlas } from "tickatlas";

// Explicit key
const client = new TickAtlas({ apiKey: "claw_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" });

// …or rely on the TICKATLAS_API_KEY env var
const client2 = new TickAtlas();
```

> **Never** hardcode, log, or commit your API key. Prefer the `TICKATLAS_API_KEY` environment variable. This SDK never writes your key to disk or logs.

### Base URL

Defaults to `https://tickatlas.com/v1`. Override for staging/self-hosted deployments via the `baseURL` option or the `TICKATLAS_BASE_URL` env var (option wins).

```ts
const client = new TickAtlas({
  apiKey: process.env.TICKATLAS_API_KEY,
  baseURL: "https://staging.tickatlas.com/v1",
});
```

### Client options

| Option        | Default                       | Description                                   |
| ------------- | ----------------------------- | --------------------------------------------- |
| `apiKey`      | `TICKATLAS_API_KEY` env       | API key (`X-API-Key` header).                 |
| `baseURL`     | `https://tickatlas.com/v1`    | API base URL (`TICKATLAS_BASE_URL` env).      |
| `timeout`     | `30000`                       | Per-request timeout in ms (`AbortController`).  |
| `maxRetries`  | `3`                           | Retries for 429 / 5xx / network errors.       |
| `backoffBase` | `500`                         | Exponential-backoff base in ms.               |
| `backoffCap`  | `30000`                       | Maximum backoff delay in ms.                  |
| `fetch`       | global `fetch`                | Custom `fetch` implementation (advanced).     |

---

## Quickstart

### TypeScript

```ts
import { TickAtlas, Indicators, Timeframes } from "tickatlas";

const client = new TickAtlas({ apiKey: process.env.TICKATLAS_API_KEY });

// A single real-time quote
const quote = await client.getQuote("EURUSD");
console.log(`${quote.symbol}: ${quote.bid} / ${quote.ask}  (spread ${quote.spread_pips} pips)`);

// RSI(14) on the H1 timeframe
const rsi = await client.getIndicator("EURUSD", Indicators.RSI_14, {
  timeframe: Timeframes.H1,
});
console.log(`RSI: ${rsi.value}`);
```

### JavaScript (ESM)

```js
import { TickAtlas } from "tickatlas";

const client = new TickAtlas({ apiKey: process.env.TICKATLAS_API_KEY });
const quote = await client.getQuote("EURUSD");
console.log(quote.bid, quote.ask);
```

### JavaScript (CommonJS)

```js
const { TickAtlas } = require("tickatlas");

(async () => {
  const client = new TickAtlas({ apiKey: process.env.TICKATLAS_API_KEY });
  const quote = await client.getQuote("EURUSD");
  console.log(quote.bid, quote.ask);
})();
```

Both the `import` and `require` forms are wired through the package `exports` map, with `.d.ts` types for either entry point.

---

## Enums & constants

For autocomplete, the SDK exports `as const` objects. **You can always pass raw strings instead** — these exist purely for convenience.

```ts
import {
  Timeframes,        // M1 M5 M15 M30 H1 H4 D1
  HeatmapTimeframes, // H1 H4 D1 W1
  Indicators,        // all 42 indicator ids
  IndicatorsByCategory,
  ALL_INDICATORS,
  SpreadPeriods,     // 1h 24h 7d 30d
  CalendarImpacts,   // high medium low
  SymbolCategories,  // forex metals commodities indices crypto stocks
} from "tickatlas";

client.getIndicator("EURUSD", Indicators.MACD_hist, { timeframe: Timeframes.H4 });
client.getIndicator("EURUSD", "MACD_hist", { timeframe: "H4" }); // identical
```

**Indicator naming gotchas** (the names below are the *correct* ones — common doc typos 404):
`SAR` (not `Parabolic_SAR`), `Volumes` (not `Tick_Volume`), `WilliamsR_14` (no underscore before `R`), `ADX_plusDI` / `ADX_minusDI`. `EMA` stops at `EMA_50`; `SMA` goes to `SMA_200`. There is no `RSI_9` or `EMA_200`, and only three Ichimoku keys.

---

## Endpoint reference

All methods return a `Promise` of the **unwrapped, typed** `data` payload (the `{ success, data }` envelope is handled for you).

### Symbols

```ts
await client.getSymbols({ category: "forex", search: "EUR", offset: 0, limit: 100 });
await client.getSymbol("EURUSD"); // full contract spec
```

### Quotes

```ts
await client.getQuote("EURUSD", { includeSources: true });
await client.getQuotes(["EURUSD", "GBPUSD", "USDJPY"], ["bid", "ask", "spread_pips"]);
```

`getQuotes` is a `POST` under the hood (the API's batch endpoint is POST-only); `fields` is optional and defaults to all five.

### OHLC & ticks

```ts
await client.getOhlc("EURUSD", {
  timeframe: "H1",
  from: "2026-05-01T00:00:00Z",
  to: "2026-05-25T00:00:00Z",
  limit: 500,
});

// Ticks require from/to (ISO 8601); the range must be <= 1 hour. Plan: pro/enterprise.
await client.getTicks("EURUSD", "2026-05-25T13:00:00Z", "2026-05-25T13:30:00Z");
```

### Indicators

```ts
await client.getIndicator("EURUSD", "RSI_14", { timeframe: "H1" });
await client.getIndicators("EURUSD", { timeframe: "H1", category: "oscillator" });
await client.listIndicators(); // the full catalogue with descriptions

// History (plan: starter+)
await client.getIndicatorHistory("EURUSD", "RSI_14", { timeframe: "H1", limit: 500 });

// Batch across symbols (supplying `from` switches to historical mode, plan: starter+)
await client.getMulti(["EURUSD", "GBPUSD"], ["RSI_14", "ADX"], { timeframe: "H1" });
```

### Screener

```ts
// Find oversold symbols by RSI. Note: minVal/maxVal -> min_val/max_val.
await client.screen("RSI_14", {
  timeframe: "H1",
  maxVal: 30,
  sort: "asc",
  offset: 0,
  limit: 50,
});
```

### Summary, spread & sessions

```ts
await client.getSummary("EURUSD", "H4");          // market-bias summary
await client.getSpread("EURUSD", "24h");          // spread statistics
await client.compareSpread(["EURUSD", "GBPUSD"], "24h");
await client.getSessions();                         // market session clock
```

### Heatmap & calendar

```ts
await client.getHeatmap({ type: "strength", timeframe: "H4" });
await client.getHeatmap({ correlations: true }); // correlation matrix

await client.getCalendar({
  currencies: ["USD", "EUR"], // string or string[]
  impact: "high",
  nextHours: 24,
  limit: 100,
});
```

### Account & layout

```ts
await client.getAccount(); // { name, plan, prepaid_credits, daily_quota, daily_used }
await client.getLayout();  // saved dashboard layout (or null)

// ADVANCED / WRITE — overwrites the saved dashboard layout for this API key.
await client.saveLayout([{ widget: "quote", symbol: "EURUSD" }]);
```

> `saveLayout` is the **only** mutating method in the SDK. Use it deliberately.

### Health probe

```ts
await client.health(); // { status, components: { redis, postgres } }
```

---

## Error handling

Every failure throws a typed error. Catch the base class, or branch on specific subclasses / the stable `code` string.

```ts
import {
  TickAtlasError,
  TickAtlasAPIError,
  AuthenticationError,
  PermissionDeniedError,
  NotFoundError,
  ValidationError,
  RateLimitError,
  ServerError,
  TickAtlasNetworkError,
} from "tickatlas";

try {
  const quote = await client.getQuote("NOPE");
} catch (e) {
  if (e instanceof NotFoundError) {
    console.error("Symbol not found:", e.code); // SYMBOL_NOT_FOUND
  } else if (e instanceof RateLimitError) {
    console.error(`Rate limited; retry after ${e.retryAfter}s`);
  } else if (e instanceof TickAtlasAPIError) {
    console.error(`API error ${e.statusCode} (${e.code}): ${e.message}`);
    console.error("request id:", e.requestId);
    console.error("context:", e.raw); // raw error object — read extra fields here
  } else if (e instanceof TickAtlasNetworkError) {
    console.error("Network/timeout failure:", e.isTimeout ? "timeout" : "connection");
  }
}
```

### Exception hierarchy

```
TickAtlasError                  base for everything
├── TickAtlasAPIError           server returned a structured error
│   │   .statusCode .code .message .details .requestId .raw
│   ├── AuthenticationError     HTTP 401  (MISSING_API_KEY, INVALID_API_KEY)
│   ├── PermissionDeniedError   HTTP 403  (API_KEY_DISABLED, PLAN_UPGRADE_REQUIRED, …)
│   ├── NotFoundError           HTTP 404  (SYMBOL_NOT_FOUND, DATA_NOT_FOUND, INDICATOR_NOT_FOUND)
│   ├── ValidationError         HTTP 400 & 422  (INVALID_*, RANGE_TOO_LARGE, VALIDATION_ERROR, …)
│   ├── RateLimitError          HTTP 429  (RATE_LIMIT_EXCEEDED, QUOTA_EXCEEDED) — has .retryAfter
│   └── ServerError             HTTP 5xx  (INTERNAL_ERROR, SERVICE_UNAVAILABLE)
└── TickAtlasNetworkError       no HTTP response (connection / timeout / DNS) — has .isTimeout
```

`TickAtlasConfigError` (also extends `TickAtlasError`) is thrown at construction time for misconfiguration, e.g. a missing API key.

The `.raw` property exposes the full server `error` object, so you can read forward-compatible context fields (`valid_timeframes`, `required_plan`, `retention_period`, …) that aren't first-class properties.

---

## Retries & rate limiting

By default the client makes up to **4 attempts** (1 + `maxRetries`) and retries **only** on:

- `429` (rate limit / quota),
- `5xx` (server errors), and
- network / timeout errors.

All other errors fail fast. Backoff is **exponential with full jitter** (`base * 2^attempt`, capped at `backoffCap`). On `429`, the client honours the server's **`Retry-After`** header (falling back to `X-RateLimit-Reset`, then the body's `reset_in_seconds`) instead of the computed backoff. All `/v1` endpoints are read-only/idempotent (except the explicit `saveLayout` write), so retries are safe.

Tune the behaviour per client:

```ts
const client = new TickAtlas({
  apiKey: process.env.TICKATLAS_API_KEY,
  timeout: 10_000,
  maxRetries: 5,
  backoffBase: 250,
});
```

Each response also carries `X-RateLimit-Limit` / `-Remaining` / `-Reset` and an `X-Request-ID` (echoed on `TickAtlasAPIError.requestId`).

---

## Contributing

```bash
git clone https://github.com/abuzant/tickatlas-sdk.git
cd tickatlas-sdk/javascript

npm install
npm run build      # tsup -> dist/ (ESM .mjs + CJS .cjs + .d.ts)
npm run typecheck  # tsc --noEmit
npm test           # vitest (unit tests, fully mocked — no network)
```

The unit suite mocks `fetch` and never touches the network. There is a separate, **read-only** integration suite that is **skipped** unless both `RUN_INTEGRATION=1` and `TICKATLAS_API_KEY` are set:

```bash
RUN_INTEGRATION=1 TICKATLAS_API_KEY=claw_xxx npm run test:integration
```

It never exercises the write endpoint (`saveLayout`). Please don't commit API keys.

---

## License

[MIT](./LICENSE) © TickAtlas
