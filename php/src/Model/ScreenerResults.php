<?php

declare(strict_types=1);

namespace TickAtlas\Model;

/**
 * Result of GET /screener.
 */
final class ScreenerResults extends AbstractModel
{
    /**
     * @param array{min: float|null, max: float|null} $filter
     * @param list<ScreenerResult>                     $results
     */
    public function __construct(
        public readonly string $indicator,
        public readonly string $timeframe,
        public readonly array $filter,
        public readonly array $results,
        public readonly int $totalMatches,
        public readonly Pagination $pagination,
        public readonly ?int $updatedAt,
    ) {
    }

    /** @param array<string, mixed> $data */
    public static function fromArray(array $data): self
    {
        $results = array_map(
            static fn (array $row): ScreenerResult => ScreenerResult::fromArray($row),
            array_values(self::arr($data, 'results')),
        );

        $filterRaw = self::arr($data, 'filter');
        $filter = [
            'min' => isset($filterRaw['min']) && $filterRaw['min'] !== null ? (float) $filterRaw['min'] : null,
            'max' => isset($filterRaw['max']) && $filterRaw['max'] !== null ? (float) $filterRaw['max'] : null,
        ];

        $m = new self(
            indicator: (string) ($data['indicator'] ?? ''),
            timeframe: (string) ($data['timeframe'] ?? ''),
            filter: $filter,
            results: $results,
            totalMatches: (int) ($data['total_matches'] ?? count($results)),
            pagination: Pagination::fromArray(self::arr($data, 'pagination')),
            updatedAt: self::int($data, 'updated_at'),
        );
        $m->raw = $data;

        return $m;
    }
}
