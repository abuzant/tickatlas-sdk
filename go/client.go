package tickatlas

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"math"
	"math/rand"
	"net/http"
	"net/url"
	"os"
	"strconv"
	"strings"
	"time"
)

// Default client configuration.
const (
	defaultTimeout    = 30 * time.Second
	defaultMaxRetries = 3
	backoffBase       = 500 * time.Millisecond
	backoffCap        = 30 * time.Second
)

// Client is a TickAtlas API client. It is safe for concurrent use by multiple
// goroutines. Create one with [NewClient].
type Client struct {
	apiKey     string
	baseURL    string
	userAgent  string
	httpClient *http.Client
	maxRetries int

	// sleep and randFloat are injection points used to make the retry backoff
	// deterministic in tests. They default to time.After-based sleeping and
	// math/rand respectively.
	sleep     func(ctx context.Context, d time.Duration) error
	randFloat func() float64
}

// Option configures a [Client]. Pass options to [NewClient].
type Option func(*Client)

// WithAPIKey sets the API key. It takes priority over the TICKATLAS_API_KEY
// environment variable. The key is treated as an opaque string.
func WithAPIKey(key string) Option {
	return func(c *Client) { c.apiKey = key }
}

// WithBaseURL overrides the API base URL. It takes priority over the
// TICKATLAS_BASE_URL environment variable and the production default. A trailing
// slash is trimmed.
func WithBaseURL(baseURL string) Option {
	return func(c *Client) { c.baseURL = baseURL }
}

// WithHTTPClient sets the underlying [*http.Client]. Use this to customise
// transport, proxies or TLS. If the supplied client has a zero Timeout it is
// left untouched; otherwise [WithTimeout] can be used to set it.
func WithHTTPClient(hc *http.Client) Option {
	return func(c *Client) {
		if hc != nil {
			c.httpClient = hc
		}
	}
}

// WithMaxRetries sets the maximum number of retries for retryable failures
// (429, 5xx and network errors). The default is 3 (4 attempts total). Negative
// values are clamped to 0.
func WithMaxRetries(n int) Option {
	return func(c *Client) {
		if n < 0 {
			n = 0
		}
		c.maxRetries = n
	}
}

// WithTimeout sets the per-request timeout on the underlying HTTP client. The
// default is 30s. A non-positive duration disables the client-level timeout
// (callers can still bound requests with the context).
func WithTimeout(d time.Duration) Option {
	return func(c *Client) { c.httpClient.Timeout = d }
}

// WithUserAgent overrides the User-Agent header. The default is
// "tickatlas-go/<version>".
func WithUserAgent(ua string) Option {
	return func(c *Client) {
		if ua != "" {
			c.userAgent = ua
		}
	}
}

// NewClient creates a TickAtlas API client.
//
// The API key is resolved from [WithAPIKey], then the TICKATLAS_API_KEY
// environment variable; if neither is set, NewClient returns an error. The base
// URL is resolved from [WithBaseURL], then TICKATLAS_BASE_URL, then the
// production default ([DefaultBaseURL]).
func NewClient(opts ...Option) (*Client, error) {
	c := &Client{
		baseURL:    "",
		userAgent:  defaultUserAgent,
		httpClient: &http.Client{Timeout: defaultTimeout},
		maxRetries: defaultMaxRetries,
	}

	for _, opt := range opts {
		opt(c)
	}

	// Key resolution: option -> env -> error.
	if c.apiKey == "" {
		c.apiKey = os.Getenv(EnvAPIKey)
	}
	if c.apiKey == "" {
		return nil, fmt.Errorf("tickatlas: API key is required: set it with WithAPIKey or the %s environment variable", EnvAPIKey)
	}

	// Base URL resolution: option -> env -> default.
	if c.baseURL == "" {
		c.baseURL = os.Getenv(EnvBaseURL)
	}
	if c.baseURL == "" {
		c.baseURL = DefaultBaseURL
	}
	c.baseURL = strings.TrimRight(c.baseURL, "/")

	// Default injection points.
	c.sleep = sleepCtx
	c.randFloat = rand.Float64

	return c, nil
}

// sleepCtx sleeps for d or until ctx is done, whichever comes first. It returns
// ctx.Err() if the context is cancelled during the sleep.
func sleepCtx(ctx context.Context, d time.Duration) error {
	if d <= 0 {
		return ctx.Err()
	}
	t := time.NewTimer(d)
	defer t.Stop()
	select {
	case <-ctx.Done():
		return ctx.Err()
	case <-t.C:
		return nil
	}
}

