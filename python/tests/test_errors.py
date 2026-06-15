"""Error-envelope -> typed-exception mapping (SPEC section 4)."""

from __future__ import annotations

import httpx
import pytest

import tickatlas
from tickatlas import (
    AuthenticationError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    ServerError,
    TickAtlasAPIError,
    ValidationError,
)

from conftest import error_envelope, make_sync_client, single_response


def call_expecting(status, body, headers=None):
    handler = single_response(status, body, headers)
    client = make_sync_client(handler, max_retries=0)
    try:
        client.get_quote("EURUSD")
    finally:
        client.close()


def test_404_symbol_not_found_maps_to_not_found():
    body = error_envelope(
        "SYMBOL_NOT_FOUND",
        "Symbol 'NOPE' not found",
        available_symbols=["EURUSD", "GBPUSD"],
    )
    handler = single_response(404, body, {"X-Request-ID": "req-404"})
    client = make_sync_client(handler, max_retries=0)
    with pytest.raises(NotFoundError) as exc_info:
        client.get_quote("NOPE")
    client.close()

    err = exc_info.value
    assert isinstance(err, TickAtlasAPIError)
    assert err.status_code == 404
    assert err.code == "SYMBOL_NOT_FOUND"
    assert err.message == "Symbol 'NOPE' not found"
    assert err.request_id == "req-404"
    # Forward-compat context fields are exposed via .raw.
    assert err.raw["available_symbols"] == ["EURUSD", "GBPUSD"]


def test_401_invalid_api_key_maps_to_authentication_error():
    with pytest.raises(AuthenticationError) as exc_info:
        call_expecting(401, error_envelope("INVALID_API_KEY", "Key not recognised"))
    assert exc_info.value.status_code == 401
    assert exc_info.value.code == "INVALID_API_KEY"


def test_403_plan_upgrade_maps_to_permission_denied():
    body = error_envelope(
        "PLAN_UPGRADE_REQUIRED",
        "Upgrade required",
        current_plan="free",
        required_plan="pro",
    )
    with pytest.raises(PermissionDeniedError) as exc_info:
        call_expecting(403, body)
    assert exc_info.value.code == "PLAN_UPGRADE_REQUIRED"
    assert exc_info.value.raw["required_plan"] == "pro"


def test_422_validation_error_carries_details():
    details = [{"type": "int_parsing", "loc": ["query", "limit"], "msg": "bad int"}]
    body = error_envelope("VALIDATION_ERROR", "Validation failed", details=details)
    with pytest.raises(ValidationError) as exc_info:
        call_expecting(422, body)
    err = exc_info.value
    assert err.status_code == 422
    assert err.code == "VALIDATION_ERROR"
    assert err.details == details


def test_400_invalid_timeframe_maps_to_validation_error():
    body = error_envelope(
        "INVALID_TIMEFRAME", "Bad timeframe", valid_timeframes=["H1", "H4"]
    )
    with pytest.raises(ValidationError) as exc_info:
        call_expecting(400, body)
    assert exc_info.value.code == "INVALID_TIMEFRAME"
    assert exc_info.value.raw["valid_timeframes"] == ["H1", "H4"]


def test_429_rate_limit_carries_retry_after_from_header():
    body = error_envelope("RATE_LIMIT_EXCEEDED", "Too many", reset_in_seconds=42)
    handler = single_response(429, body, {"Retry-After": "30"})
    client = make_sync_client(handler, max_retries=0)
    with pytest.raises(RateLimitError) as exc_info:
        client.get_quote("EURUSD")
    client.close()
    # Header wins over body when present.
    assert exc_info.value.retry_after == 30.0
    assert exc_info.value.code == "RATE_LIMIT_EXCEEDED"


def test_429_retry_after_falls_back_to_body_reset_seconds():
    body = error_envelope("QUOTA_EXCEEDED", "Quota", reset_in_seconds=3600)
    handler = single_response(429, body)  # no Retry-After header
    client = make_sync_client(handler, max_retries=0)
    with pytest.raises(RateLimitError) as exc_info:
        client.get_quote("EURUSD")
    client.close()
    assert exc_info.value.retry_after == 3600.0


def test_500_internal_error_maps_to_server_error():
    with pytest.raises(ServerError) as exc_info:
        call_expecting(500, error_envelope("INTERNAL_ERROR", "boom"), {})
    assert exc_info.value.status_code == 500
    assert exc_info.value.code == "INTERNAL_ERROR"


def test_503_service_unavailable_maps_to_server_error():
    with pytest.raises(ServerError):
        call_expecting(503, error_envelope("SERVICE_UNAVAILABLE", "down"))


def test_string_detail_error_becomes_http_code():
    # Server normalises plain-string details to {"code": "HTTP_<status>"}.
    handler = single_response(400, {"success": False, "error": "layout must be an array"})
    client = make_sync_client(handler, max_retries=0)
    with pytest.raises(ValidationError) as exc_info:
        client.get_quote("EURUSD")
    client.close()
    assert exc_info.value.code == "HTTP_400"
    assert exc_info.value.message == "layout must be an array"


def test_405_maps_to_validation_error():
    with pytest.raises(ValidationError) as exc_info:
        call_expecting(405, error_envelope("HTTP_405", "Method not allowed"))
    assert exc_info.value.status_code == 405


def test_unparseable_error_body_still_raises_typed():
    # Body is not JSON at all.
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="<html>not found</html>")

    client = make_sync_client(handler, max_retries=0)
    with pytest.raises(NotFoundError) as exc_info:
        client.get_quote("EURUSD")
    client.close()
    assert exc_info.value.status_code == 404
    # No code available, message falls back to "HTTP 404".
    assert exc_info.value.code is None
    assert exc_info.value.message == "HTTP 404"


def test_malformed_2xx_envelope_raises_server_error():
    handler = single_response(200, {"unexpected": "shape"})
    client = make_sync_client(handler, max_retries=0)
    with pytest.raises(ServerError) as exc_info:
        client.get_quote("EURUSD")
    client.close()
    assert exc_info.value.code == "MALFORMED_RESPONSE"


def test_exception_hierarchy_is_correct():
    assert issubclass(AuthenticationError, TickAtlasAPIError)
    assert issubclass(NotFoundError, TickAtlasAPIError)
    assert issubclass(RateLimitError, TickAtlasAPIError)
    assert issubclass(TickAtlasAPIError, tickatlas.TickAtlasError)
    assert issubclass(tickatlas.TickAtlasNetworkError, tickatlas.TickAtlasError)


def test_error_str_includes_status_code_and_request_id():
    err = NotFoundError(
        "Symbol not found",
        status_code=404,
        code="SYMBOL_NOT_FOUND",
        request_id="xyz",
    )
    text = str(err)
    assert "404" in text
    assert "SYMBOL_NOT_FOUND" in text
    assert "xyz" in text
