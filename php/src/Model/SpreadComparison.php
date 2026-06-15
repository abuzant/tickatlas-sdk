<?php

declare(strict_types=1);

namespace TickAtlas\Model;

/**
 * Result of GET /spread/compare (sorted by avg_pips ascending, server-side).
 */
final class SpreadComparison extends AbstractModel
{
    /**
     * @param list<SpreadCompareItem> $symbols
     */
    public function __construct(
        public readonly string $period,
        public readonly array $symbols,
        public readonly int $count,
    ) {
    }

    /** @param array<string, mixed> $data */
    public static function fromArray(array $data): self
    {
        $symbols = array_map(
            static fn (array $row): SpreadCompareItem => SpreadCompareItem::fromArray($row),
            array_values(self::arr($data, 'symbols')),
        );

        $m = new self(
            period: (string) ($data['period'] ?? ''),
            symbols: $symbols,
            count: (int) ($data['count'] ?? count($symbols)),
        );
        $m->raw = $data;

        return $m;
    }
}
