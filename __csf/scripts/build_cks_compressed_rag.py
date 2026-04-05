#!/usr/bin/env python
"""Build CKS compressed FAISS index from SQLite database.

This script creates an IVF+PQ compressed index for memory-efficient
semantic search over CKS entries. The index provides 75% memory
reduction with 90-95% recall accuracy.

Usage:
    python -m scripts.build_cks_compressed_rag
    python -m scripts.build_cks_compressed_rag --entry-type pattern

The index is saved to P:/__csf/data/cks_compressed_rag.{index,json}
"""

import argparse
import logging
import sqlite3
import sys
from pathlib import Path

# Suppress faiss loader AVX-512 noise (AMD Ryzen doesn't support AVX-512)
logging.getLogger("faiss.loader").setLevel(logging.ERROR)

logger = logging.getLogger(__name__)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cks.memory_efficient_rag import CKSMemoryEfficientRAG


def get_database_path() -> Path:
    """Get path to CKS SQLite database."""
    return Path(__file__).parent.parent / "data" / "cks.db"


def get_index_path() -> Path:
    """Get path where compressed index should be saved.

    Note: CKS unified.py expects the index at .data/cks/memory_efficient_rag
    """
    # Create .data/cks directory (where CKS unified.py looks for the index)
    index_dir = Path(__file__).parent.parent / ".data" / "cks"
    return index_dir / "memory_efficient_rag"


def build_index(entry_type: str | None = None) -> bool:
    """Build compressed FAISS index from CKS database.

    Args:
        entry_type: Filter by entry type (None for all entries)

    Returns:
        True if successful, False otherwise
    """
    cks_db = get_database_path()
    index_path = get_index_path()

    if not cks_db.exists():
        logger.error(f"CKS database not found: {cks_db}")
        return False

    logger.info(f"Building CKS compressed index from {cks_db}")
    if entry_type:
        logger.info(f"Filtering by entry type: {entry_type}")

    try:
        conn = sqlite3.connect(str(cks_db))
        conn.row_factory = sqlite3.Row

        # Get entry count
        cursor = conn.cursor()
        if entry_type:
            cursor.execute(
                "SELECT COUNT(*) as count FROM entries WHERE type = ? AND embedding IS NOT NULL",
                (entry_type,)
            )
        else:
            cursor.execute(
                "SELECT COUNT(*) as count FROM entries WHERE embedding IS NOT NULL"
            )
        count = cursor.fetchone()["count"]
        logger.info(f"Found {count} entries with embeddings")

        # Build index
        rag = CKSMemoryEfficientRAG()
        if rag.build_from_sqlite(conn, entry_type=entry_type):
            # Save index
            index_path.parent.mkdir(parents=True, exist_ok=True)
            if rag.save(index_path):
                logger.info(f"✅ Index built and saved to {index_path}")

                # Show statistics
                stats = rag.get_statistics()
                logger.info(f"Statistics: {stats}")
                return True
            else:
                logger.error("Failed to save index")
                return False
        else:
            logger.error("Failed to build index")
            return False

    except Exception as e:
        logger.exception(f"Error building index: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )

    parser = argparse.ArgumentParser(
        description="Build CKS compressed FAISS index for memory-efficient semantic search"
    )
    parser.add_argument(
        "--entry-type",
        choices=["memory", "pattern", "code", "knowledge", "correction", "decision", "commitment", "insight", "learning"],
        help="Filter by entry type (default: all entries)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    success = build_index(entry_type=args.entry_type)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
