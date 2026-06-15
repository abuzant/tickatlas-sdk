# TickAtlas PHP SDK

Official PHP client for the [TickAtlas](https://tickatlas.com) API — real-time
forex/markets quotes, OHLC & tick history, 42 technical indicators, market-bias
summaries, spread analytics, currency-strength heatmaps and an economic calendar.

- PHP 8.1+
- Strongly-typed response models and a typed exception hierarchy
- Built-in retries with backoff + `Retry-After` handling
- Covers all 21 `/v1` endpoints plus the `/health` probe

> **Version 0.1.0.** The WebSocket quote stream is not part of this REST SDK yet
> and is tracked as a future addition.

## Installation

```bash
composer require tickatlas/php-sdk
```

## Authentication

Every request is authenticated with an API key sent as the `X-API-Key` header.
The key is resolved in this order:

1. The explicit constructor argument
2. The `TICKATLAS_API_KEY` environment variable

If neither is present the constructor throws `ConfigurationException`. **Never
hardcode, log or commit your key** — the SDK never writes it to disk or logs.

```php
use TickAtlas\Client;

// Explicit key
$client = new Client('claw_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');

// Or rely on the environment (TICKATLAS_API_KEY)
$client = new Client();
```

The base URL defaults to `https://tickatlas.com/v1` and can be overridden via the
second argument or the `TICKATLAS_BASE_URL` environment variable (useful for
staging / self-hosted deployments):

```php
$client = new Client(
    apiKey: 'claw_...',
    baseUrl: 'https://staging.tickatlas.com/v1',
);
```

### Client options

```php
$client = new Client('claw_...', null, [
    'timeout'     => 30,    // per-request timeout in seconds
    'maxRetries'  => 3,     // retry attempts on 429/5xx/network (4 total tries)
    'backoffBase' => 0.5,   // base seconds for exponential backoff
    'backoffCap'  => 30.0,  // backoff ceiling in seconds
    // 'httpClient' => $guzzle,  // inject a Guzzle client/handler (testing)
    // 'sleeper'    => $sleeper, // inject a TickAtlas\Retry\Sleeper (testing)
]);
```

## Quickstart

```php
use TickAtlas\Client;
use TickAtlas\Exception\TickAtlasException;

$client = new Client(); // reads TICKATLAS_API_KEY

try {
    $quote = $client->getQuote('EURUSD');
    printf("EURUSD  bid=%s ask=%s spread=%s pips\n",
        $quote->bid, $quote->ask, $quote->spreadPips);

    $rsi = $client->getIndicator('EURUSD', 'RSI_14', ['timeframe' => 'H1']);
    printf("RSI(14) = %s\n", $rsi->value);
} catch (TickAtlasException $e) {
    fwrite(STDERR, "TickAtlas error: {$e->getMessage()}\n");
}
```

Every method returns a typed, `readonly` model. Each model also exposes the raw
decoded payload, so forward-compatible fields are never lost:

```php
$quote->toArray();                 // full decoded data array
$quote->get('some_new_field');     // single raw key
```

## Enums

Backed enums are provided for convenience and discoverability; **every method
also accepts a plain string**, so you can use whichever you prefer.

```php
use TickAtlas\Enums\{Timeframe, Period, Impact, HeatmapType, HeatmapTimeframe, Bias, Category, Indicator};

$client->getOhlc('EURUSD', ['timeframe' => Timeframe::H4]);
$client->getOhlc('EURUSD', ['timeframe' => 'H4']);              // equivalent

$client->getIndicator('EURUSD', Indicator::RSI_14);
$client->getIndicator('EURUSD', 'RSI_14');                      // equivalent

Indicator::all();         // the 42 valid indicator identifiers
Indicator::byCategory();  // grouped by trend/oscillator/volatility/volume
```

Indicator identifiers are **case-sensitive**. Mind the naming gotchas: it is
`SAR` (not `Parabolic_SAR`), `Volumes` (not `Tick_Volume`), `WilliamsR_14`,
`ADX_plusDI` / `ADX_minusDI`; `EMA` stops at `EMA_50` while `SMA` goes to
`SMA_200`; there is no `RSI_9` or `EMA_200`.

## Endpoint reference

### Symbols

```php
$client->getSymbols([
    'category' => 'forex',  // or Category::Forex; forex|metals|commodities|indices|crypto|stocks
    'search'   => 'eur',
    'offset'   => 0,
    'limit'    => 100,      // 1..500
]);

$client->getSymbol('EURUSD'); // full contract spec
```

### Quotes

```php
// single real-time quote
$client->getQuote('EURUSD', [
    'include_sources' => true,   // include per-broker sources[]
    // 'source' => 'Equiti Securities',
]);

// batch quotes (1..100 symbols), optional field projection
$client->getQuotes(['EURUSD', 'GBPUSD'], ['bid', 'ask']);
// fields ⊆ ['bid','ask','spread','spread_pips','timestamp'] (default: all)
```

### OHLC & ticks

```php
$client->getOhlc('EURUSD', [
    'timeframe' => 'H1',                    // M1,M5,M15,M30,H1,H4,D1 (default H1)
    'from'      => '2026-05-01T00:00:00Z',
    'to'        => '2026-05-02T00:00:00Z',
    'limit'     => 100,                     // 1..1000
]);

// tick data (plan: pro/enterprise). to - from must be <= 1 hour
$client->getTicks('EURUSD', '2026-05-25T13:00:00Z', '2026-05-25T13:30:00Z');
```

### Indicators

```php
// single value
$client->getIndicator('EURUSD', 'RSI_14', ['timeframe' => 'H1']);

// all indicators for a symbol
$client->getIndicators('EURUSD', [
    'timeframe' => 'H1',
    'category'  => 'oscillator', // trend|oscillator|volatility|volume
]);
$set = $client->getIndicators('EURUSD');
$set->value('RSI_14'); // convenience accessor

// catalogue
$client->listIndicators();

// indicator series (plan: starter+)
$client->getIndicatorHistory('EURUSD', 'RSI_14', [
    'timeframe' => 'H1',
    'from'      => '2026-05-01T00:00:00',
    'to'        => '2026-05-02T00:00:00',
    'limit'     => 500,            // 1..5000
]);

// batch indicators across symbols (historical mode when from/to supplied)
$client->getMulti(['EURUSD', 'GBPUSD'], ['RSI_14', 'SMA_20'], ['timeframe' => 'H1']);

// scan symbols by indicator value.
// note: minVal/maxVal map to the API's min_val/max_val params.
$client->screen('RSI_14', [
    'minVal' => 70,
    'maxVal' => null,
    'sort'   => 'desc',   // asc|desc (default asc)
    'limit'  => 50,       // 1..200
]);
```

### Summary & spread

```php
$client->getSummary('EURUSD', 'H1');             // market-bias summary
$summary = $client->getSummary('EURUSD');
$summary->bias;          // Bias enum: Bullish|Bearish|Neutral
$summary->keyValues['rsi_14'];

$client->getSpread('EURUSD', '24h');             // 1h|24h|7d|30d (default 24h)
$client->compareSpread(['EURUSD', 'GBPUSD', 'USDJPY'], '24h'); // <= 20 symbols
```

### Sessions, heatmap, calendar

```php
$client->getSessions();   // market session clock

$client->getHeatmap([
    'type'      => 'strength',   // strength|correlation (default strength)
    'timeframe' => 'H4',         // H1|H4|D1|W1 (default H4)
    // 'correlations' => true,   // alternative way to force correlation mode
]);

$client->getCalendar([
    'from'       => '2026-06-15',
    'to'         => '2026-06-22',          // range <= 30 days
    'currencies' => ['USD', 'EUR'],        // string or list; 'country' is an alias
    'impact'     => 'high',                // high|medium|low
    'q'          => 'CPI',                 // title search
    // 'next_hours' => 24,                 // 1..168; overrides from/to
    'offset'     => 0,
    'limit'      => 100,                   // 1..500
]);
```

> Calendar `datetime` values are naive UTC with **no** timezone suffix — treat
> them as UTC.

### Account & dashboard layout

```php
$client->getAccount();   // identity & quota: name, plan, prepaid_credits, daily_quota, daily_used
$client->getLayout();    // saved dashboard layout (or null)

// ADVANCED / WRITE — mutates the authenticated user's saved dashboard (<= 60 widgets).
// This is the only write endpoint in the SDK; use deliberately.
$client->saveLayout([
    ['widget' => 'chart', 'symbol' => 'EURUSD'],
]);
```

### Health

```php
$client->health(); // infra probe: { status, components: { redis, postgres } }
```

## Error handling

All errors derive from `TickAtlas\Exception\TickAtlasException`. Structured API
errors are `ApiException` subclasses chosen by HTTP status (and a few error
codes); connectivity failures are `NetworkException`; client misconfiguration is
`ConfigurationException`.

```
TickAtlasException                  (base)
├── ConfigurationException          (missing key, bad option)
├── NetworkException                (no HTTP response: connect/timeout/DNS)
└── ApiException                    (server returned a structured error)
    ├── AuthenticationException     401  MISSING_API_KEY, INVALID_API_KEY
    ├── PermissionDeniedException   403  API_KEY_*, ACCOUNT_*, PERMISSION_DENIED, PLAN_UPGRADE_REQUIRED
    ├── NotFoundException           404  SYMBOL_NOT_FOUND, DATA_NOT_FOUND, INDICATOR_NOT_FOUND
    ├── ValidationException         400 & 422  INVALID_*, RANGE_TOO_LARGE, VALIDATION_ERROR, ...
    ├── RateLimitException          429  RATE_LIMIT_EXCEEDED, QUOTA_EXCEEDED  (carries retryAfter)
    └── ServerException             5xx  INTERNAL_ERROR, SERVICE_UNAVAILABLE
```

`ApiException` exposes the full server context:

```php
use TickAtlas\Exception\{ApiException, NotFoundException, RateLimitException, ValidationException};

try {
    $client->getSymbol('NOPE');
} catch (NotFoundException $e) {
    $e->getStatusCode();   // 404
    $e->getErrorCode();    // 'SYMBOL_NOT_FOUND'  (string error.code)
    $e->getMessage();      // human-readable message
    $e->getDetails();      // extra context, e.g. ['available_symbols' => [...]]
    $e->getRequestId();    // X-Request-ID for support
    $e->getRaw();          // full decoded response body
} catch (ValidationException $e) {
    // 422 VALIDATION_ERROR exposes per-field problems under details['details']
    $e->getDetails()['details'] ?? [];
} catch (RateLimitException $e) {
    $e->getRetryAfter();   // seconds the server asked you to wait
} catch (ApiException $e) {
    // any other structured API error
}
```

> Note: PHP's `Exception::getCode()` is final and returns the integer code, so
> the SDK exposes the string `error.code` via `getErrorCode()` (and the readonly
> `$errorCode` property).

## Retries & rate limiting

The client automatically retries **only** on `429`, `5xx` and network/timeout
errors (all endpoints are read-only/idempotent, except the clearly-marked
`saveLayout`). Defaults: up to 3 retries (4 total attempts), exponential backoff
with full jitter (`base 0.5s`, `cap 30s`). On `429` the `Retry-After` header
(falling back to `X-RateLimit-Reset`) is honoured instead of the computed
backoff. Validation and not-found errors are never retried.

Tune via the constructor options (`maxRetries`, `backoffBase`, `backoffCap`,
`timeout`). Every `/v1` response also carries `X-RateLimit-Limit`,
`X-RateLimit-Remaining`, `X-RateLimit-Reset` and `X-Request-ID` headers — read
them rather than assuming specific plan limits.

## Contributing

```bash
composer install
composer test            # unit + (skipped) integration suites
composer test:unit       # unit suite only (no network)
```

Unit tests use Guzzle's `MockHandler` and never touch the network. The
integration suite is read-only and **gated**: it runs only when both
`RUN_INTEGRATION=1` and `TICKATLAS_API_KEY` are set, and is skipped otherwise.

```bash
RUN_INTEGRATION=1 TICKATLAS_API_KEY=claw_xxx composer test:integration
```

Please keep changes covered by tests and consistent with the typed-model /
typed-exception design.

## License

MIT — see [LICENSE](../LICENSE).
