<?php

declare(strict_types=1);

namespace TickAtlas\Http;

use GuzzleHttp\Client as GuzzleClient;
use GuzzleHttp\ClientInterface;
use GuzzleHttp\Exception\ConnectException;
use GuzzleHttp\Exception\GuzzleException;
use GuzzleHttp\Psr7\Request;
use Psr\Http\Message\ResponseInterface;
use TickAtlas\Exception\ApiException;
use TickAtlas\Exception\ExceptionFactory;
use TickAtlas\Exception\NetworkException;
use TickAtlas\Exception\RateLimitException;
use TickAtlas\Exception\ServerException;
use TickAtlas\Exception\TickAtlasException;
use TickAtlas\Retry\RealSleeper;
use TickAtlas\Retry\Sleeper;

/**
 * Low-level transport: builds authenticated requests, decodes the JSON envelope,
 * applies the SPEC §5 retry policy, and maps errors to typed exceptions.
 *
 * The {@see \TickAtlas\Client} sits on top of this and exposes per-endpoint
 * methods returning typed models. This class only ever deals in decoded `data`.
 */
final class HttpClient
{
    public const VERSION = '0.1.0';
    public const USER_AGENT = 'tickatlas-php/0.1.0';

    private readonly ClientInterface $http;

    private readonly string $apiKey;

    private readonly string $baseUrl;

    private readonly int $timeout;

    private readonly int $maxRetries;

    private readonly float $backoffBase;

    private readonly float $backoffCap;

    private readonly Sleeper $sleeper;

    public function __construct(
        string $apiKey,
        string $baseUrl,
        int $timeout = 30,
        int $maxRetries = 3,
        float $backoffBase = 0.5,
        float $backoffCap = 30.0,
        ?ClientInterface $httpClient = null,
        ?Sleeper $sleeper = null,
    ) {
        $this->apiKey = $apiKey;
        $this->baseUrl = rtrim($baseUrl, '/');
        $this->timeout = $timeout;
        $this->maxRetries = max(0, $maxRetries);
        $this->backoffBase = $backoffBase;
        $this->backoffCap = $backoffCap;
        $this->sleeper = $sleeper ?? new RealSleeper();
        $this->http = $httpClient ?? new GuzzleClient();
    }

    /**
     * Perform a GET and return the unwrapped `data` payload.
     *
     * @param array<string, mixed> $query
     *
     * @return array<int|string, mixed>
     */
    public function get(string $path, array $query = []): array
    {
        return $this->request('GET', $path, $query, null);
    }

    /**
     * Perform a GET against the API origin (scheme+host) rather than the
     * versioned base URL — for root probes like /health.
     *
     * @param array<string, mixed> $query
     *
     * @return array<int|string, mixed>
     */
    public function getRoot(string $path, array $query = []): array
    {
        return $this->request('GET', $path, $query, null, true);
    }

    /**
     * Perform a POST with a JSON body and return the unwrapped `data` payload.
     *
     * @param array<string, mixed> $body
     *
     * @return array<int|string, mixed>
     */
    public function post(string $path, array $body): array
    {
        return $this->request('POST', $path, [], $body);
    }

    /**
     * Perform a PUT with a JSON body and return the unwrapped `data` payload.
     *
     * @param array<string, mixed> $body
     *
     * @return array<int|string, mixed>
     */
    public function put(string $path, array $body): array
    {
        return $this->request('PUT', $path, [], $body);
    }

    /**
     * Core request loop with retry handling.
     *
     * @param array<string, mixed>      $query
     * @param array<string, mixed>|null $body
     *
     * @return array<int|string, mixed>
     */
    private function request(string $method, string $path, array $query, ?array $body, bool $root = false): array
    {
        $url = $this->buildUrl($path, $query, $root);
        $request = $this->buildRequest($method, $url, $body);

        $attempt = 0;

        $options = [
            'http_errors' => false,
            'timeout' => $this->timeout,
            'connect_timeout' => $this->timeout,
        ];

        while (true) {
            try {
                $response = $this->http->send($request, $options);
            } catch (ConnectException $e) {
                // No response at all: connection/timeout/DNS — retryable.
                if ($this->shouldRetry($attempt)) {
                    $this->sleeper->sleep($this->computeBackoff($attempt));
                    ++$attempt;

                    continue;
                }

                throw new NetworkException(
                    'Network error contacting TickAtlas: ' . $e->getMessage(),
                    (int) $e->getCode(),
                    $e,
                );
            } catch (GuzzleException $e) {
                // Other transport-level failures (no HTTP response): not retried.
                throw new NetworkException(
                    'HTTP transport error: ' . $e->getMessage(),
                    (int) $e->getCode(),
                    $e,
                );
            }

            $status = $response->getStatusCode();

            if ($status >= 200 && $status < 300) {
                return $this->parseSuccess($response);
            }

            $exception = $this->buildException($response);

            if ($this->isRetryable($exception) && $this->shouldRetry($attempt)) {
                $delay = $this->retryDelay($exception, $response, $attempt);
                $this->sleeper->sleep($delay);
                ++$attempt;

                continue;
            }

            throw $exception;
        }
    }

    /**
     * @return array<int|string, mixed>
     */
    private function parseSuccess(ResponseInterface $response): array
    {
        $body = $this->decode($response);

        // Spec envelope: { success: true, data: <object|array> }. Be tolerant if
        // an endpoint ever returns a bare object without the wrapper.
        if (array_key_exists('data', $body)) {
            $data = $body['data'];

            return is_array($data) ? $data : ['value' => $data];
        }

        unset($body['success']);

        return $body;
    }

