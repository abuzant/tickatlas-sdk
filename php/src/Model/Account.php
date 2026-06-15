<?php

declare(strict_types=1);

namespace TickAtlas\Model;

/**
 * Result of GET /monitor/account — the de-facto identity endpoint.
 *
 * `dailyQuota` is null when the plan is unlimited.
 */
final class Account extends AbstractModel
{
    public function __construct(
        public readonly string $name,
        public readonly string $plan,
        public readonly float $prepaidCredits,
        public readonly ?int $dailyQuota,
        public readonly int $dailyUsed,
    ) {
    }

    /** @param array<string, mixed> $data */
    public static function fromArray(array $data): self
    {
        $m = new self(
            name: (string) ($data['name'] ?? ''),
            plan: (string) ($data['plan'] ?? ''),
            prepaidCredits: (float) ($data['prepaid_credits'] ?? 0),
            dailyQuota: self::int($data, 'daily_quota'),
            dailyUsed: (int) ($data['daily_used'] ?? 0),
        );
        $m->raw = $data;

        return $m;
    }
}
