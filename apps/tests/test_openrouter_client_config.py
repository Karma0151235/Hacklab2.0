"""
Ensure OpenRouter client uses configured timeout/retries.
"""
import sys
from pathlib import Path
import types

import pytest

# Add apps directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def _capture_openai_kwargs(monkeypatch, module):
    captured = {}

    def fake_openai(*args, **kwargs):
        captured["kwargs"] = kwargs
        return types.SimpleNamespace()

    monkeypatch.setattr(module.openai, "OpenAI", fake_openai)
    return captured


def test_financial_agent_passes_timeout_and_retries(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    from agents.config import AgentConfig
    AgentConfig.OPENROUTER_TIMEOUT_SECONDS = 12
    AgentConfig.OPENROUTER_MAX_RETRIES = 3

    from agents import financial_agent as fin_module
    captured = _capture_openai_kwargs(monkeypatch, fin_module)

    fin_module.FinancialAgent()

    assert captured["kwargs"]["timeout"] == 12
    assert captured["kwargs"]["max_retries"] == 3


def test_alert_agent_passes_timeout_and_retries(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    from agents.config import AgentConfig
    AgentConfig.OPENROUTER_TIMEOUT_SECONDS = 12
    AgentConfig.OPENROUTER_MAX_RETRIES = 3

    from agents import alert_agent as alert_module
    captured = _capture_openai_kwargs(monkeypatch, alert_module)

    alert_module.AlertAgent()

    assert captured["kwargs"]["timeout"] == 12
    assert captured["kwargs"]["max_retries"] == 3


def test_rag_agent_passes_timeout_and_retries(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    # Fake pymilvus module so import succeeds
    fake_pymilvus = types.SimpleNamespace(
        connections=types.SimpleNamespace(connect=lambda *args, **kwargs: None),
        Collection=lambda *args, **kwargs: types.SimpleNamespace(load=lambda: None),
    )
    sys.modules["pymilvus"] = fake_pymilvus

    from agents.config import AgentConfig
    AgentConfig.OPENROUTER_TIMEOUT_SECONDS = 12
    AgentConfig.OPENROUTER_MAX_RETRIES = 3

    from agents import rag_agent as rag_module

    class DummyEmbeddingGenerator:
        def __init__(self, *args, **kwargs):
            pass

    monkeypatch.setattr(rag_module, "EmbeddingGenerator", DummyEmbeddingGenerator)
    captured = _capture_openai_kwargs(monkeypatch, rag_module)

    rag_module.RAGAgent()

    assert captured["kwargs"]["timeout"] == 12
    assert captured["kwargs"]["max_retries"] == 3
