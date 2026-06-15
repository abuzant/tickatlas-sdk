<?php

declare(strict_types=1);

namespace TickAtlas\Model;

/**
 * Result of GET /multi (batch indicators across symbols).
 *
 * Two shapes share this model:
 *   - real-time: `data` maps symbol => { indicator => value|null }
 *   - historical (when from/to supplied): `mode` = "historical" and `data`
 *     maps symbol => list of { time, indicator => value|null }
 *
 * The decoded `data` map is exposed verbatim (it is dynamically keyed by the
 * requested symbols), with typed scalars around it.
 */
final class MultiIndicators extends AbstractModel
{
    /**
     * @param array<string, mixed> $data     symbol => indicator map (RT) or rows (historical)
     * @param list<string>|null    $notFound
     */
    public function __construct(
        public readonly string $timeframe,
        public readonly array $data,
        public readonly ?array $notFound,
        public readonly ?int $updatedAt,
        public readonly ?string $mode = null,
        public readonly ?string $from = null,
        public readonly ?string $to = null,
    ) {
    }

    /** @param array<string, mixed> $data */
    public static function fromArray(array $data): self
    {
        $notFound = $data['not_found'] ?? null;

        $m = new self(
            timeframe: (string) ($data['timeframe'] ?? ''),
            data: self::arr($data, 'data'),
            notFound: is_array($notFound) ? array_values(array_map('strval', $notFound)) : null,
            updatedAt: self::int($data, 'updated_at'),
            mode: self::str($data, 'mode'),
            from: self::str($data, 'from'),
            to: self::str($data, 'to'),
        );
        $m->raw = $data;

        return $m;
    }

    /** True when this response is in historical mode. */
    public function isHistorical(): bool
    {
        return $this->mode === 'historical';
    }
}