    private function buildException(ResponseInterface $response): ApiException
    {
        $body = $this->decode($response, allowEmpty: true);
        $requestId = $this->header($response, 'X-Request-ID');
        $retryAfter = $this->retryAfterSeconds($response);

        return ExceptionFactory::fromResponse(
            statusCode: $response->getStatusCode(),
            body: $body,
            requestId: $requestId,
            retryAfter: $retryAfter,
        );
    }

    /**
     * Decode a JSON response body into an associative array.
     *
     * @return array<string, mixed>
     */
    private function decode(ResponseInterface $response, bool $allowEmpty = false): array
    {
        $raw = (string) $response->getBody();

        if ($raw === '') {
            if ($allowEmpty) {
                return [];
            }

            throw new TickAtlasException('Empty response body from TickAtlas API.');
        }

        try {
            $decoded = json_decode($raw, true, 512, JSON_THROW_ON_ERROR);
        } catch (\JsonException $e) {
            if ($allowEmpty) {
                // An error response that wasn't JSON (e.g. an upstream 502 HTML page):
                // surface a synthetic structured body so mapping still works.
                return ['error' => ['message' => 'Non-JSON error response']];
            }

            throw new TickAtlasException(
                'Failed to decode TickAtlas response as JSON: ' . $e->getMessage(),
                0,
                $e,
            );
        }

        if (!is_array($decoded)) {
            return $allowEmpty ? [] : ['value' => $decoded];
        }

        /** @var array<string, mixed> $decoded */
        return $decoded;
    }

    private function isRetryable(ApiException $exception): bool
    {
        // Per SPEC §5: retry 429 and 5xx only (network handled separately above).
        return $exception instanceof RateLimitException
            || $exception instanceof ServerException
            || $exception->getStatusCode() >= 500;
    }

    private function shouldRetry(int $attempt): bool
    {
        return $attempt < $this->maxRetries;
    }

    /**
     * Decide how long to wait before the next attempt: honour Retry-After (or
     * X-RateLimit-Reset) on 429, otherwise use jittered exponential back-off.
     */
    private function retryDelay(ApiException $exception, ResponseInterface $response, int $attempt): float
    {
        if ($exception instanceof RateLimitException) {
            $retryAfter = $exception->getRetryAfter();
            if ($retryAfter === null) {
                $reset = $this->header($response, 'X-RateLimit-Reset');
                if ($reset !== null && is_numeric($reset)) {
                    $retryAfter = (int) $reset;
                }
            }

            if ($retryAfter !== null && $retryAfter >= 0) {
                return (float) $retryAfter;
            }
        }

        return $this->computeBackoff($attempt);
    }

    /**
     * Exponential backoff with full jitter: min(cap, base * 2^attempt) * rand[0,1].
     */
    private function computeBackoff(int $attempt): float
    {
        $exp = $this->backoffBase * (2 ** $attempt);
        $capped = min($this->backoffCap, $exp);

        // Full jitter.
        $jitter = mt_rand() / mt_getrandmax();

        return $capped * $jitter;
    }

    private function retryAfterSeconds(ResponseInterface $response): ?int
    {
        $value = $this->header($response, 'Retry-After');

        if ($value !== null && is_numeric($value)) {
            return (int) $value;
        }

        return null;
    }

    private function header(ResponseInterface $response, string $name): ?string
    {
        if (!$response->hasHeader($name)) {
            return null;
        }

        $line = $response->getHeaderLine($name);

        return $line === '' ? null : $line;
    }

    /**
     * @param array<string, mixed>|null $body
     */
    private function buildRequest(string $method, string $url, ?array $body): Request
    {
        $headers = [
            'X-API-Key' => $this->apiKey,
            'User-Agent' => self::USER_AGENT,
            'Accept' => 'application/json',
        ];

        $payload = null;
        if ($body !== null) {
            $headers['Content-Type'] = 'application/json';
            $payload = json_encode($body, JSON_THROW_ON_ERROR);
        }

        return new Request($method, $url, $headers, $payload);
    }

    /**
     * @param array<string, mixed> $query
     */
    /**
     * The API origin (scheme://host[:port]) derived from the base URL — used
     * for root probes like /health that are not under the /v1 prefix.
     */
    private function origin(): string
    {
        $p = parse_url($this->baseUrl);
        $scheme = $p['scheme'] ?? 'https';
        $host = $p['host'] ?? '';
        $port = isset($p['port']) ? ':' . $p['port'] : '';

        return $scheme . '://' . $host . $port;
    }

    private function buildUrl(string $path, array $query, bool $root = false): string
    {
        $base = $root ? $this->origin() : $this->baseUrl;
        $url = $base . '/' . ltrim($path, '/');

        $normalised = $this->normaliseQuery($query);
        if ($normalised !== []) {
            $url .= '?' . http_build_query($normalised, '', '&', PHP_QUERY_RFC3986);
        }

        return $url;
    }

    /**
     * Drop null params and stringify booleans as `true`/`false`.
     *
     * @param array<string, mixed> $query
     *
     * @return array<string, scalar>
     */
    private function normaliseQuery(array $query): array
    {
        $out = [];
        foreach ($query as $key => $value) {
            if ($value === null) {
                continue;
            }

            if (is_bool($value)) {
                $out[$key] = $value ? 'true' : 'false';

                continue;
            }

            if (is_array($value)) {
                // Comma-join list params (the API uses comma-separated multi-values).
                $out[$key] = implode(',', array_map('strval', $value));

                continue;
            }

            /** @var scalar $value */
            $out[$key] = $value;
        }

        return $out;
    }

    public function getTimeout(): int
    {
        return $this->timeout;
    }

    public function getBaseUrl(): string
    {
        return $this->baseUrl;
    }

    public function getMaxRetries(): int
    {
        return $this->maxRetries;
    }
}
