"""
Ensure Milvus host/port fall back to AgentConfig when env not set.
"""
import asyncio
import sys
from pathlib import Path
import types

# Add apps directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_companies_uses_agentconfig_when_env_missing(monkeypatch):
    monkeypatch.setenv("MILVUS_HOST", "")
    monkeypatch.setenv("MILVUS_PORT", "")

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
    companies_route.AgentConfig.MILVUS_HOST = "agent-host"
    companies_route.AgentConfig.MILVUS_PORT = 1111

    asyncio.run(companies_route.get_companies())

    assert calls["kwargs"]["host"] == "agent-host"
    assert calls["kwargs"]["port"] == 1111


def test_filings_uses_agentconfig_when_env_missing(monkeypatch):
    monkeypatch.setenv("MILVUS_HOST", "")
    monkeypatch.setenv("MILVUS_PORT", "")

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
    filings_route.AgentConfig.MILVUS_HOST = "agent-host"
    filings_route.AgentConfig.MILVUS_PORT = 1111

    asyncio.run(filings_route.get_filings(company_code=None, document_type=None, limit=100, offset=0))

    assert calls["kwargs"]["host"] == "agent-host"
    assert calls["kwargs"]["port"] == 1111
