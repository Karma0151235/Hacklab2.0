"""
Embedding generation for text chunks
"""

from typing import List
import os

from etl.logging_config import get_logger

logger = get_logger(__name__)


class EmbeddingGenerator:
    """Generate embeddings for text chunks"""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize embedding generator

        Args:
            model_name: HuggingFace model name for embeddings
        """
        self.model_name = model_name
        self.model = None
        self.embedding_dim = 384  # Default for all-MiniLM-L6-v2

        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {model_name}")
            self.model = SentenceTransformer(model_name)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            logger.info(f"Embedding dimension: {self.embedding_dim}")

        except ImportError:
            logger.error("sentence-transformers not installed. Install with: pip install sentence-transformers")
            raise

    def generate(self, text: str) -> List[float]:
        """
        Generate embedding for a single text

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        if not self.model:
            logger.error("Model not initialized")
            return []

        try:
            embedding = self.model.encode(text, convert_to_tensor=False)
            return embedding.tolist()

        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            return []

    def generate_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings for multiple texts

        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing

        Returns:
            List of embedding vectors
        """
        if not self.model:
            logger.error("Model not initialized")
            return []

        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=False,
                convert_to_tensor=False
            )
            return embeddings.tolist()

        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {str(e)}")
            return []
