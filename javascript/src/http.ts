/**
 * Low-level HTTP transport for the TickAtlas SDK: a thin wrapper over the
 * global `fetch` that handles auth headers, query serialisation, timeouts
 * (via `AbortController`), envelope unwrapping, error mapping, and the retry
 * policy from SPEC.md §5.
 *
 * Zero runtime dependencies: relies on the platform `fetch`/`AbortController`
 * available in Node 18+ and modern browsers.
 */

import {
  TickAtlasNetworkError,
  createApiError,
  type ApiErrorBody,
} from "./errors.js";
import type { RateLimitInfo } from "./types.js";

/** SDK version — kept in sync with package.json. */
export const SDK_VERSION = "0.1.0";

/** A query value before serialisation. `undefined`/`null` params are dropped. */
export type QueryValue =
  | string
  | number
  | boolean
  | null
  | undefined
  | Array<string | number>;

export type QueryParams = Record<string, QueryValue>;

export interface RequestOptions {
  method: "GET" | "POST" | "PUT";
  path: string;
  query?: QueryParams;
  body?: unknown;
  /** Per-request timeout override (ms). */
  timeout?: number;
  /** Per-request signal to allow caller-driven cancellation. */
  signal?: AbortSignal;
}

/** The fully-resolved transport configuration. */
export interface TransportConfig {
  apiKey: string;
  baseURL: string;
  timeout: number;
  maxRetries: number;
  backoffBase: number;
  /** Max backoff cap in ms (SPEC §5: ≈30s). */
  backoffCap: number;
  /** Injectable fetch (defaults to global fetch). */
  fetch: typeof fetch;
  /** Injectable sleep — overridable in tests for determinism. */
  sleep: (ms: number) => Promise<void>;
  /** Injectable jitter in [0,1) — overridable in tests for determinism. */
  jitter: () => number;
  /** Whether to send a `User-Agent` header (Node only; browsers forbid it). */
  sendUserAgent: boolean;
}

const RETRYABLE_STATUSES = new Set([429, 500, 502, 503, 504]);

/** Default sleep implementation. */
export const defaultSleep = (ms: number): Promise<void> =>
  new Promise((resolve) => setTimeout(resolve, ms));

/** Default full-jitter implementation. */
export const defaultJitter = (): number => Math.random();

/** Serialise query params, dropping `undefined`/`null`, joining arrays w/ commas. */
function buildQueryString(query: QueryParams | undefined): string {
  if (!query) return "";
  const sp = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value === undefined || value === null) continue;
    if (Array.isArray(value)) {
      if (value.length === 0) continue;
      sp.append(key, value.join(","));
    } else {
      sp.append(key, String(value));
    }
  }
  const qs = sp.toString();
  return qs ? `?${qs}` : "";
}

/** Parse an integer header, returning null when absent/unparseable. */
function parseIntHeader(headers: Headers, name: string): number | null {
  const raw = headers.get(name);
  if (raw === null) return null;
  const n = Number.parseInt(raw, 10);
  return Number.isNaN(n) ? null : n;
}

/** Extract rate-limit metadata from response headers. */
export function parseRateLimitInfo(headers: Headers): RateLimitInfo {
  return {
    limit: parseIntHeader(headers, "X-RateLimit-Limit"),
    remaining: parseIntHeader(headers, "X-RateLimit-Remaining"),
    reset: parseIntHeader(headers, "X-RateLimit-Reset"),
    requestId: headers.get("X-Request-ID"),
  };
}

/**
 * Determine the retry delay for a 429: honour `Retry-After` (seconds), falling
 * back to `X-RateLimit-Reset`, then to the body's `reset_in_seconds`. Returns
 * milliseconds, or null when no server hint is present.
 */
function retryAfterMs(
  headers: Headers,
  body: ApiErrorBody | null,
): number | null {
  const ra = parseIntHeader(headers, "Retry-After");
  if (ra !== null) return ra * 1000;
  const reset = parseIntHeader(headers, "X-RateLimit-Reset");
  if (reset !== null) return reset * 1000;
  const bodyReset = body?.["reset_in_seconds"];
  if (typeof bodyReset === "number") return bodyReset * 1000;
  return null;
}

/** Compute full-jitter exponential backoff for a given attempt (0-indexed). */
function backoffMs(config: TransportConfig, attempt: number): number {
  const exp = config.backoffBase * Math.pow(2, attempt);
  const capped = Math.min(config.backoffCap, exp);
  return capped * config.jitter();
}

interface SuccessEnvelope<T> {
  success: true;
  data: T;
}

interface ErrorEnvelope {
  success: false;
  error: ApiErrorBody;
}

