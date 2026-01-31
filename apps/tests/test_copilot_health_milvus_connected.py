"""
Copilot health returns healthy when Milvus connected and OpenRouter configured.
"""
import asyncio
import sys
from pathlib import Path
import types

# Add apps directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_copilot_health_healthy_when_dependencies_ok(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    # Fake pymilvus with connected server
    fake_pymilvus = types.SimpleNamespace(
        connections=types.SimpleNamespace(
            has_connection=lambda *_: True,
            connect=lambda **kwargs: None
        ),
        utility=types.SimpleNamespace(get_server_version=lambda: "2.4.0")
    )
    sys.modules["pymilvus"] = fake_pymilvus

    from api.routes.copilot import health_check

    response = asyncio.run(health_check())

    assert response.status == "healthy"
    assert response.openrouter == "configured"
    assert response.milvus == "connected"
