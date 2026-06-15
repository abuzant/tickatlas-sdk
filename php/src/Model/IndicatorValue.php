<?php

declare(strict_types=1);

namespace TickAtlas\Model;

/**
 * Result of GET /indicator (a single indicator value for a symbol/timeframe).
 */
final class IndicatorValue extends AbstractModel
{
    public function __construct(
        public readonly string $symbol,
        public readonly string $timeframe,
        public readonly string $indicator,
        public readonly ?float $value,
        public readonly ?float $bid,
        public readonly ?float $ask,
        public readonly ?int $updatedAt,
        public readonly ?string $serverTime,
    ) {
    }

    /** @param array<string, mixed> $data */
    public static function fromArray(array $data): self
    {
        $m = new self(
            symbol: (string) ($data['symbol'] ?? ''),
            timeframe: (string) ($data['timeframe'] ?? ''),
            indicator: (string) ($data['indicator'] ?? ''),
            value: self::float($data, 'value'),
            bid: self::float($data, 'bid'),
            ask: self::float($data, 'ask'),
            updatedAt: self::int($data, 'updated_at'),
            serverTime: self::str($data, 'server_time'),
        );
        $m->raw = $data;

        return $m;
    }
}
