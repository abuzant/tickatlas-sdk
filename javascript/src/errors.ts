/**
 * Typed exception hierarchy for the TickAtlas SDK.
 *
 * Mirrors SPEC.md §4 exactly:
 *
 *   TickAtlasError                  (base for everything)
 *   ├── TickAtlasAPIError           (server returned a structured error)
 *   │   ├── AuthenticationError     HTTP 401
 *   │   ├── PermissionDeniedError   HTTP 403
 *   │   ├── NotFoundError           HTTP 404
 *   │   ├── ValidationError         HTTP 400 & 422
 *   │   ├── RateLimitError          HTTP 429 (carries retryAfter)
 *   │   └── ServerError             HTTP 5xx
 *   └── TickAtlasNetworkError       no HTTP response (connection/timeout/DNS)
 */

/** Shape of the normalised `error` object returned by the API envelope. */
export interface ApiErrorBody {
  code: string;
  message?: string;
  /** Present for `VALIDATION_ERROR` (HTTP 422). */
  details?: unknown;
  /** Forward-compatible: any additional context keys the API may attach. */
  [key: string]: unknown;
}

/** Base class for every error thrown by the SDK. */
export class TickAtlasError extends Error {
  constructor(message: string, options?: { cause?: unknown }) {
    super(message);
    this.name = "TickAtlasError";
    // Restore prototype chain (required when targeting ES5/transpiled output).
    Object.setPrototypeOf(this, new.target.prototype);
    if (options && "cause" in options) {
      (this as { cause?: unknown }).cause = options.cause;
    }
  }
}

/** Options used to construct a {@link TickAtlasAPIError}. */
export interface ApiErrorOptions {
  statusCode: number;
  code: string;
  message: string;
  details?: unknown;
  requestId?: string | null;
  /** The full raw `error` object from the response envelope. */
  raw?: ApiErrorBody | null;
}

/**
 * Raised when the server returned a structured error envelope
 * (`{ success: false, error: { code, message, ... } }`).
 */
export class TickAtlasAPIError extends TickAtlasError {
  /** HTTP status code of the response. */
  readonly statusCode: number;
  /** Stable, machine-branchable `error.code` string. */
  readonly code: string;
  /** Validation detail payload (present on `VALIDATION_ERROR`). */
  readonly details?: unknown;
  /** `X-Request-ID` correlation id, if present. */
  readonly requestId?: string | null;
  /** The full raw `error` object (read context fields off this). */
  readonly raw?: ApiErrorBody | null;

