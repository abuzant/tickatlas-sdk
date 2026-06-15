<?php

declare(strict_types=1);

namespace TickAtlas\Model;

/**
 * Result of GET /indicators/list — the indicator catalogue keyed by category.
 */
final class IndicatorCatalogue extends AbstractModel
{
    /**
     * @param array<string, array<string, string>> $indicators category => {name: description}
     * @param list<string>                          $timeframes
     * @param list<string>                          $categories
     */
    public function __construct(
        public readonly array $indicators,
        public readonly array $timeframes,
        public readonly array $categories,
    ) {
    }

    /** @param array<string, mixed> $data */
    public static function fromArray(array $data): self
    {
        /** @var array<string, array<string, string>> $indicators */
        $indicators = self::arr($data, 'indicators');

        $m = new self(
            indicators: $indicators,
            timeframes: array_values(array_map('strval', self::arr($data, 'timeframes'))),
            categories: array_values(array_map('strval', self::arr($data, 'categories'))),
        );
        $m->raw = $data;

        return $m;
    }
}
