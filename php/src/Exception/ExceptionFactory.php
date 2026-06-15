<?php

declare(strict_types=1);

namespace TickAtlas\Exception;

/**
 * Builds the correct {@see ApiException} subclass from an HTTP status, decoded
 * error body and request id, per the hierarchy in SPEC §4.
 *
 * Mapping is primarily by HTTP status; a small set of `error.code` values are
 * used to disambiguate where status alone is insufficient (e.g. 400 vs 404 are
 * already distinct by status, but PLAN_UPGRADE_REQUIRED on a 403 still maps to
 * PermissionDenied). When status is unexpected we fall back on the code, then on
 * the generic {@see ApiException}.
 */
final class ExceptionFactory
{
    /**
     * @param array<string, mixed> $body the full decoded response body
     */
    public static function fromResponse(
        int $statusCode,
        array $body,
        ?string $requestId = null,
        ?int $retryAfter = null,
    ): ApiException {
        $error = is_array($body['error'] ?? null) ? $body['error'] : [];

        $code = isset($error['code']) ? (string) $error['code'] : null;
        $message = isset($error['message']) && $error['message'] !== ''
            ? (string) $error['message']
            : self::defaultMessage($statusCode, $code);

        // Extra context = everything in the error object except code/message.
        $details = $error;
        unset($details['code'], $details['message']);

        $class = self::resolveClass($statusCode, $code);

        if ($class === RateLimitException::class) {
            return new RateLimitException(
                message: $message,
                statusCode: $statusCode,
                code: $code,
                details: $details,
                requestId: $requestId,
                raw: $body,
                retryAfter: $retryAfter,
            );
        }

        /** @var class-string<ApiException> $class */
        return new $class(
            message: $message,
            statusCode: $statusCode,
            code: $code,
            details: $details,
            requestId: $requestId,
            raw: $body,
        );
    }

    /**
     * @return class-string<ApiException>
     */
    private static function resolveClass(int $statusCode, ?string $code): string
    {
        // Code-driven overrides that must win regardless of (or alongside) status.
        switch ($code) {
            case 'PLAN_UPGRADE_REQUIRED':
            case 'PERMISSION_DENIED':
                return PermissionDeniedException::class;
            case 'RATE_LIMIT_EXCEEDED':
            case 'QUOTA_EXCEEDED':
            case 'RATE_LIMITED':
                return RateLimitException::class;
        }

        return match (true) {
            $statusCode === 401 => AuthenticationException::class,
            $statusCode === 403 => PermissionDeniedException::class,
            $statusCode === 404 => NotFoundException::class,
            $statusCode === 429 => RateLimitException::class,
            $statusCode === 400, $statusCode === 405, $statusCode === 422 => ValidationException::class,
            $statusCode >= 500 => ServerException::class,
            default => ApiException::class,
        };
    }

    private static function defaultMessage(int $statusCode, ?string $code): string
    {
        if ($code !== null && $code !== '') {
            return sprintf('TickAtlas API error %d (%s)', $statusCode, $code);
        }

        return sprintf('TickAtlas API error %d', $statusCode);
    }
}
