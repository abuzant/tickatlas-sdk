<?php

declare(strict_types=1);

namespace TickAtlas\Model;

/**
 * One row in the paginated /symbols listing.
 */
final class SymbolListItem extends AbstractModel
{
    public function __construct(
        public readonly string $symbol,
        public readonly ?string $name,
        public readonly string $category,
        public readonly ?string $baseCurrency,
        public readonly ?string $quoteCurrency,
        public readonly int $digits,
        public readonly bool $tradable,
    ) {
    }

    /** @param array<string, mixed> $data */
    public static function fromArray(array $data): self
    {
        $m = new self(
            symbol: (string) ($data['symbol'] ?? ''),
            name: self::str($data, 'name'),
            category: (string) ($data['category'] ?? ''),
            baseCurrency: self::str($data, 'base_currency'),
            quoteCurrency: self::str($data, 'quote_currency'),
            digits: (int) ($data['digits'] ?? 0),
            tradable: (bool) ($data['tradable'] ?? false),
        );
        $m->raw = $data;

        return $m;
    }
}
