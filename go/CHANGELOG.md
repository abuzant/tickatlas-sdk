# Changelog

All notable changes to the `tickatlas` Go SDK are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-06-15

Initial public release.

### Added

- `Client` with a functional-options constructor `NewClient(opts ...Option)`:
  `WithAPIKey`, `WithBaseURL`, `WithHTTPClient`, `WithMaxRetries`, `WithTimeout`,
  `WithUserAgent`.
- Coverage of all 21 `/v1` API-key endpoints plus the `/health` infra probe:
  - Symbols: `Symbols`, `Symbol`
  - Quotes: `Quote`, `Quotes`
  - History: `OHLC`, `Ticks`
  - Indicators: `Indicator`, `Indicators`, `ListIndicators`,
    `IndicatorHistory`, `Multi`, `Screen`, `Summary`
  - Spread: `Spread`, `CompareSpread`
  - Markets: `Sessions`, `Heatmap`, `Calendar`
  - Account/monitor: `Account`, `Layout`, `SaveLayout` (write)
  - Infra: `Health`
- Typed response models for every endpoint, with nullable fields modelled as
  pointers and forward-compatible decoding that tolerates unknown JSON fields.
  `MultiResult` exposes `RealTime()` / `Historical()` helpers for its two modes.
- Typed error hierarchy with `errors.As` support and predicate helpers:
  `APIError` (base) plus `AuthenticationError`, `PermissionDeniedError`,
  `NotFoundError`, `ValidationError`, `RateLimitError`, `ServerError`, and the
  transport-level `NetworkError`. Predicates: `IsAuth`, `IsPermissionDenied`,
  `IsNotFound`, `IsValidation`, `IsRateLimit`, `IsServer`, `IsNetwork`,
  `IsAPIError`. `RateLimitError.RetryAfter` carries the server-advised delay;
  `APIError` exposes `StatusCode`, `Code`, `Message`, `Details`, `RequestID` and
  the raw error body.
- Configurable retry policy: retries on 429/5xx/network only, exponential backoff
  with full jitter, honours `Retry-After` (then `reset_in_seconds`, then
  `X-RateLimit-Reset`) on 429, and respects `context.Context` cancellation during
  backoff sleeps. The sleep function and RNG are injectable for deterministic
  tests.
- Exported constants for timeframes, heatmap timeframes, categories, spread
  periods, calendar impact, bias values, heatmap types, account plans, and the
  full 42-indicator catalogue, plus `AllIndicators()`. Raw strings are accepted
  everywhere.
- API-key resolution from `WithAPIKey` then the `TICKATLAS_API_KEY` environment
  variable (error if absent); base URL from `WithBaseURL`, then
  `TICKATLAS_BASE_URL`, then the production default.
- Standard-library-only implementation (no external dependencies); Go 1.21+.
- Unit tests with `httptest` for every method (success decoding, typed-error
  mapping, and 429 retry honouring `Retry-After`), plus an environment-gated,
  build-tagged, read-only integration test suite.

### Notes

- The WebSocket quote stream is **out of scope** for `0.1.0` and tracked as a
  future addition.
- `SaveLayout` is the only write method; it is documented as advanced and is
  excluded from automated write-path integration tests.

[0.1.0]: https://github.com/tickatlas/tickatlas-sdk/releases/tag/go-v0.1.0
