"""
Copilot endpoint behavior when API key is missing.
"""
import sys
from pathlib import Path

import asyncio

from fastapi import HTTPException
import pytest

# Add apps directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_copilot_query_returns_503_when_api_key_missing(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "")

    from api.routes.copilot import CopilotQueryRequest, query_copilot

    request = CopilotQueryRequest(query="test")

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(query_copilot(request))

    assert exc_info.value.status_code == 503
