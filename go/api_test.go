package tickatlas

import (
	"context"
	"encoding/json"
	"io"
	"net/http"
	"testing"
)

func ctx() context.Context { return context.Background() }

func ptrInt(i int) *int           { return &i }
func ptrFloat(f float64) *float64 { return &f }
func ptrBool(b bool) *bool        { return &b }

// TestSymbols uses the §7.1 example payload and checks query params.
func TestSymbols(t *testing.T) {
	var gotQuery string
	c, _ := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/symbols" {
			t.Errorf("path = %q", r.URL.Path)
		}
		gotQuery = r.URL.RawQuery
		writeJSON(w, 200, `{"success":true,"data":{"symbols":[{"symbol":"EURUSD","name":null,"category":"forex","base_currency":"EUR","quote_currency":"USD","digits":5,"tradable":true}],"total":149,"pagination":{"offset":0,"limit":100,"total":149,"has_more":true}}}`)
	})

	res, err := c.Symbols(ctx(), &SymbolsParams{Category: "forex", Search: "EUR", Offset: ptrInt(0), Limit: ptrInt(100)})
	if err != nil {
		t.Fatal(err)
	}
	if len(res.Symbols) != 1 || res.Symbols[0].Symbol != "EURUSD" {
		t.Fatalf("symbols = %+v", res.Symbols)
	}
	if res.Symbols[0].Name != nil {
		t.Error("name should be nil")
	}
	if *res.Symbols[0].BaseCurrency != "EUR" {
		t.Errorf("base_currency = %v", res.Symbols[0].BaseCurrency)
	}
	if res.Total != 149 || !res.Pagination.HasMore {
		t.Errorf("total/pagination wrong: %+v", res.Pagination)
	}
	for _, want := range []string{"category=forex", "search=EUR", "limit=100"} {
		if !contains(gotQuery, want) {
			t.Errorf("query %q missing %q", gotQuery, want)
		}
	}
}

func TestSymbol(t *testing.T) {
	c, _ := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/symbols/EURUSD" {
			t.Errorf("path = %q", r.URL.Path)
		}
		writeJSON(w, 200, `{"success":true,"data":{"symbol":"EURUSD","name":"Euro vs US Dollar","category":"forex","description":null,"base_currency":"EUR","quote_currency":"USD","digits":5,"point":0.00001,"contract_size":100000,"min_volume":0.01,"max_volume":500,"volume_step":0.01,"swap_long":-7.5,"swap_short":2.1,"margin_currency":"USD","trading_hours":{"sunday":"closed","monday":"00:00-24:00","tuesday":"00:00-24:00","wednesday":"00:00-24:00","thursday":"00:00-24:00","friday":"00:00-22:00","saturday":"closed"}}}`)
	})
	res, err := c.Symbol(ctx(), "EURUSD")
	if err != nil {
		t.Fatal(err)
	}
	if res.Digits != 5 || res.Point != 0.00001 {
		t.Errorf("digits/point: %+v", res)
	}
	if res.SwapLong == nil || *res.SwapLong != -7.5 {
		t.Errorf("swap_long = %v", res.SwapLong)
	}
	if res.TradingHours.Friday != "00:00-22:00" {
		t.Errorf("friday hours = %q", res.TradingHours.Friday)
	}
}

func TestQuote(t *testing.T) {
	var gotQuery string
	c, _ := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		gotQuery = r.URL.RawQuery
		writeJSON(w, 200, `{"success":true,"data":{"symbol":"EURUSD","bid":1.16404,"ask":1.16422,"spread":18,"spread_pips":1.8,"timestamp":"2026-05-25T13:56:15.819519+00:00","source":"Equiti Securities"}}`)
	})
	res, err := c.Quote(ctx(), "EURUSD", &QuoteParams{IncludeSources: true})
	if err != nil {
		t.Fatal(err)
	}
	if res.Bid == nil || *res.Bid != 1.16404 {
		t.Errorf("bid = %v", res.Bid)
	}
	if res.SpreadPips == nil || *res.SpreadPips != 1.8 {
		t.Errorf("spread_pips = %v", res.SpreadPips)
	}
	if res.Source != "Equiti Securities" {
		t.Errorf("source = %q", res.Source)
	}
	if !contains(gotQuery, "symbol=EURUSD") || !contains(gotQuery, "include_sources=true") {
		t.Errorf("query = %q", gotQuery)
	}
}

