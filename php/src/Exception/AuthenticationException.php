<?php

declare(strict_types=1);

namespace TickAtlas\Exception;

/**
 * HTTP 401 — the API key is missing or not recognised
 * (MISSING_API_KEY, INVALID_API_KEY).
 */
class AuthenticationException extends ApiException
{
}
