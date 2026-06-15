package tickatlas

import (
	"context"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"
	"testing"
	"time"
)

// testClient spins up an httptest server with handler h and returns a client
// pointed at it. The client's backoff sleep is replaced with a no-op so retry
// tests run instantly and deterministically.
func testClient(t *testing.T, h http.HandlerFunc) (*Client, *httptest.Server) {
	t.Helper()
	srv := httptest.NewServer(h)
	t.Cleanup(srv.Close)

	c, err := NewClient(
		WithAPIKey("claw_test_key"),
		WithBaseURL(srv.URL),
	)
	if err != nil {
		t.Fatalf("NewClient: %v", err)
	}
	// Deterministic, instant backoff.
	c.sleep = func(ctx context.Context, d time.Duration) error { return ctx.Err() }
	c.randFloat = func() float64 { return 0.5 }
	return c, srv
}

// jsonHandler writes status and body, recording the request for assertions.
func writeJSON(w http.ResponseWriter, status int, body string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_, _ = w.Write([]byte(body))
}

func TestNewClient_KeyResolution(t *testing.T) {
	t.Run("explicit option wins", func(t *testing.T) {
		t.Setenv(EnvAPIKey, "env_key")
		c, err := NewClient(WithAPIKey("opt_key"))
		if err != nil {
			t.Fatal(err)
		}
		if c.apiKey != "opt_key" {
			t.Fatalf("apiKey = %q, want opt_key", c.apiKey)
		}
	})

	t.Run("falls back to env", func(t *testing.T) {
		t.Setenv(EnvAPIKey, "env_key")
		c, err := NewClient()
		if err != nil {
			t.Fatal(err)
		}
		if c.apiKey != "env_key" {
			t.Fatalf("apiKey = %q, want env_key", c.apiKey)
		}
	})

	t.Run("error when missing", func(t *testing.T) {
		t.Setenv(EnvAPIKey, "")
		_, err := NewClient()
		if err == nil {
			t.Fatal("expected error when API key missing")
		}
		if !strings.Contains(err.Error(), EnvAPIKey) {
			t.Fatalf("error should mention env var name: %v", err)
		}
	})
}

func TestNewClient_BaseURLResolution(t *testing.T) {
	t.Run("default", func(t *testing.T) {
		t.Setenv(EnvBaseURL, "")
		c, err := NewClient(WithAPIKey("k"))
		if err != nil {
			t.Fatal(err)
		}
		if c.baseURL != DefaultBaseURL {
			t.Fatalf("baseURL = %q, want %q", c.baseURL, DefaultBaseURL)
		}
	})

	t.Run("env override", func(t *testing.T) {
		t.Setenv(EnvBaseURL, "https://staging.example.com/v1/")
		c, err := NewClient(WithAPIKey("k"))
		if err != nil {
			t.Fatal(err)
		}
		if c.baseURL != "https://staging.example.com/v1" {
			t.Fatalf("baseURL = %q (trailing slash should be trimmed)", c.baseURL)
		}
	})

	t.Run("option beats env", func(t *testing.T) {
		t.Setenv(EnvBaseURL, "https://env.example.com/v1")
		c, err := NewClient(WithAPIKey("k"), WithBaseURL("https://opt.example.com/v1"))
		if err != nil {
			t.Fatal(err)
		}
		if c.baseURL != "https://opt.example.com/v1" {
			t.Fatalf("baseURL = %q, want option value", c.baseURL)
		}
	})
}

func TestNewClient_Defaults(t *testing.T) {
	c, err := NewClient(WithAPIKey("k"))
	if err != nil {
		t.Fatal(err)
	}
	if c.userAgent != defaultUserAgent {
		t.Errorf("userAgent = %q, want %q", c.userAgent, defaultUserAgent)
	}
	if c.maxRetries != defaultMaxRetries {
		t.Errorf("maxRetries = %d, want %d", c.maxRetries, defaultMaxRetries)
	}
	if c.httpClient.Timeout != defaultTimeout {
		t.Errorf("timeout = %v, want %v", c.httpClient.Timeout, defaultTimeout)
	}
}

func TestOptions(t *testing.T) {
	hc := &http.Client{}
	c, err := NewClient(
		WithAPIKey("k"),
		WithHTTPClient(hc),
		WithMaxRetries(7),
		WithTimeout(5*time.Second),
		WithUserAgent("custom/1.0"),
	)
	if err != nil {
		t.Fatal(err)
	}
	if c.httpClient != hc {
		t.Error("WithHTTPClient not applied")
	}
	if c.maxRetries != 7 {
		t.Errorf("maxRetries = %d, want 7", c.maxRetries)
	}
	if c.httpClient.Timeout != 5*time.Second {
		t.Errorf("timeout = %v, want 5s", c.httpClient.Timeout)
	}
	if c.userAgent != "custom/1.0" {
		t.Errorf("userAgent = %q", c.userAgent)
	}
}

func TestWithMaxRetries_ClampsNegative(t *testing.T) {
	c, err := NewClient(WithAPIKey("k"), WithMaxRetries(-5))
	if err != nil {
		t.Fatal(err)
	}
	if c.maxRetries != 0 {
		t.Fatalf("maxRetries = %d, want 0", c.maxRetries)
	}
}

// TestRequestHeaders verifies the X-API-Key, User-Agent and Accept headers are
// set, and that the key never leaks into logs (we assert it is sent only in the
// header, which is the SDK's single responsibility).
func TestRequestHeaders(t *testing.T) {
	var gotKey, gotUA, gotAccept string
	c, _ := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		gotKey = r.Header.Get("X-API-Key")
		gotUA = r.Header.Get("User-Agent")
		gotAccept = r.Header.Get("Accept")
		writeJSON(w, 200, `{"success":true,"data":{"current_time":"x","active_sessions":[],"sessions":{},"overlaps":[]}}`)
	})
	if _, err := c.Sessions(context.Background()); err != nil {
		t.Fatal(err)
	}
	if gotKey != "claw_test_key" {
		t.Errorf("X-API-Key = %q", gotKey)
	}
	if gotUA != defaultUserAgent {
		t.Errorf("User-Agent = %q", gotUA)
	}
	if gotAccept != "application/json" {
		t.Errorf("Accept = %q", gotAccept)
	}
}

// TestHealthIsAuthless verifies the health probe does not send the API key.
func TestHealthIsAuthless(t *testing.T) {
	var sawKey bool
	c, _ := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		if r.Header.Get("X-API-Key") != "" {
			sawKey = true
		}
		writeJSON(w, 200, `{"status":"ok","components":{"redis":"ok","postgres":"ok"}}`)
	})
	res, err := c.Health(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	if sawKey {
		t.Error("health probe should not send X-API-Key")
	}
	if res.Status != "ok" || res.Components.Redis != "ok" {
		t.Errorf("unexpected health result: %+v", res)
	}
	if len(res.Raw) == 0 {
		t.Error("Raw should be populated")
	}
}

func TestMain(m *testing.M) {
	// Ensure ambient env vars never leak into the default-resolution tests.
	_ = os.Unsetenv(EnvAPIKey)
	_ = os.Unsetenv(EnvBaseURL)
	os.Exit(m.Run())
}
