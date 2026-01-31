"""
API root health endpoint behavior.
"""
import asyncio
import sys
from pathlib import Path
import types

# Add apps directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_health_degraded_when_openrouter_missing(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "")

    fake_pymilvus = types.SimpleNamespace(
        connections=types.SimpleNamespace(
            has_connection=lambda *_: True,
            connect=lambda **kwargs: None
        ),
        utility=types.SimpleNamespace(get_server_version=lambda: "2.4.0")
    )
    sys.modules["pymilvus"] = fake_pymilvus

    from api.main import health_check

    response = asyncio.run(health_check())

    assert response["status"] == "degraded"
    assert response["openrouter"] == "missing_key"


def test_health_degraded_when_pymilvus_missing(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    sys.modules["pymilvus"] = types.SimpleNamespace()

    from api.main import health_check

    response = asyncio.run(health_check())

    assert response["status"] == "degraded"
    assert response["milvus"].startswith("disconnected")


def test_health_healthy_when_dependencies_ok(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    fake_pymilvus = types.SimpleNamespace(
        connections=types.SimpleNamespace(
            has_connection=lambda *_: True,
            connect=lambda **kwargs: None
        ),
        utility=types.SimpleNamespace(get_server_version=lambda: "2.4.0")
    )
    sys.modules["pymilvus"] = fake_pymilvus

    from api.main import health_check

    response = asyncio.run(health_check())

    assert response["status"] == "healthy"


def test_health_uses_env_milvus_host_port(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("MILVUS_HOST", "milvus-host")
    monkeypatch.setenv("MILVUS_PORT", "1234")

    calls = {}

    def connect(**kwargs):
        calls["kwargs"] = kwargs

    fake_pymilvus = types.SimpleNamespace(
        connections=types.SimpleNamespace(
            has_connection=lambda *_: False,
            connect=connect
        ),
        utility=types.SimpleNamespace(get_server_version=lambda: "2.4.0")
    )
    sys.modules["pymilvus"] = fake_pymilvus

    from api.main import health_check

    response = asyncio.run(health_check())

    assert response["status"] == "healthy"
    assert calls["kwargs"]["host"] == "milvus-host"
    assert calls["kwargs"]["port"] == 1234
