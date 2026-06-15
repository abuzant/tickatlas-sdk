<?php

declare(strict_types=1);

namespace TickAtlas;

use GuzzleHttp\ClientInterface;
use TickAtlas\Enums\Bias;
use TickAtlas\Enums\Category;
use TickAtlas\Enums\HeatmapTimeframe;
use TickAtlas\Enums\HeatmapType;
use TickAtlas\Enums\Impact;
use TickAtlas\Enums\Indicator;
use TickAtlas\Enums\IndicatorCategory;
use TickAtlas\Enums\Period;
use TickAtlas\Enums\Timeframe;
use TickAtlas\Exception\ConfigurationException;
use TickAtlas\Http\HttpClient;
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
use TickAtlas\Retry\Sleeper;

/**
 * The official TickAtlas API client.
 *
 * Covers all 21 `/v1` API-key endpoints plus the `/health` infra probe. Every
 * method returns a strongly-typed model and throws a typed exception on error
 * (see {@see \TickAtlas\Exception\TickAtlasException}).
 *
 * Configuration precedence:
 *   - API key:  explicit $apiKey arg → env TICKATLAS_API_KEY → ConfigurationException
 *   - Base URL: explicit $baseUrl arg → env TICKATLAS_BASE_URL → production default
 *
 * The constructor `$options` array accepts: timeout (int, 30), maxRetries
 * (int, 3), backoffBase (float, 0.5), backoffCap (float, 30.0), httpClient
 * (Guzzle ClientInterface, for testing) and sleeper (Sleeper, for testing).
 *
 * @example
 *   $client = new \TickAtlas\Client('claw_xxx');
 *   $quote  = $client->getQuote('EURUSD');
 *   echo $quote->bid;
 */
final class Client
{
    public const VERSION = '0.1.0';

    public const DEFAULT_BASE_URL = 'https://tickatlas.com/v1';

    private readonly HttpClient $http;

    /**
     * @param string|null          $apiKey  explicit key; falls back to TICKATLAS_API_KEY
     * @param string|null          $baseUrl explicit base URL; falls back to TICKATLAS_BASE_URL then the default
     * @param array<string, mixed> $options timeout, maxRetries, backoffBase, backoffCap, httpClient, sleeper
     */
    public function __construct(
        ?string $apiKey = null,
        ?string $baseUrl = null,
        array $options = [],
    ) {
        $key = $apiKey ?? self::envOrNull('TICKATLAS_API_KEY');
        if ($key === null || $key === '') {
            throw new ConfigurationException(
                'A TickAtlas API key is required. Pass it to the Client constructor or set the '
                . 'TICKATLAS_API_KEY environment variable.',
            );
        }

        $resolvedBaseUrl = $baseUrl
            ?? self::envOrNull('TICKATLAS_BASE_URL')
            ?? self::DEFAULT_BASE_URL;

        $httpClient = $options['httpClient'] ?? null;
        if ($httpClient !== null && !$httpClient instanceof ClientInterface) {
            throw new ConfigurationException('The "httpClient" option must be a Guzzle ClientInterface.');
        }

        $sleeper = $options['sleeper'] ?? null;
        if ($sleeper !== null && !$sleeper instanceof Sleeper) {
            throw new ConfigurationException('The "sleeper" option must implement ' . Sleeper::class . '.');
        }

        $this->http = new HttpClient(
            apiKey: $key,
            baseUrl: $resolvedBaseUrl,
            timeout: (int) ($options['timeout'] ?? 30),
            maxRetries: (int) ($options['maxRetries'] ?? 3),
            backoffBase: (float) ($options['backoffBase'] ?? 0.5),
            backoffCap: (float) ($options['backoffCap'] ?? 30.0),
            httpClient: $httpClient,
            sleeper: $sleeper,
        );
    }

    // =====================================================================
    // Symbols
    // =====================================================================

    /**
     * GET /symbols — list symbols (paginated).
     *
     * @param array<string, mixed> $opts category (string|Category), search, offset, limit
     */
    public function getSymbols(array $opts = []): SymbolList
    {
        $query = $this->filter([
            'category' => self::enumValue($opts['category'] ?? null),
            'search' => $opts['search'] ?? null,
            'offset' => $opts['offset'] ?? null,
            'limit' => $opts['limit'] ?? null,
        ]);

        return SymbolList::fromArray($this->http->get('/symbols', $query));
    }

