"""
Tests for CORS configuration.
"""
import importlib
import sys
from pathlib import Path

from fastapi.middleware.cors import CORSMiddleware

# Add apps directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def _get_cors_middleware(app):
    for middleware in app.user_middleware:
        if middleware.cls is CORSMiddleware:
            return middleware
    raise AssertionError("CORSMiddleware not configured")


def test_cors_defaults_to_localhost(monkeypatch):
    monkeypatch.delenv("CORS_ORIGINS", raising=False)

    import api.main as main
    importlib.reload(main)

    cors = _get_cors_middleware(main.app)

    assert cors.options["allow_origins"] == ["http://localhost:3000"]
    assert cors.options["allow_credentials"] is True


def test_cors_parses_env_list(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://example.com, https://app.com")

    import api.main as main
    importlib.reload(main)

    cors = _get_cors_middleware(main.app)

    assert cors.options["allow_origins"] == ["https://example.com", "https://app.com"]


def test_cors_allows_wildcard_without_credentials(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "*")

    import api.main as main
    importlib.reload(main)

    cors = _get_cors_middleware(main.app)

    assert cors.options["allow_origins"] == ["*"]
    assert cors.options["allow_credentials"] is False


def test_cors_removes_wildcard_when_specific_origins_present(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "*, https://example.com")

    import api.main as main
    importlib.reload(main)

    cors = _get_cors_middleware(main.app)

    assert cors.options["allow_origins"] == ["https://example.com"]


def test_cors_deduplicates_origins(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://example.com, https://example.com")

    import api.main as main
    importlib.reload(main)

    cors = _get_cors_middleware(main.app)

    assert cors.options["allow_origins"] == ["https://example.com"]
