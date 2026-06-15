package tickatlas

import (
	"context"
	"net/http"
	"net/url"
	"reflect"
	"strconv"
	"strings"
)

// ---------------------------------------------------------------------------
// Parameter option structs
// ---------------------------------------------------------------------------

// SymbolsParams holds the optional parameters for [Client.Symbols]. A nil
// *SymbolsParams is equivalent to the zero value (server defaults apply).
type SymbolsParams struct {
	Category string // one of the Category* constants
	Search   string // substring match on symbol or name
	Offset   *int   // >= 0 (default 0)
	Limit    *int   // 1..500 (default 100)
}

// QuoteParams holds the optional parameters for [Client.Quote].
type QuoteParams struct {
	IncludeSources bool   // include per-broker sources[]
	Source         string // force a broker source (debug)
}

// OHLCParams holds the optional parameters for [Client.OHLC].
type OHLCParams struct {
	Timeframe string // one of the Timeframe* constants (default H1)
	From      string // ISO 8601
	To        string // ISO 8601
	Limit     *int   // 1..1000 (default 100)
}

// IndicatorParams holds the optional parameters for [Client.Indicator].
type IndicatorParams struct {
	Timeframe string // one of the Timeframe* constants (default H1)
	Source    string // force a broker source
}

// IndicatorsParams holds the optional parameters for [Client.Indicators].
type IndicatorsParams struct {
	Timeframe string // one of the Timeframe* constants (default H1)
	Category  string // trend/oscillator/volatility/volume
}

// HistoryParams holds the optional parameters for [Client.IndicatorHistory].
type HistoryParams struct {
	Timeframe string // one of the Timeframe* constants (default H1)
	From      string // ISO 8601
	To        string // ISO 8601
	Limit     *int   // 1..5000 (default 500)
}

// MultiParams holds the optional parameters for [Client.Multi]. Supplying From
// (and typically To) switches the endpoint into historical mode.
type MultiParams struct {
	Timeframe string // one of the Timeframe* constants (default H1)
	From      string // presence => historical mode
	To        string // historical mode
}

// ScreenParams holds the optional parameters for [Client.Screen]. Note the
// server reads min_val / max_val (not min / max); MinVal/MaxVal map to those.
type ScreenParams struct {
	Timeframe string   // one of the Timeframe* constants (default H1)
	MinVal    *float64 // inclusive lower bound -> min_val
	MaxVal    *float64 // inclusive upper bound -> max_val
	Sort      string   // "asc" (default) or "desc"
	Offset    *int     // >= 0 (default 0)
	Limit     *int     // 1..200 (default 50)
}

// HeatmapParams holds the optional parameters for [Client.Heatmap].
type HeatmapParams struct {
	Type         string // "strength" (default) or "correlation"
	Timeframe    string // one of the HeatmapTimeframe* constants (default H4)
	Correlations *bool  // true forces correlation mode
}

// CalendarParams holds the optional parameters for [Client.Calendar]. A nil
// *CalendarParams is equivalent to the zero value (server defaults apply).
type CalendarParams struct {
	From       string // date/ISO (default today 00:00 UTC)
	To         string // range <= 30 days (default from+7d)
	Currencies string // comma-separated, e.g. "USD,EUR"
	Country    string // alias of Currencies
	Impact     string // high/medium/low
	Q          string // title search, <= 100 chars
	NextHours  *int   // 1..168; overrides from/to
	Offset     *int   // >= 0 (default 0)
	Limit      *int   // 1..500 (default 100)
}

// ---------------------------------------------------------------------------
// Query helpers
// ---------------------------------------------------------------------------

func setStr(q url.Values, key, val string) {
	if val != "" {
		q.Set(key, val)
	}
}

func setIntPtr(q url.Values, key string, val *int) {
	if val != nil {
		q.Set(key, strconv.Itoa(*val))
	}
}

func setFloatPtr(q url.Values, key string, val *float64) {
	if val != nil {
		q.Set(key, strconv.FormatFloat(*val, 'f', -1, 64))
	}
}

func setBool(q url.Values, key string, val bool) {
	if val {
		q.Set(key, "true")
	}
}

func setBoolPtr(q url.Values, key string, val *bool) {
	if val != nil {
		q.Set(key, strconv.FormatBool(*val))
	}
}

// ---------------------------------------------------------------------------
// Endpoints (the 21 /v1 endpoints)
// ---------------------------------------------------------------------------

