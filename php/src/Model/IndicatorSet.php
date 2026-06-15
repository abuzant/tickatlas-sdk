<?php

declare(strict_types=1);

namespace TickAtlas\Model;

/**
 * Result of GET /indicators (all indicators for one symbol/timeframe).
 */
final class IndicatorSet extends AbstractModel
{
    /**
     * @param array<string, float|null>   $indicators name => value
     * @param array<string, mixed>|null   $ohlcv      {open,high,low,close,volume}
     */
    public function __construct(
        public readonly string $symbol,
        public readonly string $timeframe,
        public readonly ?array $ohlcv,
        public readonly ?float $bid,
        public readonly ?float $ask,
        public readonly array $indicators,
        public readonly int $count,
        public readonly ?int $updatedAt,
    ) {
    }

    /** @param array<string, mixed> $data */
    public static function fromArray(array $data): self
    {
        $ohlcv = $data['ohlcv'] ?? null;

        /** @var array<string, float|null> $indicators */
        $indicators = self::arr($data, 'indicators');

        $m = new self(
            symbol: (string) ($data['symbol'] ?? ''),
            timeframe: (string) ($data['timeframe'] ?? ''),
            ohlcv: is_array($ohlcv) ? $ohlcv : null,
            bid: self::float($data, 'bid'),
            ask: self::float($data, 'ask'),
            indicators: $indicators,
            count: (int) ($data['count'] ?? count($indicators)),
            updatedAt: self::int($data, 'updated_at'),
        );
        $m->raw = $data;

        return $m;
    }

    /** Convenience accessor for a single indicator value by name. */
    public function value(string $indicator): ?float
    {
        $v = $this->indicators[$indicator] ?? null;

        return $v === null ? null : (float) $v;
    }
}
