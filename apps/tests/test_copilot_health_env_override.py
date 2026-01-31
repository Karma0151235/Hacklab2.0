"""
Copilot health uses runtime env for OpenRouter key.
"""
import asyncio
import sys
from pathlib import Path
import types

# Add apps directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_copilot_health_uses_env_over_config(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    fake_pymilvus = types.SimpleNamespace(
        connections=types.SimpleNamespace(
            has_connection=lambda *_: True,
            connect=lambda **kwargs: None
        ),
        utility=types.SimpleNamespace(get_server_version=lambda: "2.4.0")
    )
    sys.modules["pymilvus"] = fake_pymilvus

    from api.routes import copilot as copilot_route
    copilot_route.AgentConfig.OPENROUTER_API_KEY = ""

    response = asyncio.run(copilot_route.health_check())

    assert response.openrouter == "configured"
