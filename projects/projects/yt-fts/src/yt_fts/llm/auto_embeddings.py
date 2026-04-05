"""
Auto Embeddings Management

Provides automatic embedding generation and management for yt-fts.
Uses sentence-transformers for real semantic embeddings and FAISS for fast search.
"""
import logging
from typing import Any

from yt_fts.utils.config import get_db_path

logger = logging.getLogger(__name__)

class AutoEmbeddingsManager:
    """Auto-embeddings manager for yt-fts."""

    def __init__(self, db_path: str | None=None):
        """
        Initialize the AutoEmbeddingsManager.

        Args:
            db_path: Path to the database (optional, will use default if not provided)
        """
        self.db_path = db_path or get_db_path()
        self.logger = logging.getLogger(__name__)

    def ensure_embeddings_for_channel(self, channel_id: str, force_rebuild: bool=False, api_key: str="") -> bool:
        """
        Ensure embeddings exist for a channel.

        Args:
            channel_id: Channel ID to process
            force_rebuild: Force rebuilding existing embeddings
            api_key: API key (not used for local models, kept for compatibility)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            from .faiss_store import FaissVectorStore
            from .simple_embeddings import SemanticEmbeddingsHandler
            embeddings_handler = SemanticEmbeddingsHandler()
            vector_store = FaissVectorStore()
            status = embeddings_handler.get_embedding_status(channel_id, self.db_path)
            if status["complete"] and (not force_rebuild):
                if not vector_store.index_exists(channel_id):
                    vector_store.build_index(channel_id)
                self.logger.info("Embeddings already exist for channel %s", channel_id)
                return True
            self.logger.info("Generating embeddings for channel %s", channel_id)
            count = embeddings_handler.generate_and_store_embeddings(channel_id, self.db_path, show_progress=False)
            if count > 0 or status["complete"]:
                vector_store.build_index(channel_id)
                self.logger.info("Generated %s embeddings for channel %s", count, channel_id)
                return True
            return False
        except Exception as e:
            self.logger.exception("Error ensuring embeddings for channel %s: %s", channel_id, e)
            return False

    def ensure_embeddings_for_search(self, query: str, channel_id: str | None=None) -> bool:
        """
        Ensure embeddings are ready for search.

        Args:
            query: Search query (not used, kept for compatibility)
            channel_id: Optional channel ID

        Returns:
            bool: True if ready, False otherwise
        """
        if not channel_id:
            return False
        return self.ensure_embeddings_for_channel(channel_id)

    def get_embedding_status(self) -> dict[str, Any]:
        """
        Get current embedding status.

        Returns:
            Dict with embedding status information
        """
        from .faiss_store import FaissVectorStore
        from .simple_embeddings import SemanticEmbeddingsHandler
        handler = SemanticEmbeddingsHandler()
        FaissVectorStore()
        return {"model_name": handler.DEFAULT_MODEL, "embedding_dim": handler.EMBEDDING_DIM, "type": "sentence_transformers"}

def auto_ensure_embeddings_for_vsearch(channel_id: str, api_key: str="", force_rebuild: bool=False) -> bool:
    """
    Auto-ensure embeddings are ready for vector search.

    Args:
        channel_id: Channel ID to process
        api_key: API key (not used for local models, kept for compatibility)
        force_rebuild: Force rebuilding existing embeddings

    Returns:
        bool: True if ready, False otherwise
    """
    manager = AutoEmbeddingsManager()
    return manager.ensure_embeddings_for_channel(channel_id, force_rebuild, api_key)

def auto_ensure_embeddings_for_channel(channel_id: str, force_rebuild: bool=False) -> bool:
    """
    Auto-ensure embeddings exist for a channel.

    Args:
        channel_id: Channel ID to process
        force_rebuild: Force rebuilding existing embeddings

    Returns:
        bool: True if successful, False otherwise
    """
    manager = AutoEmbeddingsManager()
    return manager.ensure_embeddings_for_channel(channel_id, force_rebuild)
