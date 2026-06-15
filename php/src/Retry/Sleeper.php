<?php

declare(strict_types=1);

namespace TickAtlas\Retry;

/**
 * Abstraction over "wait N seconds", so retry back-off can be made instantaneous
 * (and assertable) in tests.
 */
interface Sleeper
{
    /**
     * Block for the given number of seconds (may be fractional).
     */
    public function sleep(float $seconds): void;
}
