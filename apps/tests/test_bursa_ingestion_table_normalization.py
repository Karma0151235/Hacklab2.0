"""
Test Bursa Ingestion table normalization
"""

import pytest


def test_normalize_table_rows_from_dict_list():
    """Test normalizing table rows from list of dicts to list of lists"""
    from bursa_ingestion import BursaIngestion
    
    # Create instance without calling __init__
    ingestion = BursaIngestion.__new__(BursaIngestion)
    
    # Test Case 1: List of dicts (from web scraper)
    rows_dict = [
        {"Company": "ABC Corp", "Revenue": "1000"},
        {"Company": "XYZ Ltd", "Revenue": "2000"}
    ]
    headers = ["Company", "Revenue"]
    
    normalized = ingestion._normalize_table_rows(rows_dict, headers)
    
    assert len(normalized) == 3  # header + 2 data rows
    assert normalized[0] == ["Company", "Revenue"]
    assert normalized[1] == ["ABC Corp", "1000"]
    assert normalized[2] == ["XYZ Ltd", "2000"]


def test_normalize_table_rows_from_list_list():
    """Test normalizing table rows that are already list of lists"""
    from bursa_ingestion import BursaIngestion
    
    # Create instance without calling __init__
    ingestion = BursaIngestion.__new__(BursaIngestion)
    
    # Test Case 2: List of lists (correct format)
    rows_list = [
        ["Company", "Revenue"],
        ["ABC Corp", "1000"],
        ["XYZ Ltd", "2000"]
    ]
    
    normalized = ingestion._normalize_table_rows(rows_list)
    
    assert len(normalized) == 3
    assert all(isinstance(row, list) for row in normalized)
    assert all(isinstance(cell, str) for row in normalized for cell in row)


def test_normalize_table_rows_without_headers():
    """Test normalizing dict rows without explicit headers"""
    from bursa_ingestion import BursaIngestion
    
    # Create instance without calling __init__
    ingestion = BursaIngestion.__new__(BursaIngestion)
    
    # List of dicts without headers (should extract from first row)
    rows_dict = [
        {"Stock Name": "MAYBANK", "Price": "10.50"},
        {"Stock Name": "CIMB", "Price": "5.25"}
    ]
    
    normalized = ingestion._normalize_table_rows(rows_dict)
    
    assert len(normalized) == 3
    assert len(normalized[0]) == 2  # Header row with 2 columns
    assert "Stock Name" in normalized[0]
    assert "Price" in normalized[0]


def test_normalize_table_rows_with_none_values():
    """Test normalizing rows with None values"""
    from bursa_ingestion import BursaIngestion
    
    # Create instance without calling __init__
    ingestion = BursaIngestion.__new__(BursaIngestion)
    
    rows_list = [
        ["Company", "Revenue"],
        ["ABC Corp", None],
        [None, "2000"]
    ]
    
    normalized = ingestion._normalize_table_rows(rows_list)
    
    assert len(normalized) == 3
    assert normalized[1] == ["ABC Corp", ""]
    assert normalized[2] == ["", "2000"]


def test_validate_table_data_valid():
    """Test validation of valid table data"""
    from bursa_ingestion import BursaIngestion
    
    # Create instance without calling __init__
    ingestion = BursaIngestion.__new__(BursaIngestion)
    
    valid_data = [
        ["Header1", "Header2"],
        ["Row1Col1", "Row1Col2"],
        ["Row2Col1", "Row2Col2"]
    ]
    
    assert ingestion._validate_table_data(valid_data, "test_doc", 0) == True


def test_validate_table_data_empty():
    """Test validation of empty table data"""
    from bursa_ingestion import BursaIngestion
    
    # Create instance without calling __init__
    ingestion = BursaIngestion.__new__(BursaIngestion)
    
    assert ingestion._validate_table_data([], "test_doc", 0) == False


def test_validate_table_data_invalid_format():
    """Test validation of invalid table data (not all rows are lists)"""
    from bursa_ingestion import BursaIngestion
    
    # Create instance without calling __init__
    ingestion = BursaIngestion.__new__(BursaIngestion)
    
    invalid_data = [
        ["Header1", "Header2"],
        {"key": "value"},  # Invalid: dict instead of list
        ["Row2Col1", "Row2Col2"]
    ]
    
    assert ingestion._validate_table_data(invalid_data, "test_doc", 0) == False


def test_validate_table_data_non_string_cells():
    """Test validation of table data with non-string cells"""
    from bursa_ingestion import BursaIngestion
    
    # Create instance without calling __init__
    ingestion = BursaIngestion.__new__(BursaIngestion)
    
    invalid_data = [
        ["Header1", "Header2"],
        ["Row1Col1", 123],  # Invalid: int instead of string
        ["Row2Col1", "Row2Col2"]
    ]
    
    assert ingestion._validate_table_data(invalid_data, "test_doc", 0) == False
