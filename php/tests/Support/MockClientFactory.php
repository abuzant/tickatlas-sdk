<?php

declare(strict_types=1);

namespace TickAtlas\Tests\Support;

use GuzzleHttp\Client as GuzzleClient;
use GuzzleHttp\Handler\MockHandler;
use GuzzleHttp\HandlerStack;
use GuzzleHttp\Middleware;
use GuzzleHttp\Psr7\Response;
use Psr\Http\Message\RequestInterface;
use TickAtlas\Client;
use TickAtlas\Retry\RecordingSleeper;

/**
 * Builds a {@see Client} backed by a Guzzle MockHandler so unit tests never hit
 * the network. Captures outgoing requests for assertion and uses a non-sleeping
 * {@see RecordingSleeper} so retry tests run instantly.
 */
final class MockClientFactory
{
    public readonly Client $client;

    public readonly RecordingSleeper $sleeper;

    /** @var array<int, array{request: RequestInterface, response: mixed}> */
    private array $history = [];

    /**
     * @param list<Response|\Throwable> $responses queued mock responses
     * @param array<string, mixed>      $options   extra Client options (merged)
     */
    public function __construct(array $responses, array $options = [])
    {
        $mock = new MockHandler($responses);
        $stack = HandlerStack::create($mock);
        $stack->push(Middleware::history($this->history));

        $guzzle = new GuzzleClient(['handler' => $stack]);
        $this->sleeper = new RecordingSleeper();

        $this->client = new Client('test-key', 'https://api.test/v1', array_merge([
            'httpClient' => $guzzle,
            'sleeper' => $this->sleeper,
            'backoffBase' => 0.01,
            'backoffCap' => 0.05,
        ], $options));
    }

    /**
     * @param list<Response|\Throwable> $responses
     * @param array<string, mixed>      $options
     */
    public static function create(array $responses, array $options = []): self
    {
        return new self($responses, $options);
    }

    public function lastRequest(): RequestInterface
    {
        $entry = end($this->history);
        if ($entry === false) {
            throw new \RuntimeException('No request was made.');
        }

        return $entry['request'];
    }

    public function requestCount(): int
    {
        return count($this->history);
    }

    /**
     * Build a JSON success response using the standard envelope.
     *
     * @param array<int|string, mixed> $data
     * @param array<string, string>    $headers
     */
    public static function success(array $data, int $status = 200, array $headers = []): Response
    {
        $body = json_encode(['success' => true, 'data' => $data], JSON_THROW_ON_ERROR);

        return new Response($status, array_merge(['Content-Type' => 'application/json'], $headers), $body);
    }

    /**
     * Build a JSON error response using the standard envelope.
     *
     * @param array<string, mixed>  $extra   extra error context fields
     * @param array<string, string> $headers
     */
    public static function error(
        int $status,
        string $code,
        string $message = 'error',
        array $extra = [],
        array $headers = [],
    ): Response {
        $error = array_merge(['code' => $code, 'message' => $message], $extra);
        $body = json_encode(['success' => false, 'error' => $error], JSON_THROW_ON_ERROR);

        return new Response($status, array_merge(['Content-Type' => 'application/json'], $headers), $body);
    }
}
