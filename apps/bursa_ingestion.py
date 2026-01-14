#!/usr/bin/env python3
"""
Bursa Scraper Data Ingestion Module
Takes scraped document_objects and ingests them into MilvusDB

Flow:
1. Receive document_objects from scraper
2. Chunk raw_text using existing TextChunker
3. Generate embeddings using existing EmbeddingGenerator
4. Insert into appropriate Milvus collections based on document type
"""

import sys
import os
import json
from pathlib import Path
from typing import List, Dict, Any
import uuid

sys.path.insert(0, str(Path(__file__).parent))

from etl.logging_config import get_logger
from etl.chunking.chunker import TextChunker
from etl.embeddings.generator import EmbeddingGenerator
from etl.db.milvus import MilvusStorage
from scraping.common.schemas import DocumentObject

logger = get_logger(__name__)


class BursaIngestion:
    """Ingest scraped Bursa data into MilvusDB (pdf_text_chunks collection)"""
    
    def __init__(self):
        """Initialize ingestion components"""
        logger.info("Initializing Bursa Ingestion components...")
        
        # Get Milvus connection details from environment
        milvus_host = os.getenv('MILVUS_HOST', 'localhost')
        milvus_port = int(os.getenv('MILVUS_PORT', '19639'))
        
        self.text_chunker = TextChunker(chunk_size=500, overlap=50)
        self.embedding_generator = EmbeddingGenerator()
        
        # MilvusPDFManager now uses OLD schema compatible with RAG agent
        from etl.db.milvus_pdf_manager import MilvusPDFManager
        self.milvus_manager = MilvusPDFManager(host=milvus_host, port=milvus_port)
        
        # Stats
        self.stats = {
            "documents_processed": 0,
            "chunks_created": 0,
            "embeddings_generated": 0,
            "records_inserted": 0,
            "tables_inserted": 0,  # Track table chunks separately
        }
    
    def ingest_documents(self, document_objects: List[DocumentObject]) -> Dict[str, Any]:
        """
        Ingest scraped documents into MilvusDB
        
        Args:
            document_objects: List of DocumentObject from scraper
            
        Returns:
            Dict with ingestion stats and status
        """
        logger.info(f"Starting ingestion of {len(document_objects)} documents...")
        
        # Process each document
        for idx, doc_obj in enumerate(document_objects, 1):
            logger.info(f"[{idx}/{len(document_objects)}] Processing: {doc_obj.title[:50]}...")
            self._ingest_single_document(doc_obj)
        
        logger.info(f"Ingestion complete! Stats: {self.stats}")
        
        return {
            "status": "success",
            "message": f"Ingested {self.stats['documents_processed']} documents",
            "stats": self.stats
        }
    
    def _ingest_single_document(self, doc_obj: DocumentObject) -> None:
        """Ingest a single document (text + tables)"""
        try:
            # === TEXT CHUNKS ===
            chunks_data = self._chunk_and_embed_text(
                doc_obj.raw_text,
                doc_obj.doc_id,
                doc_obj.company_code or "UNKNOWN"
            )
            
            if chunks_data:
                # Insert into pdf_text_chunks collection
                if self.milvus_manager.insert_text_chunks(chunks_data):
                    inserted_count = len(chunks_data)
                    self.stats["chunks_created"] += inserted_count
                    self.stats["embeddings_generated"] += inserted_count
                    self.stats["records_inserted"] += inserted_count
                    logger.info(f"  ✓ Inserted {inserted_count} text chunks")
                else:
                    logger.error(f"  ✗ Failed to insert text chunks")
            else:
                logger.warning(f"  ⚠ No text chunks created")
            
            # === TABLE CHUNKS ===
            if doc_obj.tables and len(doc_obj.tables) > 0:
                tables_data = self._process_and_embed_tables(
                    doc_obj.tables,
                    doc_obj.doc_id,
                    doc_obj.company_code or "UNKNOWN"
                )
                
                if tables_data:
                    # Insert into pdf_table_chunks collection
                    if self.milvus_manager.insert_table_chunks(tables_data):
                        table_count = len(tables_data)
                        self.stats["tables_inserted"] += table_count
                        self.stats["embeddings_generated"] += table_count
                        logger.info(f"  ✓ Inserted {table_count} table chunks")
                    else:
                        logger.error(f"  ✗ Failed to insert table chunks")
                else:
                    logger.warning(f"  ⚠ No table chunks created")
            
            # Update document processed count
            self.stats["documents_processed"] += 1
                
        except Exception as e:
            logger.error(f"Error ingesting document {doc_obj.doc_id}: {str(e)}")
            import traceback
            traceback.print_exc()
    

    def _chunk_and_embed_text(
        self,
        text: str,
        doc_id: str,
        company_code: str
    ) -> List[Dict[str, Any]]:
        """
        Chunk text and generate embeddings for pdf_text_chunks collection
        
        Args:
            text: Raw text content
            doc_id: Document ID
            company_code: Company code
            
        Returns:
            List of chunk dicts ready for MilvusPDFManager.insert_text_chunks()
        """
        try:
            if not text or len(text.strip()) == 0:
                logger.warning(f"Empty text for {doc_id}")
                return []
            
            # Chunk text
            chunks = self.text_chunker.chunk_text(
                text,
                filename=f"{doc_id}.txt",
                company_name=company_code,
                doc_id=doc_id
            )
            
            if not chunks:
                logger.warning(f"No chunks created for {doc_id}")
                return []
            
            # Extract content for embedding generation
            chunk_contents = [chunk.content for chunk in chunks]
            
            # Generate embeddings
            logger.debug(f"  Generating embeddings for {len(chunk_contents)} chunks...")
            embeddings = self.embedding_generator.generate_batch(chunk_contents)
            
            if len(embeddings) != len(chunks):
                logger.error(f"Embedding count mismatch: {len(embeddings)} vs {len(chunks)}")
                return []
            
            # Prepare data using STANDARD field names
            # MilvusPDFManager.insert_text_chunks() will map these to old schema
            chunks_data = []
            for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_dict = {
                    "chunk_id": f"{doc_id}_chunk_{idx:04d}_{uuid.uuid4().hex[:8]}",
                    "filename": f"{doc_id}.txt",  # Will map to doc_id
                    "company_name": company_code or "UNKNOWN",  # Will map to company_code
                    "content": chunk.content,
                    "embedding": embedding,
                    "page_number": idx,  # Will map to chunk_order
                    "source": "bursa_scraper",  # Will map to document_type
                }
                chunks_data.append(chunk_dict)
            
            return chunks_data
            
        except Exception as e:
            logger.error(f"Failed to chunk and embed text: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def _process_and_embed_tables(
        self,
        tables: List[Dict[str, Any]],
        doc_id: str,
        company_code: str
    ) -> List[Dict[str, Any]]:
        """
        Process tables and generate embeddings for pdf_table_chunks collection
        
        Args:
            tables: List of table dicts from DocumentObject
            doc_id: Document ID
            company_code: Company code
            
        Returns:
            List of table dicts ready for MilvusPDFManager.insert_table_chunks()
        """
        try:
            if not tables or len(tables) == 0:
                logger.warning(f"No tables for {doc_id}")
                return []
            
            # Convert tables to text for embedding
            table_texts = []
            for table in tables:
                # Convert table to readable text
                table_text = self._table_to_text(table)
                table_texts.append(table_text)
            
            # Generate embeddings for all tables
            logger.debug(f"  Generating embeddings for {len(table_texts)} tables...")
            embeddings = self.embedding_generator.generate_batch(table_texts)
            
            if len(embeddings) != len(tables):
                logger.error(f"Embedding count mismatch: {len(embeddings)} vs {len(tables)}")
                return []
            
            # Prepare data for pdf_table_chunks collection
            tables_data = []
            for idx, (table, embedding) in enumerate(zip(tables, embeddings)):
                # Serialize table data
                import json
                table_data_json = json.dumps(table.get('rows', []))
                
                table_dict = {
                    "table_id": f"{doc_id}_table_{idx:04d}_{uuid.uuid4().hex[:8]}",
                    "filename": f"{doc_id}.txt",
                    "company_name": company_code,
                    "table_data": table_data_json,
                    "table_index": idx,
                    "source": "bursa_scraper",
                    "doc_id": doc_id,
                    "metadata": {"title": table.get('title', f"Table {idx+1}")},
                    "embedding": embedding,
                }
                tables_data.append(table_dict)
            
            return tables_data
            
        except Exception as e:
            logger.error(f"Failed to process tables: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def _table_to_text(self, table: Dict[str, Any]) -> str:
        """Convert table dict to readable text for embedding"""
        try:
            title = table.get('title', 'Table')
            rows = table.get('rows', [])
            
            # Build text representation
            lines = [f"Table: {title}"]
            
            for row in rows:
                if isinstance(row, dict):
                    # Key-value pairs
                    for key, value in row.items():
                        if value:
                            lines.append(f"{key}: {value}")
                elif isinstance(row, list):
                    # List of values
                    lines.append(" | ".join(str(v) for v in row if v))
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"Error converting table to text: {str(e)}")
            return "Table data unavailable"



def ingest_bursa_scraping_results(document_objects: List[DocumentObject]) -> Dict[str, Any]:
    """
    Convenience function to ingest Bursa scraping results
    
    Args:
        document_objects: List of DocumentObject from scraper
        
    Returns:
        Ingestion results
    """
    ingestion = BursaIngestion()
    return ingestion.ingest_documents(document_objects)


if __name__ == "__main__":
    # Test with sample data
    logger.info("Bursa Ingestion Module - Test Mode")
    logger.info("Use ingest_bursa_scraping_results() to ingest scraped data")
