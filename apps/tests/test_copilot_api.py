"""
Integration tests for Copilot API
"""
import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add apps directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.main import app
from agents.config import AgentConfig

client = TestClient(app)

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/api/v1/copilot/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "agents" in data
    assert "milvus" in data
    assert "openrouter" in data

def test_copilot_query_structure():
    """Test that query endpoint accepts correct structure"""
    # This just tests the validation, not the full execution
    response = client.post(
        "/api/v1/copilot/query",
        json={"query": "test query", "session_id": "test-session"}
    )
    # It might fail with 500 if dependencies aren't running, but 422 would mean schema error
    assert response.status_code != 422

@pytest.mark.skipif(not AgentConfig.OPENROUTER_API_KEY, reason="OpenRouter API key required")
def test_full_workflow_integration():
    """
    Test full workflow integration
    WARNING: This consumes API credits
    """
    response = client.post(
        "/api/v1/copilot/query",
        json={"query": "What exists in the database?"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert "answer" in data
    assert "agents_used" in data
    assert "citations" in data
    assert "steps" in data
    assert "confidence_score" in data
    
    # Verify supervisor is working
    assert len(data["steps"]) > 0
    assert isinstance(data["citations"], list)
