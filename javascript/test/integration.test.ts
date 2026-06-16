/**
 * Live integration smoke test — READ-ONLY.
 *
 * Gated: runs ONLY when both `RUN_INTEGRATION=1` and `TICKATLAS_API_KEY` are
 * set. Otherwise every case is skipped (so CI / `npm test` never hits the
 * network). It exercises a handful of safe, read-only endpoints; it never
 * calls the write endpoint (`saveLayout`).
 *
 * Run explicitly with:
 *   RUN_INTEGRATION=1 TICKATLAS_API_KEY=tk_xxx npm run test:integration
 */

import { describe, it, expect, beforeAll } from "vitest";
import { TickAtlas } from "../src/index.js";

const enabled =
  typeof process !== "undefined" &&
  process.env?.RUN_INTEGRATION === "1" &&
  !!process.env?.TICKATLAS_API_KEY;

const d = enabled ? describe : describe.skip;

d("integration (live, read-only)", () => {
  // Constructed lazily in beforeAll so the skipped suite never instantiates a
  // client (which would throw a config error when no key is present).
  let client!: TickAtlas;
  beforeAll(() => {
    // Key/base URL resolved from the environment by the client itself.
    client = new TickAtlas();
  });

  it("health() returns a status", async () => {
    const res = await client.health();
    expect(res).toHaveProperty("status");
  });

  it("getAccount() returns identity & quota", async () => {
    const res = await client.getAccount();
    expect(res).toHaveProperty("plan");
    expect(res).toHaveProperty("daily_used");
  });

  it("getSymbols() returns a paginated list", async () => {
    const res = await client.getSymbols({ limit: 5 });
    expect(Array.isArray(res.symbols)).toBe(true);
    expect(res.pagination.limit).toBe(5);
  });

  it("getQuote('EURUSD') returns a quote", async () => {
    const res = await client.getQuote("EURUSD");
    expect(res.symbol).toBe("EURUSD");
    expect(typeof res.spread).toBe("number");
  });

  it("listIndicators() returns the catalogue", async () => {
    const res = await client.listIndicators();
    expect(Array.isArray(res.categories)).toBe(true);
  });

  it("getSessions() returns the session clock", async () => {
    const res = await client.getSessions();
    expect(res).toHaveProperty("current_time");
  });
});
