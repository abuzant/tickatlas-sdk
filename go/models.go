package tickatlas

import "encoding/json"

// Pagination is the shared pagination block returned by list endpoints.
type Pagination struct {
	Offset  int  `json:"offset"`
	Limit   int  `json:"limit"`
	Total   int  `json:"total"`
	HasMore bool `json:"has_more"`
}

// SymbolListItem is one entry in a [SymbolsResult].
type SymbolListItem struct {
	Symbol        string  `json:"symbol"`
	Name          *string `json:"name"`
	Category      string  `json:"category"`
	BaseCurrency  *string `json:"base_currency"`
	QuoteCurrency *string `json:"quote_currency"`
	Digits        int     `json:"digits"`
	Tradable      bool    `json:"tradable"`
}

// SymbolsResult is the data block of GET /symbols.
type SymbolsResult struct {
	Symbols    []SymbolListItem `json:"symbols"`
	Total      int              `json:"total"`
	Pagination Pagination       `json:"pagination"`
}

// TradingHours holds per-weekday trading-hour strings for a symbol.
type TradingHours struct {
	Sunday    string `json:"sunday"`
	Monday    string `json:"monday"`
	Tuesday   string `json:"tuesday"`
	Wednesday string `json:"wednesday"`
	Thursday  string `json:"thursday"`
	Friday    string `json:"friday"`
	Saturday  string `json:"saturday"`
}

// SymbolResult is the data block of GET /symbols/{symbol}: the full contract
// specification for one symbol.
type SymbolResult struct {
	Symbol         string       `json:"symbol"`
	Name           *string      `json:"name"`
	Category       string       `json:"category"`
	Description    *string      `json:"description"`
	BaseCurrency   *string      `json:"base_currency"`
	QuoteCurrency  *string      `json:"quote_currency"`
	Digits         int          `json:"digits"`
	Point          float64      `json:"point"`
	ContractSize   float64      `json:"contract_size"`
	MinVolume      float64      `json:"min_volume"`
	MaxVolume      float64      `json:"max_volume"`
	VolumeStep     float64      `json:"volume_step"`
	SwapLong       *float64     `json:"swap_long"`
	SwapShort      *float64     `json:"swap_short"`
	MarginCurrency *string      `json:"margin_currency"`
	TradingHours   TradingHours `json:"trading_hours"`
}

// QuoteSource is a per-broker quote, returned when include_sources is set.
type QuoteSource struct {
	Broker  string  `json:"broker"`
	Bid     float64 `json:"bid"`
	Ask     float64 `json:"ask"`
	Spread  float64 `json:"spread"`
	Updated string  `json:"updated"`
}

// QuoteResult is the data block of GET /quote.
type QuoteResult struct {
	Symbol     string   `json:"symbol"`
	Bid        *float64 `json:"bid"`
	Ask        *float64 `json:"ask"`
	Spread     float64  `json:"spread"`
	SpreadPips *float64 `json:"spread_pips"`
	Timestamp  string   `json:"timestamp"`

	// Present when include_sources / source is used.
	Source      string        `json:"source,omitempty"`
	BestBid     *float64      `json:"best_bid,omitempty"`
	BestAsk     *float64      `json:"best_ask,omitempty"`
	BestSpread  *float64      `json:"best_spread,omitempty"`
	SourceCount *int          `json:"source_count,omitempty"`
	Sources     []QuoteSource `json:"sources,omitempty"`
}

// BulkQuoteItem is one entry in a [QuotesResult]. Only the requested fields are
// populated by the server, so unrequested fields are nil/empty.
type BulkQuoteItem struct {
	Symbol     string   `json:"symbol"`
	Bid        *float64 `json:"bid,omitempty"`
	Ask        *float64 `json:"ask,omitempty"`
	Spread     *float64 `json:"spread,omitempty"`
	SpreadPips *float64 `json:"spread_pips,omitempty"`
	Timestamp  *string  `json:"timestamp,omitempty"`
}

// QuotesResult is the data block of POST /quotes.
type QuotesResult struct {
	Quotes    []BulkQuoteItem `json:"quotes"`
	Count     int             `json:"count"`
	NotFound  []string        `json:"not_found"`
	Timestamp string          `json:"timestamp"`
}

// Candle is one OHLC bar.
type Candle struct {
	Time   string  `json:"time"`
	Open   float64 `json:"open"`
	High   float64 `json:"high"`
	Low    float64 `json:"low"`
	Close  float64 `json:"close"`
	Volume int64   `json:"volume"`
}