func TestQuote_NullBid(t *testing.T) {
	c, _ := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, 200, `{"success":true,"data":{"symbol":"EURUSD","bid":null,"ask":null,"spread":0,"spread_pips":null,"timestamp":"2026-05-25T13:56:15Z"}}`)
	})
	res, err := c.Quote(ctx(), "EURUSD", nil)
	if err != nil {
		t.Fatal(err)
	}
	if res.Bid != nil || res.Ask != nil || res.SpreadPips != nil {
		t.Errorf("nullable fields should be nil: %+v", res)
	}
}

func TestQuotes(t *testing.T) {
	var gotMethod string
	var gotBody map[string]any
	c, _ := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		gotMethod = r.Method
		b, _ := io.ReadAll(r.Body)
		_ = json.Unmarshal(b, &gotBody)
		writeJSON(w, 200, `{"success":true,"data":{"quotes":[{"symbol":"EURUSD","bid":1.164,"ask":1.1642},{"symbol":"GBPUSD","bid":1.27,"ask":1.2702}],"count":2,"not_found":["XXXYYY"],"timestamp":"2026-05-25T13:56:15Z"}}`)
	})
	res, err := c.Quotes(ctx(), []string{"EURUSD", "GBPUSD", "XXXYYY"}, []string{"bid", "ask"})
	if err != nil {
		t.Fatal(err)
	}
	if gotMethod != http.MethodPost {
		t.Errorf("method = %q, want POST", gotMethod)
	}
	if _, ok := gotBody["symbols"]; !ok {
		t.Errorf("body missing symbols: %v", gotBody)
	}
	if _, ok := gotBody["fields"]; !ok {
		t.Errorf("body missing fields: %v", gotBody)
	}
	if res.Count != 2 || len(res.NotFound) != 1 || res.NotFound[0] != "XXXYYY" {
		t.Errorf("result = %+v", res)
	}
	if res.Quotes[0].Bid == nil || *res.Quotes[0].Bid != 1.164 {
		t.Errorf("quote bid = %v", res.Quotes[0].Bid)
	}
}

func TestOHLC(t *testing.T) {
	c, _ := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, 200, `{"success":true,"data":{"symbol":"EURUSD","timeframe":"H1","candles":[{"time":"2026-05-25T13:00:00Z","open":1.164,"high":1.165,"low":1.163,"close":1.1645,"volume":12345}],"count":1,"retention":"90d"}}`)
	})
	res, err := c.OHLC(ctx(), "EURUSD", &OHLCParams{Timeframe: TimeframeH1, Limit: ptrInt(100)})
	if err != nil {
		t.Fatal(err)
	}
	if len(res.Candles) != 1 || res.Candles[0].Volume != 12345 {
		t.Errorf("candles = %+v", res.Candles)
	}
	if res.Retention == nil || *res.Retention != "90d" {
		t.Errorf("retention = %v", res.Retention)
	}
}

func TestOHLC_EmptyButValid(t *testing.T) {
	c, _ := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, 200, `{"success":true,"data":{"symbol":"EURUSD","timeframe":"H1","candles":[],"count":0,"retention":null}}`)
	})
	res, err := c.OHLC(ctx(), "EURUSD", nil)
	if err != nil {
		t.Fatal(err)
	}
	if len(res.Candles) != 0 || res.Count != 0 || res.Retention != nil {
		t.Errorf("empty result wrong: %+v", res)
	}
}

func TestTicks(t *testing.T) {
	var gotQuery string
	c, _ := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		gotQuery = r.URL.RawQuery
		writeJSON(w, 200, `{"success":true,"data":{"symbol":"EURUSD","ticks":[{"time":"2026-05-25T13:00:00.123Z","bid":1.164,"ask":1.1642,"flags":6}],"count":1}}`)
	})
	res, err := c.Ticks(ctx(), "EURUSD", "2026-05-25T13:00:00Z", "2026-05-25T13:30:00Z")
	if err != nil {
		t.Fatal(err)
	}
	if len(res.Ticks) != 1 || res.Ticks[0].Flags != 6 {
		t.Errorf("ticks = %+v", res.Ticks)
	}
	for _, want := range []string{"symbol=EURUSD", "from=", "to="} {
		if !contains(gotQuery, want) {
			t.Errorf("query %q missing %q", gotQuery, want)
		}
	}
}

