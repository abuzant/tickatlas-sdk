<?php

declare(strict_types=1);

namespace TickAtlas\Tests\Unit;

use PHPUnit\Framework\TestCase;
use TickAtlas\Enums\HeatmapTimeframe;
use TickAtlas\Enums\HeatmapType;
use TickAtlas\Enums\Impact;
use TickAtlas\Enums\Indicator;
use TickAtlas\Enums\Period;
use TickAtlas\Enums\Timeframe;
use TickAtlas\Model\Account;
use TickAtlas\Model\BulkQuotes;
use TickAtlas\Model\Calendar;
use TickAtlas\Model\Heatmap;
use TickAtlas\Model\Health;
use TickAtlas\Model\IndicatorCatalogue;
use TickAtlas\Model\IndicatorHistory;
use TickAtlas\Model\IndicatorSet;
use TickAtlas\Model\IndicatorValue;
use TickAtlas\Model\Layout;
use TickAtlas\Model\MultiIndicators;
use TickAtlas\Model\Ohlc;
use TickAtlas\Model\Quote;
use TickAtlas\Model\ScreenerResults;
use TickAtlas\Model\Sessions;
use TickAtlas\Model\Spread;
use TickAtlas\Model\SpreadComparison;
use TickAtlas\Model\Summary;
use TickAtlas\Model\SymbolList;
use TickAtlas\Model\SymbolSpec;
use TickAtlas\Model\Ticks;
use TickAtlas\Tests\Support\MockClientFactory;

/**
 * Covers every one of the 21 /v1 endpoints (+ /health): success parsing and the
 * outgoing request shape (method, path, query/body), using SPEC §7 payloads.
 */
final class EndpointTest extends TestCase
{
    private function url(MockClientFactory $f): string
    {
        return (string) $f->lastRequest()->getUri();
    }

    private function path(MockClientFactory $f): string
    {
        return $f->lastRequest()->getUri()->getPath();
    }

    private function query(MockClientFactory $f): string
    {
        return $f->lastRequest()->getUri()->getQuery();
    }

    // ---- 7.1 GET /symbols ----

    public function testGetSymbols(): void
    {
        $payload = [
            'symbols' => [[
                'symbol' => 'EURUSD', 'name' => null, 'category' => 'forex',
                'base_currency' => 'EUR', 'quote_currency' => 'USD', 'digits' => 5, 'tradable' => true,
            ]],
            'total' => 149,
            'pagination' => ['offset' => 0, 'limit' => 100, 'total' => 149, 'has_more' => true],
        ];
        $f = MockClientFactory::create([MockClientFactory::success($payload)]);

        $result = $f->client->getSymbols(['category' => 'forex', 'search' => 'eur', 'limit' => 50]);

        self::assertInstanceOf(SymbolList::class, $result);
        self::assertSame(149, $result->total);
        self::assertCount(1, $result->symbols);
        self::assertSame('EURUSD', $result->symbols[0]->symbol);
        self::assertNull($result->symbols[0]->name);
        self::assertTrue($result->symbols[0]->tradable);
        self::assertTrue($result->pagination->hasMore);

        self::assertSame('GET', $f->lastRequest()->getMethod());
        self::assertSame('/v1/symbols', $this->path($f));
        self::assertStringContainsString('category=forex', $this->query($f));
        self::assertStringContainsString('search=eur', $this->query($f));
        self::assertStringContainsString('limit=50', $this->query($f));
    }

    public function testGetSymbolsAcceptsCategoryEnum(): void
    {
        $f = MockClientFactory::create([MockClientFactory::success([
            'symbols' => [], 'total' => 0,
            'pagination' => ['offset' => 0, 'limit' => 100, 'total' => 0, 'has_more' => false],
        ])]);

        $f->client->getSymbols(['category' => \TickAtlas\Enums\Category::Crypto]);

        self::assertStringContainsString('category=crypto', $this->query($f));
    }

    // ---- 7.2 GET /symbols/{symbol} ----

