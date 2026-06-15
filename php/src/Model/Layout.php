<?php

declare(strict_types=1);

namespace TickAtlas\Model;

/**
 * Result of GET /monitor/layout — the saved dashboard layout (or null).
 */
final class Layout extends AbstractModel
{
    /**
     * @param array<int|string, mixed>|null $layout
     */
    public function __construct(
        public readonly ?array $layout,
    ) {
    }

    /** @param array<string, mixed> $data */
    public static function fromArray(array $data): self
    {
        $layout = $data['layout'] ?? null;

        $m = new self(
            layout: is_array($layout) ? $layout : null,
        );
        $m->raw = $data;

        return $m;
    }
}
