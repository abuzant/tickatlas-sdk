<?php

declare(strict_types=1);

namespace TickAtlas\Model;

/**
 * Pagination block shared by listing endpoints (symbols, screener, calendar).
 */
final class Pagination extends AbstractModel
{
    public function __construct(
        public readonly int $offset,
        public readonly int $limit,
        public readonly int $total,
        public readonly bool $hasMore,
    ) {
    }

    /** @param array<string, mixed> $data */
    public static function fromArray(array $data): self
    {
        $m = new self(
            offset: (int) ($data['offset'] ?? 0),
            limit: (int) ($data['limit'] ?? 0),
            total: (int) ($data['total'] ?? 0),
            hasMore: (bool) ($data['has_more'] ?? false),
        );
        $m->raw = $data;

        return $m;
    }
}
