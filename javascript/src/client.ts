/**
 * The TickAtlas API client.
 *
 * A single class exposing camelCase methods for every one of the 21 `/v1`
 * endpoints (plus the `/health` infra probe). Construction resolves the API key
 * and base URL per SPEC.md §2/§10; each method serialises its parameters,
 * delegates to the retrying {@link request} transport, and returns the typed,
 * unwrapped `data` payload.
 */

import { TickAtlasConfigError } from "./errors.js";
import {
  SDK_VERSION,
  defaultJitter,
  defaultSleep,
  request,
  type QueryParams,
  type TransportConfig,
} from "./http.js";
import type {
  AccountData,
  BulkQuotesData,
  CalendarData,
  GetCalendarOptions,
  GetHeatmapOptions,
  GetIndicatorHistoryOptions,
  GetIndicatorOptions,
  GetIndicatorsOptions,
  GetMultiOptions,
  GetOhlcOptions,
  GetQuoteOptions,
  GetSymbolsOptions,
  HealthData,
  HeatmapData,
  IndicatorCatalogue,
  IndicatorHistoryData,
  IndicatorsData,
  IndicatorValue,
  LayoutData,
  MultiData,
  OHLCData,
  QuoteData,
  QuoteField,
  SaveLayoutData,
  ScreenerData,
  ScreenOptions,
  SpreadCompareData,
  SpreadData,
  SummaryData,
  SymbolDetail,
  SymbolsData,
  TicksData,
} from "./types.js";
import type { Indicator, SpreadPeriod, Timeframe } from "./constants.js";

type Loose<T extends string> = T | (string & {});

/** Options accepted by the {@link TickAtlas} constructor. */
export interface TickAtlasOptions {
  /**
   * API key. If omitted, falls back to `process.env.TICKATLAS_API_KEY`
   * (Node only), then throws {@link TickAtlasConfigError}.
   */
  apiKey?: string;
  /**
   * Base URL. Precedence: this option → `TICKATLAS_BASE_URL` env →
   * `https://tickatlas.com/v1`.
   */
  baseURL?: string;
  /** Per-request timeout in ms. Default 30000. */
  timeout?: number;
  /** Maximum retry attempts for 429/5xx/network. Default 3. */
  maxRetries?: number;
  /** Exponential-backoff base in ms. Default 500. */
  backoffBase?: number;
  /** Backoff cap in ms. Default 30000. */
  backoffCap?: number;
  /** Inject a custom fetch implementation (defaults to global `fetch`). */
  fetch?: typeof fetch;
  /** Inject a deterministic sleep (testing). */
  sleep?: (ms: number) => Promise<void>;
  /** Inject deterministic jitter in [0,1) (testing). */
  jitter?: () => number;
}

const DEFAULT_BASE_URL = "https://tickatlas.com/v1";

/** Safely read an env var without assuming `process` exists (browser-safe). */
function readEnv(name: string): string | undefined {
  if (typeof process !== "undefined" && process?.env) {
    return process.env[name];
  }
  return undefined;
}

/** Detect a Node-like runtime (so we only set `User-Agent` where allowed). */
function isNodeLike(): boolean {
  return (
    typeof process !== "undefined" &&
    !!(process as { versions?: { node?: string } })?.versions?.node
  );
}

/** Join `currencies`/`country` inputs (string | string[]) into a CSV string. */
function csv(value: string | string[] | undefined): string | undefined {
  if (value === undefined) return undefined;
  return Array.isArray(value) ? value.join(",") : value;
}

export class TickAtlas {
  /** SDK version (e.g. for diagnostics). */
  static readonly version = SDK_VERSION;

  private readonly config: TransportConfig;

  constructor(options: TickAtlasOptions = {}) {
    const apiKey = options.apiKey ?? readEnv("TICKATLAS_API_KEY");
    if (!apiKey) {
      throw new TickAtlasConfigError(
        "No TickAtlas API key provided. Pass { apiKey } to the constructor or " +
          "set the TICKATLAS_API_KEY environment variable.",
      );
    }

    const baseURL =
      options.baseURL ?? readEnv("TICKATLAS_BASE_URL") ?? DEFAULT_BASE_URL;

    const fetchImpl = options.fetch ?? globalThis.fetch;
    if (typeof fetchImpl !== "function") {
      throw new TickAtlasConfigError(
        "Global `fetch` is not available in this runtime. Use Node 18+ or a " +
          "modern browser, or pass a `fetch` implementation in the options.",
      );
    }

    this.config = {
      apiKey,
      baseURL,
      timeout: options.timeout ?? 30000,
      maxRetries: options.maxRetries ?? 3,
      backoffBase: options.backoffBase ?? 500,
      backoffCap: options.backoffCap ?? 30000,
      fetch: fetchImpl,
      sleep: options.sleep ?? defaultSleep,
      jitter: options.jitter ?? defaultJitter,
      sendUserAgent: isNodeLike(),
    };
  }

