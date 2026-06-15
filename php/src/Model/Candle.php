<?php

declare(strict_types=1);

namespace TickAtlas\Model;

/**
 * A single OHLC candle.
 */
final class Candle extends AbstractModel
{
    public function __construct(
        public readonly string $time,
        public readonly float $open,
        public readonly float $high,
        public readonly float $low,
        public readonly float $close,
        public readonly int $volume,
    ) {
    }

    /** @param array<string, mixed> $data */
    public static function fromArray(array $data): self
    {
        $m = new self(
            time: (string) ($data['time'] ?? ''),
            open: (float) ($data['open'] ?? 0),
            high: (float) ($data['high'] ?? 0),
            low: (float) ($data['low'] ?? 0),
            close: (float) ($data['close'] ?? 0),
            volume: (int) ($data['volume'] ?? 0),
        );
        $m->raw = $data;

        return $m;
    }
}
