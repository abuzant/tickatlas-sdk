<?php

declare(strict_types=1);

namespace TickAtlas\Model;

/**
 * One quote within a batch response (POST /quotes). Only the requested `fields`
 * are present; everything else is null.
 */
final class BulkQuoteItem extends AbstractModel
{
    public function __construct(
        public readonly string $symbol,
        public readonly ?float $bid = null,
        public readonly ?float $ask = null,
        public readonly ?float $spread = null,
        public readonly ?float $spreadPips = null,
        public readonly ?string $timestamp = null,
    ) {
    }

    /** @param array<string, mixed> $data */
    public static function fromArray(array $data): self
    {
        $m = new self(
            symbol: (string) ($data['symbol'] ?? ''),
            bid: self::float($data, 'bid'),
            ask: self::float($data, 'ask'),
            spread: self::float($data, 'spread'),
            spreadPips: self::float($data, 'spread_pips'),
            timestamp: self::str($data, 'timestamp'),
        );
        $m->raw = $data;

        return $m;
    }
}
