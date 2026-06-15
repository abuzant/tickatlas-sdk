/**
 * Request-parameter objects and response models for every TickAtlas endpoint.
 *
 * Response models mirror the `data` payloads from SPEC.md §7 (the SDK unwraps
 * the `{ success, data }` envelope and returns the typed `data`). All models
 * tolerate unknown extra keys via index signatures where the API is explicitly
 * forward-compatible; nullable fields use `| null` per the spec.
 */

import type {
  BiasStrength,
  BiasValue,
  CalendarImpact,
  HeatmapTimeframe,
  HeatmapType,
  Indicator,
  IndicatorCategory,
  Plan,
  SortDirection,
  SpreadPeriod,
  SymbolCategory,
  Timeframe,
} from "./constants.js";

/** A value that is accepted both as a typed enum member and as a raw string. */
type Loose<T extends string> = T | (string & {});

// ---------------------------------------------------------------------------
// Shared
// ---------------------------------------------------------------------------

/** Standard offset/limit pagination block. */
export interface Pagination {
  offset: number;
  limit: number;
  total: number;
  has_more: boolean;
}

// ---------------------------------------------------------------------------
// 7.1 GET /symbols
// ---------------------------------------------------------------------------

export interface GetSymbolsOptions {
  category?: Loose<SymbolCategory>;
  search?: string;
  offset?: number;
  limit?: number;
}

export interface SymbolListItem {
  symbol: string;
  name: string | null;
  category: string;
  base_currency: string | null;
  quote_currency: string | null;
  digits: number;
  tradable: boolean;
}

export interface SymbolsData {
  symbols: SymbolListItem[];
  total: number;
  pagination: Pagination;
}

// ---------------------------------------------------------------------------
// 7.2 GET /symbols/{symbol}
// ---------------------------------------------------------------------------

export interface TradingHours {
  sunday: string;
  monday: string;
  tuesday: string;
  wednesday: string;
  thursday: string;
  friday: string;
  saturday: string;
  [day: string]: string;
}

export interface SymbolDetail {
  symbol: string;
  name: string | null;
  category: string;
  description: string | null;
  base_currency: string | null;
  quote_currency: string | null;
  digits: number;
  point: number;
  contract_size: number;
  min_volume: number;
  max_volume: number;
  volume_step: number;
  swap_long: number | null;
  swap_short: number | null;
  margin_currency: string | null;
  trading_hours: TradingHours;
}

// ---------------------------------------------------------------------------
// 7.3 GET /quote
// ---------------------------------------------------------------------------

export interface GetQuoteOptions {
  /** Include per-broker `sources[]`. */
  includeSources?: boolean;
  /** Force a specific broker source (debug). */
  source?: string;
}

export interface QuoteSource {
  broker: string;
  bid: number;
  ask: number;
  spread: number;
  updated: string;
}

export interface QuoteData {
  symbol: string;
  bid: number | null;
  ask: number | null;
  spread: number;
  spread_pips: number | null;
  timestamp: string;
  source?: string;
  best_bid?: number | null;
  best_ask?: number | null;
  best_spread?: number | null;
  source_count?: number;
  sources?: QuoteSource[];
}

// ---------------------------------------------------------------------------
// 7.4 POST /quotes
// ---------------------------------------------------------------------------

/** Fields selectable on the batch-quotes endpoint. */
export type QuoteField =
  | "bid"
  | "ask"
  | "spread"
  | "spread_pips"
  | "timestamp";

export interface BulkQuoteItem {
  symbol: string;
  bid?: number | null;
  ask?: number | null;
  spread?: number | null;
  spread_pips?: number | null;
  timestamp?: string;
}

export interface BulkQuotesData {
  quotes: BulkQuoteItem[];
  count: number;
  not_found: string[] | null;
  timestamp: string;
}

// ---------------------------------------------------------------------------
// 7.5 GET /ohlc
// ---------------------------------------------------------------------------

export interface GetOhlcOptions {
  timeframe?: Loose<Timeframe>;
  /** ISO 8601 start; defaults server-side to retention start. */
  from?: string;
  /** ISO 8601 end; defaults to now. */
  to?: string;
  /** 1..1000, default 100. */
  limit?: number;
}

