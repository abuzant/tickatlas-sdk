<?php

declare(strict_types=1);

namespace TickAtlas\Retry;

/**
 * A {@see Sleeper} that records requested durations instead of actually sleeping.
 *
 * Intended for tests: lets you assert that the client honoured Retry-After /
 * computed back-off without slowing the suite down.
 */
final class RecordingSleeper implements Sleeper
{
    /** @var list<float> */
    public array $sleeps = [];

    public function sleep(float $seconds): void
    {
        $this->sleeps[] = $seconds;
    }

    /** Total time the client *would* have slept. */
    public function total(): float
    {
        return array_sum($this->sleeps);
    }

    public function count(): int
    {
        return count($this->sleeps);
    }
}
