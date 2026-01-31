"""
Ensure Milvus connection failures return 503.
"""
import asyncio
import sys
from pathlib import Path
import types

import pytest
from fastapi import HTTPException

# Add apps directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def _install_connect_failing_pymilvus():
    class DummyCollection:
        def __init__(self, name):
            raise RuntimeError("collection should not be created")

    sys.modules["pymilvus"] = types.SimpleNamespace(
        connections=types.SimpleNamespace(connect=lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("connect failed"))),
        Collection=DummyCollection,
    )


def test_companies_returns_503_when_milvus_connect_fails():
    _install_connect_failing_pymilvus()
    from api.routes import companies as companies_route
    companies_route._companies_collection = None

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(companies_route.get_companies())

    assert exc_info.value.status_code == 503
    assert "connect failed" in exc_info.value.detail


def test_filings_returns_503_when_milvus_connect_fails():
    _install_connect_failing_pymilvus()
    from api.routes import filings as filings_route
    filings_route._filings_collection = None

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(filings_route.get_filings(company_code=None, document_type=None, limit=100, offset=0))

    assert exc_info.value.status_code == 503
    assert "connect failed" in exc_info.value.detail
