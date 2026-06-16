// Package tickatlas is the official Go SDK for the TickAtlas market-data API
// (https://tickatlas.com).
//
// It covers the full v1 API-key surface — symbols, real-time quotes, OHLC and
// tick history, 42 technical indicators, screening, market-bias summaries,
// spread statistics, currency-strength heatmaps, the economic calendar and
// account/monitoring endpoints — plus the unauthenticated infrastructure probes.
//
// The SDK depends only on the Go standard library.
//
// # Quick start
//
//	client, err := tickatlas.NewClient(tickatlas.WithAPIKey("tk_..."))
//	if err != nil {
//		log.Fatal(err)
//	}
//
//	quote, err := client.Quote(context.Background(), "EURUSD", nil)
//	if err != nil {
//		log.Fatal(err)
//	}
//	fmt.Println(quote.Bid, quote.Ask)
//
// # Authentication
//
// Every request is authenticated with an API key sent in the X-API-Key header.
// The key is resolved, in priority order, from the [WithAPIKey] option and then
// the TICKATLAS_API_KEY environment variable. The key is treated as an opaque
// string and is never logged or serialized by the SDK.
//
// # Configuration
//
// The client is created with [NewClient] and configured with functional
// options: [WithAPIKey], [WithBaseURL], [WithHTTPClient], [WithMaxRetries],
// [WithTimeout] and [WithUserAgent]. The base URL defaults to
// https://tickatlas.com/v1 and can be overridden with the option or the
// TICKATLAS_BASE_URL environment variable.
//
// # Errors
//
// All API errors are typed. The server's structured errors are reported as
// [*APIError]; transport failures as [*NetworkError]. Use [errors.As] to inspect
// a specific type, or the predicate helpers ([IsAuth], [IsPermissionDenied],
// [IsNotFound], [IsValidation], [IsRateLimit], [IsServer], [IsNetwork]) to branch
// on a class of error. [*RateLimitError] exposes the server-advised retry delay
// via its RetryAfter field.
//
// # Retries
//
// The client automatically retries 429, 5xx and network errors using exponential
// backoff with full jitter, honouring the Retry-After header on 429 responses and
// respecting context cancellation during backoff sleeps. Retries default to a
// maximum of 3 (4 attempts total) and are configurable with [WithMaxRetries].
//
// # WebSocket
//
// The platform also exposes a WebSocket quote stream. It is not part of the
// 0.1.0 REST SDK surface and is tracked as a future addition.
package tickatlas
