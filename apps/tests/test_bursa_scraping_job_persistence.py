"""
Ensure scraping job storage persists between requests.
"""
import asyncio
import sys
from pathlib import Path

import types

import pytest

# Add apps directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_scraping_job_status_after_start(monkeypatch):
    from api.routes import bursa_scraping as route

    # Avoid actually starting threads/scraping
    class DummyThread:
        def __init__(self, *args, **kwargs):
            pass
        def start(self):
            return None

    import threading
    monkeypatch.setattr(threading, "Thread", DummyThread)
    monkeypatch.setattr(route, "run_scraping_task_sync", lambda *args, **kwargs: None)

    # Fake MilvusStorage to bypass health check
    fake_milvus_module = types.SimpleNamespace(
        MilvusStorage=lambda *args, **kwargs: types.SimpleNamespace(connected=True, health_check=lambda: True)
    )
    sys.modules["etl.db.milvus"] = fake_milvus_module

    request = route.BursaScrapingRequest(year=2025, max_announcements=5)
    response = asyncio.run(route.start_bursa_scraping(request))

    job_id = response.job_id
    status = asyncio.run(route.get_bursa_scraping_status(job_id))
    assert status.job_id == job_id
