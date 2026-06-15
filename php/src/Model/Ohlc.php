<?php

declare(strict_types=1);

namespace TickAtlas\Model;

/**
 * Result of GET /ohlc.
 */
final class Ohlc extends AbstractModel
{
    /**
     * @param list<Candle> $candles
     */
    public function __construct(
        public readonly string $symbol,
        public readonly string $timeframe,
        public readonly array $candles,
        public readonly int $count,
        public readonly ?string $retention,
    ) {
    }

    /** @param array<string, mixed> $data */
    public static function fromArray(array $data): self
    {
        $candles = array_map(
            static fn (array $row): Candle => Candle::fromArray($row),
            array_values(self::arr($data, 'candles')),
        );

        $m = new self(
            symbol: (string) ($data['symbol'] ?? ''),
            timeframe: (string) ($data['timeframe'] ?? ''),
            candles: $candles,
            count: (int) ($data['count'] ?? count($candles)),
            retention: self::str($data, 'retention'),
        );
        $m->raw = $data;

        return $m;
    }
}
