package tickatlas

import (
	"context"
	"errors"
	"net/http"
	"sync/atomic"
	"testing"
	"time"
)

// TestErrorMapping checks that each HTTP status maps to the right typed error,
// that predicates fire, and that code/message/details/request_id are populated.
func TestErrorMapping(t *testing.T) {
	tests := []struct {
		name      string
		status    int
		body      string
		wantPred  func(error) bool
		wantAs    func(error) bool // errors.As against the concrete subtype
		wantCode  string
		wantOther func(t *testing.T, err error)
	}{
		{
			name:     "401 authentication",
			status:   401,
			body:     `{"success":false,"error":{"code":"INVALID_API_KEY","message":"Key not recognised"}}`,
			wantPred: IsAuth,
			wantAs:   func(e error) bool { var x *AuthenticationError; return errors.As(e, &x) },
			wantCode: "INVALID_API_KEY",
		},
		{
			name:     "403 permission denied",
			status:   403,
			body:     `{"success":false,"error":{"code":"PLAN_UPGRADE_REQUIRED","message":"Upgrade","current_plan":"free","required_plan":"pro"}}`,
			wantPred: IsPermissionDenied,
			wantAs:   func(e error) bool { var x *PermissionDeniedError; return errors.As(e, &x) },
			wantCode: "PLAN_UPGRADE_REQUIRED",
			wantOther: func(t *testing.T, err error) {
				var apiErr *APIError
				if !errors.As(err, &apiErr) {
					t.Fatal("not an APIError")
				}
				if apiErr.Details["required_plan"] != "pro" {
					t.Errorf("details.required_plan = %v", apiErr.Details["required_plan"])
				}
			},
		},
		{
			name:     "404 not found",
			status:   404,
			body:     `{"success":false,"error":{"code":"SYMBOL_NOT_FOUND","message":"No such symbol"}}`,
			wantPred: IsNotFound,
			wantAs:   func(e error) bool { var x *NotFoundError; return errors.As(e, &x) },
			wantCode: "SYMBOL_NOT_FOUND",
		},
		{
			name:     "400 validation",
			status:   400,
			body:     `{"success":false,"error":{"code":"INVALID_TIMEFRAME","message":"bad tf","valid_timeframes":["H1","H4"]}}`,
			wantPred: IsValidation,
			wantAs:   func(e error) bool { var x *ValidationError; return errors.As(e, &x) },
			wantCode: "INVALID_TIMEFRAME",
		},
		{
			name:     "422 validation with details",
			status:   422,
			body:     `{"success":false,"error":{"code":"VALIDATION_ERROR","message":"invalid","details":[{"type":"int_parsing","loc":["query","limit"],"msg":"bad"}]}}`,
			wantPred: IsValidation,
			wantAs:   func(e error) bool { var x *ValidationError; return errors.As(e, &x) },
			wantCode: "VALIDATION_ERROR",
			wantOther: func(t *testing.T, err error) {
				var apiErr *APIError
				_ = errors.As(err, &apiErr)
				if apiErr.Details["details"] == nil {
					t.Error("expected details array preserved")
				}
			},
		},
		{
			name:     "500 server",
			status:   500,
			body:     `{"success":false,"error":{"code":"INTERNAL_ERROR","message":"boom"}}`,
			wantPred: IsServer,
			wantAs:   func(e error) bool { var x *ServerError; return errors.As(e, &x) },
			wantCode: "INTERNAL_ERROR",
		},
		{
			name:     "405 method not allowed maps to validation",
			status:   405,
			body:     `{"success":false,"error":{"code":"HTTP_405","message":"Method Not Allowed"}}`,
			wantPred: IsValidation,
			wantAs:   func(e error) bool { var x *ValidationError; return errors.As(e, &x) },
			wantCode: "HTTP_405",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			c, _ := testClient(t, func(w http.ResponseWriter, r *http.Request) {
				w.Header().Set("X-Request-ID", "req-12345")
				writeJSON(w, tt.status, tt.body)
			})
			// Use a method that doesn't retry on this status (404/401/422/400)
			// or has retries disabled. Set maxRetries=0 to avoid waiting.
			c.maxRetries = 0
			_, err := c.Quote(ctx(), "EURUSD", nil)
			if err == nil {
				t.Fatal("expected error")
			}
			if !tt.wantPred(err) {
				t.Errorf("predicate failed for %v", err)
			}
			if !tt.wantAs(err) {
				t.Errorf("errors.As failed for concrete subtype: %v", err)
			}
			var apiErr *APIError
			if !errors.As(err, &apiErr) {
				t.Fatalf("not an *APIError: %v", err)
			}
			if apiErr.Code != tt.wantCode {
				t.Errorf("code = %q, want %q", apiErr.Code, tt.wantCode)
			}
			if apiErr.StatusCode != tt.status {
				t.Errorf("status = %d, want %d", apiErr.StatusCode, tt.status)
			}
			if apiErr.RequestID != "req-12345" {
				t.Errorf("request_id = %q", apiErr.RequestID)
			}
			if len(apiErr.Raw()) == 0 {
				t.Error("raw should be populated")
			}
			if tt.wantOther != nil {
				tt.wantOther(t, err)
			}
		})
	}
}

