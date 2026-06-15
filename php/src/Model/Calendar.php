<?php

declare(strict_types=1);

namespace TickAtlas\Model;

/**
 * Result of GET /calendar.
 */
final class Calendar extends AbstractModel
{
    /**
     * @param list<CalendarEvent>             $events
     * @param array{from: string, to: string} $range
     */
    public function __construct(
        public readonly array $events,
        public readonly int $count,
        public readonly Pagination $pagination,
        public readonly array $range,
    ) {
    }

    /** @param array<string, mixed> $data */
    public static function fromArray(array $data): self
    {
        $events = array_map(
            static fn (array $row): CalendarEvent => CalendarEvent::fromArray($row),
            array_values(self::arr($data, 'events')),
        );

        $rangeRaw = self::arr($data, 'range');
        $range = [
            'from' => (string) ($rangeRaw['from'] ?? ''),
            'to' => (string) ($rangeRaw['to'] ?? ''),
        ];

        $m = new self(
            events: $events,
            count: (int) ($data['count'] ?? count($events)),
            pagination: Pagination::fromArray(self::arr($data, 'pagination')),
            range: $range,
        );
        $m->raw = $data;

        return $m;
    }
}
