import { describe, it, expect, vi, afterEach } from "vitest";
import {
  TickAtlas,
  TickAtlasConfigError,
  AuthenticationError,
  PermissionDeniedError,
  NotFoundError,
  ValidationError,
  RateLimitError,
  ServerError,
  TickAtlasNetworkError,
  TickAtlasAPIError,
  Indicators,
  Timeframes,
  ALL_INDICATORS,
  IndicatorsByCategory,
} from "../src/index.js";
import { makeClient, ok, err } from "./helpers.js";

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllEnvs();
});

/** Read the URL string from the Nth fetch call. */
function urlOf(fetchMock: ReturnType<typeof vi.fn>, n = 0): string {
  return fetchMock.mock.calls[n]![0] as string;
}
/** Read the RequestInit from the Nth fetch call. */
function initOf(fetchMock: ReturnType<typeof vi.fn>, n = 0): RequestInit {
  return fetchMock.mock.calls[n]![1] as RequestInit;
}

// ===========================================================================
// Configuration & auth
// ===========================================================================

describe("configuration", () => {
  it("throws TickAtlasConfigError when no key can be resolved", () => {
    vi.stubEnv("TICKATLAS_API_KEY", "");
    expect(() => new TickAtlas({})).toThrow(TickAtlasConfigError);
  });

  it("prefers explicit apiKey over env", async () => {
    vi.stubEnv("TICKATLAS_API_KEY", "claw_env_key");
    const { client, fetchMock } = makeClient([ok({ status: "ok" })], {
      apiKey: "claw_explicit",
    });
    await client.health();
    expect(initOf(fetchMock).headers).toMatchObject({
      "X-API-Key": "claw_explicit",
    });
  });

  it("falls back to TICKATLAS_API_KEY env var", () => {
    vi.stubEnv("TICKATLAS_API_KEY", "claw_from_env");
    const c = new TickAtlas({ baseURL: "https://api.test/v1" });
    expect(c).toBeInstanceOf(TickAtlas);
  });

  it("uses TICKATLAS_BASE_URL env then the production default", async () => {
    vi.stubEnv("TICKATLAS_BASE_URL", "https://staging.test/v1");
    const { client, fetchMock } = makeClient(
      [
        ok({
          current_time: "t",
          active_sessions: [],
          sessions: {},
          overlaps: [],
          next_major_event: null,
        }),
      ],
      { baseURL: undefined },
    );
    // A regular /v1 endpoint must honour the configured base URL (incl. /v1).
    await client.getSessions();
    expect(urlOf(fetchMock)).toBe("https://staging.test/v1/sessions");
  });

  it("sends the X-API-Key header and a JSON Accept", async () => {
    const { client, fetchMock } = makeClient([ok({ status: "ok" })]);
    await client.health();
    const headers = initOf(fetchMock).headers as Record<string, string>;
    expect(headers["X-API-Key"]).toBe("claw_test_key_do_not_use");
    expect(headers["Accept"]).toBe("application/json");
  });

  it("sets a User-Agent in a Node runtime", async () => {
    const { client, fetchMock } = makeClient([ok({ status: "ok" })]);
    await client.health();
    const headers = initOf(fetchMock).headers as Record<string, string>;
    expect(headers["User-Agent"]).toBe("tickatlas-js/0.1.0");
  });
});

// ===========================================================================
// Per-endpoint success parsing (payloads from SPEC §7)
// ===========================================================================

