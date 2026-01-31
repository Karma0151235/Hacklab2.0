"""
Test Supervisor orchestration early-exit optimization
"""

import pytest
from unittest.mock import Mock, MagicMock
from agents.schemas import RAGOutput, ChunkMetadata, TableChunk


def test_assess_rag_quality_no_chunks():
    """Test RAG quality assessment when no chunks are retrieved"""
    from agents.supervisor import SupervisorAgent
    
    # Create instance without calling __init__
    supervisor = SupervisorAgent.__new__(SupervisorAgent)
    
    # Mock RAG output with no metadata
    rag_output = RAGOutput(
        summary="Failed to find relevant documents",
        table_chunks=[],
        entities=[],
        metadata=[]
    )
    
    quality = supervisor._assess_rag_quality(rag_output)
    
    assert quality["skip_expensive_agents"] == True
    assert "No relevant documents" in quality["reason"]
    assert quality["confidence"] == 0.1


def test_assess_rag_quality_low_confidence():
    """Test RAG quality assessment with low confidence scores"""
    from agents.supervisor import SupervisorAgent
    
    supervisor = SupervisorAgent.__new__(SupervisorAgent)
    
    # Mock RAG output with low confidence metadata
    rag_output = RAGOutput(
        summary="Some text here",
        table_chunks=[],
        entities=[],
        metadata=[
            ChunkMetadata(
                filename="test.pdf",
                company_name="TEST",
                page_number=1,
                confidence_score=0.2,
                collection="pdf_text_chunks"
            ),
            ChunkMetadata(
                filename="test.pdf",
                company_name="TEST",
                page_number=2,
                confidence_score=0.25,
                collection="pdf_text_chunks"
            )
        ]
    )
    
    quality = supervisor._assess_rag_quality(rag_output)
    
    assert quality["skip_expensive_agents"] == True
    assert "Low relevance confidence" in quality["reason"]
    assert quality["confidence"] < 0.3


def test_assess_rag_quality_short_summary():
    """Test RAG quality assessment with insufficient content"""
    from agents.supervisor import SupervisorAgent
    
    supervisor = SupervisorAgent.__new__(SupervisorAgent)
    
    # Mock RAG output with short summary
    rag_output = RAGOutput(
        summary="Test",  # Too short
        table_chunks=[],
        entities=[],
        metadata=[
            ChunkMetadata(
                filename="test.pdf",
                company_name="TEST",
                page_number=1,
                confidence_score=0.8,
                collection="pdf_text_chunks"
            )
        ]
    )
    
    quality = supervisor._assess_rag_quality(rag_output)
    
    assert quality["skip_expensive_agents"] == True
    assert "Insufficient context" in quality["reason"]
    assert quality["confidence"] == 0.2


def test_assess_rag_quality_error_in_summary():
    """Test RAG quality assessment with error messages in summary"""
    from agents.supervisor import SupervisorAgent
    
    supervisor = SupervisorAgent.__new__(SupervisorAgent)
    
    # Mock RAG output with error message
    rag_output = RAGOutput(
        summary="Error retrieving context: unable to process the query properly",
        table_chunks=[],
        entities=[],
        metadata=[
            ChunkMetadata(
                filename="test.pdf",
                company_name="TEST",
                page_number=1,
                confidence_score=0.7,
                collection="pdf_text_chunks"
            )
        ]
    )
    
    quality = supervisor._assess_rag_quality(rag_output)
    
    assert quality["skip_expensive_agents"] == True
    assert "encountered errors" in quality["reason"]
    assert quality["confidence"] == 0.2


def test_assess_rag_quality_good():
    """Test RAG quality assessment with good results"""
    from agents.supervisor import SupervisorAgent
    
    supervisor = SupervisorAgent.__new__(SupervisorAgent)
    
    # Mock RAG output with good quality
    rag_output = RAGOutput(
        summary="This is a comprehensive summary of the financial data retrieved from the documents. It includes detailed information about the company's performance.",
        table_chunks=[],
        entities=["Company A", "Q4 2024"],
        metadata=[
            ChunkMetadata(
                filename="test.pdf",
                company_name="TEST",
                page_number=1,
                confidence_score=0.8,
                collection="pdf_text_chunks"
            ),
            ChunkMetadata(
                filename="test.pdf",
                company_name="TEST",
                page_number=2,
                confidence_score=0.75,
                collection="pdf_text_chunks"
            )
        ]
    )
    
    quality = supervisor._assess_rag_quality(rag_output)
    
    assert quality["skip_expensive_agents"] == False
    assert "High-quality" in quality["reason"]
    assert quality["confidence"] > 0.7


def test_synthesize_response_rag_only_empty():
    """Test RAG-only response synthesis with empty results"""
    from agents.supervisor import SupervisorAgent
    
    supervisor = SupervisorAgent.__new__(SupervisorAgent)
    
    rag_output = RAGOutput(
        summary="",
        table_chunks=[],
        entities=[],
        metadata=[]
    )
    
    rag_quality = {
        "skip_expensive_agents": True,
        "reason": "No relevant documents found",
        "confidence": 0.1
    }
    
    response = supervisor._synthesize_response_rag_only(
        "Test query",
        rag_output,
        rag_quality,
        []
    )
    
    assert "couldn't find relevant information" in response
    assert "No relevant documents found" in response


def test_synthesize_response_rag_only_with_context():
    """Test RAG-only response synthesis with some context"""
    from agents.supervisor import SupervisorAgent
    
    supervisor = SupervisorAgent.__new__(SupervisorAgent)
    
    rag_output = RAGOutput(
        summary="Some limited information about the company's financial performance was found.",
        table_chunks=[],
        entities=["Company A"],
        metadata=[
            ChunkMetadata(
                filename="test.pdf",
                company_name="TEST",
                page_number=1,
                confidence_score=0.25,
                collection="pdf_text_chunks"
            )
        ]
    )
    
    rag_quality = {
        "skip_expensive_agents": True,
        "reason": "Low relevance confidence (0.25)",
        "confidence": 0.25
    }
    
    response = supervisor._synthesize_response_rag_only(
        "Test query",
        rag_output,
        rag_quality,
        []
    )
    
    assert "limited context" in response.lower()
    assert rag_output.summary in response
    assert rag_quality["reason"] in response
    assert "Company A" in response
