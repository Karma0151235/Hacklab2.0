"""
Ensure Copilot handler reuses IntelligenceFlow instance.
"""
import asyncio
import sys
from pathlib import Path
import types

import pytest

# Add apps directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_copilot_reuses_flow_instance(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    # Fake workflows.intelligence_flow module
    flow_state = {"instances": 0}

    class FakeFlow:
        def __init__(self):
            flow_state["instances"] += 1

        async def arun(self, query: str):
            return types.SimpleNamespace(
                answer="ok",
                agents_used=[],
                citations=[],
                steps=[],
                confidence_score=0.0,
                table_data=None,
            )

    fake_module = types.SimpleNamespace(IntelligenceFlow=FakeFlow)
    sys.modules["workflows.intelligence_flow"] = fake_module

    from api.routes import copilot as copilot_routes

    request = copilot_routes.CopilotQueryRequest(query="test")

    asyncio.run(copilot_routes.query_copilot(request))
    asyncio.run(copilot_routes.query_copilot(request))

    assert flow_state["instances"] == 1
