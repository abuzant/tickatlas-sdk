/**
 * Test helpers: a tiny fetch mock and a factory for a deterministic client
 * (no real network, no real timers, no random jitter).
 */

import { vi } from "vitest";
import { TickAtlas } from "../src/index.js";

export interface MockResponseSpec {
  status?: number;
  /** JSON body (object). Mutually exclusive with `text`. */
  json?: unknown;
  /** Raw text body. */
  text?: string;
  /** Response headers. */
  headers?: Record<string, string>;
  /** Throw this instead of resolving (simulates a network error). */
  throw?: unknown;
}

/** Build a `Response`-like object that the SDK's transport understands. */
export function makeResponse(spec: MockResponseSpec): Response {
  const status = spec.status ?? 200;
  const headers = new Headers(spec.headers ?? {});
  const bodyText =
    spec.text !== undefined
      ? spec.text
      : spec.json !== undefined
        ? JSON.stringify(spec.json)
        : "";
  return {
    ok: status >= 200 && status < 300,
    status,
    headers,
    text: async () => bodyText,
  } as Response;
}

/**
 * Create a mocked fetch that returns the given specs in sequence. The LAST
 * spec is reused for any further calls (handy for "always 200" cases).
 */
export function sequenceFetch(specs: MockResponseSpec[]): typeof fetch {
  let i = 0;
  return vi.fn(async () => {
    const spec = specs[Math.min(i, specs.length - 1)];
    i += 1;
    if (spec?.throw !== undefined) throw spec.throw;
    return makeResponse(spec ?? {});
  }) as unknown as typeof fetch;
}

export interface TestClientResult {
  client: TickAtlas;
  fetchMock: ReturnType<typeof vi.fn>;
  sleepMock: ReturnType<typeof vi.fn>;
  /** Records of ms passed to the injected sleep (i.e. retry delays). */
  sleeps: number[];
}

/** A wrapped success envelope, the way the API returns 2xx bodies. */
export function ok(data: unknown): MockResponseSpec {
  return { status: 200, json: { success: true, data } };
}

/** An error envelope, the way the API returns non-2xx bodies. */
export function err(
  status: number,
  code: string,
  message = "error",
  extra: Record<string, unknown> = {},
  headers: Record<string, string> = {},
): MockResponseSpec {
  return {
    status,
    json: { success: false, error: { code, message, ...extra } },
    headers,
  };
}

/**
 * Build a TickAtlas client wired to a sequenced mock fetch with deterministic
 * sleep (records delays, resolves instantly) and zero jitter.
 */
export function makeClient(
  specs: MockResponseSpec[],
  overrides: Record<string, unknown> = {},
): TestClientResult {
  const fetchMock = sequenceFetch(specs) as unknown as ReturnType<typeof vi.fn>;
  const sleeps: number[] = [];
  const sleepMock = vi.fn(async (ms: number) => {
    sleeps.push(ms);
  });
  const client = new TickAtlas({
    apiKey: "claw_test_key_do_not_use",
    baseURL: "https://api.test/v1",
    fetch: fetchMock as unknown as typeof fetch,
    sleep: sleepMock as unknown as (ms: number) => Promise<void>,
    jitter: () => 0.5, // deterministic
    ...overrides,
  });
  return { client, fetchMock, sleepMock, sleeps };
}