// OHLCResult is the data block of GET /ohlc.
type OHLCResult struct {
	Symbol    string   `json:"symbol"`
	Timeframe string   `json:"timeframe"`
	Candles   []Candle `json:"candles"`
	Count     int      `json:"count"`
	Retention *string  `json:"retention"`
}

// Tick is one tick (bid/ask snapshot).
type Tick struct {
	Time  string  `json:"time"`
	Bid   float64 `json:"bid"`
	Ask   float64 `json:"ask"`
	Flags int     `json:"flags"`
}

// TicksResult is the data block of GET /ticks.
type TicksResult struct {
	Symbol string `json:"symbol"`
	Ticks  []Tick `json:"ticks"`
	Count  int    `json:"count"`
}

// IndicatorResult is the data block of GET /indicator.
type IndicatorResult struct {
	Symbol     string   `json:"symbol"`
	Timeframe  string   `json:"timeframe"`
	Indicator  string   `json:"indicator"`
	Value      *float64 `json:"value"`
	Bid        *float64 `json:"bid"`
	Ask        *float64 `json:"ask"`
	UpdatedAt  int64    `json:"updated_at"`
	ServerTime *string  `json:"server_time"`
}

// OHLCV is the open/high/low/close/volume block embedded in [IndicatorsResult].
type OHLCV struct {
	Open   float64 `json:"open"`
	High   float64 `json:"high"`
	Low    float64 `json:"low"`
	Close  float64 `json:"close"`
	Volume float64 `json:"volume"`
}

// IndicatorsResult is the data block of GET /indicators. Indicator values are
// nullable, hence *float64.
type IndicatorsResult struct {
	Symbol     string              `json:"symbol"`
	Timeframe  string              `json:"timeframe"`
	OHLCV      *OHLCV              `json:"ohlcv"`
	Bid        *float64            `json:"bid"`
	Ask        *float64            `json:"ask"`
	Indicators map[string]*float64 `json:"indicators"`
	Count      int                 `json:"count"`
	UpdatedAt  int64               `json:"updated_at"`
}

// ListIndicatorsResult is the data block of GET /indicators/list. Indicators is
// keyed by category then by indicator name, mapping to a human description.
type ListIndicatorsResult struct {
	Indicators map[string]map[string]string `json:"indicators"`
	Timeframes []string                     `json:"timeframes"`
	Categories []string                     `json:"categories"`
}

// HistoryPoint is one point in an [IndicatorHistoryResult] series.
type HistoryPoint struct {
	Time  string   `json:"time"`
	Value *float64 `json:"value"`
}

// IndicatorHistoryResult is the data block of GET /indicator/history.
type IndicatorHistoryResult struct {
	Symbol         string         `json:"symbol"`
	Indicator      string         `json:"indicator"`
	Timeframe      string         `json:"timeframe"`
	From           *string        `json:"from"`
	To             *string        `json:"to"`
	Count          int            `json:"count"`
	MaxWindowHours *int           `json:"max_window_hours"`
	Series         []HistoryPoint `json:"series"`
}

// MultiResult is the data block of GET /multi. It covers both the real-time and
// historical response shapes; [MultiResult.Mode] is "historical" in historical
// mode and empty otherwise.
//
// In real-time mode, Data maps a symbol to a map of indicator name to value.
// In historical mode, Data maps a symbol to an ordered list of time-stamped
// rows (each row is a map with a "time" key plus one entry per indicator). Use
// [MultiResult.RealTime] and [MultiResult.Historical] to decode into typed
// shapes.
type MultiResult struct {
	Timeframe string          `json:"timeframe"`
	Mode      string          `json:"mode,omitempty"`
	From      *string         `json:"from,omitempty"`
	To        *string         `json:"to,omitempty"`
	Data      json.RawMessage `json:"data"`
	NotFound  []string        `json:"not_found"`
	UpdatedAt int64           `json:"updated_at,omitempty"`
}

// RealTime decodes the real-time Data block into a map of symbol to a map of
// indicator name to value. It is only meaningful when [MultiResult.Mode] is
// empty.
func (m *MultiResult) RealTime() (map[string]map[string]*float64, error) {
	out := map[string]map[string]*float64{}
	if len(m.Data) == 0 {
		return out, nil
	}
	if err := json.Unmarshal(m.Data, &out); err != nil {
		return nil, err
	}
	return out, nil
}

// Historical decodes the historical Data block into a map of symbol to an
// ordered list of rows; each row maps "time" and each indicator name to a raw
// JSON value (indicator values are nullable numbers, the time is a string). It
// is only meaningful when [MultiResult.Mode] is "historical".
func (m *MultiResult) Historical() (map[string][]map[string]json.RawMessage, error) {
	out := map[string][]map[string]json.RawMessage{}
	if len(m.Data) == 0 {
		return out, nil
	}
	if err := json.Unmarshal(m.Data, &out); err != nil {
		return nil, err
	}
	return out, nil
}