export interface Candle {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface OHLCData {
  symbol: string;
  timeframe: string;
  candles: Candle[];
  count: number;
  retention: string | null;
}

// ---------------------------------------------------------------------------
// 7.6 GET /ticks
// ---------------------------------------------------------------------------

export interface Tick {
  time: string;
  bid: number;
  ask: number;
  flags: number;
}

export interface TicksData {
  symbol: string;
  ticks: Tick[];
  count: number;
}

// ---------------------------------------------------------------------------
// 7.7 GET /indicator
// ---------------------------------------------------------------------------

export interface GetIndicatorOptions {
  timeframe?: Loose<Timeframe>;
  /** Force a broker source. */
  source?: string;
}

export interface IndicatorValue {
  symbol: string;
  timeframe: string;
  indicator: string;
  value: number | null;
  bid: number | null;
  ask: number | null;
  updated_at: number;
  server_time: string | null;
}

// ---------------------------------------------------------------------------
// 7.8 GET /indicators
// ---------------------------------------------------------------------------

export interface GetIndicatorsOptions {
  timeframe?: Loose<Timeframe>;
  category?: Loose<IndicatorCategory>;
}

export interface OHLCV {
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface IndicatorsData {
  symbol: string;
  timeframe: string;
  ohlcv: OHLCV | null;
  bid: number | null;
  ask: number | null;
  indicators: Record<string, number | null>;
  count: number;
  updated_at: number;
}

// ---------------------------------------------------------------------------
// 7.9 GET /indicators/list
// ---------------------------------------------------------------------------

export interface IndicatorCatalogue {
  indicators: Record<string, Record<string, string>>;
  timeframes: string[];
  categories: string[];
}

// ---------------------------------------------------------------------------
// 7.10 GET /indicator/history
// ---------------------------------------------------------------------------

export interface GetIndicatorHistoryOptions {
  timeframe?: Loose<Timeframe>;
  /** ISO 8601 start; defaults to `to − max_window`. */
  from?: string;
  /** ISO 8601 end; defaults to now. */
  to?: string;
  /** 1..5000, default 500 (also capped per-timeframe). */
  limit?: number;
}

export interface IndicatorHistoryPoint {
  time: string;
  value: number | null;
}

export interface IndicatorHistoryData {
  symbol: string;
  indicator: string;
  timeframe: string;
  from: string | null;
  to: string | null;
  count: number;
  max_window_hours: number | null;
  series: IndicatorHistoryPoint[];
}

// ---------------------------------------------------------------------------
// 7.11 GET /multi
// ---------------------------------------------------------------------------

export interface GetMultiOptions {
  timeframe?: Loose<Timeframe>;
  /** ISO 8601 start; its presence switches the endpoint to historical mode. */
  from?: string;
  /** ISO 8601 end (historical mode). */
  to?: string;
}

/** Real-time response shape (no `from`/`to` supplied). */
export interface MultiRealtimeData {
  timeframe: string;
  data: Record<string, Record<string, number | null>>;
  not_found: string[] | null;
  updated_at: number;
  mode?: undefined;
}

/** Historical response shape (returned when `from` is supplied). */
export interface MultiHistoricalData {
  timeframe: string;
  mode: "historical";
  from: string;
  to: string;
  data: Record<
    string,
    Array<{ time: string } & Record<string, number | null | string>>
  >;
  not_found: string[] | null;
}

export type MultiData = MultiRealtimeData | MultiHistoricalData;

// ---------------------------------------------------------------------------
// 7.12 GET /screener
// ---------------------------------------------------------------------------

export interface ScreenOptions {
  /** Not validated server-side; still sent through. */
  timeframe?: Loose<Timeframe>;
  /** Inclusive lower bound. Serialised to `min_val`. */
  minVal?: number;
  /** Inclusive upper bound. Serialised to `max_val`. */
  maxVal?: number;
  /** `asc` (default) or `desc`. */
  sort?: Loose<SortDirection>;
  /** `≥ 0`, default 0. */
  offset?: number;
  /** 1..200, default 50. */
  limit?: number;
}

export interface ScreenerResult {
  symbol: string;
  value: number | null;
  bid: number | null;
}

export interface ScreenerData {
  indicator: string;
  timeframe: string;
  filter: { min: number | null; max: number | null };
  results: ScreenerResult[];
  total_matches: number;
  pagination: Pagination;
  updated_at: number;
}

// ---------------------------------------------------------------------------
// 7.13 GET /summary
// ---------------------------------------------------------------------------

export interface SummarySignals {
  trend: string;
  momentum: string;
  volatility: string;
  volume: string;
  [key: string]: string;
}

export interface SummaryKeyLevels {
  resistance: number[];
  support: number[];
}

export interface SummaryKeyValues {
  bid: number | null;
  ask: number | null;
  rsi_14: number | null;
  macd_hist: number | null;
  adx: number | null;
  atr_14: number | null;
  sma_20: number | null;
  sma_50: number | null;
  sma_200: number | null;
  bb_upper: number | null;
  bb_lower: number | null;
  stochastic_k: number | null;
  mfi_14: number | null;
  [key: string]: number | null;
}

export interface SummaryData {
  symbol: string;
  timeframe: string;
  bias: BiasValue;
  bias_strength: BiasStrength;
  confidence: number;
  trend_score: number;
  momentum_score: number;
  volatility_score: number;
  signals: SummarySignals;
  key_levels: SummaryKeyLevels;
  bullish_signals: string[];
  bearish_signals: string[];
  neutral_signals: string[];
  volatility_info: string[];
  volume_info: string[];
  summary: string;
  recommendations: string[];
  key_values: SummaryKeyValues;
  updated_at: number;
}

// ---------------------------------------------------------------------------
// 7.14 GET /spread
// ---------------------------------------------------------------------------

export interface SpreadCurrent {
  spread_pips: number;
  spread_points: number;
}

export interface SpreadStatistics {
  period: string;
  avg_spread: number;
  min_spread: number;
  max_spread: number;
  std_deviation: number;
}

export interface SpreadBySession {
  asian: number | null;
  london: number | null;
  new_york: number | null;
}

export interface SpreadData {
  symbol: string;
  current: SpreadCurrent;
  statistics: SpreadStatistics;
  by_session: SpreadBySession;
}

// ---------------------------------------------------------------------------
// 7.15 GET /spread/compare
// ---------------------------------------------------------------------------

export interface SpreadCompareItem {
  symbol: string;
  current_pips: number | null;
  avg_pips: number | null;
  min_pips: number | null;
  max_pips: number | null;
  has_live_data: boolean;
}

export interface SpreadCompareData {
  period: string;
  symbols: SpreadCompareItem[];
  count: number;
}

// ---------------------------------------------------------------------------
// 7.16 GET /sessions
// ---------------------------------------------------------------------------

export interface SessionState {
  status: "open" | "closed";
  closes_in?: string;
  opens_in?: string;
  weekend?: boolean;
  [key: string]: unknown;
}

export interface SessionsData {
  current_time: string;
  active_sessions: string[];
  sessions: {
    sydney: SessionState;
    tokyo: SessionState;
    london: SessionState;
    new_york: SessionState;
    [name: string]: SessionState;
  };
  overlaps: string[];
  next_major_event: { event: string; in: string } | null;
}

// ---------------------------------------------------------------------------
// 7.17 GET /heatmap
// ---------------------------------------------------------------------------

export interface GetHeatmapOptions {
  type?: Loose<HeatmapType>;
  timeframe?: Loose<HeatmapTimeframe>;
  /** `true` forces correlation mode (alternative to `type: "correlation"`). */
  correlations?: boolean;
}

export interface CurrencyStrength {
  strength: number;
  trend: BiasValue;
  change: number;
  pairs_analyzed: number;
}

export interface HeatmapStrengthData {
  type: "strength";
  timeframe: string;
  currencies: Record<string, CurrencyStrength>;
  strongest: string | null;
  weakest: string | null;
  range: number;
  timestamp: string;
}

export interface HeatmapCorrelationData {
  type: "correlation";
  timeframe: string;
  correlation_matrix: Record<string, Record<string, number>>;
  available: boolean;
  message?: string;
  timestamp: string;
}

export type HeatmapData = HeatmapStrengthData | HeatmapCorrelationData;

// ---------------------------------------------------------------------------
// 7.18 GET /calendar
// ---------------------------------------------------------------------------

export interface GetCalendarOptions {
  /** Date/ISO; default today 00:00 UTC. */
  from?: string;
  /** Date/ISO; default from+7d; range ≤ 30 days. */
  to?: string;
  /** Comma-separated list, or string[] — e.g. ["USD","EUR"]. */
  currencies?: string | string[];
  /** Alias of `currencies`. */
  country?: string | string[];
  impact?: Loose<CalendarImpact>;
  /** Title search, ≤100 chars. */
  q?: string;
  /** 1..168; overrides from/to. */
  nextHours?: number;
  offset?: number;
  limit?: number;
}

export interface CalendarEvent {
  id: string;
  /** ISO, naive-UTC, no suffix — treat as UTC. */
  datetime: string;
  currency: string;
  event: string;
  impact: string;
  forecast: string | null;
  previous: string | null;
  actual: string | null;
}

export interface CalendarData {
  events: CalendarEvent[];
  count: number;
  pagination: Pagination;
  range: { from: string; to: string };
}

// ---------------------------------------------------------------------------
// 7.19 GET /monitor/account
// ---------------------------------------------------------------------------

export interface AccountData {
  name: string;
  plan: Plan | string;
  prepaid_credits: number;
  /** `null` means unlimited. */
  daily_quota: number | null;
  daily_used: number;
}

// ---------------------------------------------------------------------------
// 7.20 / 7.21 GET & PUT /monitor/layout
// ---------------------------------------------------------------------------

export interface LayoutData {
  layout: unknown[] | null;
}

export interface SaveLayoutData {
  saved: true;
}

// ---------------------------------------------------------------------------
// Infra probe: GET /health
// ---------------------------------------------------------------------------

export interface HealthData {
  status: string;
  components: {
    redis?: string;
    postgres?: string;
    [component: string]: unknown;
  };
  [key: string]: unknown;
}

// ---------------------------------------------------------------------------
// Rate-limit metadata (parsed from response headers)
// ---------------------------------------------------------------------------

export interface RateLimitInfo {
  limit: number | null;
  remaining: number | null;
  reset: number | null;
  requestId: string | null;
}
