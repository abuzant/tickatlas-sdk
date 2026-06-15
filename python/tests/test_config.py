"""Client configuration: key/base-url resolution, options, secret hygiene."""

from __future__ import annotations

import pytest

import tickatlas
from tickatlas import AsyncTickAtlas, TickAtlas, TickAtlasConfigError
from tickatlas._transport import DEFAULT_BASE_URL


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch):
    monkeypatch.delenv("TICKATLAS_API_KEY", raising=False)
    monkeypatch.delenv("TICKATLAS_BASE_URL", raising=False)


def test_missing_api_key_raises_config_error():
    with pytest.raises(TickAtlasConfigError) as exc:
        TickAtlas()
    assert "API key" in str(exc.value)


def test_config_error_is_a_tickatlas_error_and_value_error():
    assert issubclass(TickAtlasConfigError, tickatlas.TickAtlasError)
    assert issubclass(TickAtlasConfigError, ValueError)


def test_explicit_key_takes_priority_over_env(monkeypatch):
    monkeypatch.setenv("TICKATLAS_API_KEY", "env_key")
    client = TickAtlas(api_key="explicit_key")
    assert client._api_key == "explicit_key"
    client.close()


def test_key_from_env(monkeypatch):
    monkeypatch.setenv("TICKATLAS_API_KEY", "env_key")
    client = TickAtlas()
    assert client._api_key == "env_key"
    client.close()


def test_base_url_default():
    client = TickAtlas(api_key="k")
    assert client.base_url == DEFAULT_BASE_URL
    client.close()


def test_base_url_from_env(monkeypatch):
    monkeypatch.setenv("TICKATLAS_BASE_URL", "https://staging.example.com/v1/")
    client = TickAtlas(api_key="k")
    # Trailing slash is stripped.
    assert client.base_url == "https://staging.example.com/v1"
    client.close()


def test_base_url_arg_beats_env(monkeypatch):
    monkeypatch.setenv("TICKATLAS_BASE_URL", "https://env.example.com/v1")
    client = TickAtlas(api_key="k", base_url="https://arg.example.com/v1")
    assert client.base_url == "https://arg.example.com/v1"
    client.close()


def test_default_options():
    client = TickAtlas(api_key="k")
    assert client.timeout == 30.0
    assert client.max_retries == 3
    assert client.backoff_base == 0.5
    client.close()


def test_invalid_options_rejected():
    with pytest.raises(TickAtlasConfigError):
        TickAtlas(api_key="k", max_retries=-1)
    with pytest.raises(TickAtlasConfigError):
        TickAtlas(api_key="k", backoff_base=0)


def test_repr_never_leaks_key():
    client = TickAtlas(api_key="super_secret_claw_key")
    text = repr(client)
    assert "super_secret_claw_key" not in text
    assert "TickAtlas" in text
    client.close()


def test_default_headers_never_logged_but_set():
    client = TickAtlas(api_key="super_secret_claw_key")
    headers = client._default_headers()
    assert headers["X-API-Key"] == "super_secret_claw_key"
    assert headers["User-Agent"] == f"tickatlas-python/{tickatlas.__version__}"
    # The key must not appear in repr/str of the client.
    assert "super_secret_claw_key" not in repr(client)
    client.close()


def test_async_client_missing_key_raises():
    with pytest.raises(TickAtlasConfigError):
        AsyncTickAtlas()


def test_user_agent_value():
    from tickatlas._transport import USER_AGENT

    assert USER_AGENT == f"tickatlas-python/{tickatlas.__version__}"
    assert tickatlas.__version__ == "0.1.0"