func TestIndicator(t *testing.T) {
	c, _ := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, 200, `{"success":true,"data":{"symbol":"EURUSD","timeframe":"H1","indicator":"RSI_14","value":58.34,"bid":1.0831,"ask":1.0832,"updated_at":1711548000,"server_time":"2026.06.15 21:38:54"}}`)
	})
	res, err := c.Indicator(ctx(), "EURUSD", RSI14, &IndicatorParams{Timeframe: TimeframeH1})
	if err != nil {
		t.Fatal(err)
	}
	if res.Value == nil || *res.Value != 58.34 {
		t.Errorf("value = %v", res.Value)
	}
	if res.UpdatedAt != 1711548000 {
		t.Errorf("updated_at = %d", res.UpdatedAt)
	}
	// server_time is the dotted, space-separated broker-local form the live API
	// emits (e.g. "2026.06.15 21:38:54"), NOT ISO 8601. The field is a string;
	// the SDK passes it through verbatim.
	if res.ServerTime == nil || *res.ServerTime != "2026.06.15 21:38:54" {
		t.Errorf("server_time = %v", res.ServerTime)
	}
}

func TestIndicators(t *testing.T) {
	c, _ := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, 200, `{"success":true,"data":{"symbol":"EURUSD","timeframe":"H1","ohlcv":{"open":1.16,"high":1.17,"low":1.15,"close":1.165,"volume":1000},"bid":1.164,"ask":1.1642,"indicators":{"RSI_14":58.34,"SMA_200":null},"count":42,"updated_at":1711548000}}`)
	})
	res, err := c.Indicators(ctx(), "EURUSD", &IndicatorsParams{Category: IndicatorCategoryOscillator})
	if err != nil {
		t.Fatal(err)
	}
	if res.OHLCV == nil || res.OHLCV.Close != 1.165 {
		t.Errorf("ohlcv = %+v", res.OHLCV)
	}
	if v, ok := res.Indicators["RSI_14"]; !ok || v == nil || *v != 58.34 {
		t.Errorf("RSI_14 = %v", res.Indicators["RSI_14"])
	}
	if v, ok := res.Indicators["SMA_200"]; !ok || v != nil {
		t.Errorf("SMA_200 should be present and null, got %v", v)
	}
	if res.Count != 42 {
		t.Errorf("count = %d", res.Count)
	}
}

func TestListIndicators(t *testing.T) {
	c, _ := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/indicators/list" {
			t.Errorf("path = %q", r.URL.Path)
		}
		writeJSON(w, 200, `{"success":true,"data":{"indicators":{"oscillator":{"RSI_14":"Relative Strength Index"}},"timeframes":["M1","H1","D1"],"categories":["trend","oscillator","volatility","volume"]}}`)
	})
	res, err := c.ListIndicators(ctx())
	if err != nil {
		t.Fatal(err)
	}
	if res.Indicators["oscillator"]["RSI_14"] != "Relative Strength Index" {
		t.Errorf("catalogue = %+v", res.Indicators)
	}
	if len(res.Categories) != 4 {
		t.Errorf("categories = %v", res.Categories)
	}
}

func TestIndicatorHistory(t *testing.T) {
	c, _ := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, 200, `{"success":true,"data":{"symbol":"EURUSD","indicator":"RSI_14","timeframe":"H1","from":"2026-05-01T00:00:00Z","to":"2026-05-02T00:00:00Z","count":2,"max_window_hours":720,"series":[{"time":"2026-05-01T00:00:00Z","value":55.1},{"time":"2026-05-01T01:00:00Z","value":null}]}}`)
	})
	res, err := c.IndicatorHistory(ctx(), "EURUSD", RSI14, &HistoryParams{Limit: ptrInt(500)})
	if err != nil {
		t.Fatal(err)
	}
	if res.Count != 2 || len(res.Series) != 2 {
		t.Errorf("series = %+v", res.Series)
	}
	if res.Series[1].Value != nil {
		t.Error("second series value should be null")
	}
	if res.MaxWindowHours == nil || *res.MaxWindowHours != 720 {
		t.Errorf("max_window_hours = %v", res.MaxWindowHours)
	}
}

