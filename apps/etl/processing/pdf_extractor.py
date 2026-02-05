"""
PDF text and table extraction module
"""

from pathlib import Path
from typing import List, Optional, NamedTuple
from dataclasses import dataclass

from etl.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class PDFContent:
    """Extracted PDF content"""
    text_content: str
    tables: List[List[List[str]]]
    pages: int
    filename: str


class PDFExtractor:
    """Extract text and tables from PDF files"""

    def __init__(self):
        """Initialize PDF extractor with dependencies"""
        try:
            import pdfplumber
            self.pdfplumber = pdfplumber
        except ImportError:
            logger.error("pdfplumber not installed. Install with: pip install pdfplumber")
            raise

    def extract_from_file(self, pdf_path: Path) -> Optional[PDFContent]:
        """
        Extract text and tables from a PDF file

        Args:
            pdf_path: Path to PDF file

        Returns:
            PDFContent with text and tables, or None if extraction fails
        """
        try:
            logger.info(f"Extracting from: {pdf_path.name}")

            text_content = self._extract_text(pdf_path)
            tables = self._extract_tables(pdf_path)
            num_pages = self._get_page_count(pdf_path)

            logger.info(f"Extracted: {len(text_content)} chars, {len(tables)} tables from {num_pages} pages")

            return PDFContent(
                text_content=text_content,
                tables=tables,
                pages=num_pages,
                filename=pdf_path.name
            )

        except Exception as e:
            logger.error(f"Failed to extract PDF: {str(e)}")
            return None

    def _extract_text(self, pdf_path: Path) -> str:
        """Extract text from PDF using pdfplumber"""
        try:
            text_parts = []

            with self.pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(f"--- Page {page_num} ---\n{page_text}")

            return "\n".join(text_parts)

        except Exception as e:
            logger.warning(f"Text extraction failed: {str(e)}")
            return ""

    def _extract_tables(self, pdf_path: Path) -> List[List[List[str]]]:
        """Extract tables from PDF using pdfplumber (no Java dependency)"""
        try:
            tables = []

            with self.pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        # Extract tables from current page
                        page_tables = page.extract_tables()

                        if page_tables:
                            for table in page_tables:
                                # Convert table to list of lists with safe encoding
                                safe_table = []
                                for row in table:
                                    safe_row = [self._safe_str(cell) for cell in row]
                                    safe_table.append(safe_row)
                                tables.append(safe_table)

                    except Exception as e:
                        logger.debug(f"Failed to extract tables from page {page_num}: {str(e)}")
                        continue

            if not tables:
                logger.warning("No tables found in PDF")
                return []

            logger.debug(f"Extracted {len(tables)} tables using pdfplumber")
            return tables

        except Exception as e:
            logger.warning(f"Table extraction failed: {str(e)}")
            return []
    
    def _safe_str(self, value) -> str:
        """Safely convert a value to string, handling encoding issues"""
        # Handle None and NaN values
        if value is None:
            return ""
        
        # Check for NaN (float type)
        try:
            import math
            if isinstance(value, float) and math.isnan(value):
                return ""
        except (TypeError, ValueError):
            pass
        
        try:
            # Convert to string
            s = str(value)
            # Encode to UTF-8 and decode, replacing invalid characters
            return s.encode('utf-8', errors='replace').decode('utf-8')
        except Exception:
            # If all else fails, return empty string
            return ""

    def _get_page_count(self, pdf_path: Path) -> int:
        """Get number of pages in PDF"""
        try:
            with self.pdfplumber.open(pdf_path) as pdf:
                return len(pdf.pages)
        except Exception:
            return 0
