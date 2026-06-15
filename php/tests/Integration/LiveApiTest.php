<?php

declare(strict_types=1);

namespace TickAtlas\Tests\Integration;

use PHPUnit\Framework\TestCase;
use TickAtlas\Client;
use TickAtlas\Model\Account;
use TickAtlas\Model\Quote;
use TickAtlas\Model\SymbolList;

/**
 * Read-only smoke tests against the live API.
 *
 * GATED: these only run when BOTH RUN_INTEGRATION=1 and a TICKATLAS_API_KEY are
 * present in the environment; otherwise every test is skipped. They never
 * mutate state (the write endpoint PUT /monitor/layout is deliberately not
 * exercised here). Do NOT run these as part of the normal unit suite.
 *
 * Example:
 *   RUN_INTEGRATION=1 TICKATLAS_API_KEY=claw_xxx vendor/bin/phpunit --testsuite integration
 */
final class LiveApiTest extends TestCase
{
    private Client $client;

    protected function setUp(): void
    {
        if (getenv('RUN_INTEGRATION') !== '1') {
            self::markTestSkipped('Integration tests disabled (set RUN_INTEGRATION=1 to enable).');
        }

        $key = getenv('TICKATLAS_API_KEY');
        if ($key === false || $key === '') {
            self::markTestSkipped('TICKATLAS_API_KEY not set; skipping live integration tests.');
        }

        // Key/base URL resolved from the environment by the Client itself.
        $this->client = new Client();
    }

    public function testHealthProbe(): void
    {
        $health = $this->client->health();
        self::assertNotNull($health->status);
    }

    public function testListSymbols(): void
    {
        $symbols = $this->client->getSymbols(['limit' => 5]);
        self::assertInstanceOf(SymbolList::class, $symbols);
        self::assertGreaterThan(0, $symbols->total);
    }

    public function testQuote(): void
    {
        $quote = $this->client->getQuote('EURUSD');
        self::assertInstanceOf(Quote::class, $quote);
        self::assertSame('EURUSD', $quote->symbol);
    }

    public function testAccountIdentity(): void
    {
        $account = $this->client->getAccount();
        self::assertInstanceOf(Account::class, $account);
        self::assertNotSame('', $account->plan);
    }
}
