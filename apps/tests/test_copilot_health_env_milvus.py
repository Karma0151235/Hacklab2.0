"""
Copilot health uses env for Milvus host/port.
"""
import asyncio
import sys
from pathlib import Path
import types

# Add apps directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_copilot_health_uses_env_milvus_host_port(monkeypatch):
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

    from api.routes import copilot as copilot_route
    copilot_route.AgentConfig.MILVUS_HOST = "wrong-host"
    copilot_route.AgentConfig.MILVUS_PORT = 9999

    response = asyncio.run(copilot_route.health_check())

    assert response.status == "healthy"
    assert calls["kwargs"]["host"] == "milvus-host"
    assert calls["kwargs"]["port"] == 1234