describe("endpoints — success parsing", () => {
  it("getSymbols unwraps data and serialises paging/filter params", async () => {
    const data = {
      symbols: [
        {
          symbol: "EURUSD",
          name: null,
          category: "forex",
          base_currency: "EUR",
          quote_currency: "USD",
          digits: 5,
          tradable: true,
        },
      ],
      total: 149,
      pagination: { offset: 0, limit: 100, total: 149, has_more: true },
    };
    const { client, fetchMock } = makeClient([ok(data)]);
    const res = await client.getSymbols({
      category: "forex",
      search: "EUR",
      offset: 0,
      limit: 50,
    });
    expect(res.total).toBe(149);
    expect(res.symbols[0]!.symbol).toBe("EURUSD");
    const url = urlOf(fetchMock);
    expect(url).toContain("/symbols?");
    expect(url).toContain("category=forex");
    expect(url).toContain("search=EUR");
    expect(url).toContain("limit=50");
  });

  it("getSymbol path-encodes the symbol", async () => {
    const data = {
      symbol: "EURUSD",
      name: "Euro vs US Dollar",
      category: "forex",
      description: null,
      base_currency: "EUR",
      quote_currency: "USD",
      digits: 5,
      point: 0.00001,
      contract_size: 100000,
      min_volume: 0.01,
      max_volume: 500,
      volume_step: 0.01,
      swap_long: -7.2,
      swap_short: 1.1,
      margin_currency: "USD",
      trading_hours: {
        sunday: "closed",
        monday: "00:00-24:00",
        tuesday: "00:00-24:00",
        wednesday: "00:00-24:00",
        thursday: "00:00-24:00",
        friday: "00:00-22:00",
        saturday: "closed",
      },
    };
    const { client, fetchMock } = makeClient([ok(data)]);
    const res = await client.getSymbol("EURUSD");
    expect(res.digits).toBe(5);
    expect(res.trading_hours.friday).toBe("00:00-22:00");
    expect(urlOf(fetchMock)).toBe("https://api.test/v1/symbols/EURUSD");
  });

  it("getQuote parses the §7.3 example and maps includeSources", async () => {
    const data = {
      symbol: "EURUSD",
      bid: 1.16404,
      ask: 1.16422,
      spread: 18,
      spread_pips: 1.8,
      timestamp: "2026-05-25T13:56:15.819519+00:00",
      source: "Equiti Securities",
    };
    const { client, fetchMock } = makeClient([ok(data)]);
    const res = await client.getQuote("EURUSD", { includeSources: true });
    expect(res.bid).toBe(1.16404);
    expect(res.spread_pips).toBe(1.8);
    const url = urlOf(fetchMock);
    expect(url).toContain("symbol=EURUSD");
    expect(url).toContain("include_sources=true");
  });

  it("getQuotes issues a POST with a JSON body (symbols + fields)", async () => {
    const data = {
      quotes: [{ symbol: "EURUSD", bid: 1.164, ask: 1.1642 }],
      count: 1,
      not_found: null,
      timestamp: "2026-05-25T13:56:15Z",
    };
    const { client, fetchMock } = makeClient([ok(data)]);
    const res = await client.getQuotes(["EURUSD", "GBPUSD"], ["bid", "ask"]);
    expect(res.count).toBe(1);
    const init = initOf(fetchMock);
    expect(init.method).toBe("POST");
    expect(urlOf(fetchMock)).toBe("https://api.test/v1/quotes");
    expect(JSON.parse(init.body as string)).toEqual({
      symbols: ["EURUSD", "GBPUSD"],
      fields: ["bid", "ask"],
    });
    expect((init.headers as Record<string, string>)["Content-Type"]).toBe(
      "application/json",
    );
  });

  it("getOhlc parses candles and forwards timeframe/from/to/limit", async () => {
    const data = {
      symbol: "EURUSD",
      timeframe: "H1",
      candles: [
        {
          time: "2026-05-25T13:00:00Z",
          open: 1.16,
          high: 1.17,
          low: 1.15,
          close: 1.165,
          volume: 1234,
        },
      ],
      count: 1,
      retention: "90d",
    };
    const { client, fetchMock } = makeClient([ok(data)]);
    const res = await client.getOhlc("EURUSD", {
      timeframe: Timeframes.H1,
      from: "2026-05-01T00:00:00Z",
      to: "2026-05-25T00:00:00Z",
      limit: 500,
    });
    expect(res.candles[0]!.close).toBe(1.165);
    expect(res.count).toBe(1);
    const url = urlOf(fetchMock);
    expect(url).toContain("timeframe=H1");
    expect(url).toContain("limit=500");
  });

  it("getTicks requires from/to and parses ticks", async () => {
    const data = {
      symbol: "EURUSD",
      ticks: [
        { time: "2026-05-25T13:00:00.123Z", bid: 1.164, ask: 1.1642, flags: 6 },
      ],
      count: 1,
    };
    const { client, fetchMock } = makeClient([ok(data)]);
    const res = await client.getTicks(
      "EURUSD",
      "2026-05-25T13:00:00Z",
      "2026-05-25T13:30:00Z",
    );
    expect(res.ticks[0]!.flags).toBe(6);
    const url = urlOf(fetchMock);
    expect(url).toContain("from=");
    expect(url).toContain("to=");
  });

  it("getIndicator parses the §7.7 example", async () => {
    const data = {
      symbol: "EURUSD",
      timeframe: "H1",
      indicator: "RSI_14",
      value: 58.34,
      bid: 1.0831,
      ask: 1.0832,
      updated_at: 1711548000,
      server_time: "2026-03-27T14:00:00",
    };
    const { client, fetchMock } = makeClient([ok(data)]);
    const res = await client.getIndicator("EURUSD", Indicators.RSI_14, {
      timeframe: "H1",
    });
    expect(res.value).toBe(58.34);
    expect(res.updated_at).toBe(1711548000);
    const url = urlOf(fetchMock);
    expect(url).toContain("indicator=RSI_14");
  });

  it("getIndicators parses the dict of indicator values", async () => {
    const data = {
      symbol: "EURUSD",
      timeframe: "H1",
      ohlcv: { open: 1.16, high: 1.17, low: 1.15, close: 1.165, volume: 999 },
      bid: 1.164,
      ask: 1.1642,
      indicators: { RSI_14: 58.34, MACD_hist: -0.0002, ATR_14: null },
      count: 3,
      updated_at: 1711548000,
    };
    const { client, fetchMock } = makeClient([ok(data)]);
    const res = await client.getIndicators("EURUSD", { category: "oscillator" });
    expect(res.indicators["RSI_14"]).toBe(58.34);
    expect(res.indicators["ATR_14"]).toBeNull();
    expect(urlOf(fetchMock)).toContain("category=oscillator");
  });

  it("listIndicators parses the catalogue shape", async () => {
    const data = {
      indicators: {
        oscillator: { RSI_14: "Relative Strength Index (14)" },
        trend: { SMA_20: "Simple Moving Average (20)" },
      },
      timeframes: ["M1", "M5", "H1", "D1"],
      categories: ["trend", "oscillator", "volatility", "volume"],
    };
    const { client, fetchMock } = makeClient([ok(data)]);
    const res = await client.listIndicators();
    expect(res.categories).toContain("volume");
    expect(res.indicators["oscillator"]!["RSI_14"]).toContain("Strength");
    expect(urlOf(fetchMock)).toBe("https://api.test/v1/indicators/list");
  });

  it("getIndicatorHistory parses the series", async () => {
    const data = {
      symbol: "EURUSD",
      indicator: "RSI_14",
      timeframe: "H1",
      from: "2026-05-01T00:00:00Z",
      to: "2026-05-02T00:00:00Z",
      count: 2,
      max_window_hours: 720,
      series: [
        { time: "2026-05-01T00:00:00Z", value: 55.1 },
        { time: "2026-05-01T01:00:00Z", value: null },
      ],
    };
    const { client, fetchMock } = makeClient([ok(data)]);
    const res = await client.getIndicatorHistory("EURUSD", "RSI_14", {
      limit: 500,
    });
    expect(res.series).toHaveLength(2);
    expect(res.series[1]!.value).toBeNull();
    expect(urlOf(fetchMock)).toContain("indicator=RSI_14");
  });

  it("getMulti (realtime) joins symbols/indicators with commas", async () => {
    const data = {
      timeframe: "H1",
      data: {
        EURUSD: { RSI_14: 58.3, ADX: 22.1 },
        GBPUSD: { RSI_14: 47.9, ADX: 18.0 },
      },
      not_found: null,
      updated_at: 1711548000,
    };
    const { client, fetchMock } = makeClient([ok(data)]);
    const res = await client.getMulti(
      ["EURUSD", "GBPUSD"],
      [Indicators.RSI_14, Indicators.ADX],
    );
    expect("mode" in res).toBe(false);
    const url = urlOf(fetchMock);
    expect(url).toContain("symbols=EURUSD%2CGBPUSD");
    expect(url).toContain("indicators=RSI_14%2CADX");
  });

  it("getMulti (historical) is selected by `from` and parses mode", async () => {
    const data = {
      timeframe: "H1",
      mode: "historical",
      from: "2026-05-01T00:00:00Z",
      to: "2026-05-02T00:00:00Z",
      data: { EURUSD: [{ time: "2026-05-01T00:00:00Z", RSI_14: 55.1 }] },
      not_found: null,
    };
    const { client, fetchMock } = makeClient([ok(data)]);
    const res = await client.getMulti(["EURUSD"], ["RSI_14"], {
      from: "2026-05-01T00:00:00Z",
      to: "2026-05-02T00:00:00Z",
    });
    expect(res.mode).toBe("historical");
    expect(urlOf(fetchMock)).toContain("from=");
  });

  it("screen serialises minVal/maxVal to min_val/max_val", async () => {
    const data = {
      indicator: "RSI_14",
      timeframe: "H1",
      filter: { min: 70, max: null },
      results: [{ symbol: "EURUSD", value: 72.5, bid: 1.164 }],
      total_matches: 1,
      pagination: { offset: 0, limit: 50, total: 1, has_more: false },
      updated_at: 1711548000,
    };
    const { client, fetchMock } = makeClient([ok(data)]);
    const res = await client.screen(Indicators.RSI_14, {
      minVal: 70,
      sort: "desc",
      limit: 50,
    });
    expect(res.results[0]!.value).toBe(72.5);
    const url = urlOf(fetchMock);
    expect(url).toContain("min_val=70");
    expect(url).not.toContain("minVal");
    expect(url).not.toMatch(/[?&]min=/);
    expect(url).toContain("sort=desc");
  });

  it("getSummary forwards the timeframe positional arg", async () => {
    const data = {
      symbol: "EURUSD",
      timeframe: "H4",
      bias: "bullish",
      bias_strength: "strong",
      confidence: 0.82,
      trend_score: 3,
      momentum_score: 2,
      volatility_score: 1,
      signals: { trend: "up", momentum: "up", volatility: "normal", volume: "high" },
      key_levels: { resistance: [1.18], support: [1.15] },
      bullish_signals: ["RSI rising"],
      bearish_signals: [],
      neutral_signals: [],
      volatility_info: [],
      volume_info: [],
      summary: "Bullish bias",
      recommendations: ["watch 1.18"],
      key_values: {
        bid: 1.164,
        ask: 1.1642,
        rsi_14: 58.3,
        macd_hist: 0.0001,
        adx: 25,
        atr_14: 0.002,
        sma_20: 1.16,
        sma_50: 1.15,
        sma_200: 1.13,
        bb_upper: 1.17,
        bb_lower: 1.15,
        stochastic_k: 80,
        mfi_14: 60,
      },
      updated_at: 1711548000,
    };
    const { client, fetchMock } = makeClient([ok(data)]);
    const res = await client.getSummary("EURUSD", "H4");
    expect(res.bias).toBe("bullish");
    expect(res.bias_strength).toBe("strong");
    expect(urlOf(fetchMock)).toContain("timeframe=H4");
  });

  it("getSpread parses statistics and by_session", async () => {
    const data = {
      symbol: "EURUSD",
      current: { spread_pips: 1.8, spread_points: 18 },
      statistics: {
        period: "24h",
        avg_spread: 1.9,
        min_spread: 1.2,
        max_spread: 3.4,
        std_deviation: 0.4,
      },
      by_session: { asian: 2.1, london: 1.5, new_york: 1.7 },
    };
    const { client, fetchMock } = makeClient([ok(data)]);
    const res = await client.getSpread("EURUSD", "24h");
    expect(res.statistics.avg_spread).toBe(1.9);
    expect(res.by_session.london).toBe(1.5);
    expect(urlOf(fetchMock)).toContain("period=24h");
  });

  it("compareSpread joins symbols and parses the list", async () => {
    const data = {
      period: "24h",
      symbols: [
        {
          symbol: "EURUSD",
          current_pips: 1.8,
          avg_pips: 1.9,
          min_pips: 1.2,
          max_pips: 3.4,
          has_live_data: true,
        },
        {
          symbol: "FAKE",
          current_pips: null,
          avg_pips: null,
          min_pips: null,
          max_pips: null,
          has_live_data: false,
        },
      ],
      count: 2,
    };
    const { client, fetchMock } = makeClient([ok(data)]);
    const res = await client.compareSpread(["EURUSD", "FAKE"], "24h");
    expect(res.count).toBe(2);
    expect(res.symbols[1]!.has_live_data).toBe(false);
    expect(urlOf(fetchMock)).toContain("symbols=EURUSD%2CFAKE");
  });

  it("getSessions parses the session clock", async () => {
    const data = {
      current_time: "2026-06-15T12:00:00Z",
      active_sessions: ["london", "new_york"],
      sessions: {
        sydney: { status: "closed", opens_in: "8h" },
        tokyo: { status: "closed", opens_in: "9h" },
        london: { status: "open", closes_in: "4h" },
        new_york: { status: "open", closes_in: "7h" },
      },
      overlaps: ["london/new_york"],
      next_major_event: { event: "London close", in: "4h" },
    };
    const { client, fetchMock } = makeClient([ok(data)]);
    const res = await client.getSessions();
    expect(res.active_sessions).toContain("london");
    expect(res.sessions.london.status).toBe("open");
    expect(urlOf(fetchMock)).toBe("https://api.test/v1/sessions");
  });

  it("getHeatmap (strength) parses currencies", async () => {
    const data = {
      type: "strength",
      timeframe: "H4",
      currencies: {
        USD: { strength: 7.2, trend: "bullish", change: 0.3, pairs_analyzed: 7 },
        EUR: { strength: 4.1, trend: "bearish", change: -0.2, pairs_analyzed: 7 },
      },
      strongest: "USD",
      weakest: "EUR",
      range: 3.1,
      timestamp: "2026-06-15T12:00:00Z",
    };
    const { client, fetchMock } = makeClient([ok(data)]);
    const res = await client.getHeatmap({ type: "strength", timeframe: "H4" });
    expect(res.type).toBe("strength");
    if (res.type === "strength") {
      expect(res.currencies["USD"]!.strength).toBe(7.2);
    }
    expect(urlOf(fetchMock)).toContain("type=strength");
  });

  it("getHeatmap (correlation) handles available:false", async () => {
    const data = {
      type: "correlation",
      timeframe: "H4",
      correlation_matrix: {},
      available: false,
      message: "Not enough data",
      timestamp: "2026-06-15T12:00:00Z",
    };
    const { client, fetchMock } = makeClient([ok(data)]);
    const res = await client.getHeatmap({ correlations: true });
    expect(res.type).toBe("correlation");
    if (res.type === "correlation") {
      expect(res.available).toBe(false);
    }
    expect(urlOf(fetchMock)).toContain("correlations=true");
  });

  it("getCalendar serialises arrays and nextHours", async () => {
    const data = {
      events: [
        {
          id: "evt1",
          datetime: "2026-06-15T12:30:00",
          currency: "USD",
          event: "CPI",
          impact: "high",
          forecast: "3.1%",
          previous: "3.0%",
          actual: null,
        },
      ],
      count: 1,
      pagination: { offset: 0, limit: 100, total: 1, has_more: false },
      range: { from: "2026-06-15", to: "2026-06-22" },
    };
    const { client, fetchMock } = makeClient([ok(data)]);
    const res = await client.getCalendar({
      currencies: ["USD", "EUR"],
      impact: "high",
      nextHours: 24,
      limit: 100,
    });
    expect(res.events[0]!.event).toBe("CPI");
    const url = urlOf(fetchMock);
    expect(url).toContain("currencies=USD%2CEUR");
    expect(url).toContain("impact=high");
    expect(url).toContain("next_hours=24");
  });

  it("getAccount parses identity & quota", async () => {
    const data = {
      name: "Acme Trading",
      plan: "pro",
      prepaid_credits: 12.5,
      daily_quota: null,
      daily_used: 412,
    };
    const { client, fetchMock } = makeClient([ok(data)]);
    const res = await client.getAccount();
    expect(res.plan).toBe("pro");
    expect(res.daily_quota).toBeNull();
    expect(urlOf(fetchMock)).toBe("https://api.test/v1/monitor/account");
  });

  it("getLayout parses the layout payload", async () => {
    const { client, fetchMock } = makeClient([ok({ layout: null })]);
    const res = await client.getLayout();
    expect(res.layout).toBeNull();
    expect(urlOf(fetchMock)).toBe("https://api.test/v1/monitor/layout");
  });

  it("saveLayout issues a PUT with the layout body", async () => {
    const { client, fetchMock } = makeClient([ok({ saved: true })]);
    const res = await client.saveLayout([{ widget: "quote", symbol: "EURUSD" }]);
    expect(res.saved).toBe(true);
    const init = initOf(fetchMock);
    expect(init.method).toBe("PUT");
    expect(JSON.parse(init.body as string)).toEqual({
      layout: [{ widget: "quote", symbol: "EURUSD" }],
    });
  });

  it("health parses the infra probe", async () => {
    const data = {
      status: "ok",
      components: { redis: { status: "up" }, postgres: { status: "up" } },
    };
    const { client, fetchMock } = makeClient([ok(data)]);
    const res = await client.health();
    expect(res.status).toBe("ok");
    expect(res.components.redis.status).toBe("up");
    // Root probe: resolved against the origin, not the /v1 base.
    expect(urlOf(fetchMock)).toBe("https://api.test/health");
  });

  it("health parses a RAW (non-enveloped) body — the real /health shape", async () => {
    // The live /health endpoint returns a BARE object (no {success,data}
    // envelope), so this exercises the unwrapped-body branch in http.ts.
    const raw = {
      status: "ok",
      components: {
        redis: { status: "ok" },
        postgres: { status: "ok" },
      },
    };
    const { client, fetchMock } = makeClient([{ status: 200, json: raw }]);
    const res = await client.health();
    expect(res.status).toBe("ok");
    expect(res.components.redis.status).toBe("ok");
    // No `data` key was present, yet the bare object is handed back verbatim.
    expect(res).toEqual(raw);
    expect(urlOf(fetchMock)).toBe("https://api.test/health");
  });
});