/**
 * Execute a request with retries and return the unwrapped, typed `data`.
 *
 * Retries on 429, 5xx, and network/timeout errors only; everything else throws
 * immediately. Backoff is full-jitter exponential, except 429 honours the
 * server's `Retry-After` hint when present.
 */
export async function request<T>(
  config: TransportConfig,
  opts: RequestOptions,
): Promise<T> {
  const url = config.baseURL.replace(/\/+$/, "") + opts.path + buildQueryString(opts.query);
  const maxAttempts = config.maxRetries + 1;

  let lastError: unknown;

  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    const isLastAttempt = attempt === maxAttempts - 1;

    // --- Build per-attempt request --------------------------------------
    const headers: Record<string, string> = {
      "X-API-Key": config.apiKey,
      Accept: "application/json",
    };
    if (config.sendUserAgent) {
      headers["User-Agent"] = `tickatlas-js/${SDK_VERSION}`;
    }
    let bodyInit: string | undefined;
    if (opts.body !== undefined) {
      headers["Content-Type"] = "application/json";
      bodyInit = JSON.stringify(opts.body);
    }

    // --- Timeout via AbortController (combined with caller signal) -------
    const controller = new AbortController();
    const timeoutMs = opts.timeout ?? config.timeout;
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    let timedOut = false;
    const onTimeout = () => {
      timedOut = true;
    };
    controller.signal.addEventListener("abort", onTimeout, { once: true });

    let abortListener: (() => void) | undefined;
    if (opts.signal) {
      if (opts.signal.aborted) controller.abort();
      else {
        abortListener = () => controller.abort();
        opts.signal.addEventListener("abort", abortListener, { once: true });
      }
    }

    let response: Response;
    try {
      response = await config.fetch(url, {
        method: opts.method,
        headers,
        body: bodyInit,
        signal: controller.signal,
      });
    } catch (err) {
      clearTimeout(timer);
      if (abortListener && opts.signal) {
        opts.signal.removeEventListener("abort", abortListener);
      }
      // Caller explicitly aborted (not our timeout) → surface, don't retry.
      if (opts.signal?.aborted && !timedOut) {
        throw new TickAtlasNetworkError("Request aborted by caller", {
          cause: err,
        });
      }
      const netErr = new TickAtlasNetworkError(
        timedOut
          ? `Request timed out after ${timeoutMs}ms`
          : `Network request failed: ${(err as Error)?.message ?? String(err)}`,
        { cause: err, isTimeout: timedOut },
      );
      lastError = netErr;
      if (isLastAttempt) throw netErr;
      await config.sleep(backoffMs(config, attempt));
      continue;
    } finally {
      clearTimeout(timer);
      if (abortListener && opts.signal) {
        opts.signal.removeEventListener("abort", abortListener);
      }
    }

    // --- Parse body -----------------------------------------------------
    const requestId = response.headers.get("X-Request-ID");
    const text = await response.text();
    let parsed: unknown = undefined;
    if (text.length > 0) {
      try {
        parsed = JSON.parse(text);
      } catch {
        parsed = undefined;
      }
    }

    // --- Success --------------------------------------------------------
    if (response.ok) {
      const env = parsed as SuccessEnvelope<T> | undefined;
      if (env && typeof env === "object" && "data" in env) {
        return env.data;
      }
      // Tolerate responses that are not wrapped (e.g. infra probes return the
      // object directly); hand back whatever we parsed.
      return parsed as T;
    }

    // --- Error envelope -------------------------------------------------
    const env = parsed as Partial<ErrorEnvelope> | undefined;
    const errorBody: ApiErrorBody =
      env && typeof env === "object" && env.error && typeof env.error === "object"
        ? env.error
        : {
            code: `HTTP_${response.status}`,
            message:
              text.length > 0
                ? text
                : `TickAtlas API returned HTTP ${response.status}`,
          };

    const retryMs =
      response.status === 429 ? retryAfterMs(response.headers, errorBody) : null;
    const apiError = createApiError(
      response.status,
      errorBody,
      requestId,
      retryMs !== null ? Math.round(retryMs / 1000) : null,
    );

    const retryable = RETRYABLE_STATUSES.has(response.status);
    if (!retryable || isLastAttempt) {
      throw apiError;
    }

    lastError = apiError;
    const delay =
      response.status === 429 && retryMs !== null
        ? retryMs
        : backoffMs(config, attempt);
    await config.sleep(delay);
  }

  // Unreachable in practice (loop either returns or throws), but satisfies TS.
  throw lastError ??
    new TickAtlasNetworkError("Request failed after all retries");
}