    public function testGetSymbol(): void
    {
        $payload = [
            'symbol' => 'EURUSD', 'name' => 'Euro vs US Dollar', 'category' => 'forex',
            'description' => 'desc', 'base_currency' => 'EUR', 'quote_currency' => 'USD',
            'digits' => 5, 'point' => 0.00001, 'contract_size' => 100000, 'min_volume' => 0.01,
            'max_volume' => 500, 'volume_step' => 0.01, 'swap_long' => -5.2, 'swap_short' => 1.1,
            'margin_currency' => 'USD',
            'trading_hours' => ['monday' => '00:00-24:00', 'sunday' => 'closed'],
        ];
        $f = MockClientFactory::create([MockClientFactory::success($payload)]);

        $result = $f->client->getSymbol('EURUSD');

        self::assertInstanceOf(SymbolSpec::class, $result);
        self::assertSame('EURUSD', $result->symbol);
        self::assertSame(100000.0, $result->contractSize);
        self::assertSame(-5.2, $result->swapLong);
        self::assertSame('00:00-24:00', $result->tradingHours['monday']);
        self::assertSame('/v1/symbols/EURUSD', $this->path($f));
    }

    // ---- 7.3 GET /quote ----

    public function testGetQuote(): void
    {
        $payload = [
            'symbol' => 'EURUSD', 'bid' => 1.16404, 'ask' => 1.16422, 'spread' => 18,
            'spread_pips' => 1.8, 'timestamp' => '2026-05-25T13:56:15.819519+00:00',
            'source' => 'Equiti Securities',
        ];
        $f = MockClientFactory::create([MockClientFactory::success($payload)]);

        $result = $f->client->getQuote('EURUSD', ['include_sources' => true]);

        self::assertInstanceOf(Quote::class, $result);
        self::assertSame(1.16404, $result->bid);
        self::assertSame(1.16422, $result->ask);
        self::assertSame(18.0, $result->spread);
        self::assertSame(1.8, $result->spreadPips);
        self::assertSame('Equiti Securities', $result->source);

        self::assertSame('/v1/quote', $this->path($f));
        self::assertStringContainsString('symbol=EURUSD', $this->query($f));
        self::assertStringContainsString('include_sources=true', $this->query($f));
    }

    public function testGetQuoteWithSources(): void
    {
        $payload = [
            'symbol' => 'EURUSD', 'bid' => 1.1, 'ask' => 1.1002, 'spread' => 2.0,
            'spread_pips' => 2.0, 'timestamp' => 't', 'best_bid' => 1.1001, 'best_ask' => 1.1002,
            'best_spread' => 1.0, 'source_count' => 2,
            'sources' => [
                ['broker' => 'A', 'bid' => 1.1, 'ask' => 1.1002, 'spread' => 2.0, 'updated' => 'u'],
                ['broker' => 'B', 'bid' => 1.1001, 'ask' => 1.1003, 'spread' => 2.0, 'updated' => 'u'],
            ],
        ];
        $f = MockClientFactory::create([MockClientFactory::success($payload)]);

        $result = $f->client->getQuote('EURUSD', ['include_sources' => true]);

        self::assertSame(2, $result->sourceCount);
        self::assertCount(2, $result->sources);
        self::assertSame('A', $result->sources[0]->broker);
    }

    // ---- 7.4 POST /quotes ----

    public function testGetQuotes(): void
    {
        $payload = [
            'quotes' => [
                ['symbol' => 'EURUSD', 'bid' => 1.1, 'ask' => 1.1002, 'spread' => 2.0, 'spread_pips' => 2.0, 'timestamp' => 't'],
                ['symbol' => 'GBPUSD', 'bid' => 1.27, 'ask' => 1.2703, 'spread' => 3.0, 'spread_pips' => 3.0, 'timestamp' => 't'],
            ],
            'count' => 2, 'not_found' => null, 'timestamp' => 't',
        ];
        $f = MockClientFactory::create([MockClientFactory::success($payload)]);

        $result = $f->client->getQuotes(['EURUSD', 'GBPUSD'], ['bid', 'ask']);

        self::assertInstanceOf(BulkQuotes::class, $result);
        self::assertSame(2, $result->count);
        self::assertNull($result->notFound);
        self::assertSame('GBPUSD', $result->quotes[1]->symbol);

        // POST with JSON body
        $req = $f->lastRequest();
        self::assertSame('POST', $req->getMethod());
        self::assertSame('/v1/quotes', $req->getUri()->getPath());
        $body = json_decode((string) $req->getBody(), true);
        self::assertSame(['EURUSD', 'GBPUSD'], $body['symbols']);
        self::assertSame(['bid', 'ask'], $body['fields']);
        self::assertStringContainsString('application/json', $req->getHeaderLine('Content-Type'));
    }

