<?php

declare(strict_types=1);

namespace TickAtlas\Retry;

/**
 * Default {@see Sleeper}: actually sleeps the current process via usleep().
 */
final class RealSleeper implements Sleeper
{
    public function sleep(float $seconds): void
    {
        if ($seconds <= 0) {
            return;
        }

        usleep((int) round($seconds * 1_000_000));
    }
}
