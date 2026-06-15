<?php

declare(strict_types=1);

namespace TickAtlas\Model;

/**
 * One point in an indicator series (GET /indicator/history).
 */
final class IndicatorHistoryPoint extends AbstractModel
{
    public function __construct(
        public readonly string $time,
        public readonly ?float $value,
    ) {
    }

    /** @param array<string, mixed> $data */
    public static function fromArray(array $data): self
    {
        $m = new self(
            time: (string) ($data['time'] ?? ''),
            value: self::float($data, 'value'),
        );
        $m->raw = $data;

        return $m;
    }
}
