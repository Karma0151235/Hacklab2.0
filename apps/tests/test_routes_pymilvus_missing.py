"""
Route behavior when pymilvus is unavailable.
"""
import asyncio
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

# Add apps directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def _skip_if_pymilvus_installed() -> None:
    try:
        import pymilvus  # noqa: F401
        pytest.skip("pymilvus installed; missing-module behavior not applicable")
    except ModuleNotFoundError:
        return


def test_get_companies_returns_503_when_pymilvus_missing():
    _skip_if_pymilvus_installed()

    from api.routes.companies import get_companies

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(get_companies())

    assert exc_info.value.status_code == 503


def test_get_filings_returns_503_when_pymilvus_missing():
    _skip_if_pymilvus_installed()

    from api.routes.filings import get_filings

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(get_filings())

    assert exc_info.value.status_code == 503
