"""
Copilot health returns degraded when pymilvus missing.
"""
import asyncio
import sys
from pathlib import Path
import types

# Add apps directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_copilot_health_degraded_when_pymilvus_missing(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    # Force pymilvus import to fail at runtime
    sys.modules["pymilvus"] = types.SimpleNamespace()

    from api.routes.copilot import health_check

    response = asyncio.run(health_check())

    assert response.status == "degraded"
    assert response.openrouter == "configured"
    assert response.milvus.startswith("disconnected")
