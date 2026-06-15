<?php

declare(strict_types=1);

namespace TickAtlas\Exception;

/**
 * Thrown when no HTTP response was received: connection refused, DNS failure,
 * TLS error or timeout. These are retried by the client per SPEC §5 before the
 * exception surfaces.
 */
class NetworkException extends TickAtlasException
{
}
