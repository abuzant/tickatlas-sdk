<?php

declare(strict_types=1);

namespace TickAtlas\Enums;

/**
 * The 42 technical indicators accepted by the API.
 *
 * Identifiers are **case-sensitive** and must be used verbatim (source of truth:
 * the server's INDICATOR_COLUMN_MAP). Naming gotchas worth remembering:
 *   - `SAR` (not `Parabolic_SAR`)
 *   - `Volumes` (not `Tick_Volume`)
 *   - `WilliamsR_14` (no underscore before R)
 *   - `ADX_plusDI` / `ADX_minusDI` (camel DI)
 *   - `EMA` stops at `EMA_50`; `SMA` goes to `SMA_200`
 *   - no `RSI_9`, no `EMA_200`, only three Ichimoku keys
 *
 * Client methods also accept plain strings, so this enum is a convenience /
 * discoverability aid rather than a hard requirement.
 */
enum Indicator: string
{
    // ---- Trend (23) ----
    case SMA_10 = 'SMA_10';
    case SMA_20 = 'SMA_20';
    case SMA_50 = 'SMA_50';
    case SMA_100 = 'SMA_100';
    case SMA_200 = 'SMA_200';
    case EMA_10 = 'EMA_10';
    case EMA_20 = 'EMA_20';
    case EMA_50 = 'EMA_50';
    case MACD_main = 'MACD_main';
    case MACD_signal = 'MACD_signal';
    case MACD_hist = 'MACD_hist';
    case ADX = 'ADX';
    case ADX_plusDI = 'ADX_plusDI';
    case ADX_minusDI = 'ADX_minusDI';
    case Ichimoku_tenkan = 'Ichimoku_tenkan';
    case Ichimoku_kijun = 'Ichimoku_kijun';
    case Ichimoku_senkou_a = 'Ichimoku_senkou_a';
    case Alligator_jaw = 'Alligator_jaw';
    case Alligator_teeth = 'Alligator_teeth';
    case Alligator_lips = 'Alligator_lips';
    case SAR = 'SAR';
    case TEMA_20 = 'TEMA_20';
    case DEMA_20 = 'DEMA_20';

    // ---- Oscillator (8) ----
    case RSI_14 = 'RSI_14';
    case Stochastic_K = 'Stochastic_K';
    case Stochastic_D = 'Stochastic_D';
    case CCI_14 = 'CCI_14';
    case CCI_20 = 'CCI_20';
    case WilliamsR_14 = 'WilliamsR_14';
    case Momentum_14 = 'Momentum_14';
    case DeMarker_14 = 'DeMarker_14';

    // ---- Volatility (7) ----
    case BB_upper = 'BB_upper';
    case BB_middle = 'BB_middle';
    case BB_lower = 'BB_lower';
    case BB_width = 'BB_width';
    case ATR_14 = 'ATR_14';
    case ATR_7 = 'ATR_7';
    case StdDev_20 = 'StdDev_20';

    // ---- Volume (4) ----
    case OBV = 'OBV';
    case MFI_14 = 'MFI_14';
    case AD = 'AD';
    case Volumes = 'Volumes';

    /**
     * Indicators grouped by category, mirroring the server's catalogue buckets.
     *
     * @return array<string, list<string>>
     */
    public static function byCategory(): array
    {
        return [
            'trend' => [
                'SMA_10', 'SMA_20', 'SMA_50', 'SMA_100', 'SMA_200',
                'EMA_10', 'EMA_20', 'EMA_50',
                'MACD_main', 'MACD_signal', 'MACD_hist',
                'ADX', 'ADX_plusDI', 'ADX_minusDI',
                'Ichimoku_tenkan', 'Ichimoku_kijun', 'Ichimoku_senkou_a',
                'Alligator_jaw', 'Alligator_teeth', 'Alligator_lips',
                'SAR', 'TEMA_20', 'DEMA_20',
            ],
            'oscillator' => [
                'RSI_14', 'Stochastic_K', 'Stochastic_D', 'CCI_14', 'CCI_20',
                'WilliamsR_14', 'Momentum_14', 'DeMarker_14',
            ],
            'volatility' => [
                'BB_upper', 'BB_middle', 'BB_lower', 'BB_width',
                'ATR_14', 'ATR_7', 'StdDev_20',
            ],
            'volume' => [
                'OBV', 'MFI_14', 'AD', 'Volumes',
            ],
        ];
    }

    /**
     * Flat list of every valid indicator identifier (42 entries).
     *
     * @return list<string>
     */
    public static function all(): array
    {
        return array_map(static fn (self $i): string => $i->value, self::cases());
    }
}
