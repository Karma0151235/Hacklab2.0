"""
Ensure Milvus collection load failures return 503.
"""
import asyncio
import sys
from pathlib import Path
import types

import pytest
from fastapi import HTTPException

# Add apps directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def _install_failing_pymilvus():
    class FailingCollection:
        def __init__(self, name):
            self.name = name
        def load(self):
            raise RuntimeError("load failed")
        def query(self, *args, **kwargs):
            return []

    fake_module = types.SimpleNamespace(
        connections=types.SimpleNamespace(connect=lambda *args, **kwargs: None, has_connection=lambda *_: True),
        Collection=FailingCollection,
    )
    sys.modules["pymilvus"] = fake_module


def test_companies_returns_503_when_collection_load_fails():
    _install_failing_pymilvus()
    from api.routes import companies as companies_route
    companies_route._companies_collection = None

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(companies_route.get_companies())

    assert exc_info.value.status_code == 503


def test_filings_returns_503_when_collection_load_fails():
    _install_failing_pymilvus()
    from api.routes import filings as filings_route
    filings_route._filings_collection = None

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(filings_route.get_filings(company_code=None, document_type=None, limit=100, offset=0))

    assert exc_info.value.status_code == 503