// Symbols lists available symbols (paginated). GET /symbols.
func (c *Client) Symbols(ctx context.Context, params *SymbolsParams) (*SymbolsResult, error) {
	q := url.Values{}
	if params != nil {
		setStr(q, "category", params.Category)
		setStr(q, "search", params.Search)
		setIntPtr(q, "offset", params.Offset)
		setIntPtr(q, "limit", params.Limit)
	}
	var out SymbolsResult
	if err := c.do(ctx, request{method: http.MethodGet, path: "/symbols", query: q}, &out); err != nil {
		return nil, err
	}
	return &out, nil
}

// Symbol returns the full contract specification for one symbol.
// GET /symbols/{symbol}.
func (c *Client) Symbol(ctx context.Context, symbol string) (*SymbolResult, error) {
	var out SymbolResult
	path := "/symbols/" + url.PathEscape(symbol)
	if err := c.do(ctx, request{method: http.MethodGet, path: path}, &out); err != nil {
		return nil, err
	}
	return &out, nil
}

// Quote returns a single real-time quote. GET /quote.
func (c *Client) Quote(ctx context.Context, symbol string, params *QuoteParams) (*QuoteResult, error) {
	q := url.Values{}
	q.Set("symbol", symbol)
	if params != nil {
		setBool(q, "include_sources", params.IncludeSources)
		setStr(q, "source", params.Source)
	}
	var out QuoteResult
	if err := c.do(ctx, request{method: http.MethodGet, path: "/quote", query: q}, &out); err != nil {
		return nil, err
	}
	return &out, nil
}

// Quotes returns a batch of quotes. POST /quotes. fields may be nil to request
// all five fields (bid, ask, spread, spread_pips, timestamp).
func (c *Client) Quotes(ctx context.Context, symbols []string, fields []string) (*QuotesResult, error) {
	body := map[string]any{"symbols": symbols}
	if len(fields) > 0 {
		body["fields"] = fields
	}
	var out QuotesResult
	if err := c.do(ctx, request{method: http.MethodPost, path: "/quotes", body: body}, &out); err != nil {
		return nil, err
	}
	return &out, nil
}

// OHLC returns OHLC candles. GET /ohlc.
func (c *Client) OHLC(ctx context.Context, symbol string, params *OHLCParams) (*OHLCResult, error) {
	q := url.Values{}
	q.Set("symbol", symbol)
	if params != nil {
		setStr(q, "timeframe", params.Timeframe)
		setStr(q, "from", params.From)
		setStr(q, "to", params.To)
		setIntPtr(q, "limit", params.Limit)
	}
	var out OHLCResult
	if err := c.do(ctx, request{method: http.MethodGet, path: "/ohlc", query: q}, &out); err != nil {
		return nil, err
	}
	return &out, nil
}

// Ticks returns tick data for a symbol over [from, to] (range <= 1 hour).
// GET /ticks. Requires a pro or enterprise plan.
func (c *Client) Ticks(ctx context.Context, symbol, from, to string) (*TicksResult, error) {
	q := url.Values{}
	q.Set("symbol", symbol)
	q.Set("from", from)
	q.Set("to", to)
	var out TicksResult
	if err := c.do(ctx, request{method: http.MethodGet, path: "/ticks", query: q}, &out); err != nil {
		return nil, err
	}
	return &out, nil
}

// Indicator returns a single indicator value. GET /indicator. indicator must be
// one of the catalogue identifiers (see the indicator constants).
func (c *Client) Indicator(ctx context.Context, symbol, indicator string, params *IndicatorParams) (*IndicatorResult, error) {
	q := url.Values{}
	q.Set("symbol", symbol)
	q.Set("indicator", indicator)
	if params != nil {
		setStr(q, "timeframe", params.Timeframe)
		setStr(q, "source", params.Source)
	}
	var out IndicatorResult
	if err := c.do(ctx, request{method: http.MethodGet, path: "/indicator", query: q}, &out); err != nil {
		return nil, err
	}
	return &out, nil
}

// Indicators returns all indicators for a symbol. GET /indicators.
func (c *Client) Indicators(ctx context.Context, symbol string, params *IndicatorsParams) (*IndicatorsResult, error) {
	q := url.Values{}
	q.Set("symbol", symbol)
	if params != nil {
		setStr(q, "timeframe", params.Timeframe)
		setStr(q, "category", params.Category)
	}
	var out IndicatorsResult
	if err := c.do(ctx, request{method: http.MethodGet, path: "/indicators", query: q}, &out); err != nil {
		return nil, err
	}
	return &out, nil
}