  // =========================================================================
  // Symbols
  // =========================================================================

  /** 7.1 `GET /symbols` — list symbols (paginated). */
  getSymbols(opts: GetSymbolsOptions = {}): Promise<SymbolsData> {
    const query: QueryParams = {
      category: opts.category,
      search: opts.search,
      offset: opts.offset,
      limit: opts.limit,
    };
    return request<SymbolsData>(this.config, {
      method: "GET",
      path: "/symbols",
      query,
    });
  }

  /** 7.2 `GET /symbols/{symbol}` — symbol contract spec. */
  getSymbol(symbol: string): Promise<SymbolDetail> {
    return request<SymbolDetail>(this.config, {
      method: "GET",
      path: `/symbols/${encodeURIComponent(symbol)}`,
    });
  }

  // =========================================================================
  // Quotes
  // =========================================================================

  /** 7.3 `GET /quote` — single real-time quote. */
  getQuote(symbol: string, opts: GetQuoteOptions = {}): Promise<QuoteData> {
    const query: QueryParams = {
      symbol,
      include_sources: opts.includeSources,
      source: opts.source,
    };
    return request<QuoteData>(this.config, {
      method: "GET",
      path: "/quote",
      query,
    });
  }

  /**
   * 7.4 `POST /quotes` — batch quotes (1..100 symbols).
   * `fields` ⊆ ["bid","ask","spread","spread_pips","timestamp"] (default all).
   */
  getQuotes(
    symbols: string[],
    fields?: QuoteField[],
  ): Promise<BulkQuotesData> {
    const body: { symbols: string[]; fields?: QuoteField[] } = { symbols };
    if (fields) body.fields = fields;
    return request<BulkQuotesData>(this.config, {
      method: "POST",
      path: "/quotes",
      body,
    });
  }

  // =========================================================================
  // OHLC / Ticks
  // =========================================================================

  /** 7.5 `GET /ohlc` — OHLC candles. */
  getOhlc(symbol: string, opts: GetOhlcOptions = {}): Promise<OHLCData> {
    const query: QueryParams = {
      symbol,
      timeframe: opts.timeframe,
      from: opts.from,
      to: opts.to,
      limit: opts.limit,
    };
    return request<OHLCData>(this.config, {
      method: "GET",
      path: "/ohlc",
      query,
    });
  }

  /**
   * 7.6 `GET /ticks` — tick data (plan: pro/enterprise).
   * `from`/`to` are required ISO 8601; range must be ≤ 1 hour.
   */
  getTicks(symbol: string, from: string, to: string): Promise<TicksData> {
    return request<TicksData>(this.config, {
      method: "GET",
      path: "/ticks",
      query: { symbol, from, to },
    });
  }

  // =========================================================================
  // Indicators
  // =========================================================================

  /** 7.7 `GET /indicator` — single indicator value. */
  getIndicator(
    symbol: string,
    indicator: Loose<Indicator>,
    opts: GetIndicatorOptions = {},
  ): Promise<IndicatorValue> {
    const query: QueryParams = {
      symbol,
      indicator,
      timeframe: opts.timeframe,
      source: opts.source,
    };
    return request<IndicatorValue>(this.config, {
      method: "GET",
      path: "/indicator",
      query,
    });
  }

  /** 7.8 `GET /indicators` — all indicators for a symbol. */
  getIndicators(
    symbol: string,
    opts: GetIndicatorsOptions = {},
  ): Promise<IndicatorsData> {
    const query: QueryParams = {
      symbol,
      timeframe: opts.timeframe,
      category: opts.category,
    };
    return request<IndicatorsData>(this.config, {
      method: "GET",
      path: "/indicators",
      query,
    });
  }

  /** 7.9 `GET /indicators/list` — indicator catalogue. */
  listIndicators(): Promise<IndicatorCatalogue> {
    return request<IndicatorCatalogue>(this.config, {
      method: "GET",
      path: "/indicators/list",
    });
  }

  /**
   * 7.10 `GET /indicator/history` — indicator series (plan: starter+).
   */
  getIndicatorHistory(
    symbol: string,
    indicator: Loose<Indicator>,
    opts: GetIndicatorHistoryOptions = {},
  ): Promise<IndicatorHistoryData> {
    const query: QueryParams = {
      symbol,
      indicator,
      timeframe: opts.timeframe,
      from: opts.from,
      to: opts.to,
      limit: opts.limit,
    };
    return request<IndicatorHistoryData>(this.config, {
      method: "GET",
      path: "/indicator/history",
      query,
    });
  }

