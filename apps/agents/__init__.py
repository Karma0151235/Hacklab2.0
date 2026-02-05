"""
Agents for Market Intelligence Hackathon MVP
"""

from typing import Any

__all__ = ["SupervisorAgent", "RAGAgent", "FinancialAgent", "AlertAgent", "SentimentAgent"]


def __getattr__(name: str) -> Any:
    """
    Lazy attribute access to avoid importing heavy dependencies at package import time.
    """
    if name == "SupervisorAgent":
        from .supervisor import SupervisorAgent
        return SupervisorAgent
    if name == "RAGAgent":
        from .rag_agent import RAGAgent
        return RAGAgent
    if name == "FinancialAgent":
        from .financial_agent import FinancialAgent
        return FinancialAgent
    if name == "AlertAgent":
        from .alert_agent import AlertAgent
        return AlertAgent
    if name == "SentimentAgent":
        from .sentiment_agent import SentimentAgent
        return SentimentAgent
    raise AttributeError(f"module 'agents' has no attribute '{name}'")

