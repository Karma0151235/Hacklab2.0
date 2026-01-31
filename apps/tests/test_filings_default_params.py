"""
Ensure get_filings works with default parameters outside FastAPI.
"""
import asyncio
import sys
from pathlib import Path
import types

# Add apps directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_get_filings_default_params(monkeypatch):
    # Fake pymilvus module so import succeeds
    fake_pymilvus = types.SimpleNamespace(
        connections=types.SimpleNamespace(connect=lambda *args, **kwargs: None, has_connection=lambda *_: True),
        Collection=lambda *args, **kwargs: types.SimpleNamespace(load=lambda: None, query=lambda **kw: []),
    )
    sys.modules["pymilvus"] = fake_pymilvus

    from api.routes import filings as filings_route
    filings_route._filings_collection = None

    # Should not raise with defaults when called directly
    result = asyncio.run(filings_route.get_filings(company_code=None, document_type=None, limit=100, offset=0))
    assert result.total == 0
