# Changelog

All notable changes to the `tickatlas` JavaScript/TypeScript SDK are documented
here. This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
and [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.0] - 2026-06-15

Initial public release. Built against TickAtlas API `v1` (app `1.0.0`) per the
authoritative SDK contract (`SPEC.md`).

### Added

- `TickAtlas` client class covering all **21** `/v1` endpoints plus the
  `/health` infra probe:
  - Symbols: `getSymbols`, `getSymbol`
  - Quotes: `getQuote`, `getQuotes`
  - History: `getOhlc`, `getTicks`
  - Indicators: `getIndicator`, `getIndicators`, `listIndicators`,
    `getIndicatorHistory`, `getMulti`
  - Screener: `screen`
  - Analytics: `getSummary`, `getSpread`, `compareSpread`, `getSessions`,
    `getHeatmap`, `getCalendar`
  - Account: `getAccount`, `getLayout`, `saveLayout` (write)
  - Infra: `health`
- Full TypeScript types for every request parameter object and response model.
- Typed exception hierarchy: `TickAtlasError`, `TickAtlasAPIError`,
  `AuthenticationError`, `PermissionDeniedError`, `NotFoundError`,
  `ValidationError`, `RateLimitError`, `ServerError`, `TickAtlasNetworkError`,
  and `TickAtlasConfigError`, with HTTP-status + `error.code` mapping.
- `as const` enums/catalogues for autocomplete: `Timeframes`,
  `HeatmapTimeframes`, `SymbolCategories`, `SpreadPeriods`, `CalendarImpacts`,
  `Bias`, `BiasStrengths`, `HeatmapTypes`, `IndicatorCategories`, `Plans`,
  `SortDirections`, the full 42-id `Indicators` catalogue,
  `IndicatorsByCategory`, and `ALL_INDICATORS`. Methods also accept raw strings.
- Automatic retries for `429`/`5xx`/network errors with exponential backoff and
  full jitter; honours `Retry-After` (then `X-RateLimit-Reset`,
  `reset_in_seconds`) on `429`.
- Request timeouts via `AbortController` (default 30s); configurable `timeout`,
  `maxRetries`, `backoffBase`, `backoffCap`, and an injectable `fetch`.
- API-key resolution from an explicit option or `TICKATLAS_API_KEY`; base URL
  from option, `TICKATLAS_BASE_URL`, or the production default. Browser-safe
  `process` guarding; `User-Agent` set on Node only.
- Zero runtime dependencies (platform `fetch`); dual **ESM + CJS** build with
  `.d.ts` declarations and an `exports` map. Targets Node 18+ and browsers.
- Unit tests (vitest) with a mocked `fetch` covering success parsing for every
  method, error→exception mapping, and the retry/`Retry-After` behaviour; plus a
  gated, read-only live integration suite.

### Notes

- The WebSocket quote stream is **not** part of `0.1.0` and is tracked for a
  future release.
- `saveLayout` (`PUT /monitor/layout`) is the only mutating method and is
  documented as advanced/optional.

[0.1.0]: https://github.com/tickatlas/tickatlas-sdk/releases/tag/js-v0.1.0