// TestErrorPredicatesDisjoint ensures predicates don't cross-fire.
func TestErrorPredicatesDisjoint(t *testing.T) {
	c, _ := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, 404, `{"success":false,"error":{"code":"SYMBOL_NOT_FOUND","message":"x"}}`)
	})
	c.maxRetries = 0
	_, err := c.Quote(ctx(), "EURUSD", nil)
	if !IsNotFound(err) {
		t.Fatal("want IsNotFound")
	}
	if IsAuth(err) || IsValidation(err) || IsRateLimit(err) || IsServer(err) || IsNetwork(err) || IsPermissionDenied(err) {
		t.Error("only IsNotFound should be true")
	}
}

// TestRateLimitError_RetryAfter verifies a 429 carries RetryAfter from the
// Retry-After header.
func TestRateLimitError_RetryAfter(t *testing.T) {
	c, _ := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Retry-After", "7")
		writeJSON(w, 429, `{"success":false,"error":{"code":"RATE_LIMIT_EXCEEDED","message":"slow down","reset_in_seconds":7}}`)
	})
	c.maxRetries = 0 // surface the error rather than retrying
	_, err := c.Quote(ctx(), "EURUSD", nil)
	if !IsRateLimit(err) {
		t.Fatalf("want IsRateLimit, got %v", err)
	}
	var rle *RateLimitError
	if !errors.As(err, &rle) {
		t.Fatal("not a *RateLimitError")
	}
	if rle.RetryAfter != 7*time.Second {
		t.Errorf("RetryAfter = %v, want 7s", rle.RetryAfter)
	}
}

// TestRateLimitError_RetryAfterFromBody falls back to reset_in_seconds when no
// header is present.
func TestRateLimitError_RetryAfterFromBody(t *testing.T) {
	c, _ := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, 429, `{"success":false,"error":{"code":"RATE_LIMIT_EXCEEDED","message":"x","reset_in_seconds":12}}`)
	})
	c.maxRetries = 0
	_, err := c.Quote(ctx(), "EURUSD", nil)
	var rle *RateLimitError
	if !errors.As(err, &rle) {
		t.Fatal("not a rate limit error")
	}
	if rle.RetryAfter != 12*time.Second {
		t.Errorf("RetryAfter = %v, want 12s (from body)", rle.RetryAfter)
	}
}

// TestRetryOn429ThenSuccess verifies the client retries a 429 and honours
// Retry-After for the backoff delay.
func TestRetryOn429ThenSuccess(t *testing.T) {
	var calls int32
	var sleptFor time.Duration
	c, _ := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		n := atomic.AddInt32(&calls, 1)
		if n == 1 {
			w.Header().Set("Retry-After", "5")
			writeJSON(w, 429, `{"success":false,"error":{"code":"RATE_LIMIT_EXCEEDED","message":"slow"}}`)
			return
		}
		writeJSON(w, 200, `{"success":true,"data":{"symbol":"EURUSD","bid":1.1,"ask":1.2,"spread":1,"spread_pips":1,"timestamp":"t"}}`)
	})
	// Capture the backoff sleep duration instead of actually sleeping.
	c.sleep = func(ctx context.Context, d time.Duration) error {
		sleptFor = d
		return nil
	}

	res, err := c.Quote(ctx(), "EURUSD", nil)
	if err != nil {
		t.Fatalf("expected success after retry, got %v", err)
	}
	if res.Bid == nil || *res.Bid != 1.1 {
		t.Errorf("bid = %v", res.Bid)
	}
	if atomic.LoadInt32(&calls) != 2 {
		t.Errorf("calls = %d, want 2", calls)
	}
	if sleptFor != 5*time.Second {
		t.Errorf("backoff = %v, want 5s (Retry-After honoured)", sleptFor)
	}
}

