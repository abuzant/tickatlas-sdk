package tickatlas

import (
	"encoding/json"
	"errors"
	"fmt"
	"time"
)

// errorEnvelope is the wire shape of an error response body:
//
//	{ "success": false, "error": { "code": "...", "message": "...", ... } }
type errorEnvelope struct {
	Success bool            `json:"success"`
	Error   json.RawMessage `json:"error"`
}

// APIError is returned when the TickAtlas server responds with a structured
// error envelope. It corresponds to TickAtlasAPIError in the SDK contract (§4)
// and is the base type for every server-side error class.
//
// Callers typically branch on the error class with the predicate helpers
// ([IsAuth], [IsNotFound], …) or with [errors.As] against the concrete subtype
// (for example [*RateLimitError] to read RetryAfter). The machine-branchable
// [APIError.Code] and the forward-compatible [APIError.Details] map expose the
// full server context, including extra keys the SDK does not model explicitly.
type APIError struct {
	// StatusCode is the HTTP status code of the response.
	StatusCode int
	// Code is the stable, machine-branchable error code (for example
	// "SYMBOL_NOT_FOUND"). It may be empty if the server omitted it.
	Code string
	// Message is the human-readable error description.
	Message string
	// Details holds every field of the error object other than code/message,
	// so callers can read context keys such as valid_timeframes,
	// available_symbols, required_plan, limit, reset_in_seconds, etc. For
	// VALIDATION_ERROR responses the "details" array is available here under
	// the "details" key.
	Details map[string]any
	// RequestID is the X-Request-ID correlation header, if present.
	RequestID string

	// raw is the verbatim error object as returned by the server.
	raw json.RawMessage
}

// Error implements the error interface.
func (e *APIError) Error() string {
	switch {
	case e.Code != "" && e.Message != "":
		return fmt.Sprintf("tickatlas: %s (code=%s, status=%d)", e.Message, e.Code, e.StatusCode)
	case e.Code != "":
		return fmt.Sprintf("tickatlas: %s (status=%d)", e.Code, e.StatusCode)
	case e.Message != "":
		return fmt.Sprintf("tickatlas: %s (status=%d)", e.Message, e.StatusCode)
	default:
		return fmt.Sprintf("tickatlas: request failed with status %d", e.StatusCode)
	}
}

// Raw returns the verbatim JSON of the server's error object.
func (e *APIError) Raw() json.RawMessage { return e.raw }

// The structured error subtypes below embed [APIError] by value and expose it
// through Unwrap, so that both errors.As(err, &someSubtype) and
// errors.As(err, &apiErr) (with apiErr of type *APIError) succeed against the
// same error value. The predicate helpers ([IsAuth] etc.) rely on the former;
// callers wanting the shared fields use the latter.

// AuthenticationError is an [APIError] for HTTP 401 responses
// (MISSING_API_KEY, INVALID_API_KEY).
type AuthenticationError struct{ APIError }

// Unwrap exposes the embedded [*APIError].
func (e *AuthenticationError) Unwrap() error { return &e.APIError }

// PermissionDeniedError is an [APIError] for HTTP 403 responses
// (API_KEY_DISABLED, API_KEY_EXPIRED, IP_NOT_ALLOWED, ACCOUNT_*,
// PERMISSION_DENIED, PLAN_UPGRADE_REQUIRED).
type PermissionDeniedError struct{ APIError }

// Unwrap exposes the embedded [*APIError].
func (e *PermissionDeniedError) Unwrap() error { return &e.APIError }

// NotFoundError is an [APIError] for HTTP 404 responses
// (SYMBOL_NOT_FOUND, DATA_NOT_FOUND, INDICATOR_NOT_FOUND).
type NotFoundError struct{ APIError }

// Unwrap exposes the embedded [*APIError].
func (e *NotFoundError) Unwrap() error { return &e.APIError }