// ===========================================================================
// Coverage assertion — all 21 endpoints + health are present as methods
// ===========================================================================

describe("coverage", () => {
  it("exposes all 21 endpoints + health as methods", () => {
    const { client } = makeClient([ok({})]);
    const methods = [
      "getSymbols",
      "getSymbol",
      "getQuote",
      "getQuotes",
      "getOhlc",
      "getTicks",
      "getIndicator",
      "getIndicators",
      "listIndicators",
      "getIndicatorHistory",
      "getMulti",
      "screen",
      "getSummary",
      "getSpread",
      "compareSpread",
      "getSessions",
      "getHeatmap",
      "getCalendar",
      "getAccount",
      "getLayout",
      "saveLayout",
      "health",
    ];
    for (const m of methods) {
      expect(typeof (client as unknown as Record<string, unknown>)[m]).toBe(
        "function",
      );
    }
    expect(methods).toHaveLength(22); // 21 endpoints + health
  });

  it("ships the full 42-indicator catalogue", () => {
    expect(ALL_INDICATORS).toHaveLength(42);
    expect(IndicatorsByCategory.trend).toHaveLength(23);
    expect(IndicatorsByCategory.oscillator).toHaveLength(8);
    expect(IndicatorsByCategory.volatility).toHaveLength(7);
    expect(IndicatorsByCategory.volume).toHaveLength(4);
    // naming gotchas
    expect(Indicators.SAR).toBe("SAR");
    expect(Indicators.Volumes).toBe("Volumes");
    expect(Indicators.WilliamsR_14).toBe("WilliamsR_14");
    expect((Indicators as Record<string, string>)["EMA_200"]).toBeUndefined();
    expect((Indicators as Record<string, string>)["RSI_9"]).toBeUndefined();
  });
});