func TestMulti_RealTime(t *testing.T) {
	var gotQuery string
	c, _ := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		gotQuery = r.URL.RawQuery
		writeJSON(w, 200, `{"success":true,"data":{"timeframe":"H1","data":{"EURUSD":{"RSI_14":58.3,"SMA_20":1.164},"GBPUSD":{"RSI_14":null,"SMA_20":1.27}},"not_found":null,"updated_at":1711548000}}`)
	})
	res, err := c.Multi(ctx(), []string{"EURUSD", "GBPUSD"}, []string{"RSI_14", "SMA_20"}, nil)
	if err != nil {
		t.Fatal(err)
	}
	if res.Mode != "" {
		t.Errorf("mode should be empty for real-time, got %q", res.Mode)
	}
	rt, err := res.RealTime()
	if err != nil {
		t.Fatal(err)
	}
	if rt["EURUSD"]["RSI_14"] == nil || *rt["EURUSD"]["RSI_14"] != 58.3 {
		t.Errorf("EURUSD RSI_14 = %v", rt["EURUSD"]["RSI_14"])
	}
	if rt["GBPUSD"]["RSI_14"] != nil {
		t.Error("GBPUSD RSI_14 should be null")
	}
	if !contains(gotQuery, "symbols=EURUSD%2CGBPUSD") {
		t.Errorf("symbols not comma-joined: %q", gotQuery)
	}
}

func TestMulti_Historical(t *testing.T) {
	c, _ := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, 200, `{"success":true,"data":{"timeframe":"H1","mode":"historical","from":"2026-05-01T00:00:00Z","to":"2026-05-02T00:00:00Z","data":{"EURUSD":[{"time":"2026-05-01T00:00:00Z","RSI_14":55.1}]},"not_found":null}}`)
	})
	res, err := c.Multi(ctx(), []string{"EURUSD"}, []string{"RSI_14"}, &MultiParams{From: "2026-05-01T00:00:00Z", To: "2026-05-02T00:00:00Z"})
	if err != nil {
		t.Fatal(err)
	}
	if res.Mode != "historical" {
		t.Errorf("mode = %q", res.Mode)
	}
	hist, err := res.Historical()
	if err != nil {
		t.Fatal(err)
	}
	rows := hist["EURUSD"]
	if len(rows) != 1 {
		t.Fatalf("rows = %+v", rows)
	}
	if string(rows[0]["RSI_14"]) != "55.1" {
		t.Errorf("RSI_14 raw = %s", rows[0]["RSI_14"])
	}
}

func TestScreen_MinMaxValParam(t *testing.T) {
	var gotQuery string
	c, _ := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		gotQuery = r.URL.RawQuery
		writeJSON(w, 200, `{"success":true,"data":{"indicator":"RSI_14","timeframe":"H1","filter":{"min":30,"max":70},"results":[{"symbol":"EURUSD","value":58.3,"bid":1.164}],"total_matches":1,"pagination":{"offset":0,"limit":50,"total":1,"has_more":false},"updated_at":1711548000}}`)
	})
	res, err := c.Screen(ctx(), RSI14, &ScreenParams{MinVal: ptrFloat(30), MaxVal: ptrFloat(70), Sort: "asc"})
	if err != nil {
		t.Fatal(err)
	}
	// Critical: the spec (F2) says params are min_val / max_val, NOT min / max.
	if !contains(gotQuery, "min_val=30") || !contains(gotQuery, "max_val=70") {
		t.Errorf("expected min_val/max_val in query, got %q", gotQuery)
	}
	if contains(gotQuery, "min=30") || contains(gotQuery, "max=70") {
		t.Errorf("must NOT send bare min/max: %q", gotQuery)
	}
	if res.TotalMatches != 1 || res.Filter.Min == nil || *res.Filter.Min != 30 {
		t.Errorf("result = %+v", res)
	}
	if res.Results[0].Bid == nil || *res.Results[0].Bid != 1.164 {
		t.Errorf("result bid = %v", res.Results[0].Bid)
	}
}

