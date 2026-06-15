<?php

declare(strict_types=1);

namespace TickAtlas\Model;

/**
 * Result of POST /quotes.
 */
final class BulkQuotes extends AbstractModel
{
    /**
     * @param list<BulkQuoteItem> $quotes
     * @param list<string>|null   $notFound
     */
    public function __construct(
        public readonly array $quotes,
        public readonly int $count,
        public readonly ?array $notFound,
        public readonly string $timestamp,
    ) {
    }

    /** @param array<string, mixed> $data */
    public static function fromArray(array $data): self
    {
        $quotes = array_map(
            static fn (array $row): BulkQuoteItem => BulkQuoteItem::fromArray($row),
            array_values(self::arr($data, 'quotes')),
        );

        $notFound = $data['not_found'] ?? null;

        $m = new self(
            quotes: $quotes,
            count: (int) ($data['count'] ?? count($quotes)),
            notFound: is_array($notFound) ? array_values(array_map('strval', $notFound)) : null,
            timestamp: (string) ($data['timestamp'] ?? ''),
        );
        $m->raw = $data;

        return $m;
    }
}
