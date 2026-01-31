"""
Ensure Milvus host/port use env overrides in routes.
"""
import asyncio
import sys
from pathlib import Path
import types

# Add apps directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_companies_uses_env_milvus_host_port(monkeypatch):
    monkeypatch.setenv("MILVUS_HOST", "milvus-host")
    monkeypatch.setenv("MILVUS_PORT", "1234")

    calls = {}

    def connect(*args, **kwargs):
        calls["kwargs"] = kwargs

    fake_pymilvus = types.SimpleNamespace(
        connections=types.SimpleNamespace(connect=connect, has_connection=lambda *_: False),
        Collection=lambda *args, **kwargs: types.SimpleNamespace(load=lambda: None, query=lambda **kw: []),
    )
    sys.modules["pymilvus"] = fake_pymilvus

    from api.routes import companies as companies_route
    companies_route._companies_collection = None

    asyncio.run(companies_route.get_companies())

    assert calls["kwargs"]["host"] == "milvus-host"
    assert calls["kwargs"]["port"] == 1234


def test_filings_uses_env_milvus_host_port(monkeypatch):
    monkeypatch.setenv("MILVUS_HOST", "milvus-host")
    monkeypatch.setenv("MILVUS_PORT", "1234")

    calls = {}

    def connect(*args, **kwargs):
        calls["kwargs"] = kwargs

    fake_pymilvus = types.SimpleNamespace(
        connections=types.SimpleNamespace(connect=connect, has_connection=lambda *_: False),
        Collection=lambda *args, **kwargs: types.SimpleNamespace(load=lambda: None, query=lambda **kw: []),
    )
    sys.modules["pymilvus"] = fake_pymilvus

    from api.routes import filings as filings_route
    filings_route._filings_collection = None

    asyncio.run(filings_route.get_filings(company_code=None, document_type=None, limit=100, offset=0))

    assert calls["kwargs"]["host"] == "milvus-host"
    assert calls["kwargs"]["port"] == 1234
