<?php

declare(strict_types=1);

namespace TickAtlas\Model;

/**
 * Result of GET /indicator/history.
 */
final class IndicatorHistory extends AbstractModel
{
    /**
     * @param list<IndicatorHistoryPoint> $series
     */
    public function __construct(
        public readonly string $symbol,
        public readonly string $indicator,
        public readonly string $timeframe,
        public readonly ?string $from,
        public readonly ?string $to,
        public readonly int $count,
        public readonly ?int $maxWindowHours,
        public readonly array $series,
    ) {
    }

    /** @param array<string, mixed> $data */
    public static function fromArray(array $data): self
    {
        $series = array_map(
            static fn (array $row): IndicatorHistoryPoint => IndicatorHistoryPoint::fromArray($row),
            array_values(self::arr($data, 'series')),
        );

        $m = new self(
            symbol: (string) ($data['symbol'] ?? ''),
            indicator: (string) ($data['indicator'] ?? ''),
            timeframe: (string) ($data['timeframe'] ?? ''),
            from: self::str($data, 'from'),
            to: self::str($data, 'to'),
            count: (int) ($data['count'] ?? count($series)),
            maxWindowHours: self::int($data, 'max_window_hours'),
            series: $series,
        );
        $m->raw = $data;

        return $m;
    }
}