  constructor(opts: ApiErrorOptions) {
    super(opts.message);
    this.name = "TickAtlasAPIError";
    this.statusCode = opts.statusCode;
    this.code = opts.code;
    this.details = opts.details;
    this.requestId = opts.requestId ?? null;
    this.raw = opts.raw ?? null;
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

/** HTTP 401 — `MISSING_API_KEY`, `INVALID_API_KEY`. */
export class AuthenticationError extends TickAtlasAPIError {
  constructor(opts: ApiErrorOptions) {
    super(opts);
    this.name = "AuthenticationError";
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

/**
 * HTTP 403 — `API_KEY_DISABLED`, `API_KEY_EXPIRED`, `IP_NOT_ALLOWED`,
 * `ACCOUNT_*`, `PERMISSION_DENIED`, `PLAN_UPGRADE_REQUIRED`.
 */
export class PermissionDeniedError extends TickAtlasAPIError {
  constructor(opts: ApiErrorOptions) {
    super(opts);
    this.name = "PermissionDeniedError";
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

/** HTTP 404 — `SYMBOL_NOT_FOUND`, `DATA_NOT_FOUND`, `INDICATOR_NOT_FOUND`. */
export class NotFoundError extends TickAtlasAPIError {
  constructor(opts: ApiErrorOptions) {
    super(opts);
    this.name = "NotFoundError";
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

/**
 * HTTP 400 & 422 — all `INVALID_*`, `RANGE_TOO_LARGE`, `OUTSIDE_RETENTION`,
 * `TOO_MANY_SYMBOLS`, `NO_SYMBOLS`, `VALIDATION_ERROR`, `HTTP_400`, …
 */
export class ValidationError extends TickAtlasAPIError {
  constructor(opts: ApiErrorOptions) {
    super(opts);
    this.name = "ValidationError";
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

/**
 * HTTP 429 — `RATE_LIMIT_EXCEEDED`, `QUOTA_EXCEEDED`, `RATE_LIMITED`.
 * Carries {@link retryAfter} (seconds), derived from the `Retry-After`
 * header (fallback `X-RateLimit-Reset`, then `reset_in_seconds`).
 */
export class RateLimitError extends TickAtlasAPIError {
  /** Seconds to wait before retrying, if the server advertised one. */
  readonly retryAfter?: number | null;

  constructor(opts: ApiErrorOptions & { retryAfter?: number | null }) {
    super(opts);
    this.name = "RateLimitError";
    this.retryAfter = opts.retryAfter ?? null;
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

/** HTTP 5xx — `INTERNAL_ERROR`, `SERVICE_UNAVAILABLE`. */
export class ServerError extends TickAtlasAPIError {
  constructor(opts: ApiErrorOptions) {
    super(opts);
    this.name = "ServerError";
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

/**
 * Raised when no HTTP response was received at all — connection refused, DNS
 * failure, TLS error, or a request that exceeded the configured `timeout`
 * (aborted via `AbortController`).
 */
export class TickAtlasNetworkError extends TickAtlasError {
  /** True when the failure was caused by the request timing out. */
  readonly isTimeout: boolean;

  constructor(
    message: string,
    options?: { cause?: unknown; isTimeout?: boolean },
  ) {
    super(message, options);
    this.name = "TickAtlasNetworkError";
    this.isTimeout = options?.isTimeout ?? false;
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

/**
 * Raised before any request is made when the SDK is misconfigured (e.g. no API
 * key could be resolved). This is a usage error, not an API error.
 */
export class TickAtlasConfigError extends TickAtlasError {
  constructor(message: string) {
    super(message);
    this.name = "TickAtlasConfigError";
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

/**
 * Build the correct {@link TickAtlasAPIError} subclass from an HTTP status and
 * the parsed error body, per the SPEC §4 mapping.
 *
 * Mapping is primarily by HTTP status; `error.code` is used to disambiguate the
 * handful of cross-status codes (e.g. a 403 `RATE_LIMITED` would never occur,
 * but `QUOTA_EXCEEDED` always implies rate limiting).
 */
export function createApiError(
  statusCode: number,
  body: ApiErrorBody,
  requestId: string | null,
  retryAfter: number | null,
): TickAtlasAPIError {
  const code = body.code ?? `HTTP_${statusCode}`;
  const message =
    body.message ?? `TickAtlas API error (HTTP ${statusCode}, code ${code})`;
  const base: ApiErrorOptions = {
    statusCode,
    code,
    message,
    details: body.details,
    requestId,
    raw: body,
  };

  // Code-first disambiguation for the rate-limit family (these can in
  // principle arrive on a non-429 status; honour the code regardless).
  if (
    code === "RATE_LIMIT_EXCEEDED" ||
    code === "QUOTA_EXCEEDED" ||
    code === "RATE_LIMITED"
  ) {
    return new RateLimitError({ ...base, retryAfter });
  }

  switch (statusCode) {
    case 401:
      return new AuthenticationError(base);
    case 403:
      return new PermissionDeniedError(base);
    case 404:
      return new NotFoundError(base);
    case 400:
    case 422:
      return new ValidationError(base);
    case 429:
      return new RateLimitError({ ...base, retryAfter });
    default:
      if (statusCode >= 500) return new ServerError(base);
      // Any other 4xx (e.g. 405) is a client/validation-class error.
      if (statusCode >= 400) return new ValidationError(base);
      // Should not happen (2xx never reaches here) — fall back to base API error.
      return new TickAtlasAPIError(base);
  }
}
