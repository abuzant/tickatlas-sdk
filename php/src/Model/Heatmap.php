<?php

declare(strict_types=1);

namespace TickAtlas\Model;

/**
 * Result of GET /heatmap — currency strength or correlation.
 *
 * Both modes share this model (distinguished by {@see $type}):
 *   - strength: {@see $currencies} is populated, plus strongest/weakest/range
 *   - correlation: {@see $correlationMatrix} is populated; when the matrix is
 *     unavailable it is empty, {@see $available} is false and {@see $message}
 *     explains why (still HTTP 200)
 */
final class Heatmap extends AbstractModel
{
    /**
     * @param array<string, mixed>           $currencies        CCY => {strength,trend,change,pairs_analyzed}
     * @param array<string, array<string, float>> $correlationMatrix CCY => {CCY => value}
     */
    public function __construct(
        public readonly string $type,
        public readonly string $timeframe,
        public readonly string $timestamp,
        public readonly array $currencies = [],
        public readonly ?string $strongest = null,
        public readonly ?string $weakest = null,
        public readonly ?float $range = null,
        public readonly array $correlationMatrix = [],
        public readonly ?bool $available = null,
        public readonly ?string $message = null,
    ) {
    }

    /** @param array<string, mixed> $data */
    public static function fromArray(array $data): self
    {
        $m = new self(
            type: (string) ($data['type'] ?? ''),
            timeframe: (string) ($data['timeframe'] ?? ''),
            timestamp: (string) ($data['timestamp'] ?? ''),
            currencies: self::arr($data, 'currencies'),
            strongest: self::str($data, 'strongest'),
            weakest: self::str($data, 'weakest'),
            range: self::float($data, 'range'),
            correlationMatrix: self::arr($data, 'correlation_matrix'),
            available: self::bool($data, 'available'),
            message: self::str($data, 'message'),
        );
        $m->raw = $data;

        return $m;
    }

    public function isCorrelation(): bool
    {
        return $this->type === 'correlation';
    }
}