    public function testGetQuotesWithNotFound(): void
    {
        $payload = [
            'quotes' => [['symbol' => 'EURUSD', 'bid' => 1.1]],
            'count' => 1, 'not_found' => ['FAKEPAIR'], 'timestamp' => 't',
        ];
        $f = MockClientFactory::create([MockClientFactory::success($payload)]);

        $result = $f->client->getQuotes(['EURUSD', 'FAKEPAIR']);

        self::assertSame(['FAKEPAIR'], $result->notFound);
        // no fields => body has no 'fields' key
        $body = json_decode((string) $f->lastRequest()->getBody(), true);
        self::assertArrayNotHasKey('fields', $body);
    }

    // ---- 7.5 GET /ohlc ----

    public function testGetOhlc(): void
    {
        $payload = [
            'symbol' => 'EURUSD', 'timeframe' => 'H1',
            'candles' => [
                ['time' => '2026-05-25T13:00:00Z', 'open' => 1.1, 'high' => 1.2, 'low' => 1.0, 'close' => 1.15, 'volume' => 1234],
            ],
            'count' => 1, 'retention' => '90d',
        ];
        $f = MockClientFactory::create([MockClientFactory::success($payload)]);

        $result = $f->client->getOhlc('EURUSD', ['timeframe' => Timeframe::H1, 'limit' => 500]);

        self::assertInstanceOf(Ohlc::class, $result);
        self::assertSame('H1', $result->timeframe);
        self::assertCount(1, $result->candles);
        self::assertSame(1234, $result->candles[0]->volume);
        self::assertIsInt($result->candles[0]->volume);
        self::assertSame('90d', $result->retention);

        self::assertSame('/v1/ohlc', $this->path($f));
        self::assertStringContainsString('timeframe=H1', $this->query($f));
        self::assertStringContainsString('limit=500', $this->query($f));
    }

    public function testGetOhlcEmptyButValid(): void
    {
        $f = MockClientFactory::create([MockClientFactory::success([
            'symbol' => 'EURUSD', 'timeframe' => 'H1', 'candles' => [], 'count' => 0, 'retention' => null,
        ])]);

        $result = $f->client->getOhlc('EURUSD');

        self::assertSame([], $result->candles);
        self::assertSame(0, $result->count);
        self::assertNull($result->retention);
    }

    // ---- 7.6 GET /ticks ----

    public function testGetTicks(): void
    {
        $payload = [
            'symbol' => 'EURUSD',
            'ticks' => [
                ['time' => '2026-05-25T13:00:00.123Z', 'bid' => 1.1, 'ask' => 1.1002, 'flags' => 6],
            ],
            'count' => 1,
        ];
        $f = MockClientFactory::create([MockClientFactory::success($payload)]);

        $result = $f->client->getTicks('EURUSD', '2026-05-25T13:00:00Z', '2026-05-25T13:30:00Z');

        self::assertInstanceOf(Ticks::class, $result);
        self::assertCount(1, $result->ticks);
        self::assertSame(6, $result->ticks[0]->flags);

        self::assertSame('/v1/ticks', $this->path($f));
        $q = $this->query($f);
        self::assertStringContainsString('symbol=EURUSD', $q);
        self::assertStringContainsString('from=', $q);
        self::assertStringContainsString('to=', $q);
    }

    // ---- 7.7 GET /indicator ----

    public function testGetIndicator(): void
    {
        $payload = [
            'symbol' => 'EURUSD', 'timeframe' => 'H1', 'indicator' => 'RSI_14', 'value' => 58.34,
            'bid' => 1.0831, 'ask' => 1.0832, 'updated_at' => 1711548000, 'server_time' => '2026-03-27T14:00:00',
        ];
        $f = MockClientFactory::create([MockClientFactory::success($payload)]);

        $result = $f->client->getIndicator('EURUSD', Indicator::RSI_14, ['timeframe' => 'H1']);

        self::assertInstanceOf(IndicatorValue::class, $result);
        self::assertSame(58.34, $result->value);
        self::assertSame(1711548000, $result->updatedAt);
        self::assertSame('2026-03-27T14:00:00', $result->serverTime);

        self::assertSame('/v1/indicator', $this->path($f));
        self::assertStringContainsString('indicator=RSI_14', $this->query($f));
    }

