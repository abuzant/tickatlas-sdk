<?php

declare(strict_types=1);

namespace TickAtlas\Model;

/**
 * Result of GET /health (infrastructure probe, no API key required).
 */
final class Health extends AbstractModel
{
    /**
     * @param array<string, mixed> $components redis, postgres, ...
     */
    public function __construct(
        public readonly ?string $status,
        public readonly array $components,
    ) {
    }

    /** @param array<string, mixed> $data */
    public static function fromArray(array $data): self
    {
        $m = new self(
            status: self::str($data, 'status'),
            components: self::arr($data, 'components'),
        );
        $m->raw = $data;

        return $m;
    }
}
