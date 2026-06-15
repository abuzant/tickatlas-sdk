<?php

declare(strict_types=1);

namespace TickAtlas\Model;

/**
 * A single tick.
 */
final class Tick extends AbstractModel
{
    public function __construct(
        public readonly string $time,
        public readonly float $bid,
        public readonly float $ask,
        public readonly int $flags,
    ) {
    }

    /** @param array<string, mixed> $data */
    public static function fromArray(array $data): self
    {
        $m = new self(
            time: (string) ($data['time'] ?? ''),
            bid: (float) ($data['bid'] ?? 0),
            ask: (float) ($data['ask'] ?? 0),
            flags: (int) ($data['flags'] ?? 0),
        );
        $m->raw = $data;

        return $m;
    }
}
