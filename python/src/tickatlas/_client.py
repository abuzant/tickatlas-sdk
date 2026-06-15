"""Public sync (:class:`TickAtlas`) and async (:class:`AsyncTickAtlas`) clients.

Both clients delegate request shaping/parsing to :mod:`tickatlas._endpoints` and
the retry/parse pipeline to :class:`tickatlas._transport.BaseTransport`. The only
real difference between them is the blocking vs. awaitable send + sleep loop.
"""

from __future__ import annotations

import time
from typing import Any, Callable, List, Optional, TypeVar, Union

import httpx

from . import _endpoints as ep
from . import _models as m
from ._constants import HeatmapType, SpreadPeriod, Timeframe
from ._transport import (
    DEFAULT_BACKOFF_BASE,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    BaseTransport,
    RequestSpec,
    RngFn,
    _clean_params,
)

__all__ = ["TickAtlas", "AsyncTickAtlas"]

T = TypeVar("T")
StrLike = Union[str, Any]


class _ClientBase(BaseTransport):
    """Common constructor surface for both clients."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_base: float = DEFAULT_BACKOFF_BASE,
        jitter: bool = True,
        rng: Optional[RngFn] = None,
        http_client: Optional[Any] = None,
    ) -> None:
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            backoff_base=backoff_base,
            jitter=jitter,
            rng=rng,
        )
        self._provided_client = http_client is not None


# ==========================================================================
# Synchronous client
# ==========================================================================
class TickAtlas(_ClientBase):
    """Synchronous TickAtlas API client.

    Examples
    --------
    >>> from tickatlas import TickAtlas
    >>> client = TickAtlas(api_key="claw_...")          # or TICKATLAS_API_KEY env
    >>> quote = client.get_quote("EURUSD")
    >>> quote.bid, quote.ask
    (1.16404, 1.16422)
    >>> client.close()

    Or as a context manager::

        with TickAtlas() as client:
            symbols = client.get_symbols(category="forex")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_base: float = DEFAULT_BACKOFF_BASE,
        jitter: bool = True,
        rng: Optional[RngFn] = None,
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            backoff_base=backoff_base,
            jitter=jitter,
            rng=rng,
            http_client=http_client,
        )
        self._client: httpx.Client = http_client or httpx.Client(
            timeout=timeout,
        )

    # -- lifecycle ----------------------------------------------------------
    def close(self) -> None:
        """Close the underlying HTTP client (unless one was injected)."""
        if not self._provided_client:
            self._client.close()

    def __enter__(self) -> "TickAtlas":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # -- core request loop --------------------------------------------------
    def _request(self, spec: RequestSpec) -> Any:
        url = f"{self.base_url}{spec.path}"
        headers = self._default_headers()
        params = _clean_params(spec.params)

        attempt = 0
        while True:
            response: Optional[httpx.Response] = None
            is_network_error = False
            try:
                response = self._client.request(
                    spec.method,
                    url,
                    params=params,
                    json=spec.json,
                    headers=headers,
                    timeout=self.timeout,
                )
            except httpx.HTTPError as exc:
                is_network_error = True
                network_exc = exc

            if self._should_retry(
                response=response,
                is_network_error=is_network_error,
                attempt=attempt,
            ):
                delay = self._retry_delay(response, attempt)
                attempt += 1
                if response is not None:
                    response.close()
                time.sleep(delay)
                continue

            if is_network_error:
                raise self._wrap_network_error(network_exc)
            assert response is not None
            return self._parse_response(response)

    def _run(self, plan: ep.Plan[T]) -> T:
        spec, parser = plan
        data = self._request(spec)
        return parser(data)

    # -- endpoints (24) -----------------------------------------------------
    def get_symbols(
        self,
        category: Optional[StrLike] = None,
        search: Optional[str] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> m.SymbolList:
        """List symbols (paginated). See SPEC 7.1."""
        return self._run(ep.get_symbols(category, search, offset, limit))

    def get_symbol(self, symbol: str) -> m.SymbolSpec:
        """Get a symbol's contract specification. See SPEC 7.2."""
        return self._run(ep.get_symbol(symbol))

    def get_quote(
        self,
        symbol: str,
        include_sources: bool = False,
        source: Optional[str] = None,
    ) -> m.Quote:
        """Get a single real-time quote. See SPEC 7.3."""
        return self._run(ep.get_quote(symbol, include_sources, source))

    def get_quotes(
        self,
        symbols: Union[str, List[str]],
        fields: Optional[List[str]] = None,
    ) -> m.BulkQuotes:
        """Get batch quotes (POST). See SPEC 7.4."""
        return self._run(ep.get_quotes(symbols, fields))

    def get_ohlc(
        self,
        symbol: str,
        timeframe: StrLike = Timeframe.H1,
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 100,
    ) -> m.OHLC:
        """Get OHLC candles. ``start``/``end`` map to ``from``/``to``. See SPEC 7.5."""
        return self._run(ep.get_ohlc(symbol, timeframe, start, end, limit))

    def get_ticks(self, symbol: str, start: str, end: str) -> m.Ticks:
        """Get tick data (pro/enterprise; range <= 1h). See SPEC 7.6."""
        return self._run(ep.get_ticks(symbol, start, end))

    def get_indicator(
        self,
        symbol: str,
        indicator: StrLike,
        timeframe: StrLike = Timeframe.H1,
        source: Optional[str] = None,
    ) -> m.Indicator:
        """Get a single indicator value. See SPEC 7.7."""
        return self._run(ep.get_indicator(symbol, indicator, timeframe, source))

    def get_indicators(
        self,
        symbol: str,
        timeframe: StrLike = Timeframe.H1,
        category: Optional[str] = None,
    ) -> m.Indicators:
        """Get all indicators for a symbol. See SPEC 7.8."""
        return self._run(ep.get_indicators(symbol, timeframe, category))

    def list_indicators(self) -> m.IndicatorCatalogue:
        """Get the indicator catalogue. See SPEC 7.9."""
        return self._run(ep.list_indicators())

    def get_indicator_history(
        self,
        symbol: str,
        indicator: StrLike,
        timeframe: StrLike = Timeframe.H1,
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 500,
    ) -> m.IndicatorHistory:
        """Get an indicator series (starter+). See SPEC 7.10."""
        return self._run(
            ep.get_indicator_history(symbol, indicator, timeframe, start, end, limit)
        )

    def get_multi(
        self,
        symbols: Union[str, List[str]],
        indicators: Union[str, List[str]],
        timeframe: StrLike = Timeframe.H1,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> m.MultiIndicators:
        """Get batch indicators across symbols. See SPEC 7.11."""
        return self._run(
            ep.get_multi(symbols, indicators, timeframe, start, end)
        )

    def screen(
        self,
        indicator: StrLike,
        timeframe: StrLike = Timeframe.H1,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
        sort: str = "asc",
        offset: int = 0,
        limit: int = 50,
    ) -> m.Screener:
        """Scan symbols by indicator. See SPEC 7.12."""
        return self._run(
            ep.screen(indicator, timeframe, min_val, max_val, sort, offset, limit)
        )

    def get_summary(
        self, symbol: str, timeframe: StrLike = Timeframe.H1
    ) -> m.Summary:
        """Get a market-bias summary. See SPEC 7.13."""
        return self._run(ep.get_summary(symbol, timeframe))

    def get_spread(
        self, symbol: str, period: StrLike = SpreadPeriod.H24
    ) -> m.Spread:
        """Get spread statistics. See SPEC 7.14."""
        return self._run(ep.get_spread(symbol, period))

    def compare_spread(
        self,
        symbols: Union[str, List[str]],
        period: StrLike = SpreadPeriod.H24,
    ) -> m.SpreadCompare:
        """Compare spread across symbols. See SPEC 7.15."""
        return self._run(ep.compare_spread(symbols, period))

    def get_sessions(self) -> m.Sessions:
        """Get the market session clock. See SPEC 7.16."""
        return self._run(ep.get_sessions())

    def get_heatmap(
        self,
        type: StrLike = HeatmapType.STRENGTH,
        timeframe: StrLike = "H4",
        correlations: Optional[bool] = None,
    ) -> m.Heatmap:
        """Get the currency strength / correlation heatmap. See SPEC 7.17."""
        return self._run(ep.get_heatmap(type, timeframe, correlations))

    def get_calendar(
        self,
        start: Optional[str] = None,
        end: Optional[str] = None,
        currencies: Optional[Union[str, List[str]]] = None,
        country: Optional[Union[str, List[str]]] = None,
        impact: Optional[StrLike] = None,
        q: Optional[str] = None,
        next_hours: Optional[int] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> m.Calendar:
        """Get the economic calendar. See SPEC 7.18."""
        return self._run(
            ep.get_calendar(
                start, end, currencies, country, impact, q, next_hours, offset, limit
            )
        )

    def get_account(self) -> m.Account:
        """Get account identity & quota. See SPEC 7.19."""
        return self._run(ep.get_account())

    def get_layout(self) -> m.Layout:
        """Get the saved dashboard layout. See SPEC 7.20."""
        return self._run(ep.get_layout())

    def save_layout(self, layout: List[Any]) -> m.LayoutSaveResult:
        """Save the dashboard layout (ADVANCED / WRITE).

        This mutates the API key's server-side dashboard state. See SPEC 7.21.
        """
        return self._run(ep.save_layout(layout))

    def health(self) -> m.Health:
        """Health probe (no auth required server-side). See SPEC infra probes."""
        return self._run(ep.health())


# ==========================================================================
# Asynchronous client
# ==========================================================================
class AsyncTickAtlas(_ClientBase):
    """Asynchronous TickAtlas API client (httpx.AsyncClient).

    Examples
    --------
    >>> import asyncio
    >>> from tickatlas import AsyncTickAtlas
    >>> async def main():
    ...     async with AsyncTickAtlas() as client:
    ...         quote = await client.get_quote("EURUSD")
    ...         print(quote.bid, quote.ask)
    >>> asyncio.run(main())  # doctest: +SKIP
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_base: float = DEFAULT_BACKOFF_BASE,
        jitter: bool = True,
        rng: Optional[RngFn] = None,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            backoff_base=backoff_base,
            jitter=jitter,
            rng=rng,
            http_client=http_client,
        )
        self._client: httpx.AsyncClient = http_client or httpx.AsyncClient(
            timeout=timeout,
        )
        # Injectable async sleep for deterministic tests.
        self._sleep: Callable[[float], Any] = _async_sleep

    # -- lifecycle ----------------------------------------------------------
    async def aclose(self) -> None:
        """Close the underlying async HTTP client (unless one was injected)."""
        if not self._provided_client:
            await self._client.aclose()

    async def __aenter__(self) -> "AsyncTickAtlas":
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.aclose()

    # -- core request loop --------------------------------------------------
    async def _request(self, spec: RequestSpec) -> Any:
        url = f"{self.base_url}{spec.path}"
        headers = self._default_headers()
        params = _clean_params(spec.params)

        attempt = 0
        while True:
            response: Optional[httpx.Response] = None
            is_network_error = False
            try:
                response = await self._client.request(
                    spec.method,
                    url,
                    params=params,
                    json=spec.json,
                    headers=headers,
                    timeout=self.timeout,
                )
            except httpx.HTTPError as exc:
                is_network_error = True
                network_exc = exc

            if self._should_retry(
                response=response,
                is_network_error=is_network_error,
                attempt=attempt,
            ):
                delay = self._retry_delay(response, attempt)
                attempt += 1
                if response is not None:
                    await response.aclose()
                await self._sleep(delay)
                continue

            if is_network_error:
                raise self._wrap_network_error(network_exc)
            assert response is not None
            return self._parse_response(response)

    async def _run(self, plan: ep.Plan[T]) -> T:
        spec, parser = plan
        data = await self._request(spec)
        return parser(data)

    # -- endpoints (24) -----------------------------------------------------
    async def get_symbols(
        self,
        category: Optional[StrLike] = None,
        search: Optional[str] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> m.SymbolList:
        """List symbols (paginated). See SPEC 7.1."""
        return await self._run(ep.get_symbols(category, search, offset, limit))

    async def get_symbol(self, symbol: str) -> m.SymbolSpec:
        """Get a symbol's contract specification. See SPEC 7.2."""
        return await self._run(ep.get_symbol(symbol))

    async def get_quote(
        self,
        symbol: str,
        include_sources: bool = False,
        source: Optional[str] = None,
    ) -> m.Quote:
        """Get a single real-time quote. See SPEC 7.3."""
        return await self._run(ep.get_quote(symbol, include_sources, source))

    async def get_quotes(
        self,
        symbols: Union[str, List[str]],
        fields: Optional[List[str]] = None,
    ) -> m.BulkQuotes:
        """Get batch quotes (POST). See SPEC 7.4."""
        return await self._run(ep.get_quotes(symbols, fields))

    async def get_ohlc(
        self,
        symbol: str,
        timeframe: StrLike = Timeframe.H1,
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 100,
    ) -> m.OHLC:
        """Get OHLC candles. ``start``/``end`` map to ``from``/``to``. See SPEC 7.5."""
        return await self._run(ep.get_ohlc(symbol, timeframe, start, end, limit))

    async def get_ticks(self, symbol: str, start: str, end: str) -> m.Ticks:
        """Get tick data (pro/enterprise; range <= 1h). See SPEC 7.6."""
        return await self._run(ep.get_ticks(symbol, start, end))

    async def get_indicator(
        self,
        symbol: str,
        indicator: StrLike,
        timeframe: StrLike = Timeframe.H1,
        source: Optional[str] = None,
    ) -> m.Indicator:
        """Get a single indicator value. See SPEC 7.7."""
        return await self._run(ep.get_indicator(symbol, indicator, timeframe, source))

    async def get_indicators(
        self,
        symbol: str,
        timeframe: StrLike = Timeframe.H1,
        category: Optional[str] = None,
    ) -> m.Indicators:
        """Get all indicators for a symbol. See SPEC 7.8."""
        return await self._run(ep.get_indicators(symbol, timeframe, category))

    async def list_indicators(self) -> m.IndicatorCatalogue:
        """Get the indicator catalogue. See SPEC 7.9."""
        return await self._run(ep.list_indicators())

    async def get_indicator_history(
        self,
        symbol: str,
        indicator: StrLike,
        timeframe: StrLike = Timeframe.H1,
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 500,
    ) -> m.IndicatorHistory:
        """Get an indicator series (starter+). See SPEC 7.10."""
        return await self._run(
            ep.get_indicator_history(symbol, indicator, timeframe, start, end, limit)
        )

    async def get_multi(
        self,
        symbols: Union[str, List[str]],
        indicators: Union[str, List[str]],
        timeframe: StrLike = Timeframe.H1,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> m.MultiIndicators:
        """Get batch indicators across symbols. See SPEC 7.11."""
        return await self._run(
            ep.get_multi(symbols, indicators, timeframe, start, end)
        )

    async def screen(
        self,
        indicator: StrLike,
        timeframe: StrLike = Timeframe.H1,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
        sort: str = "asc",
        offset: int = 0,
        limit: int = 50,
    ) -> m.Screener:
        """Scan symbols by indicator. See SPEC 7.12."""
        return await self._run(
            ep.screen(indicator, timeframe, min_val, max_val, sort, offset, limit)
        )

    async def get_summary(
        self, symbol: str, timeframe: StrLike = Timeframe.H1
    ) -> m.Summary:
        """Get a market-bias summary. See SPEC 7.13."""
        return await self._run(ep.get_summary(symbol, timeframe))

    async def get_spread(
        self, symbol: str, period: StrLike = SpreadPeriod.H24
    ) -> m.Spread:
        """Get spread statistics. See SPEC 7.14."""
        return await self._run(ep.get_spread(symbol, period))

    async def compare_spread(
        self,
        symbols: Union[str, List[str]],
        period: StrLike = SpreadPeriod.H24,
    ) -> m.SpreadCompare:
        """Compare spread across symbols. See SPEC 7.15."""
        return await self._run(ep.compare_spread(symbols, period))

    async def get_sessions(self) -> m.Sessions:
        """Get the market session clock. See SPEC 7.16."""
        return await self._run(ep.get_sessions())

    async def get_heatmap(
        self,
        type: StrLike = HeatmapType.STRENGTH,
        timeframe: StrLike = "H4",
        correlations: Optional[bool] = None,
    ) -> m.Heatmap:
        """Get the currency strength / correlation heatmap. See SPEC 7.17."""
        return await self._run(ep.get_heatmap(type, timeframe, correlations))

    async def get_calendar(
        self,
        start: Optional[str] = None,
        end: Optional[str] = None,
        currencies: Optional[Union[str, List[str]]] = None,
        country: Optional[Union[str, List[str]]] = None,
        impact: Optional[StrLike] = None,
        q: Optional[str] = None,
        next_hours: Optional[int] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> m.Calendar:
        """Get the economic calendar. See SPEC 7.18."""
        return await self._run(
            ep.get_calendar(
                start, end, currencies, country, impact, q, next_hours, offset, limit
            )
        )

    async def get_account(self) -> m.Account:
        """Get account identity & quota. See SPEC 7.19."""
        return await self._run(ep.get_account())

    async def get_layout(self) -> m.Layout:
        """Get the saved dashboard layout. See SPEC 7.20."""
        return await self._run(ep.get_layout())

    async def save_layout(self, layout: List[Any]) -> m.LayoutSaveResult:
        """Save the dashboard layout (ADVANCED / WRITE).

        This mutates the API key's server-side dashboard state. See SPEC 7.21.
        """
        return await self._run(ep.save_layout(layout))

    async def health(self) -> m.Health:
        """Health probe (no auth required server-side). See SPEC infra probes."""
        return await self._run(ep.health())


async def _async_sleep(delay: float) -> None:
    import asyncio

    await asyncio.sleep(delay)
