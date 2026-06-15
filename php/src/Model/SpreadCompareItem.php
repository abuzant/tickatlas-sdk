<?php

declare(strict_types=1);

namespace TickAtlas\Model;

/**
 * One symbol's spread stats in a /spread/compare response. Missing symbols come
 * back with null stats and hasLiveData=false (never a 404).
 */
final class SpreadCompareItem extends AbstractModel
{
    public function __construct(
        public readonly string $symbol,
        public readonly ?float $currentPips,
        public readonly ?float $avgPips,
        public readonly ?float $minPips,
        public readonly ?float $maxPips,
        public readonly bool $hasLiveData,
    ) {
    }

    /** @param array<string, mixed> $data */
    public static function fromArray(array $data): self
    {
        $m = new self(
            symbol: (string) ($data['symbol'] ?? ''),
            currentPips: self::float($data, 'current_pips'),
            avgPips: self::float($data, 'avg_pips'),
            minPips: self::float($data, 'min_pips'),
            maxPips: self::float($data, 'max_pips'),
            hasLiveData: (bool) ($data['has_live_data'] ?? false),
        );
        $m->raw = $data;

        return $m;
    }
}
