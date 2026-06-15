"""Typed exception hierarchy for the TickAtlas SDK.

Mirrors SPEC section 4 exactly::

    TickAtlasError                     (base for everything)
    +-- TickAtlasAPIError              (the server returned a structured error)
    |   |   .status_code .code .message .details .request_id .raw
    |   +-- AuthenticationError        HTTP 401
    |   +-- PermissionDeniedError      HTTP 403
    |   +-- NotFoundError              HTTP 404
    |   +-- ValidationError            HTTP 400 & 422
    |   +-- RateLimitError             HTTP 429 (carries retry_after)
    |   +-- ServerError                HTTP 5xx
    +-- TickAtlasNetworkError          no HTTP response (connection/timeout/DNS)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Type

__all__ = [
    "TickAtlasError",
    "TickAtlasConfigError",
    "TickAtlasNetworkError",
    "TickAtlasAPIError",
    "AuthenticationError",
    "PermissionDeniedError",
    "NotFoundError",
    "ValidationError",
    "RateLimitError",
    "ServerError",
    "exception_from_response",
]


class TickAtlasError(Exception):
    """Base class for every error raised by the SDK."""


class TickAtlasConfigError(TickAtlasError, ValueError):
    """Raised for client misconfiguration (e.g. a missing API key).

    This is a local/client-side error and is intentionally *not* an
    ``TickAtlasAPIError`` (no HTTP request was made).
    """


class TickAtlasNetworkError(TickAtlasError):
    """Raised when the request never produced an HTTP response.

    Covers connection failures, timeouts, and DNS errors. The originating
    :mod:`httpx` exception is available via ``__cause__`` / the ``cause``
    attribute.
    """

    def __init__(self, message: str, *, cause: Optional[BaseException] = None) -> None:
        super().__init__(message)
        self.cause = cause


class TickAtlasAPIError(TickAtlasError):
    """Raised when the server returns a structured (``success: false``) error.

    Attributes
    ----------
    status_code:
        The HTTP status code of the response.
    code:
        The stable, machine-branchable ``error.code`` string (e.g.
        ``"SYMBOL_NOT_FOUND"``). May be ``None`` if the body was unparseable.
    message:
        The human-readable ``error.message``.
    details:
        The ``error.details`` payload (present for ``VALIDATION_ERROR``); a list
        of validation problems, or ``None``.
    request_id:
        The ``X-Request-ID`` correlation id, if the server sent one.
    raw:
        The full raw ``error`` object so callers can read forward-compatible
        context fields (``valid_timeframes``, ``current_plan``, ``limit``, ...).
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        code: Optional[str] = None,
        details: Optional[List[Any]] = None,
        request_id: Optional[str] = None,
        raw: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        self.request_id = request_id
        self.raw: Dict[str, Any] = raw if raw is not None else {}

    def __str__(self) -> str:
        parts = [f"HTTP {self.status_code}"]
        if self.code:
            parts.append(self.code)
        base = " ".join(parts)
        text = f"{base}: {self.message}" if self.message else base
        if self.request_id:
            text = f"{text} (request_id={self.request_id})"
        return text

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return (
            f"{type(self).__name__}(status_code={self.status_code!r}, "
            f"code={self.code!r}, message={self.message!r})"
        )


class AuthenticationError(TickAtlasAPIError):
    """HTTP 401 - missing or invalid API key."""


class PermissionDeniedError(TickAtlasAPIError):
    """HTTP 403 - key disabled/expired, IP not allowed, account block, or plan gate."""


class NotFoundError(TickAtlasAPIError):
    """HTTP 404 - unknown symbol, indicator, or data."""


class ValidationError(TickAtlasAPIError):
    """HTTP 400 / 422 - invalid parameters or request validation failure."""


