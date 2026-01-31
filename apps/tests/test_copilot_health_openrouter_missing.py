"""
Copilot health returns degraded when OpenRouter key missing.
"""
import asyncio
import sys
from pathlib import Path

# Add apps directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_copilot_health_degraded_when_openrouter_missing(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "")

    from api.routes.copilot import health_check

    response = asyncio.run(health_check())

    assert response.status == "degraded"
    assert response.openrouter == "missing_key"
