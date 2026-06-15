"""Shared HTTP plumbing: config, request building, retry policy, response parsing.

Both :class:`tickatlas.TickAtlas` (sync) and :class:`tickatlas.AsyncTickAtlas`
(async) compose a :class:`BaseTransport`. The request-shaping, retry-decision and
response-parsing logic lives here once; only the actual ``send`` + ``sleep`` calls
differ between sync and async, and those are tiny.
"""

from __future__ import annotations

import os
import random
from dataclasses import dataclass
from typing import Any, Callable, Dict, Mapping, Optional

import httpx

from ._exceptions import (
    ServerError,
    TickAtlasAPIError,
    TickAtlasConfigError,
    TickAtlasNetworkError,
    exception_from_response,
)
from ._version import __version__

__all__ = ["BaseTransport", "RequestSpec"]

DEFAULT_BASE_URL = "https://tickatlas.com/v1"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_BASE = 0.5
BACKOFF_CAP = 30.0
USER_AGENT = f"tickatlas-python/{__version__}"

_RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})

# A callable that returns a float in [0, 1); injectable for deterministic tests.
RngFn = Callable[[], float]


@dataclass
class RequestSpec:
    """A fully-resolved, transport-agnostic description of one HTTP request."""

    method: str
    path: str
    params: Optional[Dict[str, Any]] = None
    json: Optional[Any] = None


def _clean_params(params: Optional[Mapping[str, Any]]) -> Optional[Dict[str, Any]]:
    """Drop ``None`` values; stringify enums/bools the way the API expects."""
    if not params:
        return None
    out: Dict[str, Any] = {}
    for key, value in params.items():
        if value is None:
            continue
        if isinstance(value, bool):
            out[key] = "true" if value else "false"
        else:
            # str() turns our _StrEnum members into their bare value.
            out[key] = str(value)
    return out or None


class BaseTransport:
    """Holds config and implements the shared request/retry/parse pipeline.

    The networking primitives (creating the ``httpx`` client, sending a request,
    sleeping between retries) are provided by the sync/async subclasses; this base
    only orchestrates them.
    """

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_base: float = DEFAULT_BACKOFF_BASE,
        jitter: bool = True,
        rng: Optional[RngFn] = None,
    ) -> None:
        resolved_key = api_key or os.environ.get("TICKATLAS_API_KEY")
        if not resolved_key:
            raise TickAtlasConfigError(
                "No TickAtlas API key found. Pass api_key=... to the client or set "
                "the TICKATLAS_API_KEY environment variable."
            )
        if max_retries < 0:
            raise TickAtlasConfigError("max_retries must be >= 0")
        if backoff_base <= 0:
            raise TickAtlasConfigError("backoff_base must be > 0")

        self._api_key = resolved_key
        self.base_url = (
            base_url
            or os.environ.get("TICKATLAS_BASE_URL")
            or DEFAULT_BASE_URL
        ).rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self._jitter = jitter
        # Default rng is module-level random; injectable for deterministic tests.
        self._rng: RngFn = rng if rng is not None else random.random

    # -- header construction ------------------------------------------------
    def _default_headers(self) -> Dict[str, str]:
        return {
            "X-API-Key": self._api_key,
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        }

    def __repr__(self) -> str:  # pragma: no cover - cosmetic, never leaks the key
        return (
            f"{type(self).__name__}(base_url={self.base_url!r}, "
            f"timeout={self.timeout!r}, max_retries={self.max_retries!r})"
        )

    # -- retry helpers (pure, shared, testable) -----------------------------
    def _compute_backoff(self, attempt: int) -> float:
        """Exponential backoff with full jitter (SPEC section 5).

        ``delay = min(cap, base * 2**attempt) * rand`` with ``rand`` in [0, 1).
        Jitter can be disabled (``jitter=False``) for deterministic behaviour.
        """
        ceiling: float = min(BACKOFF_CAP, self.backoff_base * float(2 ** attempt))
        if not self._jitter:
            return ceiling
        return float(ceiling * self._rng())

    def _retry_delay(
        self, response: Optional[httpx.Response], attempt: int
    ) -> float:
        """Pick the delay before the next attempt.

        On 429, honour ``Retry-After`` (fallback ``X-RateLimit-Reset``) when
        present; otherwise use the computed backoff.
        """
        if response is not None and response.status_code == 429:
            ra = _parse_retry_after(response.headers)
            if ra is not None:
                return ra
        return self._compute_backoff(attempt)

    def _should_retry(
        self,
        *,
        response: Optional[httpx.Response],
        is_network_error: bool,
        attempt: int,
    ) -> bool:
        """Decide whether another attempt is warranted (SPEC section 5)."""
        if attempt >= self.max_retries:
            return False
        if is_network_error:
            return True
        if response is not None and response.status_code in _RETRYABLE_STATUS:
            return True
        return False

    # -- response parsing (pure, shared) ------------------------------------
    def _parse_response(self, response: httpx.Response) -> Any:
        """Validate the envelope and return the unwrapped ``data`` payload.

        Returns the ``data`` value from the success envelope (a dict for every
        documented endpoint). Raises the appropriate typed exception on any
        non-2xx response or malformed body.
        """
        request_id = response.headers.get("X-Request-ID")
        status = response.status_code

        body: Any = None
        try:
            body = response.json()
        except ValueError:  # invalid / empty JSON (json.JSONDecodeError subclasses this)
            body = None

        if 200 <= status < 300:
            if isinstance(body, dict) and body.get("success") is True:
                return body.get("data")
            # 2xx without the documented envelope: surface as a server error so
            # the caller is not silently handed garbage.
            raise ServerError(
                "Malformed success response: missing or false 'success' flag.",
                status_code=status,
                code="MALFORMED_RESPONSE",
                request_id=request_id,
                raw=body if isinstance(body, dict) else {},
            )

        # Error path: pull the normalised error object out of the envelope.
        error_obj: Optional[Dict[str, Any]] = None
        if isinstance(body, dict):
            err = body.get("error")
            if isinstance(err, dict):
                error_obj = err
            elif isinstance(err, str):
                error_obj = {"code": f"HTTP_{status}", "message": err}
            elif body.get("message") or body.get("code"):
                # Tolerate a flat error body just in case.
                error_obj = body

        retry_after = (
            _parse_retry_after(response.headers) if status == 429 else None
        )
        raise exception_from_response(
            status,
            error_obj,
            request_id=request_id,
            retry_after=retry_after,
        )

    @staticmethod
    def _wrap_network_error(exc: httpx.HTTPError) -> TickAtlasNetworkError:
        return TickAtlasNetworkError(
            f"Network error contacting TickAtlas: {exc}", cause=exc
        )


def _parse_retry_after(headers: httpx.Headers) -> Optional[float]:
    """Parse ``Retry-After`` (seconds), falling back to ``X-RateLimit-Reset``."""
    for header in ("Retry-After", "X-RateLimit-Reset"):
        value = headers.get(header)
        if value is None:
            continue
        try:
            seconds = float(value)
        except (TypeError, ValueError):
            continue
        if seconds >= 0:
            return seconds
    return None
