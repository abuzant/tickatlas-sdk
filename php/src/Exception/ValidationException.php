<?php

declare(strict_types=1);

namespace TickAtlas\Exception;

/**
 * HTTP 400 & 422 — the request was rejected as invalid (all INVALID_* codes,
 * RANGE_TOO_LARGE, OUTSIDE_RETENTION, TOO_MANY_SYMBOLS, NO_SYMBOLS,
 * VALIDATION_ERROR, HTTP_400, ...).
 *
 * For 422 VALIDATION_ERROR the per-field problems are available via
 * {@see ApiException::getDetails()} under the `details` key.
 */
class ValidationException extends ApiException
{
}
