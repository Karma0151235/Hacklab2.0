"""
Copilot handler behavior when dependencies fail during flow execution.
"""
import asyncio
import sys
from pathlib import Path
import types

import pytest
from fastapi import HTTPException

# Add apps directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_copilot_returns_503_when_flow_arun_raises_module_error(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    class FailingFlow:
        async def arun(self, query: str):
            raise ModuleNotFoundError("sentence_transformers")

    fake_module = types.SimpleNamespace(IntelligenceFlow=FailingFlow)
    sys.modules["workflows.intelligence_flow"] = fake_module

    from api.routes.copilot import CopilotQueryRequest, query_copilot, _flow_instance

    # Reset cached flow so our fake is used
    import api.routes.copilot as copilot_module
    copilot_module._flow_instance = None

    request = CopilotQueryRequest(query="test")

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(query_copilot(request))

    assert exc_info.value.status_code == 503
