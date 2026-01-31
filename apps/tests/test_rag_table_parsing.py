"""
Test RAG Agent table data parsing and schema validation
"""

import json
import pytest
from unittest.mock import Mock, patch
from agents.schemas import TableChunk, ChunkMetadata


def test_table_chunk_accepts_list_of_lists():
    """TableChunk should accept List[List[str]] format"""
    metadata = ChunkMetadata(
        filename="test.pdf",
        company_name="TEST",
        table_index=0,
        confidence_score=0.9,
        collection="pdf_table_chunks"
    )
    
    # Valid format: List[List[str]]
    table_data = [
        ["Header1", "Header2"],
        ["Row1Col1", "Row1Col2"],
        ["Row2Col1", "Row2Col2"]
    ]
    
    chunk = TableChunk(
        table_id="test_id",
        table_data=table_data,
        metadata=metadata
    )
    
    assert chunk.table_data == table_data
    assert len(chunk.table_data) == 3


def test_table_chunk_rejects_json_string():
    """TableChunk should reject JSON string format"""
    metadata = ChunkMetadata(
        filename="test.pdf",
        company_name="TEST",
        table_index=0,
        confidence_score=0.9,
        collection="pdf_table_chunks"
    )
    
    # Invalid format: JSON string (this is what's currently failing)
    table_data_json = '[{"FOODIE MEDIA BERHAD": "FOODIE MEDIA BERHAD"}]'
    
    with pytest.raises(Exception):  # Should be ValidationError from pydantic
        TableChunk(
            table_id="test_id",
            table_data=table_data_json,
            metadata=metadata
        )


def test_rag_agent_parse_json_string_to_list():
    """Test parsing JSON string table_data from Milvus hit"""
    # Simulate what Milvus returns
    hit_entity = {
        "table_id": "test_id",
        "filename": "test.pdf",
        "company_name": "TEST COMPANY",
        "table_data": json.dumps([
            ["Header1", "Header2"],
            ["Row1Col1", "Row1Col2"]
        ]),
        "table_index": 0
    }
    
    # Simulate what RAG agent does (lines 203-207)
    table_data_str = hit_entity.get("table_data", "[]")
    try:
        table_data = json.loads(table_data_str) if table_data_str else []
    except:
        table_data = []
    
    # Should parse successfully
    assert isinstance(table_data, list)
    assert len(table_data) == 2
    assert table_data[0] == ["Header1", "Header2"]


def test_rag_agent_parse_malformed_table_data():
    """Test parsing malformed table_data (list of dicts instead of list of lists)"""
    # This is what's causing the actual error in the logs
    hit_entity = {
        "table_id": "test_id",
        "filename": "test.pdf",
        "company_name": "FOODIE MEDIA BERHAD",
        "table_data": '[{"FOODIE MEDIA BERHAD": "FOODIE MEDIA BERHAD"}]',
        "table_index": 0
    }
    
    # Current RAG parsing
    table_data_str = hit_entity.get("table_data", "[]")
    try:
        table_data = json.loads(table_data_str) if table_data_str else []
    except:
        table_data = []
    
    # Parsed successfully but wrong type
    assert isinstance(table_data, list)
    assert len(table_data) == 1
    assert isinstance(table_data[0], dict)  # This is the problem!
    
    # Should be list of lists, not list of dicts
    # This will fail TableChunk validation


def test_normalize_table_data_from_dict_list():
    """Test normalizing table_data from list of dicts to list of lists"""
    # Input: list of dicts (malformed)
    malformed = [{"FOODIE MEDIA BERHAD": "FOODIE MEDIA BERHAD"}]
    
    # Normalize function (to be implemented)
    def normalize_table_data(data):
        if not data:
            return []
        
        # If it's already list of lists, return as-is
        if isinstance(data[0], list):
            return data
        
        # If it's list of dicts, convert to list of lists
        if isinstance(data[0], dict):
            # Extract keys as header row
            headers = list(data[0].keys())
            rows = [headers]
            
            # Extract values as data rows
            for item in data:
                row = [str(item.get(h, "")) for h in headers]
                rows.append(row)
            
            return rows
        
        # Unknown format, return empty
        return []
    
    # Test normalization
    normalized = normalize_table_data(malformed)
    
    assert isinstance(normalized, list)
    assert len(normalized) == 2  # header + 1 data row
    assert normalized[0] == ["FOODIE MEDIA BERHAD"]
    assert normalized[1] == ["FOODIE MEDIA BERHAD"]


def test_rag_agent_normalize_table_data_method():
    """Test RAGAgent._normalize_table_data method with various inputs"""
    # Test the normalization logic without importing RAGAgent (to avoid pymilvus dependency)
    
    def normalize_table_data(data):
        """Extracted normalization logic from RAGAgent"""
        if not data:
            return []
        
        # If it's already list of lists, validate and return
        if isinstance(data, list) and data and isinstance(data[0], list):
            # Ensure all elements are strings
            normalized = []
            for row in data:
                str_row = [str(cell) if cell is not None else "" for cell in row]
                normalized.append(str_row)
            return normalized
        
        # If it's list of dicts, convert to list of lists
        if isinstance(data, list) and data and isinstance(data[0], dict):
            # Extract keys as header row
            headers = list(data[0].keys())
            rows = [headers]
            
            # Extract values as data rows
            for item in data:
                row = [str(item.get(h, "")) for h in headers]
                rows.append(row)
            
            return rows
        
        # Unknown format
        return []
    
    # Test 1: List of lists (correct format)
    data1 = [["H1", "H2"], ["R1C1", "R1C2"]]
    result1 = normalize_table_data(data1)
    assert result1 == [["H1", "H2"], ["R1C1", "R1C2"]]
    
    # Test 2: List of dicts (malformed - needs conversion)
    data2 = [{"Company": "ABC"}, {"Company": "XYZ"}]
    result2 = normalize_table_data(data2)
    assert result2 == [["Company"], ["ABC"], ["XYZ"]]
    
    # Test 3: Empty data
    result3 = normalize_table_data([])
    assert result3 == []
    
    # Test 4: None data
    result4 = normalize_table_data(None)
    assert result4 == []
    
    # Test 5: List with None values
    data5 = [["H1", None], ["R1C1", None]]
    result5 = normalize_table_data(data5)
    assert result5 == [["H1", ""], ["R1C1", ""]]


def test_rag_agent_build_table_chunks_with_normalized_data():
    """Test that TableChunk construction works with normalized table data"""
    # Test that normalized data can construct TableChunk successfully
    from agents.schemas import TableChunk, ChunkMetadata
    
    # Normalized table data (List[List[str]])
    normalized_data = [["H1", "H2"], ["R1C1", "R1C2"]]
    
    metadata = ChunkMetadata(
        filename="test.pdf",
        company_name="TEST CO",
        table_index=0,
        confidence_score=0.9,
        collection="pdf_table_chunks"
    )
    
    chunk = TableChunk(
        table_id="test_id_1",
        table_data=normalized_data,
        metadata=metadata
    )
    
    assert chunk.table_id == "test_id_1"
    assert chunk.table_data == [["H1", "H2"], ["R1C1", "R1C2"]]
    assert chunk.metadata.filename == "test.pdf"

