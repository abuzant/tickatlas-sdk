<?php

declare(strict_types=1);

namespace TickAtlas\Model;

/**
 * One row in a screener scan.
 */
final class ScreenerResult extends AbstractModel
{
    public function __construct(
        public readonly string $symbol,
        public readonly ?float $value,
        public readonly ?float $bid,
    ) {
    }

    /** @param array<string, mixed> $data */
    public static function fromArray(array $data): self
    {
        $m = new self(
            symbol: (string) ($data['symbol'] ?? ''),
            value: self::float($data, 'value'),
            bid: self::float($data, 'bid'),
        );
        $m->raw = $data;

        return $m;
    }
}
