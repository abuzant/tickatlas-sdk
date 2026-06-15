<?php

declare(strict_types=1);

namespace TickAtlas\Tests\Unit;

use PHPUnit\Framework\TestCase;
use TickAtlas\Enums\Indicator;

/**
 * Guards the 42-indicator catalogue (SPEC §6) and its naming gotchas.
 */
final class IndicatorCatalogueTest extends TestCase
{
    public function testThereAreExactly42Indicators(): void
    {
        self::assertCount(42, Indicator::cases());
        self::assertCount(42, Indicator::all());
    }

    public function testCategoryCounts(): void
    {
        $byCat = Indicator::byCategory();

        self::assertCount(23, $byCat['trend']);
        self::assertCount(8, $byCat['oscillator']);
        self::assertCount(7, $byCat['volatility']);
        self::assertCount(4, $byCat['volume']);
        self::assertSame(42, array_sum(array_map('count', $byCat)));
    }

    public function testNamingGotchas(): void
    {
        // correct names per SPEC §6 / F6
        self::assertSame('SAR', Indicator::SAR->value);
        self::assertSame('Volumes', Indicator::Volumes->value);
        self::assertSame('WilliamsR_14', Indicator::WilliamsR_14->value);
        self::assertSame('ADX_plusDI', Indicator::ADX_plusDI->value);
        self::assertSame('ADX_minusDI', Indicator::ADX_minusDI->value);

        $all = Indicator::all();
        // wrong names that should NOT exist
        self::assertNotContains('Parabolic_SAR', $all);
        self::assertNotContains('Tick_Volume', $all);
        self::assertNotContains('RSI_9', $all);
        self::assertNotContains('EMA_200', $all);
        self::assertNotContains('Ichimoku_senkou_b', $all);
        self::assertNotContains('Ichimoku_chikou', $all);

        // boundaries
        self::assertContains('SMA_200', $all);
        self::assertContains('EMA_50', $all);
        self::assertContains('RSI_14', $all);
    }

    public function testByCategoryMatchesEnumValues(): void
    {
        $flat = array_merge(...array_values(Indicator::byCategory()));
        sort($flat);
        $cases = Indicator::all();
        sort($cases);

        self::assertSame($cases, $flat);
    }
}