    public function testGetIndicatorAcceptsRawString(): void
    {
        $f = MockClientFactory::create([MockClientFactory::success([
            'symbol' => 'EURUSD', 'timeframe' => 'H1', 'indicator' => 'SAR', 'value' => 1.05,
            'bid' => null, 'ask' => null, 'updated_at' => 1, 'server_time' => null,
        ])]);

        $result = $f->client->getIndicator('EURUSD', 'SAR');

        self::assertSame('SAR', $result->indicator);
        self::assertStringContainsString('indicator=SAR', $this->query($f));
    }

    // ---- 7.8 GET /indicators ----

    public function testGetIndicators(): void
    {
        $payload = [
            'symbol' => 'EURUSD', 'timeframe' => 'H1',
            'ohlcv' => ['open' => 1.1, 'high' => 1.2, 'low' => 1.0, 'close' => 1.15, 'volume' => 100],
            'bid' => 1.1, 'ask' => 1.1002,
            'indicators' => ['RSI_14' => 58.34, 'SMA_20' => 1.1, 'MACD_hist' => null],
            'count' => 3, 'updated_at' => 1711548000,
        ];
        $f = MockClientFactory::create([MockClientFactory::success($payload)]);

        $result = $f->client->getIndicators('EURUSD', ['timeframe' => 'H1', 'category' => 'oscillator']);

        self::assertInstanceOf(IndicatorSet::class, $result);
        self::assertSame(58.34, $result->value('RSI_14'));
        self::assertNull($result->value('MACD_hist'));
        self::assertSame(100, $result->ohlcv['volume']);
        self::assertSame(3, $result->count);

        self::assertSame('/v1/indicators', $this->path($f));
        self::assertStringContainsString('category=oscillator', $this->query($f));
    }

    // ---- 7.9 GET /indicators/list ----

    public function testListIndicators(): void
    {
        $payload = [
            'indicators' => [
                'trend' => ['SMA_10' => 'Simple Moving Average 10'],
                'oscillator' => ['RSI_14' => 'Relative Strength Index 14'],
            ],
            'timeframes' => ['M1', 'M5', 'H1'],
            'categories' => ['trend', 'oscillator', 'volatility', 'volume'],
        ];
        $f = MockClientFactory::create([MockClientFactory::success($payload)]);

        $result = $f->client->listIndicators();

        self::assertInstanceOf(IndicatorCatalogue::class, $result);
        self::assertSame('Relative Strength Index 14', $result->indicators['oscillator']['RSI_14']);
        self::assertContains('H1', $result->timeframes);
        self::assertContains('volume', $result->categories);
        self::assertSame('/v1/indicators/list', $this->path($f));
    }

    // ---- 7.10 GET /indicator/history ----

    public function testGetIndicatorHistory(): void
    {
        $payload = [
            'symbol' => 'EURUSD', 'indicator' => 'RSI_14', 'timeframe' => 'H1',
            'from' => '2026-05-01T00:00:00', 'to' => '2026-05-02T00:00:00', 'count' => 2,
            'max_window_hours' => 720,
            'series' => [
                ['time' => '2026-05-01T00:00:00', 'value' => 55.1],
                ['time' => '2026-05-01T01:00:00', 'value' => null],
            ],
        ];
        $f = MockClientFactory::create([MockClientFactory::success($payload)]);

        $result = $f->client->getIndicatorHistory('EURUSD', 'RSI_14', [
            'timeframe' => 'H1', 'from' => '2026-05-01T00:00:00', 'to' => '2026-05-02T00:00:00', 'limit' => 100,
        ]);

        self::assertInstanceOf(IndicatorHistory::class, $result);
        self::assertSame(720, $result->maxWindowHours);
        self::assertCount(2, $result->series);
        self::assertSame(55.1, $result->series[0]->value);
        self::assertNull($result->series[1]->value);

        self::assertSame('/v1/indicator/history', $this->path($f));
        self::assertStringContainsString('indicator=RSI_14', $this->query($f));
        self::assertStringContainsString('limit=100', $this->query($f));
    }

    // ---- 7.11 GET /multi ----