// ValidationError is an [APIError] for HTTP 400 and 422 responses
// (all INVALID_*, RANGE_TOO_LARGE, OUTSIDE_RETENTION, TOO_MANY_SYMBOLS,
// NO_SYMBOLS, VALIDATION_ERROR, HTTP_400, …).
type ValidationError struct{ APIError }

// Unwrap exposes the embedded [*APIError].
func (e *ValidationError) Unwrap() error { return &e.APIError }

// RateLimitError is an [APIError] for HTTP 429 responses
// (RATE_LIMIT_EXCEEDED, QUOTA_EXCEEDED, RATE_LIMITED).
type RateLimitError struct {
	APIError
	// RetryAfter is the server-advised delay before retrying, taken from the
	// Retry-After header (falling back to the JSON reset_in_seconds field, then
	// X-RateLimit-Reset). It is zero if the server advised no delay.
	RetryAfter time.Duration
}

// Unwrap exposes the embedded [*APIError].
func (e *RateLimitError) Unwrap() error { return &e.APIError }

// ServerError is an [APIError] for HTTP 5xx responses
// (INTERNAL_ERROR, SERVICE_UNAVAILABLE).
type ServerError struct{ APIError }

// Unwrap exposes the embedded [*APIError].
func (e *ServerError) Unwrap() error { return &e.APIError }

// NetworkError wraps a transport-level failure where no HTTP response was
// received (connection refused, timeout, DNS failure, context cancellation).
// It corresponds to TickAtlasNetworkError in the SDK contract (§4).
type NetworkError struct {
	// Err is the underlying transport error.
	Err error
}

// Error implements the error interface.
func (e *NetworkError) Error() string {
	return fmt.Sprintf("tickatlas: network error: %v", e.Err)
}

// Unwrap returns the underlying transport error so callers can match it with
// [errors.Is] (for example against context.Canceled or os.ErrDeadlineExceeded).
func (e *NetworkError) Unwrap() error { return e.Err }

// asAPIError extracts the embedded [*APIError] from any of the structured error
// types, allowing the predicates to treat the whole hierarchy uniformly.
func asAPIError(err error) (*APIError, bool) {
	var apiErr *APIError
	if errors.As(err, &apiErr) {
		return apiErr, true
	}
	return nil, false
}

// IsAuth reports whether err is (or wraps) an [*AuthenticationError] (HTTP 401).
func IsAuth(err error) bool {
	var e *AuthenticationError
	return errors.As(err, &e)
}

// IsPermissionDenied reports whether err is (or wraps) a
// [*PermissionDeniedError] (HTTP 403).
func IsPermissionDenied(err error) bool {
	var e *PermissionDeniedError
	return errors.As(err, &e)
}

// IsNotFound reports whether err is (or wraps) a [*NotFoundError] (HTTP 404).
func IsNotFound(err error) bool {
	var e *NotFoundError
	return errors.As(err, &e)
}

// IsValidation reports whether err is (or wraps) a [*ValidationError]
// (HTTP 400 or 422).
func IsValidation(err error) bool {
	var e *ValidationError
	return errors.As(err, &e)
}

// IsRateLimit reports whether err is (or wraps) a [*RateLimitError] (HTTP 429).
func IsRateLimit(err error) bool {
	var e *RateLimitError
	return errors.As(err, &e)
}

// IsServer reports whether err is (or wraps) a [*ServerError] (HTTP 5xx).
func IsServer(err error) bool {
	var e *ServerError
	return errors.As(err, &e)
}

// IsNetwork reports whether err is (or wraps) a [*NetworkError] (no HTTP
// response: connection, timeout or DNS failure).
func IsNetwork(err error) bool {
	var e *NetworkError
	return errors.As(err, &e)
}

// IsAPIError reports whether err is (or wraps) any structured server error
// ([*APIError] or one of its subtypes). When it returns true the pointer out
// parameter, if non-nil, is populated with the embedded [*APIError].
func IsAPIError(err error) bool {
	_, ok := asAPIError(err)
	return ok
}
