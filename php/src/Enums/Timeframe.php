<?php

declare(strict_types=1);

namespace TickAtlas\Enums;

/**
 * Candle / indicator timeframes.
 *
 * Valid for indicator, indicators, summary, ohlc, multi, history and screener
 * endpoints (default: H1). Note the heatmap endpoint uses a different set
 * (H1, H4, D1, W1) — see {@see HeatmapTimeframe}.
 */
enum Timeframe: string
{
    case M1 = 'M1';
    case M5 = 'M5';
    case M15 = 'M15';
    case M30 = 'M30';
    case H1 = 'H1';
    case H4 = 'H4';
    case D1 = 'D1';
}