// request describes a single HTTP call.
type request struct {
	method string
	// path is relative to the base URL (for example "/quote").
	path  string
	query url.Values
	// body, when non-nil, is JSON-encoded as the request body.
	body any
	// authless skips the X-API-Key header (used for infra probes).
	authless bool
	// root resolves path against the API origin (scheme+host) instead of the
	// versioned base URL — for root probes like /health, which live at
	// https://tickatlas.com/health, not /v1/health.
	root bool
}

// do executes req with retries and decodes the success envelope's data block
// into out (which may be nil to discard the body). It is the single funnel for
// every API call.
func (c *Client) do(ctx context.Context, req request, out any) error {
	var bodyBytes []byte
	if req.body != nil {
		b, err := json.Marshal(req.body)
		if err != nil {
			return fmt.Errorf("tickatlas: encoding request body: %w", err)
		}
		bodyBytes = b
	}

	base := c.baseURL
	if req.root {
		if u, err := url.Parse(c.baseURL); err == nil && u.Host != "" {
			base = u.Scheme + "://" + u.Host
		}
	}
	fullURL := base + req.path
	if len(req.query) > 0 {
		fullURL += "?" + req.query.Encode()
	}

	var lastErr error
	// attempts = 1 initial try + maxRetries.
	for attempt := 0; attempt <= c.maxRetries; attempt++ {
		if attempt > 0 {
			delay := c.backoffDelay(attempt-1, lastErr)
			if err := c.sleep(ctx, delay); err != nil {
				// Context cancelled/expired during backoff.
				return &NetworkError{Err: err}
			}
		}

		var bodyReader io.Reader
		if bodyBytes != nil {
			bodyReader = bytes.NewReader(bodyBytes)
		}

		httpReq, err := http.NewRequestWithContext(ctx, req.method, fullURL, bodyReader)
		if err != nil {
			// Malformed request: not retryable.
			return fmt.Errorf("tickatlas: building request: %w", err)
		}
		httpReq.Header.Set("Accept", "application/json")
		httpReq.Header.Set("User-Agent", c.userAgent)
		if bodyBytes != nil {
			httpReq.Header.Set("Content-Type", "application/json")
		}
		if !req.authless {
			httpReq.Header.Set("X-API-Key", c.apiKey)
		}

		resp, err := c.httpClient.Do(httpReq)
		if err != nil {
			// Transport failure. Honour context cancellation immediately.
			if ctxErr := ctx.Err(); ctxErr != nil {
				return &NetworkError{Err: ctxErr}
			}
			lastErr = &NetworkError{Err: err}
			continue // network errors are retryable
		}

		decodeErr := c.handleResponse(resp, out)
		if decodeErr == nil {
			return nil
		}

		if isRetryable(decodeErr) && attempt < c.maxRetries {
			lastErr = decodeErr
			continue
		}
		return decodeErr
	}

	return lastErr
}

// handleResponse reads resp, maps non-2xx into the typed error hierarchy, and on
// success unwraps the data block into out.
func (c *Client) handleResponse(resp *http.Response, out any) error {
	defer resp.Body.Close()
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return &NetworkError{Err: fmt.Errorf("reading response body: %w", err)}
	}

	requestID := resp.Header.Get("X-Request-ID")

	if resp.StatusCode >= 200 && resp.StatusCode < 300 {
		if out == nil {
			return nil
		}
		// Health/status/ready probes are not wrapped in the success envelope.
		if hr, ok := out.(*HealthResult); ok {
			if err := json.Unmarshal(body, hr); err != nil {
				return fmt.Errorf("tickatlas: decoding response: %w", err)
			}
			hr.Raw = append(json.RawMessage(nil), body...)
			return nil
		}
		var env struct {
			Success bool            `json:"success"`
			Data    json.RawMessage `json:"data"`
		}
		if err := json.Unmarshal(body, &env); err != nil {
			return fmt.Errorf("tickatlas: decoding response envelope: %w", err)
		}
		if len(env.Data) == 0 {
			// 2xx with no data block: nothing to decode.
			return nil
		}
		if err := json.Unmarshal(env.Data, out); err != nil {
			return fmt.Errorf("tickatlas: decoding response data: %w", err)
		}
		return nil
	}

	return c.parseError(resp.StatusCode, body, requestID, resp.Header)
}

