<?php

declare(strict_types=1);

namespace TickAtlas\Enums;

/**
 * Spread statistics aggregation periods (default: 24h).
 */
enum Period: string
{
    case OneHour = '1h';
    case TwentyFourHours = '24h';
    case SevenDays = '7d';
    case ThirtyDays = '30d';
}
