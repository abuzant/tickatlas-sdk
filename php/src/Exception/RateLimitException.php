<?php

declare(strict_types=1);

namespace TickAtlas\Exception;

/**
 * HTTP 429 — rate limit or quota exceeded (RATE_LIMIT_EXCEEDED, QUOTA_EXCEEDED,
 * RATE_LIMITED).
 *
 * The client retries these automatically (honouring Retry-After) up to
 * `maxRetries`; if retries are exhausted this surfaces with {@see $retryAfter}
 * set to the number of seconds the server asked the caller to wait.
 */
class RateLimitException extends ApiException
{
    /**
     * @param array<string, mixed> $details
     * @param array<string, mixed> $raw
     */
    public function __construct(
        string $message,
        int $statusCode,
        ?string $code = null,
        array $details = [],
        ?string $requestId = null,
        array $raw = [],
        public readonly ?int $retryAfter = null,
        ?\Throwable $previous = null,
    ) {
        parent::__construct($message, $statusCode, $code, $details, $requestId, $raw, $previous);
    }

    /** Seconds the server asked the caller to wait before retrying, if provided. */
    public function getRetryAfter(): ?int
    {
        return $this->retryAfter;
    }
}
