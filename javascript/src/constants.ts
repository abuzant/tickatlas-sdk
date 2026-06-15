/**
 * Enums & constant catalogues for the TickAtlas API.
 *
 * Every constant object below is exported `as const` so that, in TypeScript,
 * the union of its values is available as a type (see the companion type
 * aliases). All methods that accept these values also accept raw strings, so
 * these objects exist purely for discoverability / autocomplete.
 *
 * Source of truth: SPEC.md §6 ("Common enums & constants").
 */

/**
 * Bar timeframes accepted by the indicator / indicators / summary / ohlc /
 * multi / history / screener endpoints. Default everywhere is `H1`.
 */
export const Timeframes = {
  M1: "M1",
  M5: "M5",
  M15: "M15",
  M30: "M30",
  H1: "H1",
  H4: "H4",
  D1: "D1",
} as const;
export type Timeframe = (typeof Timeframes)[keyof typeof Timeframes];

/**
 * Timeframes accepted by the heatmap endpoint (note: different set — no
 * intraday below H1, adds W1). Default is `H4`.
 */
export const HeatmapTimeframes = {
  H1: "H1",
  H4: "H4",
  D1: "D1",
  W1: "W1",
} as const;
export type HeatmapTimeframe =
  (typeof HeatmapTimeframes)[keyof typeof HeatmapTimeframes];

/** Symbol categories. */
export const SymbolCategories = {
  forex: "forex",
  metals: "metals",
  commodities: "commodities",
  indices: "indices",
  crypto: "crypto",
  stocks: "stocks",
} as const;
export type SymbolCategory =
  (typeof SymbolCategories)[keyof typeof SymbolCategories];

/** Spread statistic periods. Default is `24h`. */
export const SpreadPeriods = {
  "1h": "1h",
  "24h": "24h",
  "7d": "7d",
  "30d": "30d",
} as const;
export type SpreadPeriod = (typeof SpreadPeriods)[keyof typeof SpreadPeriods];

/** Economic-calendar impact levels. */
export const CalendarImpacts = {
  high: "high",
  medium: "medium",
  low: "low",
} as const;
export type CalendarImpact =
  (typeof CalendarImpacts)[keyof typeof CalendarImpacts];

/** Summary market-bias values. */
export const Bias = {
  bullish: "bullish",
  bearish: "bearish",
  neutral: "neutral",
} as const;
export type BiasValue = (typeof Bias)[keyof typeof Bias];

/** Summary bias strength. */
export const BiasStrengths = {
  normal: "normal",
  strong: "strong",
} as const;
export type BiasStrength =
  (typeof BiasStrengths)[keyof typeof BiasStrengths];

/** Heatmap mode. Default is `strength`. */
export const HeatmapTypes = {
  strength: "strength",
  correlation: "correlation",
} as const;
export type HeatmapType = (typeof HeatmapTypes)[keyof typeof HeatmapTypes];

/** Indicator catalogue categories (used by `getIndicators` filtering). */
export const IndicatorCategories = {
  trend: "trend",
  oscillator: "oscillator",
  volatility: "volatility",
  volume: "volume",
} as const;
export type IndicatorCategory =
  (typeof IndicatorCategories)[keyof typeof IndicatorCategories];

/** Account plans. */
export const Plans = {
  free: "free",
  trial: "trial",
  starter: "starter",
  pro: "pro",
  enterprise: "enterprise",
  payg: "payg",
} as const;
export type Plan = (typeof Plans)[keyof typeof Plans];

/** Screener sort direction. Default is `asc`. */
export const SortDirections = {
  asc: "asc",
  desc: "desc",
} as const;
export type SortDirection =
  (typeof SortDirections)[keyof typeof SortDirections];

