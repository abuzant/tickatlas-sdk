//go:build integration

// Package tickatlas integration tests exercise the SDK against the live
// TickAtlas API. They are read-only and gated behind a build tag *and* runtime
// environment variables so they never run in normal `go test ./...` invocations.
//
// To run them:
//
//	RUN_INTEGRATION=1 TICKATLAS_API_KEY=claw_... go test -tags integration ./...
//
// They are skipped (not failed) unless RUN_INTEGRATION=1 and TICKATLAS_API_KEY
// are both set. The write path (SaveLayout) is deliberately NOT exercised — it
// would overwrite a real user's saved dashboard layout.
package tickatlas

import (
	"context"
	"os"
	"testing"
	"time"
)

// integrationClient builds a live client or skips the test if the gating
// environment is not present.
func integrationClient(t *testing.T) *Client {
	t.Helper()
	if os.Getenv("RUN_INTEGRATION") != "1" {
		t.Skip("integration tests disabled: set RUN_INTEGRATION=1 to enable")
	}
	if os.Getenv(EnvAPIKey) == "" {
		t.Skip("integration tests require " + EnvAPIKey)
	}
	c, err := NewClient(WithTimeout(20 * time.Second))
	if err != nil {
		t.Fatalf("NewClient: %v", err)
	}
	return c
}

func TestIntegration_Health(t *testing.T) {
	c := integrationClient(t)
	res, err := c.Health(context.Background())
	if err != nil {
		t.Fatalf("Health: %v", err)
	}
	if res.Status == "" {
		t.Error("empty status")
	}
}

func TestIntegration_Account(t *testing.T) {
	c := integrationClient(t)
	res, err := c.Account(context.Background())
	if err != nil {
		t.Fatalf("Account: %v", err)
	}
	if res.Plan == "" {
		t.Error("empty plan")
	}
}

func TestIntegration_Symbols(t *testing.T) {
	c := integrationClient(t)
	res, err := c.Symbols(context.Background(), &SymbolsParams{Limit: ptrIntI(5)})
	if err != nil {
		t.Fatalf("Symbols: %v", err)
	}
	if len(res.Symbols) == 0 {
		t.Error("no symbols returned")
	}
}

func TestIntegration_Quote(t *testing.T) {
	c := integrationClient(t)
	res, err := c.Quote(context.Background(), "EURUSD", nil)
	if err != nil {
		t.Fatalf("Quote: %v", err)
	}
	if res.Symbol != "EURUSD" {
		t.Errorf("symbol = %q", res.Symbol)
	}
}

func TestIntegration_Indicator(t *testing.T) {
	c := integrationClient(t)
	res, err := c.Indicator(context.Background(), "EURUSD", RSI14, nil)
	if err != nil {
		t.Fatalf("Indicator: %v", err)
	}
	if res.Indicator != RSI14 {
		t.Errorf("indicator = %q", res.Indicator)
	}
}

func TestIntegration_Sessions(t *testing.T) {
	c := integrationClient(t)
	if _, err := c.Sessions(context.Background()); err != nil {
		t.Fatalf("Sessions: %v", err)
	}
}

// ptrIntI is a local helper so the integration build (which excludes the unit
// test files) still compiles.
func ptrIntI(i int) *int { return &i }
