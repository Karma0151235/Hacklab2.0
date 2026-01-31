"""
Ensure query failures reset cached collections.
"""
import asyncio
import sys
from pathlib import Path
import types

import pytest
from fastapi import HTTPException

# Add apps directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def _install_failing_query_pymilvus():
    class QueryFailCollection:
        def __init__(self, name):
            self.name = name
        def load(self):
            return None
        def query(self, *args, **kwargs):
            raise RuntimeError("query failed")

    sys.modules["pymilvus"] = types.SimpleNamespace(
        connections=types.SimpleNamespace(connect=lambda *args, **kwargs: None, has_connection=lambda *_: True),
        Collection=QueryFailCollection,
    )


def _install_working_pymilvus(state):
    class WorkingCollection:
        def __init__(self, name):
            state["inits"] += 1
            self.name = name
        def load(self):
            state["loads"] += 1
        def query(self, *args, **kwargs):
            return []

    sys.modules["pymilvus"] = types.SimpleNamespace(
        connections=types.SimpleNamespace(connect=lambda *args, **kwargs: None, has_connection=lambda *_: True),
        Collection=WorkingCollection,
    )


def test_companies_cache_resets_after_query_failure():
    from api.routes import companies as companies_route
    companies_route._companies_collection = None

    _install_failing_query_pymilvus()
    with pytest.raises(HTTPException):
        asyncio.run(companies_route.get_companies())

    state = {"inits": 0, "loads": 0}
    _install_working_pymilvus(state)

    asyncio.run(companies_route.get_companies())
    assert state["inits"] == 1
    assert state["loads"] == 1


def test_filings_cache_resets_after_query_failure():
    from api.routes import filings as filings_route
    filings_route._filings_collection = None

    _install_failing_query_pymilvus()
    with pytest.raises(HTTPException):
        asyncio.run(filings_route.get_filings(company_code=None, document_type=None, limit=100, offset=0))

    state = {"inits": 0, "loads": 0}
    _install_working_pymilvus(state)

    asyncio.run(filings_route.get_filings(company_code=None, document_type=None, limit=100, offset=0))
    assert state["inits"] == 1
    assert state["loads"] == 1