    /**
     * GET /symbols/{symbol} — full contract specification for one symbol.
     */
    public function getSymbol(string $symbol): SymbolSpec
    {
        return SymbolSpec::fromArray($this->http->get('/symbols/' . rawurlencode($symbol)));
    }

    // =====================================================================
    // Quotes
    // =====================================================================

    /**
     * GET /quote — single real-time quote.
     *
     * @param array<string, mixed> $opts include_sources (bool), source (string)
     */
    public function getQuote(string $symbol, array $opts = []): Quote
    {
        $query = $this->filter([
            'symbol' => $symbol,
            'include_sources' => $opts['include_sources'] ?? null,
            'source' => $opts['source'] ?? null,
        ]);

        return Quote::fromArray($this->http->get('/quote', $query));
    }

    /**
     * POST /quotes — batch quotes (1..100 symbols).
     *
     * @param list<string>      $symbols
     * @param list<string>|null $fields  subset of bid,ask,spread,spread_pips,timestamp
     */
    public function getQuotes(array $symbols, ?array $fields = null): BulkQuotes
    {
        $body = ['symbols' => array_values($symbols)];
        if ($fields !== null) {
            $body['fields'] = array_values($fields);
        }

        return BulkQuotes::fromArray($this->http->post('/quotes', $body));
    }

    // =====================================================================
    // OHLC / ticks
    // =====================================================================

    /**
     * GET /ohlc — OHLC candles.
     *
     * @param array<string, mixed> $opts timeframe (string|Timeframe), from, to, limit
     */
    public function getOhlc(string $symbol, array $opts = []): Ohlc
    {
        $query = $this->filter([
            'symbol' => $symbol,
            'timeframe' => self::enumValue($opts['timeframe'] ?? null),
            'from' => $opts['from'] ?? null,
            'to' => $opts['to'] ?? null,
            'limit' => $opts['limit'] ?? null,
        ]);

        return Ohlc::fromArray($this->http->get('/ohlc', $query));
    }

    /**
     * GET /ticks — tick data (plan: pro/enterprise). `to - from` must be <= 1 hour.
     */
    public function getTicks(string $symbol, string $from, string $to): Ticks
    {
        $query = [
            'symbol' => $symbol,
            'from' => $from,
            'to' => $to,
        ];

        return Ticks::fromArray($this->http->get('/ticks', $query));
    }

    // =====================================================================
    // Indicators
    // =====================================================================

    /**
     * GET /indicator — a single indicator value.
     *
     * @param string|Indicator     $indicator
     * @param array<string, mixed> $opts      timeframe (string|Timeframe), source
     */
    public function getIndicator(string $symbol, string|Indicator $indicator, array $opts = []): IndicatorValue
    {
        $query = $this->filter([
            'symbol' => $symbol,
            'indicator' => self::enumValue($indicator),
            'timeframe' => self::enumValue($opts['timeframe'] ?? null),
            'source' => $opts['source'] ?? null,
        ]);

        return IndicatorValue::fromArray($this->http->get('/indicator', $query));
    }

    /**
     * GET /indicators — all indicators for a symbol.
     *
     * @param array<string, mixed> $opts timeframe (string|Timeframe), category (string|IndicatorCategory)
     */
    public function getIndicators(string $symbol, array $opts = []): IndicatorSet
    {
        $query = $this->filter([
            'symbol' => $symbol,
            'timeframe' => self::enumValue($opts['timeframe'] ?? null),
            'category' => self::enumValue($opts['category'] ?? null),
        ]);

        return IndicatorSet::fromArray($this->http->get('/indicators', $query));
    }

    /**
     * GET /indicators/list — the indicator catalogue.
     */
    public function listIndicators(): IndicatorCatalogue
    {
        return IndicatorCatalogue::fromArray($this->http->get('/indicators/list'));
    }

