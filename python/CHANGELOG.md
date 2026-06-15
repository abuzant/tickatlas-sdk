# Changelog

All notable changes to the `tickatlas` Python SDK are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-06-15

Initial public release.

### Added

- Synchronous client `TickAtlas` and asynchronous client `AsyncTickAtlas`
  (built on `httpx`), sharing all request/retry/parse logic.
- Coverage of all 21 `/v1` API-key endpoints plus the `/health` infra probe:
  - Symbols: `get_symbols`, `get_symbol`
  - Quotes: `get_quote`, `get_quotes`
  - History: `get_ohlc`, `get_ticks`
  - Indicators: `get_indicator`, `get_indicators`, `list_indicators`,
    `get_indicator_history`, `get_multi`, `screen`, `get_summary`
  - Spread: `get_spread`, `compare_spread`
  - Markets: `get_sessions`, `get_heatmap`, `get_calendar`
  - Account/monitor: `get_account`, `get_layout`, `save_layout` (write)
  - Infra: `health`
- Frozen-dataclass response models for every endpoint, each preserving the raw
  payload via `.raw` and tolerating unknown fields for forward-compatibility.
- Typed exception hierarchy (`TickAtlasError`, `TickAtlasAPIError`,
  `AuthenticationError`, `PermissionDeniedError`, `NotFoundError`,
  `ValidationError`, `RateLimitError`, `ServerError`, `TickAtlasNetworkError`,
  plus the local `TickAtlasConfigError`) with status + `error.code` mapping.
- Configurable retry policy: retries on 429/5xx/network only, exponential backoff
  with full jitter, and honours `Retry-After` on 429. Jitter/RNG and the sleep
  function are injectable for deterministic testing.
- `Timeframe`, `HeatmapTimeframe`, `Category`, `SpreadPeriod`, `Impact`,
  `HeatmapType`, `Bias`, `BiasStrength`, `Plan` enums and an `Indicators`
  namespace covering the full 42-indicator catalogue; raw strings are also
  accepted everywhere.
- API-key resolution from the explicit `api_key=` argument then the
  `TICKATLAS_API_KEY` environment variable; base URL from `base_url=`, then
  `TICKATLAS_BASE_URL`, then the production default.
- `py.typed` marker; fully type-hinted and mypy-clean.

### Notes

- The WebSocket quote stream is **out of scope** for `0.1.0` and tracked as a
  future addition.
- `save_layout` is the only write method; it is documented as advanced and is
  excluded from automated write-path integration tests.

[0.1.0]: https://github.com/tickatlas/tickatlas-sdk/releases/tag/python-v0.1.0