    public function testGetMultiRealtime(): void
    {
        $payload = [
            'timeframe' => 'H1',
            'data' => [
                'EURUSD' => ['RSI_14' => 58.34, 'SMA_20' => 1.1],
                'GBPUSD' => ['RSI_14' => 44.0, 'SMA_20' => null],
            ],
            'not_found' => null, 'updated_at' => 1711548000,
        ];
        $f = MockClientFactory::create([MockClientFactory::success($payload)]);

        $result = $f->client->getMulti(['EURUSD', 'GBPUSD'], [Indicator::RSI_14, 'SMA_20'], ['timeframe' => 'H1']);

        self::assertInstanceOf(MultiIndicators::class, $result);
        self::assertFalse($result->isHistorical());
        self::assertSame(58.34, $result->data['EURUSD']['RSI_14']);

        self::assertSame('/v1/multi', $this->path($f));
        $q = urldecode($this->query($f));
        self::assertStringContainsString('symbols=EURUSD,GBPUSD', $q);
        self::assertStringContainsString('indicators=RSI_14,SMA_20', $q);
    }

    public function testGetMultiHistorical(): void
    {
        $payload = [
            'timeframe' => 'H1', 'mode' => 'historical', 'from' => 'f', 'to' => 't',
            'data' => ['EURUSD' => [['time' => 'f', 'RSI_14' => 55.0]]],
            'not_found' => null,
        ];
        $f = MockClientFactory::create([MockClientFactory::success($payload)]);

        $result = $f->client->getMulti(['EURUSD'], ['RSI_14'], ['from' => 'f', 'to' => 't']);

        self::assertTrue($result->isHistorical());
        self::assertSame('historical', $result->mode);
        self::assertStringContainsString('from=f', $this->query($f));
    }

    // ---- 7.12 GET /screener ----

    public function testScreen(): void
    {
        $payload = [
            'indicator' => 'RSI_14', 'timeframe' => 'H1',
            'filter' => ['min' => 70, 'max' => null],
            'results' => [
                ['symbol' => 'EURUSD', 'value' => 72.5, 'bid' => 1.1],
                ['symbol' => 'GBPUSD', 'value' => 75.0, 'bid' => 1.27],
            ],
            'total_matches' => 2,
            'pagination' => ['offset' => 0, 'limit' => 50, 'total' => 2, 'has_more' => false],
            'updated_at' => 1711548000,
        ];
        $f = MockClientFactory::create([MockClientFactory::success($payload)]);

        $result = $f->client->screen('RSI_14', ['minVal' => 70, 'sort' => 'desc', 'limit' => 50]);

        self::assertInstanceOf(ScreenerResults::class, $result);
        self::assertSame(70.0, $result->filter['min']);
        self::assertNull($result->filter['max']);
        self::assertSame(2, $result->totalMatches);
        self::assertSame('EURUSD', $result->results[0]->symbol);

        self::assertSame('/v1/screener', $this->path($f));
        $q = $this->query($f);
        // minVal -> min_val, not min
        self::assertStringContainsString('min_val=70', $q);
        self::assertStringNotContainsString('minVal', $q);
        self::assertStringContainsString('sort=desc', $q);
    }

    // ---- 7.13 GET /summary ----

    public function testGetSummary(): void
    {
        $payload = [
            'symbol' => 'EURUSD', 'timeframe' => 'H1', 'bias' => 'bullish', 'bias_strength' => 'strong',
            'confidence' => 0.82, 'trend_score' => 3.0, 'momentum_score' => 1.5, 'volatility_score' => 0.5,
            'signals' => ['trend' => 'up', 'momentum' => 'up', 'volatility' => 'normal', 'volume' => 'high'],
            'key_levels' => ['resistance' => [1.2, 1.25], 'support' => [1.1, 1.05]],
            'bullish_signals' => ['RSI rising'], 'bearish_signals' => [], 'neutral_signals' => [],
            'volatility_info' => ['ATR normal'], 'volume_info' => ['Above avg'],
            'summary' => 'Bullish bias', 'recommendations' => ['Consider longs'],
            'key_values' => ['bid' => 1.1, 'ask' => 1.1002, 'rsi_14' => 58.3, 'macd_hist' => 0.01,
                'adx' => 25, 'atr_14' => 0.002, 'sma_20' => 1.1, 'sma_50' => 1.09, 'sma_200' => 1.08,
                'bb_upper' => 1.12, 'bb_lower' => 1.08, 'stochastic_k' => 60, 'mfi_14' => 55],
            'updated_at' => 1711548000,
        ];
        $f = MockClientFactory::create([MockClientFactory::success($payload)]);

        $result = $f->client->getSummary('EURUSD', Timeframe::H1);

        self::assertInstanceOf(Summary::class, $result);
        self::assertSame(\TickAtlas\Enums\Bias::Bullish, $result->bias);
        self::assertSame('strong', $result->biasStrength);
        self::assertSame(0.82, $result->confidence);
        self::assertSame([1.2, 1.25], $result->keyLevels['resistance']);
        self::assertSame(['RSI rising'], $result->bullishSignals);
        self::assertSame(58.3, $result->keyValues['rsi_14']);

        self::assertSame('/v1/summary', $this->path($f));
        self::assertStringContainsString('timeframe=H1', $this->query($f));
    }