func TestSummary(t *testing.T) {
	c, _ := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, 200, `{"success":true,"data":{"symbol":"EURUSD","timeframe":"H1","bias":"bullish","bias_strength":"strong","confidence":0.82,"trend_score":3.5,"momentum_score":1.2,"volatility_score":0.5,"signals":{"trend":"up","momentum":"up","volatility":"normal","volume":"high"},"key_levels":{"resistance":[1.17,1.18],"support":[1.16]},"bullish_signals":["RSI rising"],"bearish_signals":[],"neutral_signals":[],"volatility_info":[],"volume_info":[],"summary":"Bullish bias","recommendations":["Consider long"],"key_values":{"bid":1.164,"ask":1.1642,"rsi_14":58.3,"macd_hist":0.0012,"adx":28.4,"atr_14":0.0021,"sma_20":1.163,"sma_50":1.16,"sma_200":1.15,"bb_upper":1.17,"bb_lower":1.155,"stochastic_k":75.2,"mfi_14":62.1},"updated_at":1711548000}}`)
	})
	res, err := c.Summary(ctx(), "EURUSD", TimeframeH1)
	if err != nil {
		t.Fatal(err)
	}
	if res.Bias != BiasBullish || res.BiasStrength != BiasStrengthStrong {
		t.Errorf("bias = %q/%q", res.Bias, res.BiasStrength)
	}
	if res.Confidence != 0.82 {
		t.Errorf("confidence = %v", res.Confidence)
	}
	if len(res.KeyLevels.Resistance) != 2 {
		t.Errorf("resistance = %v", res.KeyLevels.Resistance)
	}
	if res.KeyValues.RSI14 == nil || *res.KeyValues.RSI14 != 58.3 {
		t.Errorf("key_values.rsi_14 = %v", res.KeyValues.RSI14)
	}
	if res.Signals.Trend != "up" {
		t.Errorf("signals.trend = %q", res.Signals.Trend)
	}
}

func TestSpread(t *testing.T) {
	c, _ := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, 200, `{"success":true,"data":{"symbol":"EURUSD","current":{"spread_pips":1.8,"spread_points":18},"statistics":{"period":"24h","avg_spread":1.9,"min_spread":1.2,"max_spread":3.1,"std_deviation":0.4},"by_session":{"asian":2.1,"london":1.5,"new_york":null}}}`)
	})
	res, err := c.Spread(ctx(), "EURUSD", SpreadPeriod24h)
	if err != nil {
		t.Fatal(err)
	}
	if res.Current.SpreadPoints != 18 {
		t.Errorf("spread_points = %d", res.Current.SpreadPoints)
	}
	if res.Statistics.AvgSpread != 1.9 {
		t.Errorf("avg_spread = %v", res.Statistics.AvgSpread)
	}
	if res.BySession.London == nil || *res.BySession.London != 1.5 {
		t.Errorf("london = %v", res.BySession.London)
	}
	if res.BySession.NewYork != nil {
		t.Error("new_york should be null")
	}
}

func TestCompareSpread(t *testing.T) {
	c, _ := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, 200, `{"success":true,"data":{"period":"24h","symbols":[{"symbol":"EURUSD","current_pips":1.8,"avg_pips":1.9,"min_pips":1.2,"max_pips":3.1,"has_live_data":true},{"symbol":"XXXYYY","current_pips":null,"avg_pips":null,"min_pips":null,"max_pips":null,"has_live_data":false}],"count":2}}`)
	})
	res, err := c.CompareSpread(ctx(), []string{"EURUSD", "XXXYYY"}, SpreadPeriod24h)
	if err != nil {
		t.Fatal(err)
	}
	if res.Count != 2 {
		t.Errorf("count = %d", res.Count)
	}
	if !res.Symbols[0].HasLiveData || res.Symbols[1].HasLiveData {
		t.Errorf("has_live_data wrong: %+v", res.Symbols)
	}
	if res.Symbols[1].AvgPips != nil {
		t.Error("missing symbol avg_pips should be null")
	}
}

func TestSessions(t *testing.T) {
	c, _ := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, 200, `{"success":true,"data":{"current_time":"2026-06-15T12:00:00Z","active_sessions":["london","new_york"],"sessions":{"london":{"status":"open","closes_in":"3h"},"sydney":{"status":"closed","opens_in":"5h","weekend":false}},"overlaps":["london/new_york"],"next_major_event":{"event":"new_york open","in":"1h"}}}`)
	})
	res, err := c.Sessions(ctx())
	if err != nil {
		t.Fatal(err)
	}
	if len(res.ActiveSessions) != 2 {
		t.Errorf("active = %v", res.ActiveSessions)
	}
	if res.Sessions["london"].Status != "open" || res.Sessions["london"].ClosesIn == nil {
		t.Errorf("london = %+v", res.Sessions["london"])
	}
	if res.NextMajorEvent == nil || res.NextMajorEvent.In != "1h" {
		t.Errorf("next_major_event = %+v", res.NextMajorEvent)
	}
}

