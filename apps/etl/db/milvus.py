"""
MilvusDB storage for vector embeddings
"""

import os
from typing import List, Dict, Any
from etl.logging_config import get_logger

logger = get_logger(__name__)


class MilvusStorage:
    """MilvusDB storage operations for embeddings - category-specific collections"""

    # Map document types to collection names
    COLLECTION_MAP = {
        "SHAREHOLDING_NOTICE": "shareholding_embeddings",
        "FINANCIAL_RESULTS": "financial_embeddings",
        "DIVIDEND_ANNOUNCEMENT": "dividend_embeddings",
        "CORPORATE_ACTION": "corporate_embeddings",
        "MEETING_NOTICE": "meeting_embeddings",
        "GENERAL_ANNOUNCEMENT": "general_embeddings",
    }

    def __init__(self, host: str = None, port: int = None):
        """
        Initialize MilvusDB connection

        Args:
            host: Milvus host (default from env)
            port: Milvus port (default from env)
        """
        self.host = host or os.getenv('MILVUS_HOST', 'localhost')
        self.port = port or int(os.getenv('MILVUS_PORT', '19530'))

        logger.info(f"Connecting to MilvusDB: {self.host}:{self.port}")

        try:
            # Import here to avoid hard dependency
            from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType

            self.connections = connections
            self.Collection = Collection
            self.FieldSchema = FieldSchema
            self.CollectionSchema = CollectionSchema
            self.DataType = DataType

            # Connect to Milvus
            self.connections.connect("default", host=self.host, port=self.port)
            logger.info("✅ MilvusDB connection initialized")
            self.connected = True

        except ImportError:
            logger.warning("pymilvus not installed. Set INSTALL_MILVUS=true to enable.")
            self.connected = False
        except Exception as e:
            logger.error(f"Failed to connect to MilvusDB: {str(e)}")
            self.connected = False

    def create_collections(self, dim: int = 1536):
        """
        Create all category-specific embeddings collections

        Creates collections for:
        - shareholding_embeddings
        - financial_embeddings
        - dividend_embeddings
        - corporate_embeddings
        - meeting_embeddings
        - general_embeddings

        Args:
            dim: Embedding dimension (1536 for OpenAI)
        """
        if not self.connected:
            logger.warning("MilvusDB not connected, skipping collection creation")
            return

        logger.info("Creating category-specific MilvusDB collections...")

        for doc_type, collection_name in self.COLLECTION_MAP.items():
            self._create_single_collection(collection_name, dim)

        logger.info(f"✅ All {len(self.COLLECTION_MAP)} collections created/verified")

    def _create_single_collection(self, collection_name: str, dim: int = 1536):
        """Create a single embeddings collection"""
        try:
            logger.debug(f"  └─ Creating collection: {collection_name}")

            # Define schema
            fields = [
                self.FieldSchema(name="chunk_id", dtype=self.DataType.VARCHAR, max_length=200, is_primary=True),
                self.FieldSchema(name="doc_id", dtype=self.DataType.VARCHAR, max_length=100),
                self.FieldSchema(name="embedding", dtype=self.DataType.FLOAT_VECTOR, dim=dim),
                self.FieldSchema(name="content", dtype=self.DataType.VARCHAR, max_length=10000),
                self.FieldSchema(name="chunk_order", dtype=self.DataType.INT32),
                self.FieldSchema(name="company_code", dtype=self.DataType.VARCHAR, max_length=10),
                self.FieldSchema(name="document_type", dtype=self.DataType.VARCHAR, max_length=50),
            ]

            schema = self.CollectionSchema(fields=fields, description=f"{collection_name} collection")

            # Create collection
            collection = self.Collection(name=collection_name, schema=schema)
            logger.debug(f"     └─ Created collection: {collection_name}")

            # Create index
            index_params = {
                "metric_type": "L2",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128}
            }
            collection.create_index(field_name="embedding", index_params=index_params)
            logger.debug(f"     └─ Created index on {collection_name}")

            return collection

        except Exception as e:
            if "already exists" in str(e).lower():
                logger.debug(f"Collection already exists: {collection_name}")
                return self.Collection(name=collection_name)
            else:
                logger.error(f"Failed to create collection {collection_name}: {str(e)}")
                return None

    def create_collection(self, collection_name: str = "document_embeddings", dim: int = 1536):
        """
        Deprecated: Use create_collections() instead.

        Kept for backward compatibility. Routes to _create_single_collection.
        """
        return self._create_single_collection(collection_name, dim)

    def insert_embeddings_by_type(self, document_type: str, embeddings_data: List[Dict[str, Any]]) -> int:
        """
        Insert embeddings into category-specific collection based on document_type

        Args:
            document_type: Type of document (SHAREHOLDING_NOTICE, FINANCIAL_RESULTS, etc.)
            embeddings_data: List of embedding dicts

        Returns:
            Number of embeddings inserted
        """
        # Route to appropriate collection
        collection_name = self.COLLECTION_MAP.get(document_type, self.COLLECTION_MAP["GENERAL_ANNOUNCEMENT"])
        return self.insert_embeddings(collection_name, embeddings_data)

    def insert_embeddings(self, collection_name: str, embeddings_data: List[Dict[str, Any]]) -> int:
        """
        Insert embeddings into collection

        Args:
            collection_name: Name of collection
            embeddings_data: List of embedding dicts with keys:
                - chunk_id
                - doc_id
                - embedding (list of floats)
                - content
                - chunk_order
                - company_code
                - document_type

        Returns:
            Number of embeddings inserted
        """
        if not self.connected:
            logger.warning("MilvusDB not connected, skipping insert")
            return 0

        try:
            logger.debug(f"  └─ Inserting {len(embeddings_data)} embeddings to {collection_name}")

            collection = self.Collection(name=collection_name)

            # Prepare data
            data_to_insert = [
                [item["chunk_id"] for item in embeddings_data],
                [item["doc_id"] for item in embeddings_data],
                [item["embedding"] for item in embeddings_data],
                [item["content"] for item in embeddings_data],
                [item["chunk_order"] for item in embeddings_data],
                [item["company_code"] for item in embeddings_data],
                [item["document_type"] for item in embeddings_data],
            ]

            # Insert
            mr = collection.insert(data_to_insert)
            logger.debug(f"     └─ Inserted {len(embeddings_data)} embeddings, IDs: {mr.primary_keys[:3]}...")

            # Flush
            collection.flush()
            logger.info(f"✅ Inserted {len(embeddings_data)} embeddings to {collection_name}")

            return len(embeddings_data)

        except Exception as e:
            logger.error(f"Failed to insert embeddings: {str(e)}")
            return 0

    def search_by_type(self, document_type: str, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search within category-specific collection based on document_type

        Args:
            document_type: Type of document (SHAREHOLDING_NOTICE, FINANCIAL_RESULTS, etc.)
            query_embedding: Query embedding vector
            top_k: Number of top results

        Returns:
            List of search results
        """
        # Route to appropriate collection
        collection_name = self.COLLECTION_MAP.get(document_type, self.COLLECTION_MAP["GENERAL_ANNOUNCEMENT"])
        return self.search(collection_name, query_embedding, top_k)

    def search(self, collection_name: str, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar embeddings

        Args:
            collection_name: Collection name
            query_embedding: Query embedding vector
            top_k: Number of top results

        Returns:
            List of search results
        """
        if not self.connected:
            logger.warning("MilvusDB not connected, skipping search")
            return []

        try:
            logger.debug(f"  └─ Searching in {collection_name} for top {top_k} similar documents")

            collection = self.Collection(name=collection_name)
            collection.load()  # Load collection into memory

            search_params = {
                "metric_type": "L2",
                "params": {"nprobe": 10}
            }

            results = collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["chunk_id", "doc_id", "content", "company_code", "document_type"]
            )

            search_results = []
            for hits in results:
                for hit in hits:
                    search_results.append({
                        "chunk_id": hit.entity.get("chunk_id"),
                        "doc_id": hit.entity.get("doc_id"),
                        "content": hit.entity.get("content"),
                        "company_code": hit.entity.get("company_code"),
                        "document_type": hit.entity.get("document_type"),
                        "distance": hit.distance,
                    })

            logger.debug(f"     └─ Found {len(search_results)} results")
            return search_results

        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return []

    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get collection statistics"""
        if not self.connected:
            return {}

        try:
            collection = self.Collection(name=collection_name)
            stats = {
                "num_entities": collection.num_entities,
                "collection_name": collection_name,
            }
            return stats
        except Exception as e:
            logger.warning(f"Failed to get collection stats: {str(e)}")
            return {}

    def health_check(self) -> bool:
        """Check MilvusDB connection"""
        if not self.connected:
            return False

        try:
            # Try a simple operation
            collections = self.connections.list_collections()
            logger.debug(f"MilvusDB health check OK, found {len(collections)} collections")
            return True
        except Exception as e:
            logger.error(f"MilvusDB health check failed: {str(e)}")
            return False
