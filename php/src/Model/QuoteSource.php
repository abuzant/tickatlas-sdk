<?php

declare(strict_types=1);

namespace TickAtlas\Model;

/**
 * A per-broker quote source row (present when include_sources=true on /quote).
 */
final class QuoteSource extends AbstractModel
{
    public function __construct(
        public readonly ?string $broker,
        public readonly ?float $bid,
        public readonly ?float $ask,
        public readonly ?float $spread,
        public readonly ?string $updated,
    ) {
    }

    /** @param array<string, mixed> $data */
    public static function fromArray(array $data): self
    {
        $m = new self(
            broker: self::str($data, 'broker'),
            bid: self::float($data, 'bid'),
            ask: self::float($data, 'ask'),
            spread: self::float($data, 'spread'),
            updated: self::str($data, 'updated'),
        );
        $m->raw = $data;

        return $m;
    }
}
