<?php

declare(strict_types=1);

namespace TickAtlas\Exception;

/**
 * Base class for every exception thrown by the TickAtlas SDK.
 *
 * Catch this to handle any error originating from the client. More specific
 * subclasses (see {@see ApiException} and {@see NetworkException}) let you
 * branch on the failure mode.
 */
class TickAtlasException extends \RuntimeException
{
}
