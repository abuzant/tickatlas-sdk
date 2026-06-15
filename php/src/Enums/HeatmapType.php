<?php

declare(strict_types=1);

namespace TickAtlas\Enums;

/**
 * Heatmap rendering mode (default: strength).
 */
enum HeatmapType: string
{
    case Strength = 'strength';
    case Correlation = 'correlation';
}
