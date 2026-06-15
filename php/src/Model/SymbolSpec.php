<?php

declare(strict_types=1);

namespace TickAtlas\Model;

/**
 * Full contract specification for a symbol (GET /symbols/{symbol}).
 */
final class SymbolSpec extends AbstractModel
{
    /**
     * @param array<string, string> $tradingHours sunday..saturday => hours string
     */
    public function __construct(
        public readonly string $symbol,
        public readonly ?string $name,
        public readonly string $category,
        public readonly ?string $description,
        public readonly ?string $baseCurrency,
        public readonly ?string $quoteCurrency,
        public readonly int $digits,
        public readonly ?float $point,
        public readonly ?float $contractSize,
        public readonly ?float $minVolume,
        public readonly ?float $maxVolume,
        public readonly ?float $volumeStep,
        public readonly ?float $swapLong,
        public readonly ?float $swapShort,
        public readonly ?string $marginCurrency,
        public readonly array $tradingHours,
    ) {
    }

    /** @param array<string, mixed> $data */
    public static function fromArray(array $data): self
    {
        /** @var array<string, string> $hours */
        $hours = self::arr($data, 'trading_hours');

        $m = new self(
            symbol: (string) ($data['symbol'] ?? ''),
            name: self::str($data, 'name'),
            category: (string) ($data['category'] ?? ''),
            description: self::str($data, 'description'),
            baseCurrency: self::str($data, 'base_currency'),
            quoteCurrency: self::str($data, 'quote_currency'),
            digits: (int) ($data['digits'] ?? 0),
            point: self::float($data, 'point'),
            contractSize: self::float($data, 'contract_size'),
            minVolume: self::float($data, 'min_volume'),
            maxVolume: self::float($data, 'max_volume'),
            volumeStep: self::float($data, 'volume_step'),
            swapLong: self::float($data, 'swap_long'),
            swapShort: self::float($data, 'swap_short'),
            marginCurrency: self::str($data, 'margin_currency'),
            tradingHours: $hours,
        );
        $m->raw = $data;

        return $m;
    }
}
