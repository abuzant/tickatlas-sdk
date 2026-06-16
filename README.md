# TickAtlas SDKs

Official client SDKs for the [**TickAtlas**](https://tickatlas.com) market-data API —
real-time and historical data for forex, commodities, indices, crypto, and equities:
quotes, OHLC candles, tick data, 30+ technical indicators, market-bias summaries,
currency-strength heatmaps, spread analytics, and an economic calendar.

> **Intended GitHub repo:** `abuzant/tickatlas-sdk` (this monorepo). Each language
> package is independently publishable.

This is a **monorepo**: one package per language, each idiomatic for its ecosystem
and built against the same contract — **[`SPEC.md`](SPEC.md)**, the authoritative API
contract this repo was built and tested against.

---

## Language matrix

| Language | Package | Install | Source | Docs |
|----------|---------|---------|--------|------|
| **Python** | `tickatlas` (PyPI) | `pip install tickatlas` | [`python/`](python/) | [README](python/README.md) |
| **JavaScript / TypeScript** | `tickatlas` (npm) | `npm install tickatlas` | [`javascript/`](javascript/) | [README](javascript/README.md) |
| **PHP** | `tickatlas/php-sdk` (Packagist) | `composer require tickatlas/php-sdk` | [`php/`](php/) | [README](php/README.md) |
| **Go** | `github.com/abuzant/tickatlas-sdk/go` | `go get github.com/abuzant/tickatlas-sdk/go` | [`go/`](go/) | [README](go/README.md) |

All four cover **every one of the 21 public `/v1` endpoints** (see
[§ Endpoint coverage](#endpoint-coverage)).

---

## Authentication

Every SDK authenticates with an API key sent as the `X-API-Key` header. Get a key
from your [TickAtlas dashboard](https://tickatlas.com/dashboard).

Provide it explicitly, or set the environment variable **`TICKATLAS_API_KEY`** (the
default every SDK reads). The base URL defaults to `https://tickatlas.com/v1` and is
overridable via constructor option or `TICKATLAS_BASE_URL`.

```bash
export TICKATLAS_API_KEY="tk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

No SDK ever logs, prints, or persists your key.

---

## Quickstart

**Python**
```python
from tickatlas import TickAtlas
client = TickAtlas()                       # reads TICKATLAS_API_KEY
rsi = client.get_indicator("EURUSD", "RSI_14", timeframe="H1")
print(rsi.value)
```

**TypeScript / JavaScript**
```ts
import { TickAtlas } from "tickatlas";
const client = new TickAtlas();            // reads TICKATLAS_API_KEY
const rsi = await client.getIndicator("EURUSD", "RSI_14", { timeframe: "H1" });
console.log(rsi.value);
```

**PHP**
```php
use TickAtlas\Client;
$client = new Client();                     // reads TICKATLAS_API_KEY
$rsi = $client->getIndicator('EURUSD', 'RSI_14', ['timeframe' => 'H1']);
echo $rsi->value;
```

**Go**
```go
client, _ := tickatlas.NewClient()          // reads TICKATLAS_API_KEY
rsi, err := client.Indicator(ctx, "EURUSD", "RSI_14", &tickatlas.IndicatorParams{Timeframe: "H1"})
```

Each package README has full per-endpoint examples, error handling, and retry/rate-limit
details.

---

## Shared design (all SDKs)

- **Typed responses** — every endpoint returns a typed model parsed from the
  `{"success": true, "data": ...}` envelope.
- **Typed errors** — `AuthenticationError` (401), `PermissionDeniedError` (403),
  `NotFoundError` (404), `ValidationError` (400/422), `RateLimitError` (429, with
  `retry_after`), `ServerError` (5xx), and a network/timeout error — all under one
  base type. See [`SPEC.md` §4](SPEC.md).
- **Automatic retries** — exponential backoff with jitter on `429`/`5xx`/network
  errors, honouring the `Retry-After` header on rate limits. Configurable.
- **Rate-limit aware** — reads `X-RateLimit-*` headers and the `X-Request-ID`
  correlation id.
- **Config** — explicit arg → `TICKATLAS_API_KEY` / `TICKATLAS_BASE_URL` env →
  sensible default.

---

## Endpoint coverage

All 21 public `/v1` endpoints, in every SDK:

| Group | Endpoints |
|-------|-----------|
| **Symbols** | `GET /symbols`, `GET /symbols/{symbol}` |
| **Quotes** | `GET /quote`, `POST /quotes` |
| **History** | `GET /ohlc`, `GET /ticks` |
| **Indicators** | `GET /indicator`, `GET /indicators`, `GET /indicators/list`, `GET /indicator/history`, `GET /multi`, `GET /screener` |
| **Analytics** | `GET /summary`, `GET /heatmap`, `GET /spread`, `GET /spread/compare`, `GET /sessions` |
| **Calendar** | `GET /calendar` |
| **Account** | `GET /monitor/account`, `GET /monitor/layout`, `PUT /monitor/layout` *(write, advanced)* |

Plus convenience access to the unauthenticated `GET /health` probe. The WebSocket
quote stream is **not** part of `0.1.0` (tracked for a future release). See
[`SPEC.md` §7](SPEC.md) for the full contract and [§12](SPEC.md) for documented
docs-vs-live findings.

---

## Testing

Each SDK ships two suites:

- **Unit tests** — no network; every method is exercised against mocked HTTP using
  the real example payloads from `SPEC.md`. These run in CI on every push.
- **Integration tests** — hit the real API, **read-only**, and are gated behind
  `RUN_INTEGRATION=1` + `TICKATLAS_API_KEY`. They never run by default and are wired
  into CI behind a repository secret (`workflow_dispatch`).

```bash
# Python
cd python && python -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]" && pytest
# JavaScript
cd javascript && npm install && npm run build && npm test
# PHP
cd php && composer install && composer test
# Go
cd go && go test ./...

# Live integration (any language), once you have a key:
export TICKATLAS_API_KEY="tk_..." RUN_INTEGRATION=1
```

---

## Versioning & contributing

All packages start at **0.1.0** and follow [SemVer](https://semver.org). The API
itself is `v1`. Contributions welcome — see each package's README for dev setup.
Licensed under [MIT](LICENSE).
