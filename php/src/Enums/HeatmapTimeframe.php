<?php

declare(strict_types=1);

namespace TickAtlas\Enums;

/**
 * Timeframes accepted by the heatmap endpoint (default: H4).
 *
 * The heatmap surface deliberately differs from the general {@see Timeframe}
 * set: it has no intraday minute frames and adds W1.
 */
enum HeatmapTimeframe: string
{
    case H1 = 'H1';
    case H4 = 'H4';
    case D1 = 'D1';
    case W1 = 'W1';
}
