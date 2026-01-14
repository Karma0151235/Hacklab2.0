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

    # GLM Models (ZhipuAI via OpenRouter)
    GLM_4_5_MODEL = "zhipuai/glm-4-plus"  # GLM-4 Plus (closest to GLM-4.5)
    GLM_4_7_MODEL = "zhipuai/glm-4"  # GLM-4 (stable version)

    # Milvus Configuration
    MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
    MILVUS_PORT = int(os.getenv("MILVUS_PORT", "19639"))

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

    @classmethod
    def validate(cls) -> bool:
        """Validate configuration"""
        if not cls.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")
        return True


# Validate on import
AgentConfig.validate()
