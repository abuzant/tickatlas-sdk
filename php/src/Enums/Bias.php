<?php

declare(strict_types=1);

namespace TickAtlas\Enums;

/**
 * Market-bias direction returned by the summary endpoint.
 */
enum Bias: string
{
    case Bullish = 'bullish';
    case Bearish = 'bearish';
    case Neutral = 'neutral';
}
