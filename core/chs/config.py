"""CHS v2 Configuration - Environment variable loading and validation.

Loads configuration from environment variables with validation for:
- CHS_DB_PATH: Path to SQLite database
- EMBEDDING_MODEL: Name of embedding model
- EMBEDDING_DIMENSIONS: Dimension count for embeddings
- CHS_JSONL_DIR: Directory containing JSONL chat logs
"""

from __future__ import annotations

import os
from pathlib import Path


class Config:
    """Configuration class for CHS v2.

    Loads settings from environment variables with defaults and validation.
    All paths are normalized to Path objects.
    """

    DEFAULT_DB_PATH = Path("P:/.data/chat_history.db")
    DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"
    DEFAULT_EMBEDDING_DIMENSIONS = 768
    DEFAULT_JSONL_DIR = Path("P:\\\\\\__csf/logs/chats")

    def __init__(self) -> None:
        """Initialize configuration from environment variables."""
        db_path_env = os.getenv("CHS_DB_PATH")
        if db_path_env:
            self.db_path = Path(db_path_env)
        else:
            self.db_path = self.DEFAULT_DB_PATH
        self.embedding_model = os.getenv("EMBEDDING_MODEL", self.DEFAULT_EMBEDDING_MODEL)
        dim_env = os.getenv("EMBEDDING_DIMENSIONS")
        if dim_env is not None:
            try:
                self.embedding_dim = int(dim_env)
                if self.embedding_dim <= 0:
                    raise ValueError("EMBEDDING_DIMENSIONS must be a positive integer")
            except ValueError as e:
                if "positive integer" in str(e):
                    raise
                raise ValueError("EMBEDDING_DIMENSIONS must be a positive integer") from None
        else:
            self.embedding_dim = self.DEFAULT_EMBEDDING_DIMENSIONS
        jsonl_dir_env = os.getenv("CHS_JSONL_DIR")
        if jsonl_dir_env:
            self.jsonl_dir = Path(jsonl_dir_env)
            if not self.jsonl_dir.exists():
                raise ValueError(f"CHS_JSONL_DIR must exist: {self.jsonl_dir}")
        else:
            self.jsonl_dir = self.DEFAULT_JSONL_DIR


def get_chs_db_path() -> str:
    """Return the CHS database path as a string.

    Convenience wrapper for use by scripts that need CLI path resolution.
    """
    return str(Config().db_path)
