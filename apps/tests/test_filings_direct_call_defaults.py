"""
Ensure get_filings works when called directly with no args.
"""
import asyncio
import sys
from pathlib import Path
import types

# Add apps directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_get_filings_direct_call_no_args(monkeypatch):
    fake_pymilvus = types.SimpleNamespace(
        connections=types.SimpleNamespace(connect=lambda *args, **kwargs: None, has_connection=lambda *_: True),
        Collection=lambda *args, **kwargs: types.SimpleNamespace(load=lambda: None, query=lambda **kw: []),
    )
    sys.modules["pymilvus"] = fake_pymilvus

    from api.routes import filings as filings_route
    filings_route._filings_collection = None

    result = asyncio.run(filings_route.get_filings())
    assert result.total == 0