func TestHeatmap_Strength(t *testing.T) {
	c, _ := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, 200, `{"success":true,"data":{"type":"strength","timeframe":"H4","currencies":{"USD":{"strength":7.2,"trend":"bullish","change":0.3,"pairs_analyzed":7},"EUR":{"strength":4.1,"trend":"bearish","change":-0.2,"pairs_analyzed":7}},"strongest":"USD","weakest":"EUR","range":3.1,"timestamp":"2026-06-15T12:00:00Z"}}`)
	})
	res, err := c.Heatmap(ctx(), &HeatmapParams{Type: HeatmapTypeStrength, Timeframe: HeatmapTimeframeH4})
	if err != nil {
		t.Fatal(err)
	}
	if res.Type != "strength" {
		t.Errorf("type = %q", res.Type)
	}
	if res.Currencies["USD"].Strength != 7.2 {
		t.Errorf("USD strength = %v", res.Currencies["USD"].Strength)
	}
	if res.Strongest == nil || *res.Strongest != "USD" {
		t.Errorf("strongest = %v", res.Strongest)
	}
}

func TestHeatmap_CorrelationUnavailable(t *testing.T) {
	c, _ := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, 200, `{"success":true,"data":{"type":"correlation","timeframe":"H4","correlation_matrix":{},"available":false,"message":"insufficient data","timestamp":"2026-06-15T12:00:00Z"}}`)
	})
	res, err := c.Heatmap(ctx(), &HeatmapParams{Correlations: ptrBool(true)})
	if err != nil {
		t.Fatal(err)
	}
	if res.Available == nil || *res.Available {
		t.Errorf("available = %v", res.Available)
	}
	if res.Message != "insufficient data" {
		t.Errorf("message = %q", res.Message)
	}
}

func TestCalendar(t *testing.T) {
	var gotQuery string
	c, _ := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		gotQuery = r.URL.RawQuery
		writeJSON(w, 200, `{"success":true,"data":{"events":[{"id":"evt1","datetime":"2026-06-15T22:45:00+00:00","currency":"USD","event":"CPI","impact":"high","forecast":"3.1%","previous":"3.0%","actual":null}],"count":1,"pagination":{"offset":0,"limit":100,"total":1,"has_more":false},"range":{"from":"2026-06-15T18:38:34.037156+00:00","to":"2026-06-22T18:38:34.037156+00:00"}}}`)
	})
	res, err := c.Calendar(ctx(), &CalendarParams{Currencies: "USD,EUR", Impact: ImpactHigh, Limit: ptrInt(100)})
	if err != nil {
		t.Fatal(err)
	}
	if len(res.Events) != 1 || res.Events[0].Event != "CPI" {
		t.Errorf("events = %+v", res.Events)
	}
	if res.Events[0].Actual != nil {
		t.Error("actual should be null")
	}
	// Event datetime is the offset form the live API emits (e.g.
	// "2026-06-15T22:45:00+00:00") — NOT a naive timestamp without a suffix. The
	// field is a string; the SDK passes it through verbatim.
	if res.Events[0].Datetime != "2026-06-15T22:45:00+00:00" {
		t.Errorf("datetime = %q", res.Events[0].Datetime)
	}
	// range.from/range.to carry an offset plus microseconds in the live response.
	if res.Range.From != "2026-06-15T18:38:34.037156+00:00" {
		t.Errorf("range.from = %q", res.Range.From)
	}
	if res.Range.To != "2026-06-22T18:38:34.037156+00:00" {
		t.Errorf("range.to = %q", res.Range.To)
	}
	if !contains(gotQuery, "currencies=USD%2CEUR") || !contains(gotQuery, "impact=high") {
		t.Errorf("query = %q", gotQuery)
	}
}