class RateLimitError(TickAtlasAPIError):
    """HTTP 429 - rate limit or quota exceeded.

    Carries ``retry_after`` (seconds) parsed from the ``Retry-After`` header,
    falling back to the ``reset_in_seconds`` body field or ``X-RateLimit-Reset``
    header when present.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        retry_after: Optional[float] = None,
        code: Optional[str] = None,
        details: Optional[List[Any]] = None,
        request_id: Optional[str] = None,
        raw: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message,
            status_code=status_code,
            code=code,
            details=details,
            request_id=request_id,
            raw=raw,
        )
        self.retry_after = retry_after


class ServerError(TickAtlasAPIError):
    """HTTP 5xx - internal error or service unavailable."""


# --- status + code -> exception mapping (SPEC section 4) -------------------

# Codes that override the status-based default. The status code is the primary
# signal per the SPEC table; these handle the documented cross-status codes.
_CODE_OVERRIDES: Dict[str, Type[TickAtlasAPIError]] = {
    # 403-style permission codes can arrive on otherwise-ambiguous statuses.
    "PERMISSION_DENIED": PermissionDeniedError,
    "PLAN_UPGRADE_REQUIRED": PermissionDeniedError,
    "API_KEY_DISABLED": PermissionDeniedError,
    "API_KEY_EXPIRED": PermissionDeniedError,
    "IP_NOT_ALLOWED": PermissionDeniedError,
    "ACCOUNT_INACTIVE": PermissionDeniedError,
    "ACCOUNT_SUSPENDED": PermissionDeniedError,
    "ACCOUNT_EXPIRED": PermissionDeniedError,
    # 429-style codes.
    "RATE_LIMIT_EXCEEDED": RateLimitError,
    "QUOTA_EXCEEDED": RateLimitError,
    "RATE_LIMITED": RateLimitError,
}


def _exception_class_for(
    status_code: int, code: Optional[str]
) -> Type[TickAtlasAPIError]:
    """Resolve the exception class for a ``status_code`` + ``error.code`` pair."""
    if code is not None:
        override = _CODE_OVERRIDES.get(code)
        if override is not None:
            return override

    if status_code == 401:
        return AuthenticationError
    if status_code == 403:
        return PermissionDeniedError
    if status_code == 404:
        return NotFoundError
    if status_code == 429:
        return RateLimitError
    if status_code in (400, 422):
        return ValidationError
    if 500 <= status_code <= 599:
        return ServerError
    # 405 and any other 4xx -> ValidationError is the closest documented bucket
    # (e.g. HTTP_405). Anything truly unexpected falls back to the base API error.
    if 400 <= status_code <= 499:
        return ValidationError
    return TickAtlasAPIError


def exception_from_response(
    status_code: int,
    error_obj: Optional[Dict[str, Any]],
    *,
    request_id: Optional[str] = None,
    retry_after: Optional[float] = None,
) -> TickAtlasAPIError:
    """Build the correct typed exception from a normalised error envelope.

    Parameters
    ----------
    status_code:
        HTTP status code of the response.
    error_obj:
        The ``error`` object from the JSON envelope (``{"code", "message", ...}``).
        May be ``None`` if the body could not be parsed as JSON.
    request_id:
        ``X-Request-ID`` header value.
    retry_after:
        Pre-computed retry-after (seconds) for 429s.
    """
    error_obj = error_obj or {}
    code = error_obj.get("code")
    message = error_obj.get("message") or _default_message(status_code, code)
    details = error_obj.get("details")
    if details is not None and not isinstance(details, list):
        details = [details]

    cls = _exception_class_for(status_code, code if isinstance(code, str) else None)

    if cls is RateLimitError:
        if retry_after is None:
            retry_after = _coerce_retry_after(error_obj.get("reset_in_seconds"))
        return RateLimitError(
            message,
            status_code=status_code,
            retry_after=retry_after,
            code=code if isinstance(code, str) else None,
            details=details,
            request_id=request_id,
            raw=error_obj,
        )

    return cls(
        message,
        status_code=status_code,
        code=code if isinstance(code, str) else None,
        details=details,
        request_id=request_id,
        raw=error_obj,
    )


def _coerce_retry_after(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _default_message(status_code: int, code: Any) -> str:
    if isinstance(code, str) and code:
        return code
    return f"HTTP {status_code}"