  /**
   * 7.11 `GET /multi` — batch indicators across symbols. Supplying `from`
   * switches the server into historical mode (plan: starter+).
   */
  getMulti(
    symbols: string[],
    indicators: Array<Loose<Indicator>>,
    opts: GetMultiOptions = {},
  ): Promise<MultiData> {
    const query: QueryParams = {
      symbols: symbols.join(","),
      indicators: indicators.join(","),
      timeframe: opts.timeframe,
      from: opts.from,
      to: opts.to,
    };
    return request<MultiData>(this.config, {
      method: "GET",
      path: "/multi",
      query,
    });
  }

  // =========================================================================
  // Screener
  // =========================================================================

  /**
   * 7.12 `GET /screener` — scan symbols by indicator.
   * Note: `minVal`/`maxVal` serialise to `min_val`/`max_val` (the docs' `min`/
   * `max` are silently ignored by the API — see SPEC §12 F2).
   */
  screen(
    indicator: Loose<Indicator>,
    opts: ScreenOptions = {},
  ): Promise<ScreenerData> {
    const query: QueryParams = {
      indicator,
      timeframe: opts.timeframe,
      min_val: opts.minVal,
      max_val: opts.maxVal,
      sort: opts.sort,
      offset: opts.offset,
      limit: opts.limit,
    };
    return request<ScreenerData>(this.config, {
      method: "GET",
      path: "/screener",
      query,
    });
  }

  // =========================================================================
  // Summary
  // =========================================================================

  /** 7.13 `GET /summary` — market-bias summary. */
  getSummary(
    symbol: string,
    timeframe?: Loose<Timeframe>,
  ): Promise<SummaryData> {
    return request<SummaryData>(this.config, {
      method: "GET",
      path: "/summary",
      query: { symbol, timeframe },
    });
  }

  // =========================================================================
  // Spread
  // =========================================================================

  /** 7.14 `GET /spread` — spread statistics. */
  getSpread(
    symbol: string,
    period?: Loose<SpreadPeriod>,
  ): Promise<SpreadData> {
    return request<SpreadData>(this.config, {
      method: "GET",
      path: "/spread",
      query: { symbol, period },
    });
  }

  /** 7.15 `GET /spread/compare` — compare spread across symbols (≤20). */
  compareSpread(
    symbols: string[],
    period?: Loose<SpreadPeriod>,
  ): Promise<SpreadCompareData> {
    return request<SpreadCompareData>(this.config, {
      method: "GET",
      path: "/spread/compare",
      query: { symbols: symbols.join(","), period },
    });
  }

  // =========================================================================
  // Sessions / Heatmap / Calendar
  // =========================================================================

  /** 7.16 `GET /sessions` — market session clock. */
  getSessions(): Promise<import("./types.js").SessionsData> {
    return request(this.config, { method: "GET", path: "/sessions" });
  }

  /** 7.17 `GET /heatmap` — currency strength / correlation. */
  getHeatmap(opts: GetHeatmapOptions = {}): Promise<HeatmapData> {
    const query: QueryParams = {
      type: opts.type,
      timeframe: opts.timeframe,
      correlations: opts.correlations,
    };
    return request<HeatmapData>(this.config, {
      method: "GET",
      path: "/heatmap",
      query,
    });
  }

  /** 7.18 `GET /calendar` — economic calendar. */
  getCalendar(opts: GetCalendarOptions = {}): Promise<CalendarData> {
    const query: QueryParams = {
      from: opts.from,
      to: opts.to,
      currencies: csv(opts.currencies),
      country: csv(opts.country),
      impact: opts.impact,
      q: opts.q,
      next_hours: opts.nextHours,
      offset: opts.offset,
      limit: opts.limit,
    };
    return request<CalendarData>(this.config, {
      method: "GET",
      path: "/calendar",
      query,
    });
  }

  // =========================================================================
  // Monitor (account / layout)
  // =========================================================================

  /** 7.19 `GET /monitor/account` — account identity & quota. */
  getAccount(): Promise<AccountData> {
    return request<AccountData>(this.config, {
      method: "GET",
      path: "/monitor/account",
    });
  }

  /** 7.20 `GET /monitor/layout` — saved dashboard layout. */
  getLayout(): Promise<LayoutData> {
    return request<LayoutData>(this.config, {
      method: "GET",
      path: "/monitor/layout",
    });
  }

  /**
   * 7.21 `PUT /monitor/layout` — save dashboard layout (≤60 widgets).
   *
   * ADVANCED / WRITE: this is the only mutating endpoint in the SDK. It
   * overwrites the user's saved dashboard layout for this API key. Use with care.
   */
  saveLayout(layout: unknown[]): Promise<SaveLayoutData> {
    return request<SaveLayoutData>(this.config, {
      method: "PUT",
      path: "/monitor/layout",
      body: { layout },
    });
  }

  // =========================================================================
  // Infra probe
  // =========================================================================

  /** `GET /health` — service health probe (no API key required server-side). */
  health(): Promise<HealthData> {
    return request<HealthData>(this.config, {
      method: "GET",
      path: "/health",
      root: true,
    });
  }
}
