"""
Ensure cached IntelligenceFlow resets on arun dependency failure.
"""
import asyncio
import sys
from pathlib import Path
import types

import pytest
from fastapi import HTTPException

# Add apps directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_flow_cache_resets_after_arun_failure(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    class FailingFlow:
        async def arun(self, query: str):
            raise ModuleNotFoundError("sentence_transformers")

    sys.modules["workflows.intelligence_flow"] = types.SimpleNamespace(
        IntelligenceFlow=FailingFlow
    )

    import api.routes.copilot as copilot_module
    copilot_module._flow_instance = None

    request = copilot_module.CopilotQueryRequest(query="test")
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(copilot_module.query_copilot(request))
    assert exc_info.value.status_code == 503

    instances = {"count": 0}

    class WorkingFlow:
        def __init__(self):
            instances["count"] += 1
        async def arun(self, query: str):
            return types.SimpleNamespace(
                answer="ok",
                agents_used=[],
                citations=[],
                steps=[],
                confidence_score=0.0,
                table_data=None,
            )

    sys.modules["workflows.intelligence_flow"] = types.SimpleNamespace(
        IntelligenceFlow=WorkingFlow
    )

    asyncio.run(copilot_module.query_copilot(request))
    assert instances["count"] == 1