// ListIndicators returns the indicator catalogue. GET /indicators/list.
func (c *Client) ListIndicators(ctx context.Context) (*ListIndicatorsResult, error) {
	var out ListIndicatorsResult
	if err := c.do(ctx, request{method: http.MethodGet, path: "/indicators/list"}, &out); err != nil {
		return nil, err
	}
	return &out, nil
}

// IndicatorHistory returns an indicator series over time.
// GET /indicator/history. Requires a starter or higher plan.
func (c *Client) IndicatorHistory(ctx context.Context, symbol, indicator string, params *HistoryParams) (*IndicatorHistoryResult, error) {
	q := url.Values{}
	q.Set("symbol", symbol)
	q.Set("indicator", indicator)
	if params != nil {
		setStr(q, "timeframe", params.Timeframe)
		setStr(q, "from", params.From)
		setStr(q, "to", params.To)
		setIntPtr(q, "limit", params.Limit)
	}
	var out IndicatorHistoryResult
	if err := c.do(ctx, request{method: http.MethodGet, path: "/indicator/history", query: q}, &out); err != nil {
		return nil, err
	}
	return &out, nil
}

// Multi returns batched indicators across symbols. GET /multi. Supplying From
// in params (historical mode) requires a starter or higher plan. Use the
// [MultiResult.RealTime] and [MultiResult.Historical] helpers to decode the
// mode-specific data block.
func (c *Client) Multi(ctx context.Context, symbols, indicators []string, params *MultiParams) (*MultiResult, error) {
	q := url.Values{}
	q.Set("symbols", strings.Join(symbols, ","))
	q.Set("indicators", strings.Join(indicators, ","))
	if params != nil {
		setStr(q, "timeframe", params.Timeframe)
		setStr(q, "from", params.From)
		setStr(q, "to", params.To)
	}
	var out MultiResult
	if err := c.do(ctx, request{method: http.MethodGet, path: "/multi", query: q}, &out); err != nil {
		return nil, err
	}
	return &out, nil
}

// Screen scans symbols by an indicator value. GET /screener. The MinVal/MaxVal
// params are sent as min_val/max_val (the server ignores min/max).
func (c *Client) Screen(ctx context.Context, indicator string, params *ScreenParams) (*ScreenResult, error) {
	q := url.Values{}
	q.Set("indicator", indicator)
	if params != nil {
		setStr(q, "timeframe", params.Timeframe)
		setFloatPtr(q, "min_val", params.MinVal)
		setFloatPtr(q, "max_val", params.MaxVal)
		setStr(q, "sort", params.Sort)
		setIntPtr(q, "offset", params.Offset)
		setIntPtr(q, "limit", params.Limit)
	}
	var out ScreenResult
	if err := c.do(ctx, request{method: http.MethodGet, path: "/screener", query: q}, &out); err != nil {
		return nil, err
	}
	return &out, nil
}

// Summary returns a market-bias summary for a symbol. GET /summary. timeframe
// may be empty for the default (H1).
func (c *Client) Summary(ctx context.Context, symbol, timeframe string) (*SummaryResult, error) {
	q := url.Values{}
	q.Set("symbol", symbol)
	setStr(q, "timeframe", timeframe)
	var out SummaryResult
	if err := c.do(ctx, request{method: http.MethodGet, path: "/summary", query: q}, &out); err != nil {
		return nil, err
	}
	return &out, nil
}

// Spread returns spread statistics for a symbol. GET /spread. period may be
// empty for the default (24h).
func (c *Client) Spread(ctx context.Context, symbol, period string) (*SpreadResult, error) {
	q := url.Values{}
	q.Set("symbol", symbol)
	setStr(q, "period", period)
	var out SpreadResult
	if err := c.do(ctx, request{method: http.MethodGet, path: "/spread", query: q}, &out); err != nil {
		return nil, err
	}
	return &out, nil
}

