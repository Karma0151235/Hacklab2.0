"""
Workflows for Market Intelligence
"""

from typing import Any

__all__ = ["IntelligenceFlow", "run_intelligence_query"]


def __getattr__(name: str) -> Any:
    """
    Lazy attribute access to avoid importing heavy dependencies at package import time.
    """
    if name in ("IntelligenceFlow", "run_intelligence_query"):
        from .intelligence_flow import IntelligenceFlow, run_intelligence_query
        return IntelligenceFlow if name == "IntelligenceFlow" else run_intelligence_query
    raise AttributeError(f"module 'workflows' has no attribute '{name}'")
