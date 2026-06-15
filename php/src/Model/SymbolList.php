<?php

declare(strict_types=1);

namespace TickAtlas\Model;

/**
 * Result of GET /symbols.
 */
final class SymbolList extends AbstractModel
{
    /**
     * @param list<SymbolListItem> $symbols
     */
    public function __construct(
        public readonly array $symbols,
        public readonly int $total,
        public readonly Pagination $pagination,
    ) {
    }

    /** @param array<string, mixed> $data */
    public static function fromArray(array $data): self
    {
        $symbols = array_map(
            static fn (array $row): SymbolListItem => SymbolListItem::fromArray($row),
            array_values(self::arr($data, 'symbols')),
        );

        $m = new self(
            symbols: $symbols,
            total: (int) ($data['total'] ?? count($symbols)),
            pagination: Pagination::fromArray(self::arr($data, 'pagination')),
        );
        $m->raw = $data;

        return $m;
    }
}