/**
 * The full, case-sensitive catalogue of 42 indicator identifiers accepted by
 * the API (source of truth: server `INDICATOR_COLUMN_MAP`, SPEC.md §6).
 *
 * Use these verbatim — the docs occasionally use wrong names that 404 (e.g.
 * `Parabolic_SAR`, `Tick_Volume`, `RSI_9`, `EMA_200`). The correct names are
 * `SAR`, `Volumes`; `EMA` stops at `EMA_50`; only three Ichimoku keys exist.
 */
export const Indicators = {
  // --- Trend (23) ---
  SMA_10: "SMA_10",
  SMA_20: "SMA_20",
  SMA_50: "SMA_50",
  SMA_100: "SMA_100",
  SMA_200: "SMA_200",
  EMA_10: "EMA_10",
  EMA_20: "EMA_20",
  EMA_50: "EMA_50",
  MACD_main: "MACD_main",
  MACD_signal: "MACD_signal",
  MACD_hist: "MACD_hist",
  ADX: "ADX",
  ADX_plusDI: "ADX_plusDI",
  ADX_minusDI: "ADX_minusDI",
  Ichimoku_tenkan: "Ichimoku_tenkan",
  Ichimoku_kijun: "Ichimoku_kijun",
  Ichimoku_senkou_a: "Ichimoku_senkou_a",
  Alligator_jaw: "Alligator_jaw",
  Alligator_teeth: "Alligator_teeth",
  Alligator_lips: "Alligator_lips",
  SAR: "SAR",
  TEMA_20: "TEMA_20",
  DEMA_20: "DEMA_20",

  // --- Oscillator (8) ---
  RSI_14: "RSI_14",
  Stochastic_K: "Stochastic_K",
  Stochastic_D: "Stochastic_D",
  CCI_14: "CCI_14",
  CCI_20: "CCI_20",
  WilliamsR_14: "WilliamsR_14",
  Momentum_14: "Momentum_14",
  DeMarker_14: "DeMarker_14",

  // --- Volatility (7) ---
  BB_upper: "BB_upper",
  BB_middle: "BB_middle",
  BB_lower: "BB_lower",
  BB_width: "BB_width",
  ATR_14: "ATR_14",
  ATR_7: "ATR_7",
  StdDev_20: "StdDev_20",

  // --- Volume (4) ---
  OBV: "OBV",
  MFI_14: "MFI_14",
  AD: "AD",
  Volumes: "Volumes",
} as const;
export type Indicator = (typeof Indicators)[keyof typeof Indicators];

/** Indicators grouped by their catalogue category (4 + total 42). */
export const IndicatorsByCategory = {
  trend: [
    "SMA_10",
    "SMA_20",
    "SMA_50",
    "SMA_100",
    "SMA_200",
    "EMA_10",
    "EMA_20",
    "EMA_50",
    "MACD_main",
    "MACD_signal",
    "MACD_hist",
    "ADX",
    "ADX_plusDI",
    "ADX_minusDI",
    "Ichimoku_tenkan",
    "Ichimoku_kijun",
    "Ichimoku_senkou_a",
    "Alligator_jaw",
    "Alligator_teeth",
    "Alligator_lips",
    "SAR",
    "TEMA_20",
    "DEMA_20",
  ],
  oscillator: [
    "RSI_14",
    "Stochastic_K",
    "Stochastic_D",
    "CCI_14",
    "CCI_20",
    "WilliamsR_14",
    "Momentum_14",
    "DeMarker_14",
  ],
  volatility: [
    "BB_upper",
    "BB_middle",
    "BB_lower",
    "BB_width",
    "ATR_14",
    "ATR_7",
    "StdDev_20",
  ],
  volume: ["OBV", "MFI_14", "AD", "Volumes"],
} as const satisfies Record<IndicatorCategory, readonly Indicator[]>;

/** Flat, ordered list of all 42 indicator identifiers. */
export const ALL_INDICATORS: readonly Indicator[] = [
  ...IndicatorsByCategory.trend,
  ...IndicatorsByCategory.oscillator,
  ...IndicatorsByCategory.volatility,
  ...IndicatorsByCategory.volume,
];
