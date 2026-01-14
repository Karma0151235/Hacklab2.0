"""
MilvusDB collection manager for PDF text and table chunks
"""

import os
from typing import List, Dict, Any, Optional
import json

from etl.logging_config import get_logger

logger = get_logger(__name__)


class MilvusPDFManager:
    """Manage MilvusDB collections for PDF text and table chunks"""

    # Collection names
    TEXT_COLLECTION = "pdf_text_chunks"
    TABLE_COLLECTION = "pdf_table_chunks"

    def __init__(self, host: str = None, port: int = None):
        """
        Initialize Milvus connection

        Args:
            host: Milvus host (default from env)
            port: Milvus port (default from env)
        """
        self.host = host or os.getenv('MILVUS_HOST', 'localhost')
        self.port = port or int(os.getenv('MILVUS_PORT', '19639'))

        try:
            from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType

            self.connections = connections
            self.Collection = Collection
            self.FieldSchema = FieldSchema
            self.CollectionSchema = CollectionSchema
            self.DataType = DataType

            # Connect to Milvus
            self.connections.connect("default", host=self.host, port=self.port)
            logger.info(f"Connected to MilvusDB at {self.host}:{self.port}")

            # Create collections if they don't exist
            self._create_collections()

        except Exception as e:
            logger.error(f"Failed to initialize MilvusDB: {str(e)}")
            raise

    def _create_collections(self):
        """Create text and table chunk collections if they don't exist"""
        try:
            # Create text collection
            if not self._collection_exists(self.TEXT_COLLECTION):
                self._create_text_collection()
            else:
                logger.info(f"Text collection '{self.TEXT_COLLECTION}' already exists")

            # Create table collection
            if not self._collection_exists(self.TABLE_COLLECTION):
                self._create_table_collection()
            else:
                logger.info(f"Table collection '{self.TABLE_COLLECTION}' already exists")

        except Exception as e:
            logger.error(f"Failed to create collections: {str(e)}")
            raise

    def _collection_exists(self, collection_name: str) -> bool:
        """Check if collection exists"""
        try:
            from pymilvus import utility
            return utility.has_collection(collection_name)
        except Exception:
            return False

    def _create_text_collection(self):
        """Create collection for text chunks with embeddings - OLD SCHEMA"""
        try:
            # OLD SCHEMA - matches existing database that RAG agent queries
            fields = [
                self.FieldSchema(name="chunk_id", dtype=self.DataType.VARCHAR, max_length=200, is_primary=True),
                self.FieldSchema(name="doc_id", dtype=self.DataType.VARCHAR, max_length=100),
                self.FieldSchema(name="embedding", dtype=self.DataType.FLOAT_VECTOR, dim=384),
                self.FieldSchema(name="content", dtype=self.DataType.VARCHAR, max_length=10000),
                self.FieldSchema(name="chunk_order", dtype=self.DataType.INT32),
                self.FieldSchema(name="company_code", dtype=self.DataType.VARCHAR, max_length=10),
                self.FieldSchema(name="document_type", dtype=self.DataType.VARCHAR, max_length=50),
            ]

            schema = self.CollectionSchema(
                fields,
                description="PDF text chunks with embeddings (OLD SCHEMA)"
            )

            collection = self.Collection(self.TEXT_COLLECTION, schema=schema)
            logger.info(f"Created text collection: {self.TEXT_COLLECTION}")

            # Create index on embedding field
            index_params = {
                "metric_type": "L2",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128}
            }
            collection.create_index("embedding", index_params)
            logger.info("Created index on embedding field")

        except Exception as e:
            logger.error(f"Failed to create text collection: {str(e)}")
            raise

    def _create_table_collection(self):
        """Create collection for table chunks"""
        try:
            fields = [
                self.FieldSchema(name="table_id", dtype=self.DataType.VARCHAR, max_length=255, is_primary=True),
                self.FieldSchema(name="filename", dtype=self.DataType.VARCHAR, max_length=255),
                self.FieldSchema(name="company_name", dtype=self.DataType.VARCHAR, max_length=255),
                self.FieldSchema(name="table_data", dtype=self.DataType.VARCHAR, max_length=65535),
                self.FieldSchema(name="table_index", dtype=self.DataType.INT32),
                self.FieldSchema(name="source", dtype=self.DataType.VARCHAR, max_length=50),
                self.FieldSchema(name="doc_id", dtype=self.DataType.VARCHAR, max_length=255),
                self.FieldSchema(name="metadata_json", dtype=self.DataType.VARCHAR, max_length=2000),
                self.FieldSchema(name="embedding", dtype=self.DataType.FLOAT_VECTOR, dim=384),
            ]

            schema = self.CollectionSchema(
                fields,
                description="PDF table chunks with embeddings"
            )

            collection = self.Collection(self.TABLE_COLLECTION, schema=schema)
            logger.info(f"Created table collection: {self.TABLE_COLLECTION}")

            # Create index on embedding field
            index_params = {
                "metric_type": "L2",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128}
            }
            collection.create_index("embedding", index_params)
            logger.info("Created index on table embedding field")

        except Exception as e:
            logger.error(f"Failed to create table collection: {str(e)}")
            raise

    def insert_text_chunks(self, chunks_data: List[Dict[str, Any]]) -> bool:
        """
        Insert text chunks into collection
        Maps NEW field names to OLD schema for compatibility
        """
        if not chunks_data:
            return False

        entities = []
        for chunk in chunks_data:
            # Map new field names to old schema
            entities.append({
                "chunk_id": str(chunk.get("chunk_id", ""))[:200],
                "doc_id": chunk.get("filename", chunk.get("doc_id", "unknown"))[:100],  # filename → doc_id
                "embedding": chunk.get("embedding", []),
                "content": chunk.get("content", "")[:10000],
                "chunk_order": int(chunk.get("page_number", chunk.get("chunk_order", 0))),  # page_number → chunk_order
                "company_code": chunk.get("company_name", chunk.get("company_code", "UNKNOWN"))[:10],  # company_name → company_code
                "document_type": chunk.get("source", chunk.get("document_type", "pdf"))[:50],  # source → document_type
            })

        collection = self.Collection(self.TEXT_COLLECTION)
        collection.insert(entities)
        collection.flush()
        collection.load()

        return True


    def insert_table_chunks(self, tables: List[Dict[str, Any]]) -> bool:
        if not tables:
            return False

        rows = []
        for t in tables:
            table_id = t.get("table_id", "")
            if isinstance(table_id, list):
                table_id = json.dumps(table_id)

            rows.append({
                "table_id": table_id,
                "filename": t.get("filename", "")[:255],
                "company_name": t.get("company_name", "")[:255],
                "table_data": json.dumps(t.get("table_data", []))[:65535],
                "table_index": int(t.get("table_index", 0)),
                "source": t.get("source", "pdf"),
                "doc_id": t.get("doc_id", ""),
                "metadata_json": json.dumps(t.get("metadata", {})),
                "embedding": t.get("embedding", []),
            })

        col = self.Collection(self.TABLE_COLLECTION)
        col.insert(rows)
        col.flush()
        col.load()   # ✅

        return True


    def health_check(self) -> bool:
        """Check MilvusDB health"""
        try:
            from pymilvus import utility
            return utility.get_server_version() is not None
        except Exception as e:
            logger.error(f"MilvusDB health check failed: {str(e)}")
            return False
