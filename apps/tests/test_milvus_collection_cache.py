"""
Ensure Milvus collections are cached per route to avoid reload.
"""
import asyncio
import sys
from pathlib import Path
import types

import pytest

# Add apps directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def _install_fake_pymilvus():
    state = {"collection_inits": 0, "loads": 0}

    class FakeCollection:
        def __init__(self, name):
            state["collection_inits"] += 1
            self.name = name
        def load(self):
            state["loads"] += 1
        def query(self, *args, **kwargs):
            return []

    fake_module = types.SimpleNamespace(
        connections=types.SimpleNamespace(connect=lambda *args, **kwargs: None, has_connection=lambda *_: True),
        Collection=FakeCollection,
    )
    sys.modules["pymilvus"] = fake_module
    return state


def test_companies_collection_cached(monkeypatch):
    state = _install_fake_pymilvus()

    from api.routes import companies as companies_route
    companies_route._companies_collection = None

    asyncio.run(companies_route.get_companies())
    asyncio.run(companies_route.get_companies())

    assert state["collection_inits"] == 1
    assert state["loads"] == 1


def test_filings_collection_cached(monkeypatch):
    state = _install_fake_pymilvus()

    from api.routes import filings as filings_route
    filings_route._filings_collection = None

    asyncio.run(filings_route.get_filings(company_code=None, document_type=None, limit=100, offset=0))
    asyncio.run(filings_route.get_filings(company_code=None, document_type=None, limit=100, offset=0))

    assert state["collection_inits"] == 1
    assert state["loads"] == 1