    /**
     * GET /indicator/history — an indicator series (plan: starter+).
     *
     * @param string|Indicator     $indicator
     * @param array<string, mixed> $opts      timeframe (string|Timeframe), from, to, limit
     */
    public function getIndicatorHistory(string $symbol, string|Indicator $indicator, array $opts = []): IndicatorHistory
    {
        $query = $this->filter([
            'symbol' => $symbol,
            'indicator' => self::enumValue($indicator),
            'timeframe' => self::enumValue($opts['timeframe'] ?? null),
            'from' => $opts['from'] ?? null,
            'to' => $opts['to'] ?? null,
            'limit' => $opts['limit'] ?? null,
        ]);

        return IndicatorHistory::fromArray($this->http->get('/indicator/history', $query));
    }

    /**
     * GET /multi — batch indicators across symbols. Supplying from/to switches to
     * historical mode (plan: starter+).
     *
     * @param list<string|Indicator>|list<string> $symbols
     * @param list<string|Indicator>              $indicators
     * @param array<string, mixed>                $opts       timeframe (string|Timeframe), from, to
     */
    public function getMulti(array $symbols, array $indicators, array $opts = []): MultiIndicators
    {
        $query = $this->filter([
            'symbols' => self::joinList($symbols),
            'indicators' => self::joinList($indicators),
            'timeframe' => self::enumValue($opts['timeframe'] ?? null),
            'from' => $opts['from'] ?? null,
            'to' => $opts['to'] ?? null,
        ]);

        return MultiIndicators::fromArray($this->http->get('/multi', $query));
    }

    /**
     * GET /screener — scan symbols by indicator value.
     *
     * The `minVal`/`maxVal` option keys are serialised to the API's `min_val` /
     * `max_val` query params.
     *
     * @param string|Indicator     $indicator
     * @param array<string, mixed> $opts      timeframe, minVal, maxVal, sort (asc|desc), offset, limit
     */
    public function screen(string|Indicator $indicator, array $opts = []): ScreenerResults
    {
        $query = $this->filter([
            'indicator' => self::enumValue($indicator),
            'timeframe' => self::enumValue($opts['timeframe'] ?? null),
            'min_val' => $opts['minVal'] ?? null,
            'max_val' => $opts['maxVal'] ?? null,
            'sort' => $opts['sort'] ?? null,
            'offset' => $opts['offset'] ?? null,
            'limit' => $opts['limit'] ?? null,
        ]);

        return ScreenerResults::fromArray($this->http->get('/screener', $query));
    }

    // =====================================================================
    // Summary / spread
    // =====================================================================

    /**
     * GET /summary — market-bias summary.
     *
     * @param string|Timeframe $timeframe
     */
    public function getSummary(string $symbol, string|Timeframe $timeframe = 'H1'): Summary
    {
        $query = [
            'symbol' => $symbol,
            'timeframe' => self::enumValue($timeframe),
        ];

        return Summary::fromArray($this->http->get('/summary', $query));
    }

    /**
     * GET /spread — spread statistics for a symbol.
     *
     * @param string|Period $period
     */
    public function getSpread(string $symbol, string|Period $period = '24h'): Spread
    {
        $query = [
            'symbol' => $symbol,
            'period' => self::enumValue($period),
        ];

        return Spread::fromArray($this->http->get('/spread', $query));
    }

    /**
     * GET /spread/compare — compare spread across symbols (<= 20).
     *
     * @param list<string>  $symbols
     * @param string|Period $period
     */
    public function compareSpread(array $symbols, string|Period $period = '24h'): SpreadComparison
    {
        $query = [
            'symbols' => self::joinList($symbols),
            'period' => self::enumValue($period),
        ];

        return SpreadComparison::fromArray($this->http->get('/spread/compare', $query));
    }

    // =====================================================================
    // Sessions / heatmap / calendar
    // =====================================================================

    /**
     * GET /sessions — the market session clock.
     */
    public function getSessions(): Sessions
    {
        return Sessions::fromArray($this->http->get('/sessions'));
    }

