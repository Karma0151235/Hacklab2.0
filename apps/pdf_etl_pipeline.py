#!/usr/bin/env python3
"""
PDF ETL Pipeline - Minimal, modular implementation
Parse → Chunk → Embed → Load to MilvusDB

Flow:
1. Extract text and tables from PDFs
2. Chunk text for embeddings
3. Generate embeddings using sentence-transformers
4. Insert text chunks into MilvusDB (pdf_text_chunks collection)
5. Insert table chunks into MilvusDB (pdf_table_chunks collection)

Metadata preserved per chunk:
- filename: Source PDF filename
- company_name: Company name extracted from content
- content: Text or table data
- embedding: Vector representation
- page_number: Source page (for text chunks)
- table_index: Table index (for table chunks)
- source: Always "pdf"
- doc_id: Document identifier
"""

import sys
from pathlib import Path
from datetime import datetime
import uuid
import re

sys.path.insert(0, str(Path(__file__).parent))

from etl.logging_config import get_logger
from etl.processing.pdf_extractor import PDFExtractor
from etl.chunking.chunker import TextChunker
from etl.embeddings.generator import EmbeddingGenerator
from etl.db.milvus_pdf_manager import MilvusPDFManager

logger = get_logger(__name__)


class PDFETLPipeline:
    """PDF to MilvusDB ETL Pipeline"""

    def __init__(self):
        """Initialize pipeline components"""
        self.pdf_dir = Path(__file__).parent / "storage" / "raw" / "pdfs"
        self.output_dir = Path(__file__).parent / "storage" / "processed" / "pdf_etl_output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Initializing PDF ETL Pipeline components...")

        self.pdf_extractor = PDFExtractor()
        self.text_chunker = TextChunker(chunk_size=500, overlap=50)
        self.embedding_generator = EmbeddingGenerator()
        self.milvus_manager = MilvusPDFManager()

        # Stats
        self.stats = {
            "pdfs_processed": 0,
            "text_chunks_loaded": 0,
            "table_chunks_loaded": 0,
            "total_embeddings": 0,
        }

    def run(self) -> bool:
        """Run the PDF ETL pipeline"""
        print("\n" + "="*80)
        print("PDF ETL PIPELINE - Parse → Chunk → Embed → Load to MilvusDB")
        print("="*80 + "\n")

        if not self.pdf_dir.exists():
            logger.error(f"PDF directory not found: {self.pdf_dir}")
            return False

        # Find PDF files
        pdf_files = sorted(self.pdf_dir.glob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files")

        if not pdf_files:
            logger.warning("No PDF files found")
            return False

        # Check MilvusDB connection
        logger.info("Checking MilvusDB connection...")
        if not self.milvus_manager.health_check():
            logger.error("MilvusDB health check failed")
            return False
        logger.info("MilvusDB is ready")

        # Process each PDF
        for idx, pdf_file in enumerate(pdf_files, 1):
            print(f"\n[{idx}/{len(pdf_files)}] Processing: {pdf_file.name}")
            self._process_pdf(pdf_file)

        # Print summary
        self._print_summary()

        return True

    def _process_pdf(self, pdf_path: Path) -> None:
        """Process a single PDF file"""
        try:
            # Step 1: Extract text and tables
            logger.info("Step 1: Extracting PDF content...")
            content = self.pdf_extractor.extract_from_file(pdf_path)

            if not content:
                logger.error("Failed to extract PDF content")
                return

            logger.info(f"  Extracted: {len(content.text_content)} chars, {len(content.tables)} tables")

            # Step 2: Extract company name
            company_name = self._extract_company_name(content.text_content, pdf_path.name)
            logger.info(f"  Company: {company_name}")

            # Generate document ID
            doc_id = f"pdf_{pdf_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

            # Step 3: Chunk text and generate embeddings
            logger.info("Step 2: Chunking text and generating embeddings...")
            text_chunks_data = self._chunk_and_embed_text(
                content.text_content,
                pdf_path.name,
                company_name,
                doc_id
            )
            logger.info(f"  Created {len(text_chunks_data)} text chunks with embeddings")

            # Step 4: Prepare table chunks
            logger.info("Step 3: Preparing table chunks...")
            table_chunks_data = self._prepare_table_chunks(
                content.tables,
                pdf_path.name,
                company_name,
                doc_id
            )
            logger.info(f"  Prepared {len(table_chunks_data)} table chunks")

            # Step 5: Load to MilvusDB
            logger.info("Step 4: Loading to MilvusDB...")

            if text_chunks_data:
                if self.milvus_manager.insert_text_chunks(text_chunks_data):
                    self.stats["text_chunks_loaded"] += len(text_chunks_data)
                    self.stats["total_embeddings"] += len(text_chunks_data)
                    logger.info(f"  ✓ Loaded {len(text_chunks_data)} text chunks")
                else:
                    logger.error("Failed to load text chunks")

            if table_chunks_data:
                if self.milvus_manager.insert_table_chunks(table_chunks_data):
                    self.stats["table_chunks_loaded"] += len(table_chunks_data)
                    logger.info(f"  ✓ Loaded {len(table_chunks_data)} table chunks")
                else:
                    logger.error("Failed to load table chunks")

            self.stats["pdfs_processed"] += 1

        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            import traceback
            traceback.print_exc()

    def _extract_company_name(self, text: str, filename: str) -> str:
        """
        Extract company name from PDF text or filename

        Args:
            text: PDF text content
            filename: PDF filename

        Returns:
            Company name
        """
        try:
            # Look for company name patterns in first 500 chars
            first_section = text[:500].upper()

            # Try to find company name in filename first
            # Remove common extensions and patterns
            name = filename.replace(".pdf", "").replace("_", " ")

            # Try to find "Company: XYZ" pattern
            match = re.search(r'(?:company|name)[\s:]+([A-Za-z0-9\s&.,]+)', text[:1000], re.IGNORECASE)
            if match:
                name = match.group(1).strip()[:255]

            return name if name else "Unknown Company"

        except Exception as e:
            logger.warning(f"Failed to extract company name: {str(e)}")
            return "Unknown Company"

    def _chunk_and_embed_text(
        self,
        text: str,
        filename: str,
        company_name: str,
        doc_id: str
    ) -> list:
        """
        Chunk text and generate embeddings

        Args:
            text: Full text content
            filename: Source filename
            company_name: Company name
            doc_id: Document ID

        Returns:
            List of chunk dicts with embeddings
        """
        try:
            # Chunk text
            chunks = self.text_chunker.chunk_text(
                text,
                filename=filename,
                company_name=company_name,
                doc_id=doc_id
            )

            if not chunks:
                logger.warning("No chunks created")
                return []

            # Extract content for embedding generation
            chunk_contents = [chunk.content for chunk in chunks]

            # Generate embeddings
            logger.info(f"  Generating embeddings for {len(chunk_contents)} chunks...")
            embeddings = self.embedding_generator.generate_batch(chunk_contents)

            if len(embeddings) != len(chunks):
                logger.error(f"Embedding count mismatch: {len(embeddings)} vs {len(chunks)}")
                return []

            # Prepare chunks data for MilvusDB
            chunks_data = []
            for chunk, embedding in zip(chunks, embeddings):
                chunk_dict = {
                    "chunk_id": chunk.chunk_id,
                    "filename": filename,
                    "company_name": company_name,
                    "content": chunk.content,
                    "embedding": embedding,
                    "page_number": chunk.page_number,
                    "source": "pdf",
                    "doc_id": doc_id,
                    "metadata": chunk.metadata,
                }
                chunks_data.append(chunk_dict)

            return chunks_data

        except Exception as e:
            logger.error(f"Failed to chunk and embed text: {str(e)}")
            return []

    def _prepare_table_chunks(
        self,
        tables: list,
        filename: str,
        company_name: str,
        doc_id: str
    ) -> list:
        """
        Prepare table chunks for MilvusDB and generate embeddings

        Args:
            tables: List of extracted tables
            filename: Source filename
            company_name: Company name
            doc_id: Document ID

        Returns:
            List of table chunk dicts with embeddings
        """
        try:
            if not tables:
                return []

            # Convert tables to text representation for embedding
            table_texts = []
            table_indices = []

            for table_idx, table in enumerate(tables):
                if not table:
                    continue

                # Convert table to readable text format
                table_text = self._table_to_text(table)
                table_texts.append(table_text)
                table_indices.append(table_idx)

            if not table_texts:
                return []

            # Generate embeddings for all tables
            logger.info(f"  Generating embeddings for {len(table_texts)} tables...")
            embeddings = self.embedding_generator.generate_batch(table_texts)

            if len(embeddings) != len(table_texts):
                logger.error(f"Embedding count mismatch: {len(embeddings)} vs {len(table_texts)}")
                return []

            # Prepare table chunks with embeddings
            table_chunks = []
            for table_idx, table_text, embedding in zip(table_indices, table_texts, embeddings):
                table = tables[table_idx]

                table_dict = {
                    "table_id": f"table_{doc_id}_{table_idx}_{uuid.uuid4().hex[:8]}",
                    "filename": filename,
                    "company_name": company_name,
                    "table_data": table,  # Keep original format
                    "table_index": table_idx,
                    "source": "pdf",
                    "doc_id": doc_id,
                    "embedding": embedding,
                    "metadata": {
                        "source": "pdf",
                        "chunk_type": "table",
                        "filename": filename,
                        "company_name": company_name,
                        "table_index": table_idx,
                    },
                }
                table_chunks.append(table_dict)

            return table_chunks

        except Exception as e:
            logger.error(f"Failed to prepare table chunks: {str(e)}")
            return []

    def _table_to_text(self, table: list) -> str:
        """
        Convert table (list of lists) to readable text for embedding

        Args:
            table: Table data as list of lists

        Returns:
            Text representation of table
        """
        try:
            if not table:
                return ""

            # Convert each row to comma-separated text
            text_lines = []
            for row in table:
                row_text = " | ".join(str(cell).strip() for cell in row if cell)
                if row_text:
                    text_lines.append(row_text)

            return "\n".join(text_lines)

        except Exception as e:
            logger.warning(f"Failed to convert table to text: {str(e)}")
            return ""

    def _print_summary(self) -> None:
        """Print processing summary"""
        print("\n" + "="*80)
        print("PIPELINE COMPLETE")
        print("="*80)
        print(f"PDFs processed:           {self.stats['pdfs_processed']}")
        print(f"Text chunks loaded:       {self.stats['text_chunks_loaded']}")
        print(f"Table chunks loaded:      {self.stats['table_chunks_loaded']}")
        print(f"Total embeddings:         {self.stats['total_embeddings']}")
        print("="*80 + "\n")

        logger.info("Pipeline execution completed")


if __name__ == "__main__":
    try:
        pipeline = PDFETLPipeline()
        success = pipeline.run()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"FATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
