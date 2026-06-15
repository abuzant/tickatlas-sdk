<?php

declare(strict_types=1);

namespace TickAtlas\Tests\Unit;

use PHPUnit\Framework\TestCase;
use TickAtlas\Client;
use TickAtlas\Exception\ConfigurationException;
use TickAtlas\Tests\Support\MockClientFactory;

/**
 * Verifies config precedence (arg -> env -> default/throw) per SPEC §10.
 */
final class ConfigurationTest extends TestCase
{
    protected function setUp(): void
    {
        putenv('TICKATLAS_API_KEY');
        putenv('TICKATLAS_BASE_URL');
    }

    protected function tearDown(): void
    {
        putenv('TICKATLAS_API_KEY');
        putenv('TICKATLAS_BASE_URL');
    }

    public function testMissingApiKeyThrowsConfigurationException(): void
    {
        $this->expectException(ConfigurationException::class);
        new Client();
    }

    public function testApiKeyReadFromEnv(): void
    {
        putenv('TICKATLAS_API_KEY=env-key-123');

        // Should not throw.
        $client = new Client();

        self::assertInstanceOf(Client::class, $client);
    }

    public function testExplicitApiKeyTakesPrecedenceOverEnv(): void
    {
        putenv('TICKATLAS_API_KEY=env-key');

        $f = MockClientFactory::create([MockClientFactory::success(['status' => 'ok', 'components' => []])]);
        $f->client->health();

        // The factory always uses 'test-key' explicitly; assert that's what went out.
        self::assertSame('test-key', $f->lastRequest()->getHeaderLine('X-API-Key'));
    }

    public function testDefaultBaseUrl(): void
    {
        $client = new Client('some-key');

        self::assertSame('https://tickatlas.com/v1', $client->getBaseUrl());
    }

    public function testBaseUrlFromEnv(): void
    {
        putenv('TICKATLAS_BASE_URL=https://staging.tickatlas.com/v1');

        $client = new Client('some-key');

        self::assertSame('https://staging.tickatlas.com/v1', $client->getBaseUrl());
    }

    public function testExplicitBaseUrlBeatsEnv(): void
    {
        putenv('TICKATLAS_BASE_URL=https://staging.tickatlas.com/v1');

        $client = new Client('some-key', 'https://custom.example.com/v1');

        self::assertSame('https://custom.example.com/v1', $client->getBaseUrl());
    }

    public function testTrailingSlashOnBaseUrlIsTrimmed(): void
    {
        $client = new Client('some-key', 'https://custom.example.com/v1/');

        self::assertSame('https://custom.example.com/v1', $client->getBaseUrl());
    }

    public function testInvalidHttpClientOptionThrows(): void
    {
        $this->expectException(ConfigurationException::class);
        new Client('some-key', null, ['httpClient' => 'not-a-client']);
    }

    public function testInvalidSleeperOptionThrows(): void
    {
        $this->expectException(ConfigurationException::class);
        new Client('some-key', null, ['sleeper' => new \stdClass()]);
    }
}
