<?php

declare(strict_types=1);

namespace TickAtlas\Tests\Unit;

use GuzzleHttp\Exception\ConnectException;
use GuzzleHttp\Psr7\Request;
use PHPUnit\Framework\TestCase;
use TickAtlas\Exception\NetworkException;
use TickAtlas\Exception\ValidationException;
use TickAtlas\Tests\Support\MockClientFactory;

/**
 * Verifies the SPEC §5 retry policy: which errors retry, how many times, and
 * that Retry-After is honoured on 429.
 */
final class RetryTest extends TestCase
{
    public function test429IsRetriedAndEventuallySucceeds(): void
    {
        $f = MockClientFactory::create([
            MockClientFactory::error(429, 'RATE_LIMIT_EXCEEDED', 'slow down', [], ['Retry-After' => '2']),
            MockClientFactory::error(429, 'RATE_LIMIT_EXCEEDED', 'slow down', [], ['Retry-After' => '2']),
            MockClientFactory::success([
                'symbol' => 'EURUSD', 'bid' => 1.1, 'ask' => 1.1002, 'spread' => 2.0,
                'spread_pips' => 2.0, 'timestamp' => 't',
            ]),
        ]);

        $quote = $f->client->getQuote('EURUSD');

        self::assertSame('EURUSD', $quote->symbol);
        // two retries -> two sleeps, each honouring Retry-After (2s)
        self::assertSame(2, $f->sleeper->count());
        self::assertSame([2.0, 2.0], $f->sleeper->sleeps);
        self::assertSame(3, $f->requestCount());
    }

    public function test429HonoursRetryAfterOverComputedBackoff(): void
    {
        $f = MockClientFactory::create([
            MockClientFactory::error(429, 'RATE_LIMIT_EXCEEDED', 'slow', [], ['Retry-After' => '7']),
            MockClientFactory::success(['status' => 'ok', 'components' => []]),
        ]);

        $f->client->health();

        // Retry-After (7s) used verbatim, not the tiny backoffBase.
        self::assertSame([7.0], $f->sleeper->sleeps);
    }

    public function test429FallsBackToRateLimitResetHeader(): void
    {
        $f = MockClientFactory::create([
            MockClientFactory::error(429, 'RATE_LIMIT_EXCEEDED', 'slow', [], ['X-RateLimit-Reset' => '5']),
            MockClientFactory::success(['status' => 'ok', 'components' => []]),
        ]);

        $f->client->health();

        self::assertSame([5.0], $f->sleeper->sleeps);
    }

    public function test5xxIsRetried(): void
    {
        $f = MockClientFactory::create([
            MockClientFactory::error(503, 'SERVICE_UNAVAILABLE', 'down'),
            MockClientFactory::error(500, 'INTERNAL_ERROR', 'boom'),
            MockClientFactory::success(['status' => 'ok', 'components' => []]),
        ]);

        $f->client->health();

        self::assertSame(2, $f->sleeper->count());
        self::assertSame(3, $f->requestCount());
    }

    public function testMaxRetriesIsRespected(): void
    {
        // maxRetries=3 -> 4 total attempts, then throw
        $f = MockClientFactory::create([
            MockClientFactory::error(500, 'INTERNAL_ERROR', 'boom'),
            MockClientFactory::error(500, 'INTERNAL_ERROR', 'boom'),
            MockClientFactory::error(500, 'INTERNAL_ERROR', 'boom'),
            MockClientFactory::error(500, 'INTERNAL_ERROR', 'boom'),
        ], ['maxRetries' => 3]);

        try {
            $f->client->health();
            self::fail('Expected ServerException');
        } catch (\TickAtlas\Exception\ServerException $e) {
            self::assertSame(500, $e->getStatusCode());
        }

        self::assertSame(4, $f->requestCount());
        self::assertSame(3, $f->sleeper->count());
    }

    public function testMaxRetriesZeroDisablesRetry(): void
    {
        $f = MockClientFactory::create([
            MockClientFactory::error(500, 'INTERNAL_ERROR', 'boom'),
        ], ['maxRetries' => 0]);

        $this->expectException(\TickAtlas\Exception\ServerException::class);

        try {
            $f->client->health();
        } finally {
            self::assertSame(1, $f->requestCount());
            self::assertSame(0, $f->sleeper->count());
        }
    }

    public function test4xxValidationIsNotRetried(): void
    {
        $f = MockClientFactory::create([
            MockClientFactory::error(400, 'INVALID_TIMEFRAME', 'nope'),
            // a second response that should never be consumed
            MockClientFactory::success(['symbol' => 'EURUSD', 'timeframe' => 'H1', 'candles' => [], 'count' => 0, 'retention' => null]),
        ]);

        try {
            $f->client->getOhlc('EURUSD', ['timeframe' => 'X']);
            self::fail('Expected ValidationException');
        } catch (ValidationException $e) {
            self::assertSame(400, $e->getStatusCode());
        }

        self::assertSame(1, $f->requestCount());
        self::assertSame(0, $f->sleeper->count());
    }

    public function testNetworkErrorIsRetriedThenThrows(): void
    {
        $req = new Request('GET', 'https://api.test/v1/health');
        $f = MockClientFactory::create([
            new ConnectException('Connection refused', $req),
            new ConnectException('Connection refused', $req),
            new ConnectException('Connection refused', $req),
            new ConnectException('Connection refused', $req),
        ], ['maxRetries' => 3]);

        try {
            $f->client->health();
            self::fail('Expected NetworkException');
        } catch (NetworkException $e) {
            self::assertStringContainsString('Network error', $e->getMessage());
        }

        self::assertSame(4, $f->requestCount());
        self::assertSame(3, $f->sleeper->count());
    }

    public function testNetworkErrorRecoversOnRetry(): void
    {
        $req = new Request('GET', 'https://api.test/v1/health');
        $f = MockClientFactory::create([
            new ConnectException('timeout', $req),
            MockClientFactory::success(['status' => 'ok', 'components' => []]),
        ]);

        $result = $f->client->health();

        self::assertSame('ok', $result->status);
        self::assertSame(2, $f->requestCount());
    }
}
