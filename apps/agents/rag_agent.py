"""
RAG Agent for Market Intelligence
Retrieves top K chunks from Milvus and applies Chain-of-Thought reasoning
"""

from typing import List, Dict, Any
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pymilvus import connections, Collection
import openai

from agents.schemas import (
    RAGQuery,
    RAGOutput,
    ChunkMetadata,
    TableChunk,
    TextChunk,
)
from agents.config import AgentConfig
from etl.embeddings.generator import EmbeddingGenerator
from etl.logging_config import get_logger

logger = get_logger(__name__)


class RAGAgent:
    """
    RAG Agent for retrieving and summarizing market intelligence from PDF chunks

    System Prompt:
    You are the RAG Agent for market intelligence.

    Retrieve top K chunks from Milvus:
    • pdf_text_chunks → k=2
    • pdf_table_chunks → k=1

    Use the retrieved context to summarize relevant information.
    Apply Chain-of-Thought reasoning to produce structured summaries for Supervisor.

    Do not fetch external data.
    """

    SYSTEM_PROMPT = """You are the RAG Agent for market intelligence.

Your role:
1. Analyze retrieved context from PDF documents (text and tables)
2. Extract relevant information for the user query
3. Apply Chain-of-Thought reasoning to connect information
4. Identify key entities (companies, dates, metrics, etc.)
5. Provide structured summaries

Do NOT make up information. Only use the provided context.
If information is insufficient, clearly state this."""

    def __init__(self):
        """Initialize RAG Agent with Milvus connection and embedding model"""
        self.config = AgentConfig
        self.embedding_generator = EmbeddingGenerator()

        # Connect to Milvus
        try:
            connections.connect(
                "default",
                host=self.config.MILVUS_HOST,
                port=self.config.MILVUS_PORT
            )
            self.text_collection = Collection(self.config.TEXT_COLLECTION)
            self.table_collection = Collection(self.config.TABLE_COLLECTION)

            # Load collections
            self.text_collection.load()
            self.table_collection.load()

            logger.info("RAG Agent initialized with Milvus connection")
        except Exception as e:
            logger.error(f"Failed to initialize RAG Agent: {str(e)}")
            raise

        # Initialize OpenRouter client
        self.client = openai.OpenAI(
            api_key=self.config.OPENROUTER_API_KEY,
            base_url=self.config.OPENROUTER_BASE_URL,
            timeout=self.config.OPENROUTER_TIMEOUT_SECONDS,
            max_retries=self.config.OPENROUTER_MAX_RETRIES,
        )

    def retrieve(self, query: RAGQuery) -> RAGOutput:
        """
        Retrieve top K chunks from Milvus and summarize

        Args:
            query: RAGQuery with search query and top_k parameters

        Returns:
            RAGOutput with summary, table chunks, entities, and metadata
        """
        try:
            logger.info(f"RAG Agent processing query: {query.query}")

            # Generate query embedding
            query_embedding = self.embedding_generator.generate(query.query)
            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return RAGOutput(
                    summary="Failed to generate query embedding",
                    table_chunks=[],
                    entities=[],
                    metadata=[]
                )

            # Retrieve text chunks
            text_results = self._search_text_chunks(query_embedding, query.top_k_text)

            # Retrieve table chunks
            table_results = self._search_table_chunks(query_embedding, query.top_k_table)

            # Combine context
            context = self._build_context(text_results, table_results)

            # Apply Chain-of-Thought reasoning to summarize
            summary, entities = self._summarize_with_cot(query.query, context)

            # Extract metadata
            metadata = self._extract_metadata(text_results, table_results)

            # Build table and text chunks
            table_chunks = self._build_table_chunks(table_results)
            text_chunks = self._build_text_chunks(text_results)

            output = RAGOutput(
                summary=summary,
                table_chunks=table_chunks,
                text_chunks=text_chunks,
                entities=entities,
                metadata=metadata
            )

            logger.info(f"RAG Agent completed: {len(metadata)} chunks retrieved")
            return output

        except Exception as e:
            logger.error(f"RAG Agent error: {str(e)}")
            return RAGOutput(
                summary=f"Error retrieving context: {str(e)}",
                table_chunks=[],
                entities=[],
                metadata=[]
            )

    def _search_text_chunks(self, query_embedding: List[float], top_k: int) -> List[Dict[str, Any]]:
        """Search text chunks in Milvus"""
        try:
            search_params = {"metric_type": "L2", "params": {"nprobe": 10}}

            # Use OLD schema fields: doc_id, company_code, document_type
            results = self.text_collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["chunk_id", "doc_id", "company_code", "content", "chunk_order", "document_type"]
            )

            chunks = []
            if results and len(results) > 0:
                for hit in results[0]:
                    # Map old schema fields to expected format
                    chunks.append({
                        "chunk_id": hit.entity.get("chunk_id"),
                        "filename": hit.entity.get("doc_id", "unknown"),  # Map doc_id -> filename
                        "company_name": hit.entity.get("company_code", "unknown"),  # Map company_code -> company_name
                        "content": hit.entity.get("content"),
                        "page_number": hit.entity.get("chunk_order", 0),  # Map chunk_order -> page_number
                        "distance": hit.distance,
                        "collection": "pdf_text_chunks"
                    })

            logger.info(f"Retrieved {len(chunks)} text chunks")
            return chunks

        except Exception as e:
            logger.error(f"Error searching text chunks: {str(e)}")
            return []

    def _search_table_chunks(self, query_embedding: List[float], top_k: int) -> List[Dict[str, Any]]:
        """Search table chunks in Milvus"""
        try:
            search_params = {"metric_type": "L2", "params": {"nprobe": 10}}

            # pdf_table_chunks uses NEW schema: table_id, filename, company_name, table_data, table_index
            results = self.table_collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["table_id", "filename", "company_name", "table_data", "table_index", "source"]
            )

            chunks = []
            if results and len(results) > 0:
                for hit in results[0]:
                    table_data_str = hit.entity.get("table_data", "[]")
                    try:
                        table_data = json.loads(table_data_str) if table_data_str else []
                        # Normalize table_data to List[List[str]] format
                        table_data = self._normalize_table_data(table_data)
                    except Exception as e:
                        logger.warning(f"Failed to parse table_data for {hit.entity.get('table_id')}: {str(e)}")
                        table_data = []

                    chunks.append({
                        "table_id": hit.entity.get("table_id"),
                        "filename": hit.entity.get("filename", "unknown"),
                        "company_name": hit.entity.get("company_name", "unknown"),
                        "table_data": table_data,
                        "table_index": hit.entity.get("table_index", 0),
                        "distance": hit.distance,
                        "collection": "pdf_table_chunks"
                    })

            logger.info(f"Retrieved {len(chunks)} table chunks")
            return chunks

        except Exception as e:
            logger.error(f"Error searching table chunks: {str(e)}")
            return []

    def _build_context(self, text_results: List[Dict], table_results: List[Dict]) -> str:
        """Build context string from retrieved chunks"""
        context_parts = []

        # Add text chunks
        for i, chunk in enumerate(text_results, 1):
            context_parts.append(f"[Text Chunk {i} - {chunk['filename']} - {chunk['company_name']}]")
            context_parts.append(chunk['content'])
            context_parts.append("")

        # Add table chunks
        for i, chunk in enumerate(table_results, 1):
            context_parts.append(f"[Table {i} - {chunk['filename']} - {chunk['company_name']}]")

            # Convert table to readable format
            table_text = self._table_to_text(chunk['table_data'])
            context_parts.append(table_text)
            context_parts.append("")

        return "\n".join(context_parts)

    def _table_to_text(self, table_data: List[List[str]]) -> str:
        """Convert table data to readable text"""
        if not table_data:
            return "[Empty table]"

        lines = []
        for row in table_data:
            row_text = " | ".join(str(cell) for cell in row if cell)
            if row_text:
                lines.append(row_text)

        return "\n".join(lines)

    def _normalize_table_data(self, data: Any) -> List[List[str]]:
        """
        Normalize table_data to List[List[str]] format
        
        Handles multiple formats:
        - List[List[str]]: Return as-is (correct format)
        - List[Dict]: Convert to list of lists (malformed but recoverable)
        - Empty/None: Return empty list
        
        Args:
            data: Raw table data from Milvus
            
        Returns:
            List[List[str]]: Normalized table data
        """
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
            logger.warning(f"Converting malformed table_data from list of dicts to list of lists")
            # Extract keys as header row
            headers = list(data[0].keys())
            rows = [headers]
            
            # Extract values as data rows
            for item in data:
                row = [str(item.get(h, "")) for h in headers]
                rows.append(row)
            
            return rows
        
        # Unknown format
        logger.error(f"Unknown table_data format: {type(data)}")
        return []

    def _summarize_with_cot(self, query: str, context: str) -> tuple[str, List[str]]:
        """Apply Chain-of-Thought reasoning to summarize context"""
        try:
            prompt = f"""Based on the following context from PDF documents, answer the user query using Chain-of-Thought reasoning.

Context:
{context}

User Query: {query}

Instructions:
1. Think step-by-step about what information is relevant
2. Extract key facts and figures
3. Identify important entities (companies, dates, metrics)
4. Provide a clear, evidence-based summary
5. List extracted entities separately

Format your response as:
REASONING:
[Your step-by-step thinking]

SUMMARY:
[Clear summary answering the query]

ENTITIES:
[Comma-separated list of key entities]"""

            response = self.client.chat.completions.create(
                model=self.config.GLM_4_5_MODEL,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config.TEMPERATURE,
                max_tokens=self.config.MAX_TOKENS
            )

            content = response.choices[0].message.content

            # Parse response
            summary = ""
            entities = []

            if "SUMMARY:" in content:
                summary_part = content.split("SUMMARY:")[1]
                if "ENTITIES:" in summary_part:
                    summary = summary_part.split("ENTITIES:")[0].strip()
                    entities_str = summary_part.split("ENTITIES:")[1].strip()
                    entities = [e.strip() for e in entities_str.split(",") if e.strip()]
                else:
                    summary = summary_part.strip()
            else:
                summary = content.strip()

            return summary, entities

        except Exception as e:
            logger.error(f"Error in CoT summarization: {str(e)}")
            return f"Error summarizing context: {str(e)}", []

    def _extract_metadata(self, text_results: List[Dict], table_results: List[Dict]) -> List[ChunkMetadata]:
        """Extract metadata from retrieved chunks"""
        metadata_list = []

        for chunk in text_results:
            metadata = ChunkMetadata(
                filename=chunk['filename'],
                company_name=chunk['company_name'],
                page_number=chunk.get('page_number'),
                confidence_score=1.0 / (1.0 + chunk['distance']),  # Convert distance to confidence
                collection=chunk['collection']
            )
            metadata_list.append(metadata)

        for chunk in table_results:
            metadata = ChunkMetadata(
                filename=chunk['filename'],
                company_name=chunk['company_name'],
                table_index=chunk.get('table_index'),
                confidence_score=1.0 / (1.0 + chunk['distance']),
                collection=chunk['collection']
            )
            metadata_list.append(metadata)

        return metadata_list

    def _build_table_chunks(self, table_results: List[Dict]) -> List[TableChunk]:
        """Build TableChunk objects from retrieved results"""
        table_chunks = []

        for chunk in table_results:
            metadata = ChunkMetadata(
                filename=chunk['filename'],
                company_name=chunk['company_name'],
                table_index=chunk.get('table_index'),
                confidence_score=1.0 / (1.0 + chunk['distance']),
                collection=chunk['collection']
            )

            table_chunk = TableChunk(
                table_id=chunk['table_id'],
                table_data=chunk['table_data'],
                metadata=metadata
            )
            table_chunks.append(table_chunk)

        return table_chunks

    def _build_text_chunks(self, text_results: List[Dict]) -> List[TextChunk]:
        """Build TextChunk objects from retrieved results"""
        text_chunks = []

        for chunk in text_results:
            text_chunks.append(TextChunk(
                chunk_id=chunk.get('chunk_id', ''),
                filename=chunk.get('filename', 'unknown'),
                company_name=chunk.get('company_name', 'unknown'),
                content=chunk.get('content', ''),
                page_number=chunk.get('page_number'),
                confidence_score=1.0 / (1.0 + chunk.get('distance', 0.0)),
                collection=chunk.get('collection', 'pdf_text_chunks')
            ))

        return text_chunks