// CompareSpread compares spread across symbols (<= 20). GET /spread/compare.
// period may be empty for the default (24h).
func (c *Client) CompareSpread(ctx context.Context, symbols []string, period string) (*CompareSpreadResult, error) {
	q := url.Values{}
	q.Set("symbols", strings.Join(symbols, ","))
	setStr(q, "period", period)
	var out CompareSpreadResult
	if err := c.do(ctx, request{method: http.MethodGet, path: "/spread/compare", query: q}, &out); err != nil {
		return nil, err
	}
	return &out, nil
}

// Sessions returns the market session clock. GET /sessions.
func (c *Client) Sessions(ctx context.Context) (*SessionsResult, error) {
	var out SessionsResult
	if err := c.do(ctx, request{method: http.MethodGet, path: "/sessions"}, &out); err != nil {
		return nil, err
	}
	return &out, nil
}

// Heatmap returns a currency-strength or correlation heatmap. GET /heatmap.
func (c *Client) Heatmap(ctx context.Context, params *HeatmapParams) (*HeatmapResult, error) {
	q := url.Values{}
	if params != nil {
		setStr(q, "type", params.Type)
		setStr(q, "timeframe", params.Timeframe)
		setBoolPtr(q, "correlations", params.Correlations)
	}
	var out HeatmapResult
	if err := c.do(ctx, request{method: http.MethodGet, path: "/heatmap", query: q}, &out); err != nil {
		return nil, err
	}
	return &out, nil
}

// Calendar returns economic-calendar events. GET /calendar.
func (c *Client) Calendar(ctx context.Context, params *CalendarParams) (*CalendarResult, error) {
	q := url.Values{}
	if params != nil {
		setStr(q, "from", params.From)
		setStr(q, "to", params.To)
		setStr(q, "currencies", params.Currencies)
		setStr(q, "country", params.Country)
		setStr(q, "impact", params.Impact)
		setStr(q, "q", params.Q)
		setIntPtr(q, "next_hours", params.NextHours)
		setIntPtr(q, "offset", params.Offset)
		setIntPtr(q, "limit", params.Limit)
	}
	var out CalendarResult
	if err := c.do(ctx, request{method: http.MethodGet, path: "/calendar", query: q}, &out); err != nil {
		return nil, err
	}
	return &out, nil
}

// Account returns the account identity and quota. GET /monitor/account. This is
// the de-facto identity endpoint (there is no /me).
func (c *Client) Account(ctx context.Context) (*AccountResult, error) {
	var out AccountResult
	if err := c.do(ctx, request{method: http.MethodGet, path: "/monitor/account"}, &out); err != nil {
		return nil, err
	}
	return &out, nil
}

// Layout returns the saved dashboard layout. GET /monitor/layout. The returned
// [LayoutResult.Layout] is raw JSON (nil if nothing is stored).
func (c *Client) Layout(ctx context.Context) (*LayoutResult, error) {
	var out LayoutResult
	if err := c.do(ctx, request{method: http.MethodGet, path: "/monitor/layout"}, &out); err != nil {
		return nil, err
	}
	return &out, nil
}

// SaveLayout saves the dashboard layout. PUT /monitor/layout.
//
// This is an advanced, write operation: it mutates the user's saved dashboard
// layout (max 60 widgets). layout must be a slice or array (it is sent as the
// JSON "layout" array); anything else is rejected client-side with a
// [*ValidationError] before any request is made. Most callers will not need
// this method.
func (c *Client) SaveLayout(ctx context.Context, layout any) (*SaveLayoutResult, error) {
	if k := reflect.ValueOf(layout).Kind(); k != reflect.Slice && k != reflect.Array {
		return nil, &ValidationError{APIError{
			Code:    "INVALID_LAYOUT",
			Message: "tickatlas: SaveLayout requires layout to be a slice or array",
		}}
	}
	body := map[string]any{"layout": layout}
	var out SaveLayoutResult
	if err := c.do(ctx, request{method: http.MethodPut, path: "/monitor/layout", body: body}, &out); err != nil {
		return nil, err
	}
	return &out, nil
}

// ---------------------------------------------------------------------------
// Infrastructure probes (no API key)
// ---------------------------------------------------------------------------

// Health returns the service health probe. GET /health. It is unauthenticated
// and not wrapped in the success/data envelope.
func (c *Client) Health(ctx context.Context) (*HealthResult, error) {
	var out HealthResult
	if err := c.do(ctx, request{method: http.MethodGet, path: "/health", authless: true, root: true}, &out); err != nil {
		return nil, err
	}
	return &out, nil
}
