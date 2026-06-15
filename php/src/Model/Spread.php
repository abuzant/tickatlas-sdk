<?php

declare(strict_types=1);

namespace TickAtlas\Model;

/**
 * Result of GET /spread — spread statistics for one symbol.
 */
final class Spread extends AbstractModel
{
    /**
     * @param array{spread_pips: float, spread_points: int}                       $current
     * @param array<string, mixed>                                                $statistics period, avg/min/max_spread, std_deviation
     * @param array{asian: float|null, london: float|null, new_york: float|null}  $bySession
     */
    public function __construct(
        public readonly string $symbol,
        public readonly array $current,
        public readonly array $statistics,
        public readonly array $bySession,
    ) {
    }

    /** @param array<string, mixed> $data */
    public static function fromArray(array $data): self
    {
        $currentRaw = self::arr($data, 'current');
        $current = [
            'spread_pips' => (float) ($currentRaw['spread_pips'] ?? 0),
            'spread_points' => (int) ($currentRaw['spread_points'] ?? 0),
        ];

        $sessRaw = self::arr($data, 'by_session');
        $bySession = [
            'asian' => isset($sessRaw['asian']) && $sessRaw['asian'] !== null ? (float) $sessRaw['asian'] : null,
            'london' => isset($sessRaw['london']) && $sessRaw['london'] !== null ? (float) $sessRaw['london'] : null,
            'new_york' => isset($sessRaw['new_york']) && $sessRaw['new_york'] !== null ? (float) $sessRaw['new_york'] : null,
        ];

        $m = new self(
            symbol: (string) ($data['symbol'] ?? ''),
            current: $current,
            statistics: self::arr($data, 'statistics'),
            bySession: $bySession,
        );
        $m->raw = $data;

        return $m;
    }
}