// parseError converts an error response into the appropriate typed error.
func (c *Client) parseError(status int, body []byte, requestID string, header http.Header) error {
	base := APIError{
		StatusCode: status,
		RequestID:  requestID,
	}

	var env errorEnvelope
	if err := json.Unmarshal(body, &env); err == nil && len(env.Error) > 0 {
		base.raw = append(json.RawMessage(nil), env.Error...)
		var fields map[string]any
		if err := json.Unmarshal(env.Error, &fields); err == nil {
			if code, ok := fields["code"].(string); ok {
				base.Code = code
			}
			if msg, ok := fields["message"].(string); ok {
				base.Message = msg
			}
			delete(fields, "code")
			delete(fields, "message")
			if len(fields) > 0 {
				base.Details = fields
			}
		}
	} else {
		// Body was not the expected envelope; keep it raw for debugging.
		base.raw = append(json.RawMessage(nil), body...)
		if s := strings.TrimSpace(string(body)); s != "" {
			base.Message = s
		}
	}

	switch {
	case status == http.StatusUnauthorized:
		return &AuthenticationError{base}
	case status == http.StatusForbidden:
		return &PermissionDeniedError{base}
	case status == http.StatusNotFound:
		return &NotFoundError{base}
	case status == http.StatusTooManyRequests:
		return &RateLimitError{APIError: base, RetryAfter: retryAfter(header, base.Details)}
	case status == http.StatusBadRequest, status == http.StatusUnprocessableEntity:
		return &ValidationError{base}
	case status >= 500:
		return &ServerError{base}
	default:
		// Any other 4xx (for example 405) maps to a generic API error; the
		// validation class is the closest semantic fit for client-side faults.
		if status >= 400 && status < 500 {
			return &ValidationError{base}
		}
		return &base
	}
}

// retryAfter extracts the server-advised retry delay for a 429, preferring the
// Retry-After header, then the JSON reset_in_seconds field, then
// X-RateLimit-Reset.
func retryAfter(header http.Header, details map[string]any) time.Duration {
	if v := header.Get("Retry-After"); v != "" {
		if secs, err := strconv.Atoi(strings.TrimSpace(v)); err == nil && secs >= 0 {
			return time.Duration(secs) * time.Second
		}
		// Retry-After may also be an HTTP date.
		if t, err := http.ParseTime(strings.TrimSpace(v)); err == nil {
			if d := time.Until(t); d > 0 {
				return d
			}
		}
	}
	if details != nil {
		if secs, ok := numberFrom(details["reset_in_seconds"]); ok {
			return time.Duration(secs * float64(time.Second))
		}
	}
	if v := header.Get("X-RateLimit-Reset"); v != "" {
		if secs, err := strconv.Atoi(strings.TrimSpace(v)); err == nil && secs >= 0 {
			return time.Duration(secs) * time.Second
		}
	}
	return 0
}

// numberFrom coerces a JSON-decoded value (float64 or numeric string) to a
// float64.
func numberFrom(v any) (float64, bool) {
	switch n := v.(type) {
	case float64:
		return n, true
	case json.Number:
		f, err := n.Float64()
		return f, err == nil
	case string:
		f, err := strconv.ParseFloat(n, 64)
		return f, err == nil
	default:
		return 0, false
	}
}

// backoffDelay computes the delay before the given retry. For rate-limit errors
// it honours the server-advised Retry-After; otherwise it uses exponential
// backoff with full jitter: min(cap, base * 2^attempt) * rand.
func (c *Client) backoffDelay(attempt int, lastErr error) time.Duration {
	var rle *RateLimitError
	if errors.As(lastErr, &rle) && rle.RetryAfter > 0 {
		if rle.RetryAfter > backoffCap {
			return backoffCap
		}
		return rle.RetryAfter
	}

	// Exponential backoff with full jitter.
	exp := float64(backoffBase) * math.Pow(2, float64(attempt))
	if exp > float64(backoffCap) {
		exp = float64(backoffCap)
	}
	jitter := c.randFloat()
	return time.Duration(exp * jitter)
}

// isRetryable reports whether err is a transient failure worth retrying:
// network errors, 429, or any 5xx.
func isRetryable(err error) bool {
	var ne *NetworkError
	if errors.As(err, &ne) {
		return true
	}
	var rle *RateLimitError
	if errors.As(err, &rle) {
		return true
	}
	var se *ServerError
	if errors.As(err, &se) {
		return true
	}
	return false
}
