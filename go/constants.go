package tickatlas

// Version is the SDK version (SemVer). It is reported in the default User-Agent.
const Version = "0.1.0"

// defaultUserAgent is the User-Agent sent when one is not supplied via
// [WithUserAgent].
const defaultUserAgent = "tickatlas-go/" + Version

// DefaultBaseURL is the production API base URL used when no base URL is
// supplied via [WithBaseURL] or the TICKATLAS_BASE_URL environment variable.
const DefaultBaseURL = "https://tickatlas.com/v1"

// Environment variable names read by [NewClient].
const (
	// EnvAPIKey is the environment variable consulted for the API key when
	// WithAPIKey is not provided.
	EnvAPIKey = "TICKATLAS_API_KEY"
	// EnvBaseURL is the environment variable consulted for the base URL when
	// WithBaseURL is not provided.
	EnvBaseURL = "TICKATLAS_BASE_URL"
)

// Candle / indicator timeframes. Valid for the indicator, indicators, summary,
// ohlc, multi, history and screener endpoints (default H1). Note that the
// heatmap endpoint accepts a different set; see the Heatmap* constants.
const (
	TimeframeM1  = "M1"
	TimeframeM5  = "M5"
	TimeframeM15 = "M15"
	TimeframeM30 = "M30"
	TimeframeH1  = "H1"
	TimeframeH4  = "H4"
	TimeframeD1  = "D1"
)

// Heatmap timeframes. Valid only for the heatmap endpoint (default H4).
const (
	HeatmapTimeframeH1 = "H1"
	HeatmapTimeframeH4 = "H4"
	HeatmapTimeframeD1 = "D1"
	HeatmapTimeframeW1 = "W1"
)

// Symbol categories.
const (
	CategoryForex       = "forex"
	CategoryMetals      = "metals"
	CategoryCommodities = "commodities"
	CategoryIndices     = "indices"
	CategoryCrypto      = "crypto"
	CategoryStocks      = "stocks"
)

// Spread statistics periods (default 24h).
const (
	SpreadPeriod1h  = "1h"
	SpreadPeriod24h = "24h"
	SpreadPeriod7d  = "7d"
	SpreadPeriod30d = "30d"
)

// Economic-calendar impact levels.
const (
	ImpactHigh   = "high"
	ImpactMedium = "medium"
	ImpactLow    = "low"
)

// Summary bias values.
const (
	BiasBullish = "bullish"
	BiasBearish = "bearish"
	BiasNeutral = "neutral"
)

// Summary bias strength values.
const (
	BiasStrengthNormal = "normal"
	BiasStrengthStrong = "strong"
)

// Heatmap types (default strength).
const (
	HeatmapTypeStrength    = "strength"
	HeatmapTypeCorrelation = "correlation"
)

// Indicator-category identifiers (accepted by the indicators endpoint's
// category filter and used as keys in the indicators/list catalogue).
const (
	IndicatorCategoryTrend      = "trend"
	IndicatorCategoryOscillator = "oscillator"
	IndicatorCategoryVolatility = "volatility"
	IndicatorCategoryVolume     = "volume"
)

// Account plan identifiers.
const (
	PlanFree       = "free"
	PlanTrial      = "trial"
	PlanStarter    = "starter"
	PlanPro        = "pro"
	PlanEnterprise = "enterprise"
	PlanPAYG       = "payg"
)

// The 42 technical indicators accepted by the API. These identifiers are
// case-sensitive and must be used verbatim (source of truth:
// INDICATOR_COLUMN_MAP). See the SDK contract for naming gotchas — for example
// it is SAR (not Parabolic_SAR), Volumes (not Tick_Volume), and WilliamsR_14
// (no underscore before R).
const (
	// Trend (23).
	SMA10           = "SMA_10"
	SMA20           = "SMA_20"
	SMA50           = "SMA_50"
	SMA100          = "SMA_100"
	SMA200          = "SMA_200"
	EMA10           = "EMA_10"
	EMA20           = "EMA_20"
	EMA50           = "EMA_50"
	MACDMain        = "MACD_main"
	MACDSignal      = "MACD_signal"
	MACDHist        = "MACD_hist"
	ADX             = "ADX"
	ADXPlusDI       = "ADX_plusDI"
	ADXMinusDI      = "ADX_minusDI"
	IchimokuTenkan  = "Ichimoku_tenkan"
	IchimokuKijun   = "Ichimoku_kijun"
	IchimokuSenkouA = "Ichimoku_senkou_a"
	AlligatorJaw    = "Alligator_jaw"
	AlligatorTeeth  = "Alligator_teeth"
	AlligatorLips   = "Alligator_lips"
	SAR             = "SAR"
	TEMA20          = "TEMA_20"
	DEMA20          = "DEMA_20"

	// Oscillator (8).
	RSI14       = "RSI_14"
	StochasticK = "Stochastic_K"
	StochasticD = "Stochastic_D"
	CCI14       = "CCI_14"
	CCI20       = "CCI_20"
	WilliamsR14 = "WilliamsR_14"
	Momentum14  = "Momentum_14"
	DeMarker14  = "DeMarker_14"

	// Volatility (7).
	BBUpper  = "BB_upper"
	BBMiddle = "BB_middle"
	BBLower  = "BB_lower"
	BBWidth  = "BB_width"
	ATR14    = "ATR_14"
	ATR7     = "ATR_7"
	StdDev20 = "StdDev_20"

	// Volume (4).
	OBV     = "OBV"
	MFI14   = "MFI_14"
	AD      = "AD"
	Volumes = "Volumes"
)

// AllIndicators is the complete, ordered list of the 42 indicator identifiers
// accepted by the API. It is a fresh copy per call site — callers may sort or
// mutate the returned slice freely.
func AllIndicators() []string {
	return []string{
		// Trend (23).
		SMA10, SMA20, SMA50, SMA100, SMA200,
		EMA10, EMA20, EMA50,
		MACDMain, MACDSignal, MACDHist,
		ADX, ADXPlusDI, ADXMinusDI,
		IchimokuTenkan, IchimokuKijun, IchimokuSenkouA,
		AlligatorJaw, AlligatorTeeth, AlligatorLips,
		SAR, TEMA20, DEMA20,
		// Oscillator (8).
		RSI14, StochasticK, StochasticD, CCI14, CCI20,
		WilliamsR14, Momentum14, DeMarker14,
		// Volatility (7).
		BBUpper, BBMiddle, BBLower, BBWidth, ATR14, ATR7, StdDev20,
		// Volume (4).
		OBV, MFI14, AD, Volumes,
	}
}
