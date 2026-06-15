<?php

declare(strict_types=1);

namespace TickAtlas\Exception;

/**
 * Thrown for client-side misconfiguration before any request is made, e.g. a
 * missing API key or an invalid base URL.
 */
class ConfigurationException extends TickAtlasException
{
}
