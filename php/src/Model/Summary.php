<?php

declare(strict_types=1);

namespace TickAtlas\Model;

use TickAtlas\Enums\Bias;

/**
 * Result of GET /summary — a market-bias summary for a symbol/timeframe.
 *
 * The richer nested structures (signals, key_levels, key_values, the various
 * signal lists) are exposed as decoded arrays; the headline scalars are typed.
 */
final class Summary extends AbstractModel
{
    /**
     * @param array<string, mixed>            $signals     {trend,momentum,volatility,volume}
     * @param array{resistance: list<float>, support: list<float>} $keyLevels
     * @param list<string>                    $bullishSignals
     * @param list<string>                    $bearishSignals
     * @param list<string>                    $neutralSignals
     * @param list<string>                    $volatilityInfo
     * @param list<string>                    $volumeInfo
     * @param list<string>                    $recommendations
     * @param array<string, mixed>            $keyValues   bid, ask, rsi_14, ...
     */
    public function __construct(
        public readonly string $symbol,
        public readonly string $timeframe,
        public readonly Bias $bias,
        public readonly string $biasStrength,
        public readonly float $confidence,
        public readonly float $trendScore,
        public readonly float $momentumScore,
        public readonly float $volatilityScore,
        public readonly array $signals,
        public readonly array $keyLevels,
        public readonly array $bullishSignals,
        public readonly array $bearishSignals,
        public readonly array $neutralSignals,
        public readonly array $volatilityInfo,
        public readonly array $volumeInfo,
        public readonly string $summary,
        public readonly array $recommendations,
        public readonly array $keyValues,
        public readonly ?int $updatedAt,
    ) {
    }

    /** @param array<string, mixed> $data */
    public static function fromArray(array $data): self
    {
        $levelsRaw = self::arr($data, 'key_levels');
        $keyLevels = [
            'resistance' => array_values(array_map('floatval', self::arr($levelsRaw, 'resistance'))),
            'support' => array_values(array_map('floatval', self::arr($levelsRaw, 'support'))),
        ];

        $biasValue = (string) ($data['bias'] ?? Bias::Neutral->value);

        $m = new self(
            symbol: (string) ($data['symbol'] ?? ''),
            timeframe: (string) ($data['timeframe'] ?? ''),
            bias: Bias::tryFrom($biasValue) ?? Bias::Neutral,
            biasStrength: (string) ($data['bias_strength'] ?? 'normal'),
            confidence: (float) ($data['confidence'] ?? 0),
            trendScore: (float) ($data['trend_score'] ?? 0),
            momentumScore: (float) ($data['momentum_score'] ?? 0),
            volatilityScore: (float) ($data['volatility_score'] ?? 0),
            signals: self::arr($data, 'signals'),
            keyLevels: $keyLevels,
            bullishSignals: array_values(array_map('strval', self::arr($data, 'bullish_signals'))),
            bearishSignals: array_values(array_map('strval', self::arr($data, 'bearish_signals'))),
            neutralSignals: array_values(array_map('strval', self::arr($data, 'neutral_signals'))),
            volatilityInfo: array_values(array_map('strval', self::arr($data, 'volatility_info'))),
            volumeInfo: array_values(array_map('strval', self::arr($data, 'volume_info'))),
            summary: (string) ($data['summary'] ?? ''),
            recommendations: array_values(array_map('strval', self::arr($data, 'recommendations'))),
            keyValues: self::arr($data, 'key_values'),
            updatedAt: self::int($data, 'updated_at'),
        );
        $m->raw = $data;

        return $m;
    }
}
