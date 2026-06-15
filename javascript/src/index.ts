/**
 * tickatlas — official JavaScript/TypeScript SDK for the TickAtlas API.
 *
 * @example
 * ```ts
 * import { TickAtlas } from "tickatlas";
 *
 * const client = new TickAtlas({ apiKey: process.env.TICKATLAS_API_KEY });
 * const quote = await client.getQuote("EURUSD");
 * console.log(quote.bid, quote.ask);
 * ```
 *
 * @packageDocumentation
 */

export { TickAtlas } from "./client.js";
export type { TickAtlasOptions } from "./client.js";

export { SDK_VERSION } from "./http.js";

// --- Errors ---------------------------------------------------------------
export {
  TickAtlasError,
  TickAtlasAPIError,
  AuthenticationError,
  PermissionDeniedError,
  NotFoundError,
  ValidationError,
  RateLimitError,
  ServerError,
  TickAtlasNetworkError,
  TickAtlasConfigError,
} from "./errors.js";
export type { ApiErrorBody, ApiErrorOptions } from "./errors.js";

// --- Constants / enums ----------------------------------------------------
export {
  Timeframes,
  HeatmapTimeframes,
  SymbolCategories,
  SpreadPeriods,
  CalendarImpacts,
  Bias,
  BiasStrengths,
  HeatmapTypes,
  IndicatorCategories,
  Plans,
  SortDirections,
  Indicators,
  IndicatorsByCategory,
  ALL_INDICATORS,
} from "./constants.js";
export type {
  Timeframe,
  HeatmapTimeframe,
  SymbolCategory,
  SpreadPeriod,
  CalendarImpact,
  BiasValue,
  BiasStrength,
  HeatmapType,
  IndicatorCategory,
  Plan,
  SortDirection,
  Indicator,
} from "./constants.js";

// --- Types: request options + response models -----------------------------
export type {
  // shared
  Pagination,
  RateLimitInfo,
  // symbols
  GetSymbolsOptions,
  SymbolListItem,
  SymbolsData,
  TradingHours,
  SymbolDetail,
  // quotes
  GetQuoteOptions,
  QuoteSource,
  QuoteData,
  QuoteField,
  BulkQuoteItem,
  BulkQuotesData,
  // ohlc / ticks
  GetOhlcOptions,
  Candle,
  OHLCData,
  Tick,
  TicksData,
  // indicators
  GetIndicatorOptions,
  IndicatorValue,
  GetIndicatorsOptions,
  OHLCV,
  IndicatorsData,
  IndicatorCatalogue,
  GetIndicatorHistoryOptions,
  IndicatorHistoryPoint,
  IndicatorHistoryData,
  GetMultiOptions,
  MultiRealtimeData,
  MultiHistoricalData,
  MultiData,
  // screener
  ScreenOptions,
  ScreenerResult,
  ScreenerData,
  // summary
  SummarySignals,
  SummaryKeyLevels,
  SummaryKeyValues,
  SummaryData,
  // spread
  SpreadCurrent,
  SpreadStatistics,
  SpreadBySession,
  SpreadData,
  SpreadCompareItem,
  SpreadCompareData,
  // sessions
  SessionState,
  SessionsData,
  // heatmap
  GetHeatmapOptions,
  CurrencyStrength,
  HeatmapStrengthData,
  HeatmapCorrelationData,
  HeatmapData,
  // calendar
  GetCalendarOptions,
  CalendarEvent,
  CalendarData,
  // monitor
  AccountData,
  LayoutData,
  SaveLayoutData,
  // health
  HealthData,
} from "./types.js";
