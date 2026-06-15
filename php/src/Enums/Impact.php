<?php

declare(strict_types=1);

namespace TickAtlas\Enums;

/**
 * Economic calendar event impact levels.
 */
enum Impact: string
{
    case High = 'high';
    case Medium = 'medium';
    case Low = 'low';
}