// TestNoRetryWhenRetryAfterExceedsCap verifies that a 429 advising a Retry-After
// longer than backoffCap (e.g. QUOTA_EXCEEDED with Retry-After: 3600) is
// surfaced immediately rather than retried — the SDK must not sleep for an hour
// or storm the server with capped-delay retries.
func TestNoRetryWhenRetryAfterExceedsCap(t *testing.T) {
	var calls int32
	var slept bool
	c, _ := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		atomic.AddInt32(&calls, 1)
		w.Header().Set("Retry-After", "3600")
		writeJSON(w, 429, `{"success":false,"error":{"code":"QUOTA_EXCEEDED","message":"daily quota exhausted","reset_in_seconds":3600}}`)
	})
	// maxRetries stays at the default (3); the fix must short-circuit regardless.
	c.sleep = func(ctx context.Context, d time.Duration) error {
		slept = true
		return nil
	}

	_, err := c.Quote(ctx(), "EURUSD", nil)
	if !IsRateLimit(err) {
		t.Fatalf("want IsRateLimit, got %v", err)
	}
	var rle *RateLimitError
	if !errors.As(err, &rle) {
		t.Fatal("not a *RateLimitError")
	}
	if rle.RetryAfter != 3600*time.Second {
		t.Errorf("RetryAfter = %v, want 1h", rle.RetryAfter)
	}
	if got := atomic.LoadInt32(&calls); got != 1 {
		t.Errorf("calls = %d, want 1 (no retry for over-cap Retry-After)", got)
	}
	if slept {
		t.Error("must not sleep when Retry-After exceeds backoffCap")
	}
}

// TestRetryWhenRetryAfterWithinCap verifies a 429 with a Retry-After at or below
// backoffCap is still retried and the server-advised delay is honoured verbatim.
func TestRetryWhenRetryAfterWithinCap(t *testing.T) {
	var calls int32
	var sleptFor time.Duration
	c, _ := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		n := atomic.AddInt32(&calls, 1)
		if n == 1 {
			w.Header().Set("Retry-After", "30") // == backoffCap
			writeJSON(w, 429, `{"success":false,"error":{"code":"RATE_LIMIT_EXCEEDED","message":"slow"}}`)
			return
		}
		writeJSON(w, 200, `{"success":true,"data":{"symbol":"EURUSD","bid":1.1,"ask":1.2,"spread":1,"spread_pips":1,"timestamp":"t"}}`)
	})
	c.sleep = func(ctx context.Context, d time.Duration) error {
		sleptFor = d
		return nil
	}

	res, err := c.Quote(ctx(), "EURUSD", nil)
	if err != nil {
		t.Fatalf("expected success after retry, got %v", err)
	}
	if res.Bid == nil || *res.Bid != 1.1 {
		t.Errorf("bid = %v", res.Bid)
	}
	if got := atomic.LoadInt32(&calls); got != 2 {
		t.Errorf("calls = %d, want 2", got)
	}
	if sleptFor != backoffCap {
		t.Errorf("backoff = %v, want %v (Retry-After honoured, not capped down)", sleptFor, backoffCap)
	}
}

// TestRetryOn500 verifies 5xx is retried.
func TestRetryOn500(t *testing.T) {
	var calls int32
	c, _ := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		if atomic.AddInt32(&calls, 1) < 3 {
			writeJSON(w, 500, `{"success":false,"error":{"code":"INTERNAL_ERROR","message":"boom"}}`)
			return
		}
		writeJSON(w, 200, `{"success":true,"data":{"current_time":"x","active_sessions":[],"sessions":{},"overlaps":[]}}`)
	})
	c.sleep = func(ctx context.Context, d time.Duration) error { return nil }

	if _, err := c.Sessions(ctx()); err != nil {
		t.Fatalf("expected success after retries, got %v", err)
	}
	if atomic.LoadInt32(&calls) != 3 {
		t.Errorf("calls = %d, want 3", calls)
	}
}

