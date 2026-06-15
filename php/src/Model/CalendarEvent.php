<?php

declare(strict_types=1);

namespace TickAtlas\Model;

/**
 * One economic calendar event.
 *
 * Note: `datetime` is naive UTC with **no** timezone suffix — treat it as UTC.
 */
final class CalendarEvent extends AbstractModel
{
    public function __construct(
        public readonly string $id,
        public readonly string $datetime,
        public readonly string $currency,
        public readonly string $event,
        public readonly string $impact,
        public readonly ?string $forecast,
        public readonly ?string $previous,
        public readonly ?string $actual,
    ) {
    }

    /** @param array<string, mixed> $data */
    public static function fromArray(array $data): self
    {
        $m = new self(
            id: (string) ($data['id'] ?? ''),
            datetime: (string) ($data['datetime'] ?? ''),
            currency: (string) ($data['currency'] ?? ''),
            event: (string) ($data['event'] ?? ''),
            impact: (string) ($data['impact'] ?? ''),
            forecast: self::str($data, 'forecast'),
            previous: self::str($data, 'previous'),
            actual: self::str($data, 'actual'),
        );
        $m->raw = $data;

        return $m;
    }
}
