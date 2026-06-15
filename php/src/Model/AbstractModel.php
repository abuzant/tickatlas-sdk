<?php

declare(strict_types=1);

namespace TickAtlas\Model;

/**
 * Base for all response DTOs.
 *
 * Every model is constructed from the decoded `data` array via a static
 * {@see fromArray()} factory, retains the original payload (so unknown/extra
 * keys are never lost — forward compatibility per SPEC §3), and exposes both a
 * typed view (public readonly properties) and the raw array.
 */
abstract class AbstractModel
{
    /**
     * The original decoded payload this model was built from.
     *
     * @var array<string, mixed>
     */
    protected array $raw = [];

    /**
     * The raw decoded payload, including any keys the SDK does not yet model.
     *
     * @return array<string, mixed>
     */
    public function toArray(): array
    {
        return $this->raw;
    }

    /**
     * Alias of {@see toArray()} for callers that think in terms of "raw".
     *
     * @return array<string, mixed>
     */
    public function raw(): array
    {
        return $this->raw;
    }

    /**
     * Read a single key from the raw payload (handy for not-yet-modelled fields).
     */
    public function get(string $key, mixed $default = null): mixed
    {
        return $this->raw[$key] ?? $default;
    }

    // ---- internal extraction helpers (tolerant of nulls / missing keys) ----

    /** @param array<string, mixed> $data */
    protected static function str(array $data, string $key): ?string
    {
        $v = $data[$key] ?? null;

        return $v === null ? null : (string) $v;
    }

    /** @param array<string, mixed> $data */
    protected static function int(array $data, string $key): ?int
    {
        $v = $data[$key] ?? null;

        return $v === null ? null : (int) $v;
    }

    /** @param array<string, mixed> $data */
    protected static function float(array $data, string $key): ?float
    {
        $v = $data[$key] ?? null;

        return $v === null ? null : (float) $v;
    }

    /** @param array<string, mixed> $data */
    protected static function bool(array $data, string $key): ?bool
    {
        if (!array_key_exists($key, $data) || $data[$key] === null) {
            return null;
        }

        return (bool) $data[$key];
    }

    /**
     * Extract a sub-array, defaulting to an empty array.
     *
     * @param array<string, mixed> $data
     *
     * @return array<int|string, mixed>
     */
    protected static function arr(array $data, string $key): array
    {
        $v = $data[$key] ?? null;

        return is_array($v) ? $v : [];
    }
}