    /**
     * GET /heatmap — currency strength or correlation.
     *
     * @param array<string, mixed> $opts type (string|HeatmapType), timeframe
     *                                    (string|HeatmapTimeframe), correlations (bool)
     */
    public function getHeatmap(array $opts = []): Heatmap
    {
        $query = $this->filter([
            'type' => self::enumValue($opts['type'] ?? null),
            'timeframe' => self::enumValue($opts['timeframe'] ?? null),
            'correlations' => $opts['correlations'] ?? null,
        ]);

        return Heatmap::fromArray($this->http->get('/heatmap', $query));
    }

    /**
     * GET /calendar — economic calendar.
     *
     * @param array<string, mixed> $opts from, to, currencies (string|list), country,
     *                                    impact (string|Impact), q, next_hours, offset, limit
     */
    public function getCalendar(array $opts = []): Calendar
    {
        $query = $this->filter([
            'from' => $opts['from'] ?? null,
            'to' => $opts['to'] ?? null,
            'currencies' => self::joinList($opts['currencies'] ?? null),
            'country' => self::joinList($opts['country'] ?? null),
            'impact' => self::enumValue($opts['impact'] ?? null),
            'q' => $opts['q'] ?? null,
            'next_hours' => $opts['next_hours'] ?? null,
            'offset' => $opts['offset'] ?? null,
            'limit' => $opts['limit'] ?? null,
        ]);

        return Calendar::fromArray($this->http->get('/calendar', $query));
    }

    // =====================================================================
    // Monitor (account / layout)
    // =====================================================================

    /**
     * GET /monitor/account — account identity & quota (the de-facto /me).
     */
    public function getAccount(): Account
    {
        return Account::fromArray($this->http->get('/monitor/account'));
    }

    /**
     * GET /monitor/layout — the saved dashboard layout (or null).
     */
    public function getLayout(): Layout
    {
        return Layout::fromArray($this->http->get('/monitor/layout'));
    }

    /**
     * PUT /monitor/layout — save the dashboard layout.
     *
     * ADVANCED / WRITE: this mutates the authenticated user's saved dashboard
     * (<= 60 widgets). It is the only write endpoint in the SDK; use with care.
     *
     * @param array<int|string, mixed> $layout the widget layout array (<= 60 elements)
     *
     * @return bool true when the server confirms the save
     */
    public function saveLayout(array $layout): bool
    {
        $data = $this->http->put('/monitor/layout', ['layout' => array_values($layout)]);

        return (bool) ($data['saved'] ?? false);
    }

    // =====================================================================
    // Infra probe
    // =====================================================================

    /**
     * GET /health — infrastructure health probe (no API key strictly required,
     * but the key is still sent).
     */
    public function health(): Health
    {
        return Health::fromArray($this->http->getRoot('/health'));
    }

    // =====================================================================
    // Internals
    // =====================================================================

    /** Expose the configured base URL (handy for diagnostics). */
    public function getBaseUrl(): string
    {
        return $this->http->getBaseUrl();
    }

    private static function envOrNull(string $name): ?string
    {
        $value = getenv($name);

        return ($value === false || $value === '') ? null : $value;
    }

    /**
     * Normalise an enum-or-string-or-null param into its string value.
     */
    private static function enumValue(mixed $value): ?string
    {
        if ($value === null) {
            return null;
        }

        if ($value instanceof \BackedEnum) {
            return (string) $value->value;
        }

        return (string) $value;
    }

    /**
     * Join a comma-separated list param. Accepts a plain string (passed through),
     * a list (of strings/enums) joined on commas, or null. An empty array yields
     * null so {@see self::filter()} drops the param rather than emitting `key=`.
     */
    private static function joinList(mixed $value): ?string
    {
        if ($value === null) {
            return null;
        }

        if (is_array($value)) {
            if ($value === []) {
                return null;
            }

            $parts = array_map(static fn (mixed $v): string => self::enumValue($v) ?? '', $value);

            return implode(',', $parts);
        }

        return (string) $value;
    }

    /**
     * Drop null entries from a query array.
     *
     * @param array<string, mixed> $params
     *
     * @return array<string, mixed>
     */
    private function filter(array $params): array
    {
        return array_filter($params, static fn (mixed $v): bool => $v !== null);
    }
}
