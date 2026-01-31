"""
RAG Agent initialization behavior.
"""
import sys
from pathlib import Path
import types

import pytest

# Add apps directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_rag_agent_initializes_openrouter_client(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    # Provide fake pymilvus module so import succeeds
    fake_pymilvus = types.SimpleNamespace(
        connections=types.SimpleNamespace(connect=lambda *args, **kwargs: None),
        Collection=lambda *args, **kwargs: types.SimpleNamespace(load=lambda: None),
    )
    sys.modules["pymilvus"] = fake_pymilvus

    from agents import rag_agent as rag_module

    class DummyEmbeddingGenerator:
        def __init__(self, *args, **kwargs):
            pass

    monkeypatch.setattr(rag_module, "EmbeddingGenerator", DummyEmbeddingGenerator)

    rag = rag_module.RAGAgent()

    assert hasattr(rag, "client")
