<?php

declare(strict_types=1);

namespace TickAtlas\Model;

/**
 * Result of GET /sessions — the market session clock.
 */
final class Sessions extends AbstractModel
{
    /**
     * @param list<string>              $activeSessions
     * @param array<string, mixed>      $sessions       sydney|tokyo|london|new_york => {status, ...}
     * @param list<string>              $overlaps
     * @param array{event: string, in: string}|null $nextMajorEvent
     */
    public function __construct(
        public readonly string $currentTime,
        public readonly array $activeSessions,
        public readonly array $sessions,
        public readonly array $overlaps,
        public readonly ?array $nextMajorEvent,
    ) {
    }

    /** @param array<string, mixed> $data */
    public static function fromArray(array $data): self
    {
        $next = $data['next_major_event'] ?? null;

        $m = new self(
            currentTime: (string) ($data['current_time'] ?? ''),
            activeSessions: array_values(array_map('strval', self::arr($data, 'active_sessions'))),
            sessions: self::arr($data, 'sessions'),
            overlaps: array_values(array_map('strval', self::arr($data, 'overlaps'))),
            nextMajorEvent: is_array($next) ? $next : null,
        );
        $m->raw = $data;

        return $m;
    }
}