// TestRetryExhausted returns the last error after maxRetries.
func TestRetryExhausted(t *testing.T) {
	var calls int32
	c, _ := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		atomic.AddInt32(&calls, 1)
		writeJSON(w, 503, `{"success":false,"error":{"code":"SERVICE_UNAVAILABLE","message":"down"}}`)
	})
	c.sleep = func(ctx context.Context, d time.Duration) error { return nil }
	c.maxRetries = 2

	_, err := c.Sessions(ctx())
	if !IsServer(err) {
		t.Fatalf("want server error, got %v", err)
	}
	if got := atomic.LoadInt32(&calls); got != 3 { // 1 + 2 retries
		t.Errorf("calls = %d, want 3", got)
	}
}

// TestNoRetryOn404 confirms client errors are not retried.
func TestNoRetryOn404(t *testing.T) {
	var calls int32
	c, _ := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		atomic.AddInt32(&calls, 1)
		writeJSON(w, 404, `{"success":false,"error":{"code":"SYMBOL_NOT_FOUND","message":"x"}}`)
	})
	c.sleep = func(ctx context.Context, d time.Duration) error { return nil }

	_, err := c.Quote(ctx(), "NOPE", nil)
	if !IsNotFound(err) {
		t.Fatalf("want not found, got %v", err)
	}
	if got := atomic.LoadInt32(&calls); got != 1 {
		t.Errorf("calls = %d, want 1 (no retry)", got)
	}
}

// TestContextCancellationDuringBackoff verifies ctx cancellation aborts the
// retry sleep and surfaces a NetworkError.
func TestContextCancellationDuringBackoff(t *testing.T) {
	c, _ := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, 500, `{"success":false,"error":{"code":"INTERNAL_ERROR","message":"x"}}`)
	})
	cancelCtx, cancel := context.WithCancel(context.Background())
	// The real sleepCtx honours ctx; simulate a cancelled ctx by returning its
	// error from sleep.
	c.sleep = func(ctx context.Context, d time.Duration) error {
		cancel()
		return ctx.Err()
	}

	_, err := c.Sessions(cancelCtx)
	if !IsNetwork(err) {
		t.Fatalf("want network error from cancellation, got %v", err)
	}
	if !errors.Is(err, context.Canceled) {
		t.Errorf("error should wrap context.Canceled: %v", err)
	}
}

// TestNetworkErrorRetried verifies transport failures are retried then surfaced
// as NetworkError.
func TestNetworkErrorRetried(t *testing.T) {
	c, srv := testClient(t, func(w http.ResponseWriter, r *http.Request) {})
	srv.Close() // force connection failures
	c.sleep = func(ctx context.Context, d time.Duration) error { return nil }
	c.maxRetries = 2

	_, err := c.Sessions(ctx())
	if !IsNetwork(err) {
		t.Fatalf("want network error, got %v", err)
	}
}

// TestSleepCtxRespectsCancellation tests the real sleepCtx helper directly.
func TestSleepCtxRespectsCancellation(t *testing.T) {
	ctxC, cancel := context.WithCancel(context.Background())
	cancel()
	if err := sleepCtx(ctxC, time.Hour); err == nil {
		t.Fatal("expected ctx error from cancelled context")
	}

	// A short sleep with a live context returns nil.
	if err := sleepCtx(context.Background(), time.Millisecond); err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
}

// TestBackoffDelayJitter verifies the computed backoff respects base/cap and
// uses the injected rng.
func TestBackoffDelayJitter(t *testing.T) {
	c := &Client{randFloat: func() float64 { return 1.0 }}
	// attempt 0: base * 2^0 * 1.0 = 500ms
	if d := c.backoffDelay(0, nil); d != backoffBase {
		t.Errorf("attempt 0 delay = %v, want %v", d, backoffBase)
	}
	// Large attempt is capped.
	if d := c.backoffDelay(20, nil); d != backoffCap {
		t.Errorf("attempt 20 delay = %v, want cap %v", d, backoffCap)
	}
	// Half jitter halves the delay.
	c.randFloat = func() float64 { return 0.5 }
	if d := c.backoffDelay(1, nil); d != backoffBase {
		t.Errorf("attempt 1 with 0.5 jitter = %v, want %v", d, backoffBase)
	}
}
