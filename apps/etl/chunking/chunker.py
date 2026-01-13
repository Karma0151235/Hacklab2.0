"""
Text chunking for embeddings
"""

from typing import List, Dict, Any
from dataclasses import dataclass
import uuid

from etl.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class TextChunk:
    """A chunk of text for embedding"""
    chunk_id: str
    content: str
    page_number: int
    metadata: Dict[str, Any]


class TextChunker:
    """Split text into chunks for embeddings"""

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        """
        Initialize text chunker

        Args:
            chunk_size: Number of characters per chunk
            overlap: Number of overlapping characters between chunks
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        logger.info(f"TextChunker initialized: chunk_size={chunk_size}, overlap={overlap}")

    def chunk_text(
        self,
        text: str,
        filename: str,
        company_name: str = None,
        doc_id: str = None
    ) -> List[TextChunk]:
        """
        Split text into overlapping chunks

        Args:
            text: Full text content
            filename: Source PDF filename
            company_name: Company name for metadata
            doc_id: Document ID for tracking

        Returns:
            List of TextChunk objects
        """
        chunks = []

        try:
            # Split by pages first
            pages = text.split("--- Page ")
            if pages and not pages[0].strip():
                pages = pages[1:]

            current_chunk_id = 0

            for page_idx, page_text in enumerate(pages, 1):
                # Remove page marker if present
                if page_text.startswith(" ---"):
                    page_text = page_text.split("---", 1)[1].strip()
                else:
                    page_text = page_text.strip()

                # Chunk the page
                page_chunks = self._chunk_page(
                    page_text,
                    page_number=page_idx,
                    filename=filename,
                    company_name=company_name,
                    doc_id=doc_id
                )

                for chunk in page_chunks:
                    chunk.chunk_id = f"chunk_{current_chunk_id:05d}_{uuid.uuid4().hex[:8]}"
                    current_chunk_id += 1

                chunks.extend(page_chunks)

            logger.info(f"Created {len(chunks)} text chunks from {filename}")
            return chunks

        except Exception as e:
            logger.error(f"Failed to chunk text: {str(e)}")
            return []

    def _chunk_page(
        self,
        page_text: str,
        page_number: int,
        filename: str,
        company_name: str,
        doc_id: str
    ) -> List[TextChunk]:
        """Chunk a single page of text"""
        chunks = []

        if len(page_text) <= self.chunk_size:
            chunk = TextChunk(
                chunk_id="",  # Will be set by caller
                content=page_text,
                page_number=page_number,
                metadata={
                    "filename": filename,
                    "company_name": company_name,
                    "doc_id": doc_id,
                    "chunk_type": "text",
                    "source": "pdf"
                }
            )
            chunks.append(chunk)
        else:
            # Create overlapping chunks
            start = 0
            while start < len(page_text):
                end = min(start + self.chunk_size, len(page_text))

                chunk_content = page_text[start:end].strip()
                if chunk_content:
                    chunk = TextChunk(
                        chunk_id="",  # Will be set by caller
                        content=chunk_content,
                        page_number=page_number,
                        metadata={
                            "filename": filename,
                            "company_name": company_name,
                            "doc_id": doc_id,
                            "chunk_type": "text",
                            "source": "pdf"
                        }
                    )
                    chunks.append(chunk)

                start += self.chunk_size - self.overlap

        return chunks
