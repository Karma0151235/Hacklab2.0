"""
Unit tests for AgentConfig initialization behavior.
"""
import importlib
import sys
from pathlib import Path

import pytest

# Add apps directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_agent_config_import_without_api_key_does_not_raise(monkeypatch):
    """
    Importing agents.config should not crash the app if API key is missing.
    """
    monkeypatch.setenv("OPENROUTER_API_KEY", "")

    import agents.config as config

    try:
        importlib.reload(config)
    except Exception as exc:  # pragma: no cover - failure is the point pre-fix
        pytest.fail(f"agents.config raised on import without API key: {exc}")


def test_agent_config_handles_empty_milvus_env(monkeypatch):
    monkeypatch.setenv("MILVUS_HOST", "")
    monkeypatch.setenv("MILVUS_PORT", "")

    import agents.config as config
    importlib.reload(config)

    assert config.AgentConfig.MILVUS_HOST == "localhost"
    assert config.AgentConfig.MILVUS_PORT == 19639
