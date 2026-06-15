<?php

declare(strict_types=1);

namespace TickAtlas\Model;

/**
 * Result of GET /ticks.
 */
final class Ticks extends AbstractModel
{
    /**
     * @param list<Tick> $ticks
     */
    public function __construct(
        public readonly string $symbol,
        public readonly array $ticks,
        public readonly int $count,
    ) {
    }

    /** @param array<string, mixed> $data */
    public static function fromArray(array $data): self
    {
        $ticks = array_map(
            static fn (array $row): Tick => Tick::fromArray($row),
            array_values(self::arr($data, 'ticks')),
        );

        $m = new self(
            symbol: (string) ($data['symbol'] ?? ''),
            ticks: $ticks,
            count: (int) ($data['count'] ?? count($ticks)),
        );
        $m->raw = $data;

        return $m;
    }
}
