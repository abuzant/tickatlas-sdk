<?php

declare(strict_types=1);

namespace TickAtlas\Enums;

/**
 * Indicator category buckets (used by /indicators ?category= and /indicators/list).
 */
enum IndicatorCategory: string
{
    case Trend = 'trend';
    case Oscillator = 'oscillator';
    case Volatility = 'volatility';
    case Volume = 'volume';
}
