# Changelog

All notable changes to `tickatlas/php-sdk` are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-06-15

Initial release.

### Added

- `TickAtlas\Client` covering all 21 `/v1` API-key endpoints plus the `/health`
  infrastructure probe:
  - Symbols: `getSymbols`, `getSymbol`
  - Quotes: `getQuote`, `getQuotes` (batch, POST)
  - History: `getOhlc`, `getTicks`
  - Indicators: `getIndicator`, `getIndicators`, `listIndicators`,
    `getIndicatorHistory`, `getMulti`, `screen`
  - Analysis: `getSummary`, `getSpread`, `compareSpread`
  - Market: `getSessions`, `getHeatmap`, `getCalendar`
  - Account/monitor: `getAccount`, `getLayout`, `saveLayout` (write)
  - Infra: `health`
- Strongly-typed, `readonly` response models for every endpoint, each retaining
  the raw payload (`toArray()` / `raw()` / `get()`) and tolerating unknown keys.
- Backed enums: `Timeframe`, `HeatmapTimeframe`, `Period`, `Impact`,
  `HeatmapType`, `Bias`, `Category`, `IndicatorCategory`, and `Indicator` (the
  42-indicator catalogue). All client methods also accept raw strings.
- Typed exception hierarchy (`TickAtlasException` base; `ApiException` with
  `AuthenticationException`, `PermissionDeniedException`, `NotFoundException`,
  `ValidationException`, `RateLimitException`, `ServerException`;
  `NetworkException`; `ConfigurationException`).
- Guzzle-based transport with the standard success/error envelope handling,
  `X-API-Key` auth, and configurable retry policy (429/5xx/network only,
  exponential backoff with full jitter, honours `Retry-After`).
- API key/base URL resolution from constructor args or the `TICKATLAS_API_KEY` /
  `TICKATLAS_BASE_URL` environment variables.
- Full PHPUnit unit-test suite (Guzzle `MockHandler`, no network) and a gated,
  read-only integration test suite.

[0.1.0]: https://github.com/tickatlas/php-sdk/releases/tag/v0.1.0
