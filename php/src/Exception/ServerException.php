<?php

declare(strict_types=1);

namespace TickAtlas\Exception;

/**
 * HTTP 5xx — the server failed to process a valid request
 * (INTERNAL_ERROR, SERVICE_UNAVAILABLE, HTTP_503).
 *
 * Retried automatically per SPEC §5 before surfacing.
 */
class ServerException extends ApiException
{
}