    public function testGetSummaryDefaultTimeframe(): void
    {
        $f = MockClientFactory::create([MockClientFactory::success([
            'symbol' => 'EURUSD', 'timeframe' => 'H1', 'bias' => 'neutral', 'bias_strength' => 'normal',
            'confidence' => 0.5, 'trend_score' => 0, 'momentum_score' => 0, 'volatility_score' => 0,
            'signals' => [], 'key_levels' => ['resistance' => [], 'support' => []],
            'bullish_signals' => [], 'bearish_signals' => [], 'neutral_signals' => [],
            'volatility_info' => [], 'volume_info' => [], 'summary' => '', 'recommendations' => [],
            'key_values' => [], 'updated_at' => 1,
        ])]);

        $f->client->getSummary('EURUSD');

        self::assertStringContainsString('timeframe=H1', $this->query($f));
    }

    // ---- 7.14 GET /spread ----

    public function testGetSpread(): void
    {
        $payload = [
            'symbol' => 'EURUSD',
            'current' => ['spread_pips' => 1.8, 'spread_points' => 18],
            'statistics' => ['period' => '24h', 'avg_spread' => 1.5, 'min_spread' => 1.0,
                'max_spread' => 3.0, 'std_deviation' => 0.4],
            'by_session' => ['asian' => 1.2, 'london' => 1.5, 'new_york' => null],
        ];
        $f = MockClientFactory::create([MockClientFactory::success($payload)]);

        $result = $f->client->getSpread('EURUSD', Period::TwentyFourHours);

        self::assertInstanceOf(Spread::class, $result);
        self::assertSame(1.8, $result->current['spread_pips']);
        self::assertSame(18, $result->current['spread_points']);
        self::assertSame(1.5, $result->statistics['avg_spread']);
        self::assertSame(1.2, $result->bySession['asian']);
        self::assertNull($result->bySession['new_york']);

        self::assertSame('/v1/spread', $this->path($f));
        self::assertStringContainsString('period=24h', $this->query($f));
    }

    // ---- 7.15 GET /spread/compare ----

    public function testCompareSpread(): void
    {
        $payload = [
            'period' => '24h',
            'symbols' => [
                ['symbol' => 'EURUSD', 'current_pips' => 1.8, 'avg_pips' => 1.5, 'min_pips' => 1.0, 'max_pips' => 3.0, 'has_live_data' => true],
                ['symbol' => 'FAKEPAIR', 'current_pips' => null, 'avg_pips' => null, 'min_pips' => null, 'max_pips' => null, 'has_live_data' => false],
            ],
            'count' => 2,
        ];
        $f = MockClientFactory::create([MockClientFactory::success($payload)]);

        $result = $f->client->compareSpread(['EURUSD', 'FAKEPAIR'], '24h');

        self::assertInstanceOf(SpreadComparison::class, $result);
        self::assertSame(2, $result->count);
        self::assertTrue($result->symbols[0]->hasLiveData);
        self::assertFalse($result->symbols[1]->hasLiveData);
        self::assertNull($result->symbols[1]->avgPips);

        self::assertSame('/v1/spread/compare', $this->path($f));
        self::assertStringContainsString('symbols=EURUSD', urldecode($this->query($f)));
    }

    // ---- 7.16 GET /sessions ----

