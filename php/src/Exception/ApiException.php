<?php

declare(strict_types=1);

namespace TickAtlas\Exception;

/**
 * Thrown when the server returns a structured error envelope
 * (`{"success": false, "error": {...}}`).
 *
 * Subclasses correspond to HTTP status families (see SPEC §4). The original
 * machine-branchable `error.code`, the human message, any extra context
 * (`details` and other fields), the request id and the raw decoded body are all
 * exposed for callers that need to inspect them.
 */
class ApiException extends TickAtlasException
{
    /**
     * @param array<string, mixed> $details extra context keys from the error
     *                                       object (everything beyond code/message),
     *                                       e.g. valid_timeframes, available_symbols
     * @param array<string, mixed> $raw     the full decoded response body
     */
    /**
     * The stable, machine-branchable error code (e.g. SYMBOL_NOT_FOUND).
     *
     * Note: this is stored separately from \Exception::$code (which is an int and
     * cannot be redeclared as a readonly string). Use {@see getCode()} to read it.
     */
    public readonly ?string $errorCode;

    public function __construct(
        string $message,
        public readonly int $statusCode,
        ?string $code = null,
        public readonly array $details = [],
        public readonly ?string $requestId = null,
        public readonly array $raw = [],
        ?\Throwable $previous = null,
    ) {
        $this->errorCode = $code;
        parent::__construct($message, 0, $previous);
    }

    /** HTTP status code returned by the server. */
    public function getStatusCode(): int
    {
        return $this->statusCode;
    }

    /**
     * Stable, machine-branchable error code (e.g. SYMBOL_NOT_FOUND), if present.
     *
     * This is the SDK's `error.code`. (\Exception::getCode() is final and returns
     * the integer code, so this distinct accessor exposes the string code.)
     */
    public function getErrorCode(): ?string
    {
        return $this->errorCode;
    }

    /**
     * Extra context fields carried alongside code/message (forward-compatible:
     * unknown keys are preserved verbatim).
     *
     * @return array<string, mixed>
     */
    public function getDetails(): array
    {
        return $this->details;
    }

    /** The X-Request-ID correlation id, if the server sent one. */
    public function getRequestId(): ?string
    {
        return $this->requestId;
    }

    /**
     * The complete decoded response body.
     *
     * @return array<string, mixed>
     */
    public function getRaw(): array
    {
        return $this->raw;
    }
}
