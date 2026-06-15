<?php

declare(strict_types=1);

namespace TickAtlas\Model;

/**
 * A single real-time quote (GET /quote).
 *
 * The best_bid/best_ask/best_spread/source_count fields and the sources[] array
 * are only populated when include_sources=true was requested.
 */
final class Quote extends AbstractModel
{
    /**
     * @param list<QuoteSource> $sources
     */
    public function __construct(
        public readonly string $symbol,
        public readonly ?float $bid,
        public readonly ?float $ask,
        public readonly float $spread,
        public readonly ?float $spreadPips,
        public readonly string $timestamp,
        public readonly ?string $source = null,
        public readonly ?float $bestBid = null,
        public readonly ?float $bestAsk = null,
        public readonly ?float $bestSpread = null,
        public readonly ?int $sourceCount = null,
        public readonly array $sources = [],
    ) {
    }

    /** @param array<string, mixed> $data */
    public static function fromArray(array $data): self
    {
        $sources = array_map(
            static fn (array $row): QuoteSource => QuoteSource::fromArray($row),
            array_values(self::arr($data, 'sources')),
        );

        $m = new self(
            symbol: (string) ($data['symbol'] ?? ''),
            bid: self::float($data, 'bid'),
            ask: self::float($data, 'ask'),
            spread: (float) ($data['spread'] ?? 0),
            spreadPips: self::float($data, 'spread_pips'),
            timestamp: (string) ($data['timestamp'] ?? ''),
            source: self::str($data, 'source'),
            bestBid: self::float($data, 'best_bid'),
            bestAsk: self::float($data, 'best_ask'),
            bestSpread: self::float($data, 'best_spread'),
            sourceCount: self::int($data, 'source_count'),
            sources: $sources,
        );
        $m->raw = $data;

        return $m;
    }
}