    public function testGetSessions(): void
    {
        $payload = [
            'current_time' => '2026-06-15T12:00:00Z',
            'active_sessions' => ['london', 'new_york'],
            'sessions' => [
                'sydney' => ['status' => 'closed', 'opens_in' => '6h'],
                'london' => ['status' => 'open', 'closes_in' => '4h'],
            ],
            'overlaps' => ['london/new_york'],
            'next_major_event' => ['event' => 'NY close', 'in' => '4h'],
        ];
        $f = MockClientFactory::create([MockClientFactory::success($payload)]);

        $result = $f->client->getSessions();

        self::assertInstanceOf(Sessions::class, $result);
        self::assertSame(['london', 'new_york'], $result->activeSessions);
        self::assertSame('open', $result->sessions['london']['status']);
        self::assertSame('NY close', $result->nextMajorEvent['event']);
        self::assertSame('/v1/sessions', $this->path($f));
    }

    public function testGetSessionsNullNextEvent(): void
    {
        $f = MockClientFactory::create([MockClientFactory::success([
            'current_time' => 't', 'active_sessions' => [], 'sessions' => [],
            'overlaps' => [], 'next_major_event' => null,
        ])]);

        $result = $f->client->getSessions();

        self::assertNull($result->nextMajorEvent);
    }

    // ---- 7.17 GET /heatmap ----

    public function testGetHeatmapStrength(): void
    {
        $payload = [
            'type' => 'strength', 'timeframe' => 'H4',
            'currencies' => [
                'USD' => ['strength' => 7.5, 'trend' => 'bullish', 'change' => 0.5, 'pairs_analyzed' => 7],
                'EUR' => ['strength' => 3.2, 'trend' => 'bearish', 'change' => -0.3, 'pairs_analyzed' => 7],
            ],
            'strongest' => 'USD', 'weakest' => 'EUR', 'range' => 4.3, 'timestamp' => 't',
        ];
        $f = MockClientFactory::create([MockClientFactory::success($payload)]);

        $result = $f->client->getHeatmap(['type' => HeatmapType::Strength, 'timeframe' => HeatmapTimeframe::H4]);

        self::assertInstanceOf(Heatmap::class, $result);
        self::assertFalse($result->isCorrelation());
        self::assertSame('USD', $result->strongest);
        self::assertSame(7.5, $result->currencies['USD']['strength']);

        self::assertSame('/v1/heatmap', $this->path($f));
        self::assertStringContainsString('type=strength', $this->query($f));
        self::assertStringContainsString('timeframe=H4', $this->query($f));
    }

    public function testGetHeatmapCorrelationUnavailable(): void
    {
        $payload = [
            'type' => 'correlation', 'timeframe' => 'H4',
            'correlation_matrix' => [], 'available' => false,
            'message' => 'Not enough data', 'timestamp' => 't',
        ];
        $f = MockClientFactory::create([MockClientFactory::success($payload)]);

        $result = $f->client->getHeatmap(['correlations' => true]);

        self::assertTrue($result->isCorrelation());
        self::assertFalse($result->available);
        self::assertSame('Not enough data', $result->message);
        self::assertStringContainsString('correlations=true', $this->query($f));
    }

    // ---- 7.18 GET /calendar ----

    public function testGetCalendar(): void
    {
        $payload = [
            'events' => [
                ['id' => 'e1', 'datetime' => '2026-06-15T12:30:00', 'currency' => 'USD',
                    'event' => 'CPI', 'impact' => 'high', 'forecast' => '3.1%', 'previous' => '3.0%', 'actual' => null],
            ],
            'count' => 1,
            'pagination' => ['offset' => 0, 'limit' => 100, 'total' => 1, 'has_more' => false],
            'range' => ['from' => '2026-06-15', 'to' => '2026-06-22'],
        ];
        $f = MockClientFactory::create([MockClientFactory::success($payload)]);

        $result = $f->client->getCalendar([
            'currencies' => ['USD', 'EUR'], 'impact' => Impact::High, 'limit' => 100,
        ]);

        self::assertInstanceOf(Calendar::class, $result);
        self::assertCount(1, $result->events);
        self::assertSame('CPI', $result->events[0]->event);
        self::assertSame('high', $result->events[0]->impact);
        self::assertNull($result->events[0]->actual);
        self::assertSame('2026-06-22', $result->range['to']);

        self::assertSame('/v1/calendar', $this->path($f));
        $q = urldecode($this->query($f));
        self::assertStringContainsString('currencies=USD,EUR', $q);
        self::assertStringContainsString('impact=high', $q);
    }

    // ---- 7.19 GET /monitor/account ----