func TestAccount(t *testing.T) {
	c, _ := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/monitor/account" {
			t.Errorf("path = %q", r.URL.Path)
		}
		writeJSON(w, 200, `{"success":true,"data":{"name":"Ruslan","plan":"pro","prepaid_credits":12.5,"daily_quota":10000,"daily_used":342}}`)
	})
	res, err := c.Account(ctx())
	if err != nil {
		t.Fatal(err)
	}
	if res.Plan != "pro" || res.DailyUsed != 342 {
		t.Errorf("account = %+v", res)
	}
	if res.DailyQuota == nil || *res.DailyQuota != 10000 {
		t.Errorf("daily_quota = %v", res.DailyQuota)
	}
}

func TestAccount_UnlimitedQuota(t *testing.T) {
	c, _ := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, 200, `{"success":true,"data":{"name":"Ent","plan":"enterprise","prepaid_credits":0,"daily_quota":null,"daily_used":99999}}`)
	})
	res, err := c.Account(ctx())
	if err != nil {
		t.Fatal(err)
	}
	if res.DailyQuota != nil {
		t.Errorf("daily_quota should be nil (unlimited), got %v", *res.DailyQuota)
	}
}

func TestLayout(t *testing.T) {
	c, _ := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, 200, `{"success":true,"data":{"layout":[{"widget":"chart","symbol":"EURUSD"}]}}`)
	})
	res, err := c.Layout(ctx())
	if err != nil {
		t.Fatal(err)
	}
	if len(res.Layout) == 0 || !contains(string(res.Layout), "chart") {
		t.Errorf("layout = %s", res.Layout)
	}
}

func TestLayout_Null(t *testing.T) {
	c, _ := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, 200, `{"success":true,"data":{"layout":null}}`)
	})
	res, err := c.Layout(ctx())
	if err != nil {
		t.Fatal(err)
	}
	// JSON null decodes to the literal "null" or empty; either way no widgets.
	if s := string(res.Layout); s != "null" && s != "" {
		t.Errorf("layout = %q, want null/empty", s)
	}
}

func TestSaveLayout(t *testing.T) {
	var gotMethod string
	var gotBody map[string]any
	c, _ := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		gotMethod = r.Method
		b, _ := io.ReadAll(r.Body)
		_ = json.Unmarshal(b, &gotBody)
		writeJSON(w, 200, `{"success":true,"data":{"saved":true}}`)
	})
	res, err := c.SaveLayout(ctx(), []map[string]string{{"widget": "chart"}})
	if err != nil {
		t.Fatal(err)
	}
	if gotMethod != http.MethodPut {
		t.Errorf("method = %q, want PUT", gotMethod)
	}
	if _, ok := gotBody["layout"]; !ok {
		t.Errorf("body missing layout: %v", gotBody)
	}
	if !res.Saved {
		t.Error("saved should be true")
	}
}

// TestSaveLayout_RejectsNonArray verifies the client-side guard: a non-slice,
// non-array body is rejected with a *ValidationError before any request is sent.
func TestSaveLayout_RejectsNonArray(t *testing.T) {
	var serverHit bool
	c, _ := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		serverHit = true
		writeJSON(w, 200, `{"success":true,"data":{"saved":true}}`)
	})

	bad := []any{
		map[string]string{"widget": "chart"}, // object, not array
		"not-an-array",                       // string
		42,                                   // number
		nil,                                  // nil interface
	}
	for _, body := range bad {
		res, err := c.SaveLayout(ctx(), body)
		if err == nil {
			t.Errorf("SaveLayout(%T) = nil error, want validation error", body)
			continue
		}
		if !IsValidation(err) {
			t.Errorf("SaveLayout(%T): want *ValidationError, got %v", body, err)
		}
		if res != nil {
			t.Errorf("SaveLayout(%T): result should be nil on error", body)
		}
	}
	if serverHit {
		t.Error("server must not be reached for an invalid layout body")
	}

	// A slice still succeeds (also exercised by TestSaveLayout for the wire path).
	if _, err := c.SaveLayout(ctx(), []map[string]string{{"widget": "chart"}}); err != nil {
		t.Errorf("valid slice layout should succeed, got %v", err)
	}
}

// contains is a tiny helper to keep assertions terse.
func contains(haystack, needle string) bool {
	return len(needle) == 0 || (len(haystack) >= len(needle) && indexOf(haystack, needle) >= 0)
}

func indexOf(s, sub string) int {
	for i := 0; i+len(sub) <= len(s); i++ {
		if s[i:i+len(sub)] == sub {
			return i
		}
	}
	return -1
}
