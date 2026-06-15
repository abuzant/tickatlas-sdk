<?php

declare(strict_types=1);

namespace TickAtlas\Tests\Unit;

use PHPUnit\Framework\TestCase;
use TickAtlas\Exception\ApiException;
use TickAtlas\Exception\AuthenticationException;
use TickAtlas\Exception\NotFoundException;
use TickAtlas\Exception\PermissionDeniedException;
use TickAtlas\Exception\RateLimitException;
use TickAtlas\Exception\ServerException;
use TickAtlas\Exception\ValidationException;
use TickAtlas\Tests\Support\MockClientFactory;

/**
 * Verifies HTTP status + error.code -> typed exception mapping (SPEC §4).
 */
final class ErrorMappingTest extends TestCase
{
    public function test404SymbolNotFoundMapsToNotFoundException(): void
    {
        $f = MockClientFactory::create([
            MockClientFactory::error(404, 'SYMBOL_NOT_FOUND', 'Symbol not found',
                ['available_symbols' => ['EURUSD']], ['X-Request-ID' => 'req-123']),
        ]);

        try {
            $f->client->getSymbol('NOPE');
            self::fail('Expected NotFoundException');
        } catch (NotFoundException $e) {
            self::assertSame(404, $e->getStatusCode());
            self::assertSame('SYMBOL_NOT_FOUND', $e->getErrorCode());
            self::assertSame('Symbol not found', $e->getMessage());
            self::assertSame('req-123', $e->getRequestId());
            // extra context surfaced via details, raw preserved
            self::assertSame(['EURUSD'], $e->getDetails()['available_symbols']);
            self::assertSame('SYMBOL_NOT_FOUND', $e->getRaw()['error']['code']);
            self::assertInstanceOf(ApiException::class, $e);
        }
    }

    public function test401MapsToAuthenticationException(): void
    {
        $f = MockClientFactory::create([
            MockClientFactory::error(401, 'INVALID_API_KEY', 'Key not recognised'),
        ]);

        $this->expectException(AuthenticationException::class);
        $f->client->getQuote('EURUSD');
    }

    public function test422ValidationErrorMapsToValidationExceptionWithDetails(): void
    {
        $f = MockClientFactory::create([
            MockClientFactory::error(422, 'VALIDATION_ERROR', 'Validation failed', [
                'details' => [
                    ['type' => 'int_parsing', 'loc' => ['query', 'limit'], 'msg' => 'not an int'],
                ],
            ]),
        ]);

        try {
            $f->client->getCalendar(['limit' => 'bad']);
            self::fail('Expected ValidationException');
        } catch (ValidationException $e) {
            self::assertSame(422, $e->getStatusCode());
            self::assertSame('VALIDATION_ERROR', $e->getErrorCode());
            self::assertIsArray($e->getDetails()['details']);
            self::assertSame('int_parsing', $e->getDetails()['details'][0]['type']);
        }
    }

    public function test400InvalidTimeframeMapsToValidationException(): void
    {
        $f = MockClientFactory::create([
            MockClientFactory::error(400, 'INVALID_TIMEFRAME', 'Bad timeframe',
                ['valid_timeframes' => ['M1', 'H1']]),
        ]);

        try {
            $f->client->getOhlc('EURUSD', ['timeframe' => 'X9']);
            self::fail('Expected ValidationException');
        } catch (ValidationException $e) {
            self::assertSame(['M1', 'H1'], $e->getDetails()['valid_timeframes']);
        }
    }

    public function test403PlanUpgradeMapsToPermissionDenied(): void
    {
        $f = MockClientFactory::create([
            MockClientFactory::error(403, 'PLAN_UPGRADE_REQUIRED', 'Upgrade required',
                ['current_plan' => 'free', 'required_plan' => 'pro']),
        ]);

        try {
            $f->client->getTicks('EURUSD', 'a', 'b');
            self::fail('Expected PermissionDeniedException');
        } catch (PermissionDeniedException $e) {
            self::assertSame('PLAN_UPGRADE_REQUIRED', $e->getErrorCode());
            self::assertSame('pro', $e->getDetails()['required_plan']);
        }
    }

    public function test500MapsToServerExceptionAfterRetriesExhausted(): void
    {
        $f = MockClientFactory::create([
            MockClientFactory::error(500, 'INTERNAL_ERROR', 'boom'),
            MockClientFactory::error(500, 'INTERNAL_ERROR', 'boom'),
            MockClientFactory::error(500, 'INTERNAL_ERROR', 'boom'),
            MockClientFactory::error(500, 'INTERNAL_ERROR', 'boom'),
        ]);

        $this->expectException(ServerException::class);
        $f->client->getSessions();
    }

    public function testValidationErrorWithoutMessageGetsDefaultMessage(): void
    {
        // error.code present but message empty -> factory supplies a default
        $f = MockClientFactory::create([
            MockClientFactory::error(400, 'INVALID_SORT', ''),
        ]);

        try {
            $f->client->screen('RSI_14', ['sort' => 'sideways']);
            self::fail('Expected ValidationException');
        } catch (ValidationException $e) {
            self::assertStringContainsString('INVALID_SORT', $e->getMessage());
            self::assertStringContainsString('400', $e->getMessage());
        }
    }

    public function testQuotaExceededMapsToRateLimit(): void
    {
        // QUOTA_EXCEEDED arrives as 429 with Retry-After: 3600 per spec
        $f = MockClientFactory::create([
            MockClientFactory::error(429, 'QUOTA_EXCEEDED', 'Daily quota hit',
                ['reset_in_seconds' => 3600], ['Retry-After' => '3600']),
            MockClientFactory::error(429, 'QUOTA_EXCEEDED', 'Daily quota hit',
                ['reset_in_seconds' => 3600], ['Retry-After' => '3600']),
            MockClientFactory::error(429, 'QUOTA_EXCEEDED', 'Daily quota hit',
                ['reset_in_seconds' => 3600], ['Retry-After' => '3600']),
            MockClientFactory::error(429, 'QUOTA_EXCEEDED', 'Daily quota hit',
                ['reset_in_seconds' => 3600], ['Retry-After' => '3600']),
        ]);

        try {
            $f->client->getAccount();
            self::fail('Expected RateLimitException');
        } catch (RateLimitException $e) {
            self::assertSame('QUOTA_EXCEEDED', $e->getErrorCode());
            self::assertSame(3600, $e->getRetryAfter());
        }
    }
}