    public function testGetAccount(): void
    {
        $payload = [
            'name' => 'Acme Trading', 'plan' => 'pro', 'prepaid_credits' => 1000.0,
            'daily_quota' => 50000, 'daily_used' => 1234,
        ];
        $f = MockClientFactory::create([MockClientFactory::success($payload)]);

        $result = $f->client->getAccount();

        self::assertInstanceOf(Account::class, $result);
        self::assertSame('Acme Trading', $result->name);
        self::assertSame('pro', $result->plan);
        self::assertSame(50000, $result->dailyQuota);
        self::assertSame(1234, $result->dailyUsed);
        self::assertSame('/v1/monitor/account', $this->path($f));
    }

    public function testGetAccountUnlimitedQuota(): void
    {
        $f = MockClientFactory::create([MockClientFactory::success([
            'name' => 'Enterprise', 'plan' => 'enterprise', 'prepaid_credits' => 0,
            'daily_quota' => null, 'daily_used' => 9999,
        ])]);

        $result = $f->client->getAccount();

        self::assertNull($result->dailyQuota);
    }

    // ---- 7.20 GET /monitor/layout ----

    public function testGetLayout(): void
    {
        $payload = ['layout' => [['widget' => 'chart', 'symbol' => 'EURUSD']]];
        $f = MockClientFactory::create([MockClientFactory::success($payload)]);

        $result = $f->client->getLayout();

        self::assertInstanceOf(Layout::class, $result);
        self::assertSame('chart', $result->layout[0]['widget']);
        self::assertSame('/v1/monitor/layout', $this->path($f));
    }

    public function testGetLayoutNull(): void
    {
        $f = MockClientFactory::create([MockClientFactory::success(['layout' => null])]);

        $result = $f->client->getLayout();

        self::assertNull($result->layout);
    }

    // ---- 7.21 PUT /monitor/layout (write) ----

    public function testSaveLayout(): void
    {
        $f = MockClientFactory::create([MockClientFactory::success(['saved' => true])]);

        $layout = [['widget' => 'chart', 'symbol' => 'EURUSD']];
        $ok = $f->client->saveLayout($layout);

        self::assertTrue($ok);

        $req = $f->lastRequest();
        self::assertSame('PUT', $req->getMethod());
        self::assertSame('/v1/monitor/layout', $req->getUri()->getPath());
        $body = json_decode((string) $req->getBody(), true);
        self::assertSame($layout, $body['layout']);
    }

    // ---- /health (infra probe) ----

    public function testHealth(): void
    {
        $payload = ['status' => 'ok', 'components' => ['redis' => ['status' => 'up'], 'postgres' => ['status' => 'up']]];
        $f = MockClientFactory::create([MockClientFactory::success($payload)]);

        $result = $f->client->health();

        self::assertInstanceOf(Health::class, $result);
        self::assertSame('ok', $result->status);
        self::assertSame('up', $result->components['redis']['status']);
        self::assertSame('/health', $this->path($f));
    }

    // ---- cross-cutting: auth header + user agent + forward-compat ----

    public function testRequestsCarryAuthAndUserAgentHeaders(): void
    {
        $f = MockClientFactory::create([MockClientFactory::success([
            'symbols' => [], 'total' => 0,
            'pagination' => ['offset' => 0, 'limit' => 100, 'total' => 0, 'has_more' => false],
        ])]);

        $f->client->getSymbols();

        $req = $f->lastRequest();
        self::assertSame('test-key', $req->getHeaderLine('X-API-Key'));
        self::assertSame('tickatlas-php/0.1.0', $req->getHeaderLine('User-Agent'));
    }

    public function testModelToleratesUnknownKeys(): void
    {
        $payload = [
            'symbol' => 'EURUSD', 'bid' => 1.1, 'ask' => 1.1002, 'spread' => 2.0,
            'spread_pips' => 2.0, 'timestamp' => 't',
            'some_future_field' => 'surprise', 'nested' => ['a' => 1],
        ];
        $f = MockClientFactory::create([MockClientFactory::success($payload)]);

        $result = $f->client->getQuote('EURUSD');

        // unknown keys preserved via raw()/toArray()/get()
        self::assertSame('surprise', $result->get('some_future_field'));
        self::assertSame('surprise', $result->toArray()['some_future_field']);
        self::assertSame(['a' => 1], $result->raw()['nested']);
    }
}
