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

        try:
            import tabula
            self.tabula = tabula
        except ImportError:
            logger.error("tabula-py not installed. Install with: pip install tabula-py")
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
        """Extract tables from PDF using tabula-py"""
        try:
            import pandas as pd

            # Try stream mode first (better for financial reports)
            dfs = self.tabula.read_pdf(
                str(pdf_path),
                pages="all",
                multiple_tables=True,
                stream=True
            )

            if not dfs:
                # Fallback to lattice mode
                dfs = self.tabula.read_pdf(
                    str(pdf_path),
                    pages="all",
                    multiple_tables=True,
                    lattice=True
                )

            tables = []
            for df in dfs:
                # Convert DataFrame to list of lists
                table = [df.columns.tolist()] + df.values.tolist()
                tables.append(table)

            return tables

        except Exception as e:
            logger.warning(f"Table extraction failed: {str(e)}")
            return []

    def _get_page_count(self, pdf_path: Path) -> int:
        """Get number of pages in PDF"""
        try:
            with self.pdfplumber.open(pdf_path) as pdf:
                return len(pdf.pages)
        except Exception:
            return 0