// ===========================================================================
// Error → exception mapping
// ===========================================================================

describe("error mapping", () => {
  it("maps 404 SYMBOL_NOT_FOUND → NotFoundError", async () => {
    const { client } = makeClient([
      err(404, "SYMBOL_NOT_FOUND", "Unknown symbol"),
    ]);
    await expect(client.getSymbol("NOPE")).rejects.toBeInstanceOf(NotFoundError);
    try {
      await makeClient([
        err(404, "SYMBOL_NOT_FOUND", "Unknown symbol"),
      ]).client.getSymbol("NOPE");
    } catch (e) {
      const ae = e as NotFoundError;
      expect(ae.statusCode).toBe(404);
      expect(ae.code).toBe("SYMBOL_NOT_FOUND");
      expect(ae).toBeInstanceOf(TickAtlasAPIError);
    }
  });

  it("maps 401 INVALID_API_KEY → AuthenticationError", async () => {
    const { client } = makeClient([
      err(401, "INVALID_API_KEY", "Key not recognised"),
    ]);
    await expect(client.getQuote("EURUSD")).rejects.toBeInstanceOf(
      AuthenticationError,
    );
  });

  it("maps 403 PLAN_UPGRADE_REQUIRED → PermissionDeniedError", async () => {
    const { client } = makeClient([
      err(403, "PLAN_UPGRADE_REQUIRED", "Upgrade to pro", {
        required_plan: "pro",
      }),
    ]);
    try {
      await client.getTicks("EURUSD", "a", "b");
      expect.unreachable();
    } catch (e) {
      expect(e).toBeInstanceOf(PermissionDeniedError);
      const pe = e as PermissionDeniedError;
      expect(pe.code).toBe("PLAN_UPGRADE_REQUIRED");
      // forward-compatible context fields are exposed via raw
      expect(pe.raw?.["required_plan"]).toBe("pro");
    }
  });

  it("maps 422 VALIDATION_ERROR → ValidationError with details", async () => {
    const details = [
      { type: "int_parsing", loc: ["query", "limit"], msg: "not an int" },
    ];
    const { client } = makeClient([
      err(422, "VALIDATION_ERROR", "Validation failed", { details }),
    ]);
    try {
      await client.getCalendar({ limit: -1 });
      expect.unreachable();
    } catch (e) {
      expect(e).toBeInstanceOf(ValidationError);
      const ve = e as ValidationError;
      expect(ve.statusCode).toBe(422);
      expect(ve.details).toEqual(details);
    }
  });

  it("maps 400 INVALID_TIMEFRAME → ValidationError", async () => {
    const { client } = makeClient([err(400, "INVALID_TIMEFRAME", "bad tf")]);
    await expect(
      client.getOhlc("EURUSD", { timeframe: "X9" }),
    ).rejects.toBeInstanceOf(ValidationError);
  });

  it("does not retry non-retryable 4xx (single fetch call)", async () => {
    const { client, fetchMock } = makeClient([
      err(404, "DATA_NOT_FOUND", "no data"),
    ]);
    await expect(client.getIndicators("EURUSD")).rejects.toBeInstanceOf(
      NotFoundError,
    );
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("synthesises an error when the body is not the expected envelope", async () => {
    const { client } = makeClient([{ status: 404, text: "Not Found" }]);
    try {
      await client.getSymbol("X");
      expect.unreachable();
    } catch (e) {
      expect(e).toBeInstanceOf(NotFoundError);
      expect((e as NotFoundError).code).toBe("HTTP_404");
    }
  });

  it("maps 429 QUOTA_EXCEEDED → RateLimitError with retryAfter (SPEC §5)", async () => {
    // SPEC §5: a quota breach returns 429 with Retry-After: 3600.
    const { client, fetchMock } = makeClient(
      [
        err(429, "QUOTA_EXCEEDED", "Daily quota exhausted", {}, {
          "Retry-After": "3600",
        }),
      ],
      { maxRetries: 0 },
    );
    try {
      await client.getQuote("EURUSD");
      expect.unreachable();
    } catch (e) {
      expect(e).toBeInstanceOf(RateLimitError);
      const re = e as RateLimitError;
      expect(re.statusCode).toBe(429);
      expect(re.code).toBe("QUOTA_EXCEEDED");
      expect(re.retryAfter).toBe(3600);
    }
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("maps 405 / HTTP_405 → ValidationError", async () => {
    // A 405 with no recognised error.code synthesises HTTP_405; any other 4xx
    // is treated as a client/validation-class error.
    const { client } = makeClient([{ status: 405, text: "Method Not Allowed" }]);
    try {
      await client.getSymbol("X");
      expect.unreachable();
    } catch (e) {
      expect(e).toBeInstanceOf(ValidationError);
      const ve = e as ValidationError;
      expect(ve.statusCode).toBe(405);
      expect(ve.code).toBe("HTTP_405");
    }
  });

  it("429 with no Retry-After/X-RateLimit-Reset uses body reset_in_seconds", async () => {
    // No rate-limit headers at all; the delay must fall back to the body's
    // `reset_in_seconds` (4s → 4000ms) rather than computed backoff.
    const { client, fetchMock, sleeps } = makeClient([
      err(429, "RATE_LIMIT_EXCEEDED", "slow down", { reset_in_seconds: 4 }),
      ok({ status: "ok" }),
    ]);
    const res = await client.health();
    expect(res).toEqual({ status: "ok" });
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(sleeps).toEqual([4000]);
  });
});

// ===========================================================================
// Retry behaviour
// ===========================================================================

describe("retry policy", () => {
  it("retries 429 and honours Retry-After (seconds → ms) over backoff", async () => {
    const { client, fetchMock, sleeps } = makeClient([
      err(429, "RATE_LIMIT_EXCEEDED", "slow down", { reset_in_seconds: 2 }, {
        "Retry-After": "2",
      }),
      ok({ status: "ok" }),
    ]);
    const res = await client.health();
    expect(res).toEqual({ status: "ok" });
    expect(fetchMock).toHaveBeenCalledTimes(2);
    // Honoured Retry-After (2s) rather than computed backoff (~250ms).
    expect(sleeps).toEqual([2000]);
  });

  it("RateLimitError carries retryAfter when retries are exhausted", async () => {
    const { client, fetchMock } = makeClient(
      [
        err(429, "RATE_LIMIT_EXCEEDED", "slow down", {}, { "Retry-After": "5" }),
      ],
      { maxRetries: 0 },
    );
    try {
      await client.health();
      expect.unreachable();
    } catch (e) {
      expect(e).toBeInstanceOf(RateLimitError);
      expect((e as RateLimitError).retryAfter).toBe(5);
    }
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("falls back to X-RateLimit-Reset when Retry-After is absent", async () => {
    const { client, sleeps } = makeClient([
      err(429, "RATE_LIMIT_EXCEEDED", "slow", {}, { "X-RateLimit-Reset": "3" }),
      ok({ status: "ok" }),
    ]);
    await client.health();
    expect(sleeps).toEqual([3000]);
  });

  it("retries 5xx with jittered exponential backoff", async () => {
    const { client, fetchMock, sleeps } = makeClient([
      err(500, "INTERNAL_ERROR", "boom"),
      err(503, "SERVICE_UNAVAILABLE", "down"),
      ok({ status: "ok" }),
    ]);
    const res = await client.health();
    expect(res).toEqual({ status: "ok" });
    expect(fetchMock).toHaveBeenCalledTimes(3);
    // base=500, jitter=0.5 → attempt0: 500*1*0.5=250, attempt1: 500*2*0.5=500
    expect(sleeps).toEqual([250, 500]);
  });

  it("retries network errors, then surfaces ServerError on exhaustion", async () => {
    const { client, fetchMock } = makeClient(
      [
        { throw: new TypeError("fetch failed") },
        err(500, "INTERNAL_ERROR", "boom"),
      ],
      { maxRetries: 1 },
    );
    await expect(client.health()).rejects.toBeInstanceOf(ServerError);
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("surfaces TickAtlasNetworkError when all attempts fail at the network", async () => {
    const { client, fetchMock } = makeClient(
      [{ throw: new TypeError("ECONNREFUSED") }],
      { maxRetries: 2 },
    );
    await expect(client.health()).rejects.toBeInstanceOf(TickAtlasNetworkError);
    // 1 initial + 2 retries = 3 attempts
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it("eventually throws ServerError after exhausting 5xx retries", async () => {
    const { client, fetchMock } = makeClient(
      [err(503, "SERVICE_UNAVAILABLE", "down")],
      { maxRetries: 2 },
    );
    await expect(client.health()).rejects.toBeInstanceOf(ServerError);
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });
});

// ===========================================================================
// Timeout (AbortController)
// ===========================================================================

describe("timeout", () => {
  it("aborts via AbortController and raises a timeout network error", async () => {
    // fetch that rejects with an AbortError once the signal fires.
    const fetchImpl = vi.fn(
      (_url: string, init?: RequestInit) =>
        new Promise<Response>((_resolve, reject) => {
          const signal = init?.signal;
          if (signal) {
            signal.addEventListener("abort", () => {
              const e = new Error("The operation was aborted");
              e.name = "AbortError";
              reject(e);
            });
          }
        }),
    );
    const client = new TickAtlas({
      apiKey: "claw_test",
      baseURL: "https://api.test/v1",
      fetch: fetchImpl as unknown as typeof fetch,
      timeout: 5,
      maxRetries: 0,
      sleep: async () => {},
    });
    try {
      await client.health();
      expect.unreachable();
    } catch (e) {
      expect(e).toBeInstanceOf(TickAtlasNetworkError);
      expect((e as TickAtlasNetworkError).isTimeout).toBe(true);
    }
  });
});