// ScreenFilter is the inclusive filter echoed back by the screener.
type ScreenFilter struct {
	Min *float64 `json:"min"`
	Max *float64 `json:"max"`
}

// ScreenItem is one screener match.
type ScreenItem struct {
	Symbol string   `json:"symbol"`
	Value  *float64 `json:"value"`
	Bid    *float64 `json:"bid"`
}

// ScreenResult is the data block of GET /screener.
type ScreenResult struct {
	Indicator    string       `json:"indicator"`
	Timeframe    string       `json:"timeframe"`
	Filter       ScreenFilter `json:"filter"`
	Results      []ScreenItem `json:"results"`
	TotalMatches int          `json:"total_matches"`
	Pagination   Pagination   `json:"pagination"`
	UpdatedAt    int64        `json:"updated_at"`
}

// SummarySignals holds the per-dimension signal labels in a [SummaryResult].
type SummarySignals struct {
	Trend      string `json:"trend"`
	Momentum   string `json:"momentum"`
	Volatility string `json:"volatility"`
	Volume     string `json:"volume"`
}

// KeyLevels holds support/resistance price arrays in a [SummaryResult].
type KeyLevels struct {
	Resistance []float64 `json:"resistance"`
	Support    []float64 `json:"support"`
}

// SummaryKeyValues holds the headline indicator readings in a [SummaryResult].
// All fields are nullable.
type SummaryKeyValues struct {
	Bid         *float64 `json:"bid"`
	Ask         *float64 `json:"ask"`
	RSI14       *float64 `json:"rsi_14"`
	MACDHist    *float64 `json:"macd_hist"`
	ADX         *float64 `json:"adx"`
	ATR14       *float64 `json:"atr_14"`
	SMA20       *float64 `json:"sma_20"`
	SMA50       *float64 `json:"sma_50"`
	SMA200      *float64 `json:"sma_200"`
	BBUpper     *float64 `json:"bb_upper"`
	BBLower     *float64 `json:"bb_lower"`
	StochasticK *float64 `json:"stochastic_k"`
	MFI14       *float64 `json:"mfi_14"`
}

// SummaryResult is the data block of GET /summary.
type SummaryResult struct {
	Symbol          string           `json:"symbol"`
	Timeframe       string           `json:"timeframe"`
	Bias            string           `json:"bias"`
	BiasStrength    string           `json:"bias_strength"`
	Confidence      float64          `json:"confidence"`
	TrendScore      float64          `json:"trend_score"`
	MomentumScore   float64          `json:"momentum_score"`
	VolatilityScore float64          `json:"volatility_score"`
	Signals         SummarySignals   `json:"signals"`
	KeyLevels       KeyLevels        `json:"key_levels"`
	BullishSignals  []string         `json:"bullish_signals"`
	BearishSignals  []string         `json:"bearish_signals"`
	NeutralSignals  []string         `json:"neutral_signals"`
	VolatilityInfo  []string         `json:"volatility_info"`
	VolumeInfo      []string         `json:"volume_info"`
	Summary         string           `json:"summary"`
	Recommendations []string         `json:"recommendations"`
	KeyValues       SummaryKeyValues `json:"key_values"`
	UpdatedAt       int64            `json:"updated_at"`
}

// SpreadCurrent is the live spread block in a [SpreadResult].
type SpreadCurrent struct {
	SpreadPips   float64 `json:"spread_pips"`
	SpreadPoints int     `json:"spread_points"`
}

// SpreadStatistics is the statistics block in a [SpreadResult].
type SpreadStatistics struct {
	Period       string  `json:"period"`
	AvgSpread    float64 `json:"avg_spread"`
	MinSpread    float64 `json:"min_spread"`
	MaxSpread    float64 `json:"max_spread"`
	StdDeviation float64 `json:"std_deviation"`
}

// SpreadBySession holds per-session average spreads (nullable per session).
type SpreadBySession struct {
	Asian   *float64 `json:"asian"`
	London  *float64 `json:"london"`
	NewYork *float64 `json:"new_york"`
}

// SpreadResult is the data block of GET /spread.
type SpreadResult struct {
	Symbol     string           `json:"symbol"`
	Current    SpreadCurrent    `json:"current"`
	Statistics SpreadStatistics `json:"statistics"`
	BySession  SpreadBySession  `json:"by_session"`
}

