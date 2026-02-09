"""
Configuration for agents using OpenRouter API with GLM models
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from apps/.env
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class AgentConfig:
    """Configuration for all agents"""

    # OpenRouter API
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

    # Models via OpenRouter
    GLM_4_5_MODEL = "openai/gpt-oss-20b"  # GPT-OSS with reasoning support
    GLM_4_7_MODEL = "openai/gpt-oss-20b"  # Same model for consistency

    # OpenRouter client settings
    OPENROUTER_TIMEOUT_SECONDS = float(os.getenv("OPENROUTER_TIMEOUT_SECONDS", "30"))
    OPENROUTER_MAX_RETRIES = int(os.getenv("OPENROUTER_MAX_RETRIES", "2"))

    # Milvus Configuration
    _milvus_host = os.getenv("MILVUS_HOST")
    _milvus_port = os.getenv("MILVUS_PORT")
    MILVUS_HOST = _milvus_host if _milvus_host else "localhost"
    MILVUS_PORT = int(_milvus_port) if _milvus_port else 19639

    # Collection Names
    TEXT_COLLECTION = "pdf_text_chunks"
    TABLE_COLLECTION = "pdf_table_chunks"

    # Retrieval Parameters
    TOP_K_TEXT = 2
    TOP_K_TABLE = 1

    # Agent Parameters
    MAX_TOKENS = 4000
    TEMPERATURE = 0.1  # Low temperature for factual responses
    COT_ENABLED = True  # Chain-of-Thought reasoning

    # Alert Thresholds
    ALERT_CURRENT_RATIO_MIN = 1.0
    ALERT_DEBT_TO_EQUITY_MAX = 2.0
    ALERT_NET_PROFIT_MARGIN_MIN = 0.0
    ALERT_REVENUE_GROWTH_MIN = -10.0

    # Sentiment Agent Toggle
    USE_SENTIMENT_AGENT = os.getenv("USE_SENTIMENT_AGENT", "true").lower() == "true"

    @classmethod
    def validate(cls) -> bool:
        """Validate configuration"""
        if not cls.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")
        return True


# Validation is intentionally not executed on import to avoid
# crashing the API process when env vars are missing.
