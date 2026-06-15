<?php

declare(strict_types=1);

namespace TickAtlas\Enums;

/**
 * Symbol categories used by the /symbols listing filter.
 */
enum Category: string
{
    case Forex = 'forex';
    case Metals = 'metals';
    case Commodities = 'commodities';
    case Indices = 'indices';
    case Crypto = 'crypto';
    case Stocks = 'stocks';
}