// CompareSpreadItem is one symbol's spread comparison row.
type CompareSpreadItem struct {
	Symbol      string   `json:"symbol"`
	CurrentPips *float64 `json:"current_pips"`
	AvgPips     *float64 `json:"avg_pips"`
	MinPips     *float64 `json:"min_pips"`
	MaxPips     *float64 `json:"max_pips"`
	HasLiveData bool     `json:"has_live_data"`
}

// CompareSpreadResult is the data block of GET /spread/compare (sorted by
// avg_pips ascending).
type CompareSpreadResult struct {
	Period  string              `json:"period"`
	Symbols []CompareSpreadItem `json:"symbols"`
	Count   int                 `json:"count"`
}

// SessionState is the state of one trading session in a [SessionsResult].
type SessionState struct {
	Status   string  `json:"status"`
	ClosesIn *string `json:"closes_in,omitempty"`
	OpensIn  *string `json:"opens_in,omitempty"`
	Weekend  *bool   `json:"weekend,omitempty"`
}

// SessionEvent describes the next major session event.
type SessionEvent struct {
	Event string `json:"event"`
	In    string `json:"in"`
}

// SessionsResult is the data block of GET /sessions.
type SessionsResult struct {
	CurrentTime    string                  `json:"current_time"`
	ActiveSessions []string                `json:"active_sessions"`
	Sessions       map[string]SessionState `json:"sessions"`
	Overlaps       []string                `json:"overlaps"`
	NextMajorEvent *SessionEvent           `json:"next_major_event"`
}

// CurrencyStrength is one currency's strength entry in a strength-mode
// [HeatmapResult].
type CurrencyStrength struct {
	Strength      float64 `json:"strength"`
	Trend         string  `json:"trend"`
	Change        float64 `json:"change"`
	PairsAnalyzed int     `json:"pairs_analyzed"`
}

// HeatmapResult is the data block of GET /heatmap. It covers both strength and
// correlation modes; check [HeatmapResult.Type].
type HeatmapResult struct {
	Type      string `json:"type"`
	Timeframe string `json:"timeframe"`
	Timestamp string `json:"timestamp"`

	// Strength mode.
	Currencies map[string]CurrencyStrength `json:"currencies,omitempty"`
	Strongest  *string                     `json:"strongest,omitempty"`
	Weakest    *string                     `json:"weakest,omitempty"`
	Range      *float64                    `json:"range,omitempty"`

	// Correlation mode.
	CorrelationMatrix map[string]map[string]float64 `json:"correlation_matrix,omitempty"`
	Available         *bool                         `json:"available,omitempty"`
	Message           string                        `json:"message,omitempty"`
}

// CalendarEvent is one economic-calendar event. Note datetime is naive UTC with
// no suffix; treat it as UTC.
type CalendarEvent struct {
	ID       string  `json:"id"`
	Datetime string  `json:"datetime"`
	Currency string  `json:"currency"`
	Event    string  `json:"event"`
	Impact   string  `json:"impact"`
	Forecast *string `json:"forecast"`
	Previous *string `json:"previous"`
	Actual   *string `json:"actual"`
}

// CalendarRange is the resolved from/to range echoed by the calendar.
type CalendarRange struct {
	From string `json:"from"`
	To   string `json:"to"`
}

// CalendarResult is the data block of GET /calendar.
type CalendarResult struct {
	Events     []CalendarEvent `json:"events"`
	Count      int             `json:"count"`
	Pagination Pagination      `json:"pagination"`
	Range      CalendarRange   `json:"range"`
}

// AccountResult is the data block of GET /monitor/account. DailyQuota is nil
// when the plan has an unlimited daily quota.
type AccountResult struct {
	Name           string  `json:"name"`
	Plan           string  `json:"plan"`
	PrepaidCredits float64 `json:"prepaid_credits"`
	DailyQuota     *int    `json:"daily_quota"`
	DailyUsed      int     `json:"daily_used"`
}

// LayoutResult is the data block of GET /monitor/layout. Layout is the
// server-stored dashboard layout (nil if nothing is stored).
type LayoutResult struct {
	Layout json.RawMessage `json:"layout"`
}

// SaveLayoutResult is the data block of PUT /monitor/layout.
type SaveLayoutResult struct {
	Saved bool `json:"saved"`
}

// ComponentHealth is one dependency's status within a [HealthResult].
type ComponentHealth struct {
	Status string `json:"status"`
}

// HealthComponents maps each dependency name (e.g. "redis", "postgres") to its
// status. The /health probe reports each component as a nested status object.
type HealthComponents map[string]ComponentHealth

// HealthResult is the body of GET /health. The health probe is not wrapped in
// the success/data envelope.
type HealthResult struct {
	Status     string           `json:"status"`
	Components HealthComponents `json:"components"`
	Raw        json.RawMessage  `json:"-"`
}
