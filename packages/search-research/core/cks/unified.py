"""Constitutional Knowledge System (CKS) - Unified Interface.

Single unified database for all knowledge storage:
- Memories (chat history, Q&A)
- Patterns (documentation, best practices)
- Code (snippets, examples)
- Knowledge (articles, references)

This is a NEW simplified CKS interface for the consolidated database.
The legacy CKS system remains in src/features/cks/core/ for backward compatibility.

Usage:
    from .unified import CKS

    cks = CKS()
    cks.ingest_memory("What is JWT?", "JWT is JSON Web Tokens...")
    cks.ingest_pattern("Dual Sink Logging", pattern_content)
    results = cks.search("logging")
    semantic_results = cks.search_semantic("authentication mechanisms")
"""

import json
import math
import os
import re
import sqlite3
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

# Phase 1 & 2 enhancement imports
try:
    from .commands.auto_learning_expander import AutoLearningQueryExpander
    from .hybrid_search_patch import patch_hybrid_search
    from .optimized_search import patch_optimized_search
    from .query_expansion import QueryExpander, expand_query_if_enabled
    from .reranking import (
        SearchResultsMerger,
        adaptive_fusion,
        calculate_temporal_boost,
        combsum_fusion,
        detect_query_type,
        maximal_marginal_relevance,
        reciprocal_rank_fusion,
        weighted_average_fusion,
    )
    from .spell_correction import QuerySpellCorrector

    PHASE1_AVAILABLE = True
    PHASE2_AVAILABLE = True
except ImportError:
    PHASE1_AVAILABLE = True
    PHASE2_AVAILABLE = False

# Lazy imports for sentence-transformers (only loaded when needed)
SENTENCE_TRANSFORMERS_AVAILABLE = True  # Assume available until proven otherwise

# Module-level cache for model (shared across CKS instances for performance)
_cached_model = None
_cached_np = None
_model_loading = False
_model_load_lock = threading.Lock()  # Thread-safe model loading

# Adaptive similarity thresholds based on query type
# Lowered thresholds based on empirical testing (max observed similarity ~0.47)
QUERY_TYPE_THRESHOLDS = {
    "technical": 0.20,  # Lowered - 0.35 was too high (max obs ~0.28)
    "balanced": 0.15,  # Lowered - 0.30 was too high
    "preference": 0.12,  # Lowered - 0.25 was too high
}

# Query type keyword detection
QUERY_TYPE_KEYWORDS = {
    "technical": [
        "code",
        "function",
        "class",
        "api",
        "implement",
        "debug",
        "error",
        "syntax",
        "compile",
        "test",
        "refactor",
    ],
    "preference": [
        "prefer",
        "like",
        "want",
        "should",
        "opinion",
        "think",
        "feel",
        "believe",
        "usually",
        "typically",
    ],
}

# Valid entry types for the CKS system
VALID_ENTRY_TYPES = [
    "memory",  # Generic memories (existing)
    "pattern",  # Repeating patterns (existing)
    "code",  # Code snippets (existing)
    "knowledge",  # Factual knowledge (existing)
    "correction",  # Mistakes and fixes (NEW)
    "decision",  # Choices made and why (NEW)
    "commitment",  # Promises/resolutions (NEW)
    "insight",  # Realizations and aha moments (NEW)
    "learning",  # Lessons learned (NEW)
    "task",  # Task entities for project context (Consolidation Phase 1)
    "checkpoint",  # Session checkpoint entities (Consolidation Phase 1)
    "blocker",  # Blocker entities (Consolidation Phase 1)
    "docs",  # Documentation files
]

# Query intent boosts for intelligent type-based routing
# Supports both singular and plural forms (e.g., decisions? matches "decision" and "decisions")
QUERY_INTENT_BOOSTS = {
    "decisions?|chose|choice|selected|picked|what.*did": ["memory", "decision"],
    "prefer|like|want|should": ["memory"],
    "mistakes?|wrong|error|fail|bug|issues?": ["pattern", "correction"],
    "problem|fix": ["pattern", "correction"],
    "pattern|habit|routine": ["pattern"],
    "learn|discover|realize|found|explain|concept": ["knowledge", "learning", "insight"],
    "commits?|promise|resolves?": ["commitment"],
    "code|function|class": ["code"],
}


class CKS:
    """Unified Constitutional Knowledge System.

    Single database, unified schema, simple interface.
    """

    def __init__(
        self,
        db_path: str | Path | None = None,
        enable_semantic: bool = True,
        enable_spell_correction: bool | None = None,
        enable_auto_learning: bool = True,
        auto_learning_threshold: float = 0.4,
        use_fp16: bool = True,
        use_scalar_quantization: bool = True,
    ) -> None:
        """Initialize CKS with specified database path.

        Args:
            db_path: Path to CKS database (default: __csf/data/cks.db)
            enable_semantic: Enable semantic search with embeddings (default: True)
            enable_spell_correction: Enable spell correction (default: env var or True).
                Set to False for hooks to avoid 12s vocabulary loading overhead.
            enable_auto_learning: Enable auto-learning of abbreviations from search results (default: True).
            auto_learning_threshold: Similarity threshold below which auto-learning triggers (default: 0.4).
                Lower values = more aggressive learning, higher = more conservative.
            use_fp16: Use FP16 half-precision for faster GPU embeddings (default: True).
            use_scalar_quantization: Use 8-bit scalar quantization for 75% storage reduction (default: True).

        """
        # Spell correction: check env var if not explicitly set
        # Hooks should set CKS_SPELL_CORRECTION_ENABLED=false to avoid 12s init
        if enable_spell_correction is None:
            import os

            enable_spell_correction = (
                os.environ.get(
                    "CKS_SPELL_CORRECTION_ENABLED",
                    "true",
                ).lower()
                == "true"
            )
        self.enable_spell_correction = enable_spell_correction
        self.enable_auto_learning = enable_auto_learning
        self.auto_learning_threshold = auto_learning_threshold
        self._auto_learning_expander = None

        if db_path is None:
            # Default to main __csf data directory (absolute path for consistency)
            db_path = Path("P:/__csf/data/cks.db")
        else:
            db_path = Path(db_path)

        # Ensure parent directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self.db_path = db_path
        self.conn = None
        self.enable_semantic = enable_semantic and SENTENCE_TRANSFORMERS_AVAILABLE
        self._model = None
        self._model_loaded = False  # Track if model has been loaded
        self.use_fp16 = use_fp16  # FP16 half-precision for faster GPU embeddings
        self.use_scalar_quantization = use_scalar_quantization  # 8-bit quantization for storage

        self._initialize_database()

        # Memory-efficient RAG (IVF+PQ compressed index for large knowledge bases)
        self.memory_efficient_rag = None
        self.enable_memory_efficient_rag = False

        # Check if memory-efficient RAG index exists and load it
        # unified.py is at src/csf/cks/, need to go up 4 levels to reach project root
        project_root = Path(__file__).parent.parent.parent.parent
        rag_index_path = project_root / ".data" / "cks" / "memory_efficient_rag.index"

        if rag_index_path.exists():
            try:
                from .memory_efficient_rag import CKSMemoryEfficientRAG

                self.memory_efficient_rag = CKSMemoryEfficientRAG()
                if self.memory_efficient_rag.load(rag_index_path.with_suffix("")):
                    self.enable_memory_efficient_rag = True
                    import logging

                    logging.getLogger(__name__).info(
                        f'Memory-efficient RAG loaded (IVF+PQ compressed, 75% memory reduction, '
                        f'{self.memory_efficient_rag.get_statistics()["total_entries"]} entries)',
                    )
                else:
                    logging.getLogger(__name__).warning("Failed to load memory-efficient RAG index")
            except Exception as e:
                import logging

                logging.getLogger(__name__).warning(f"Could not load memory-efficient RAG: {e}")
        else:
            import logging

            logging.getLogger(__name__).debug(
                "Memory-efficient RAG index not found (run build script to create)",
            )

        # NOTE: Model loading is now deferred to first search_semantic() call
        # This allows fast CKS initialization for hooks with timeout constraints

        # Query result cache (LRU with TTL) - 5-10x faster repeated queries
        self._query_cache: dict[str, tuple[list[dict], float]] = {}
        self._query_cache_max_size = 1000
        self._query_cache_ttl_seconds = 3600  # 1 hour

    def _cache_key(self, query: str, entry_type: str | None, limit: int) -> str:
        """Generate cache key from query parameters."""
        import hashlib

        key = f"{query}|{entry_type or 'all'}|{limit}"
        return hashlib.md5(key.encode()).hexdigest()

    def _get_cached_result(self, cache_key: str) -> list[dict] | None:
        """Get cached result if available and not expired."""
        if cache_key in self._query_cache:
            result, timestamp = self._query_cache[cache_key]
            import time

            if time.time() - timestamp < self._query_cache_ttl_seconds:
                return result
            # Expired - remove from cache
            del self._query_cache[cache_key]
        return None

    def _cache_result(self, cache_key: str, result: list[dict]) -> None:
        """Cache result with current timestamp."""
        import time

        self._query_cache[cache_key] = (result, time.time())

        # Prune cache if too large (remove oldest entries)
        while len(self._query_cache) >= self._query_cache_max_size:
            oldest_key = min(self._query_cache, key=lambda k: self._query_cache[k][1])
            del self._query_cache[oldest_key]

    def clear_query_cache(self) -> None:
        """Clear the query cache."""
        self._query_cache.clear()

    def get_cache_stats(self) -> dict[str, int | float]:
        """Get query cache statistics."""
        import time

        valid_entries = sum(
            1
            for _, ts in self._query_cache.values()
            if time.time() - ts < self._query_cache_ttl_seconds
        )
        return {
            "total_entries": len(self._query_cache),
            "valid_entries": valid_entries,
            "max_size": self._query_cache_max_size,
            "ttl_seconds": self._query_cache_ttl_seconds,
        }

    def _cache_and_return(
        self,
        results: list[dict],
        query: str,
        entry_type: str | None,
        limit: int,
        cacheable: bool,
    ) -> list[dict]:
        """Cache results if cacheable and return them."""
        if cacheable:
            cache_key = self._cache_key(query, entry_type, limit)
            self._cache_result(cache_key, results)
        return results

    def _initialize_embedding_model(self) -> None:
        """Initialize sentence transformer model for embeddings (lazy import with caching)."""
        if not self.enable_semantic:
            return

        # Use module-level cache if available
        global _cached_model, _cached_np, _model_loading, _model_load_lock

        if _cached_model is not None:
            # Use cached model (fast path - no lock needed for read)
            self._model = _cached_model
            self._np = _cached_np
            self._SentenceTransformer = type(_cached_model)
            return

        # Thread-safe: check flag before acquiring lock to avoid contention
        if _model_loading:
            # Another thread is loading, wait and return
            return

        # Acquire lock for thread-safe initialization
        with _model_load_lock:
            # Double-check after acquiring lock (another thread may have finished)
            if _cached_model is not None:
                self._model = _cached_model
                self._np = _cached_np
                self._SentenceTransformer = type(_cached_model)
                return

            try:
                _model_loading = True

                # Lazy imports - only load when semantic search is first used
                import numpy as np
                from sentence_transformers import SentenceTransformer

                # Store references for later use
                self._SentenceTransformer = SentenceTransformer
                self._np = np

                # Detect device and load model with FP16 support
                import torch

                device = "cpu"
                use_fp16 = self.use_fp16 if hasattr(self, "use_fp16") else True

                if torch.cuda.is_available():
                    device = "cuda"
                    # Check VRAM (require at least 2GB)
                    device_props = torch.cuda.get_device_properties(0)
                    if device_props.total_memory >= 2 * 1024**3:
                        import logging

                        logging.getLogger(__name__).info(
                            f"CKS: Using CUDA with {device_props.total_memory // 1024**3}GB VRAM",
                        )
                        if use_fp16:
                            logging.getLogger(__name__).info(
                                "CKS: FP16 enabled for 2-3x faster embeddings",
                            )
                    else:
                        device = "cpu"
                        use_fp16 = False

                # Load model with device
                if self._model is None:
                    # Use local cache to avoid HuggingFace network timeouts
                    cache_folder = Path.home() / ".cache" / "huggingface" / "hub"
                    logging.getLogger(__name__).info(
                        f"CKS: Using HuggingFace cache: {cache_folder}",
                    )
                    self._model = self._SentenceTransformer(
                        "all-MiniLM-L6-v2",
                        device="cpu",
                        cache_folder=str(cache_folder),
                    )

                    # Convert to FP16 if enabled and on CUDA
                    if use_fp16 and device == "cuda" and hasattr(self._model, "half"):
                        self._model = self._model.half()

                    # Cache for other instances
                    _cached_model = self._model
                    _cached_np = np
            except ImportError as e:
                print(f"⚠️ sentence-transformers not available: {e}")
                print("   Semantic search disabled, falling back to LIKE search")
                self.enable_semantic = False
            except Exception as e:
                print(f"⚠️ Failed to load embedding model: {e}")
                print("   Semantic search disabled, falling back to LIKE search")
                self.enable_semantic = False
            finally:
                _model_loading = False

    def _initialize_database(self) -> None:
        """Initialize database schema if it doesn't exist."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row

        cursor = self.conn.cursor()

        # Create unified entries table with embedding column, usage tracking, and source_chunk
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                title TEXT,
                content TEXT NOT NULL,
                metadata TEXT,
                embedding BLOB,
                source_chunk TEXT,
                usage_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                thumbs_up INTEGER DEFAULT 0,
                thumbs_down INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_type ON entries(type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_created ON entries(created_at DESC)")

        # Performance: Add indexes for ranking queries (2-5x faster ranked results)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_count ON entries(usage_count DESC)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_success_count ON entries(success_count DESC)",
        )

        # Temporal query performance: Add index on created_at for time-based queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_on_entries ON entries(created_at)")

        # Add source_chunk column to existing databases (migration for backward compatibility)
        try:
            cursor.execute("SELECT source_chunk FROM entries LIMIT 1")
        except sqlite3.OperationalError:
            # Column doesn't exist, add it to existing databases
            cursor.execute("ALTER TABLE entries ADD COLUMN source_chunk TEXT")
            print("[CKS] Added source_chunk column to existing database")

        # Add thumbs_up and thumbs_down columns to existing databases (Enhancement 5)
        try:
            cursor.execute("SELECT thumbs_up FROM entries LIMIT 1")
        except sqlite3.OperationalError:
            # Column doesn't exist, add it to existing databases
            cursor.execute("ALTER TABLE entries ADD COLUMN thumbs_up INTEGER DEFAULT 0")
            cursor.execute("ALTER TABLE entries ADD COLUMN thumbs_down INTEGER DEFAULT 0")
            print("[CKS] Added thumbs_up and thumbs_down columns to existing database")

        # ========================================================================
        # Consolidation Phase 1: Entity Relationships Tables
        # ========================================================================

        # Create entry_entities table for entity metadata (from Project Context CKS)
        # This allows entries to have entity-specific attributes beyond standard metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entry_entities (
                entry_id TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (entry_id, entity_type),
                FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE
            )
        """)

        # Create entity_relationships table for hyper-graph relationships
        # Preserves the relationship semantics from csf.cksHyperGraphClient
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entity_relationships (
                from_entry_id TEXT NOT NULL,
                to_entry_id TEXT NOT NULL,
                relationship_type TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (from_entry_id, to_entry_id, relationship_type),
                FOREIGN KEY (from_entry_id) REFERENCES entries(id) ON DELETE CASCADE,
                FOREIGN KEY (to_entry_id) REFERENCES entries(id) ON DELETE CASCADE
            )
        """)

        # Migration for entry_entities table - check schema and update if needed
        # Old schema: (entry_id, entity_slug, linked_at)
        # New schema: (entry_id, entity_type, entity_data, created_at, updated_at)
        try:
            cursor.execute("SELECT entity_type FROM entry_entities LIMIT 1")
        except sqlite3.OperationalError:
            # Old schema detected, need to migrate
            print("[CKS] Migrating entry_entities table to new schema...")
            cursor.execute("ALTER TABLE entry_entities RENAME TO entry_entities_old")
            cursor.execute("""
                CREATE TABLE entry_entities (
                    entry_id TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (entry_id, entity_type),
                    FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE
                )
            """)
            # Migrate old data if any
            cursor.execute("""
                INSERT INTO entry_entities (entry_id, entity_type, entity_data, created_at)
                SELECT entry_id, entity_slug, NULL, linked_at FROM entry_entities_old
            """)
            cursor.execute("DROP TABLE entry_entities_old")
            print("[CKS] entry_entities table migrated")

        # Create indexes for relationship queries
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_entry_entities_type ON entry_entities(entity_type)",
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_entity_relationships_from ON entity_relationships(from_entry_id)",
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_entity_relationships_to ON entity_relationships(to_entry_id)",
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_entity_relationships_type ON entity_relationships(relationship_type)",
        )

        self.conn.commit()

    # ========================================================================
    # Embedding Helpers
    # ========================================================================

    def _generate_embedding(self, text: str) -> bytes | None:
        """Generate embedding for text using sentence transformer.

        Args:
            text: Text to embed

        Returns:
            Embedding as bytes (numpy array serialized) or None if disabled

        Note:
            If enable_semantic=True but model not loaded, will load model automatically
            to ensure embeddings are generated during ingest operations.

        """
        if not self.enable_semantic:
            return None

        # Auto-load model if not loaded yet (ensures embeddings work during ingest)
        if not self._model:
            self._initialize_embedding_model()
            if not self._model:
                # Model still not available after initialization attempt
                import logging

                logging.getLogger(__name__).warning(
                    "Embedding model not available - storing entry without semantic embedding",
                )
                return None

        try:
            # Generate embedding
            embedding = self._model.encode(text, show_progress_bar=False)

            # Ensure float32 for consistent storage (FP16 model returns float16)
            # This prevents dimension mismatch when deserializing
            if embedding.dtype != self._np.float32:
                embedding = embedding.astype(self._np.float32)

            # Apply scalar quantization if enabled (8-bit for 75% storage reduction)
            if self.use_scalar_quantization:
                # Normalize to [-1, 1] range for cosine similarity
                norm = self._np.linalg.norm(embedding)
                if norm > 0:
                    embedding = embedding / norm

                # Quantize to uint8: map [-1, 1] to [0, 255]
                # Formula: uint8 = (float32 + 1) * 127.5, then clip and cast
                quantized = self._np.clip((embedding + 1.0) * 127.5, 0, 255).astype(self._np.uint8)
                # Add marker byte to indicate quantized format (0xFF for uint8)
                return self._np.append(
                    self._np.array([0xFF], dtype=self._np.uint8), quantized,
                ).tobytes()
            # Serialize to bytes for SQLite storage (float32)
            return embedding.tobytes()
        except Exception as e:
            import logging

            logging.getLogger(__name__).warning(f"Embedding generation failed: {e}")
            return None

    def _deserialize_embedding(self, blob: bytes) -> Optional["np.ndarray"]:
        """Deserialize embedding from bytes.

        Handles both float32 and scalar-quantized uint8 formats.

        Quantized format: 385 bytes (1 marker byte + 384 uint8 values)
        Float32 format: 1536 bytes (384 * 4 bytes)

        Args:
            blob: Serialized embedding bytes

        Returns:
            NumPy array or None if numpy unavailable

        """
        if not hasattr(self, "_np") or blob is None:
            return None

        try:
            # Detect format by size and marker
            # Quantized: 385 bytes with 0xFF marker
            # Float32: 1536 bytes (or multiple of 384 * 4)
            if len(blob) == 385 and blob[0] == 255:
                # Dequantize uint8 back to float32 (skip marker byte)
                uint8_data = self._np.frombuffer(blob[1:], dtype=self._np.uint8)
                # Reverse the quantization: float32 = (uint8 / 127.5) - 1
                return (uint8_data.astype(self._np.float32) / 127.5) - 1.0
            # Float32 format (with or without accidental marker byte)
            # Remove accidental marker byte if present
            if len(blob) == 1537 and blob[0] == 255:
                blob = blob[1:]
            return self._np.frombuffer(blob, dtype=self._np.float32)
        except Exception:
            return None

    def _cosine_similarity(self, vec1: "np.ndarray", vec2: "np.ndarray") -> float:
        """Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Similarity score (-1 to 1, higher = more similar)

        """
        if not hasattr(self, "_np") or vec1 is None or vec2 is None:
            return 0.0

        try:
            dot_product = self._np.dot(vec1, vec2)
            norm1 = self._np.linalg.norm(vec1)
            norm2 = self._np.linalg.norm(vec2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            return dot_product / (norm1 * norm2)
        except Exception:
            return 0.0

    def _get_embedding(self, text: str) -> Optional["np.ndarray"]:
        """Generate and return embedding for text as numpy array.

        This is a convenience method that combines _generate_embedding
        and _deserialize_embedding for direct use in similarity calculations.

        Args:
            text: Text to embed

        Returns:
            NumPy array embedding or None if disabled

        """
        if not self.enable_semantic or not self._model:
            return None

        try:
            # Generate embedding
            return self._model.encode(text, show_progress_bar=False)
        except Exception as e:
            print(f"⚠️ Embedding generation failed: {e}")
            return None

    def _detect_intent_boost(self, query: str, entry_type: str) -> float:
        """Detect intent keywords and return boost multiplier.

        Args:
            query: Search query text
            entry_type: Type of entry being evaluated

        Returns:
            Boost multiplier (1.15 for +15% boost, 1.0 for no boost)

        """
        query_lower = query.lower()

        for keywords, types_to_boost in QUERY_INTENT_BOOSTS.items():
            if entry_type in types_to_boost:
                # Check if any keyword matches using word boundaries
                if re.search(r"\b(" + keywords + r")\b", query_lower):
                    return 1.15  # +15% boost

        return 1.0  # No boost

    def detect_intent(self, query: str) -> str:
        """Detect the primary intent type from a query.

        Analyzes the query to determine what type of content the user
        is looking for (code, pattern, knowledge, etc.).

        Args:
            query: Search query text

        Returns:
            Intent type: "code", "pattern", "knowledge", "correction",
            "decision", "commitment", "task", "checkpoint", or "general"

        """
        query_lower = query.lower()

        # Check each intent category in priority order
        # Use simple keyword matching instead of complex regex for reliability
        if "implement" in query_lower or "code" in query_lower or "function" in query_lower:
            return "code"
        if (
            "fix" in query_lower
            or "bug" in query_lower
            or "error" in query_lower
            or "debug" in query_lower
        ):
            return "correction"
        if (
            "pattern" in query_lower
            or "habit" in query_lower
            or "routine" in query_lower
            or "mistake" in query_lower
        ):
            return "pattern"
        if (
            "learn" in query_lower
            or "explain" in query_lower
            or "understand" in query_lower
            or "concept" in query_lower
        ):
            return "knowledge"
        if (
            "decid" in query_lower
            or "choice" in query_lower
            or "chose" in query_lower
            or "select" in query_lower
        ):
            return "decision"
        if "commi" in query_lower or "promise" in query_lower or "pledge" in query_lower:
            return "commitment"
        if (
            "task" in query_lower
            or "todo" in query_lower
            or "progress" in query_lower
            or "status" in query_lower
        ):
            return "task"
        if (
            "checkpoint" in query_lower
            or "snapshot" in query_lower
            or ("where" in query_lower and "we" in query_lower)
        ):
            return "checkpoint"

        return "general"

    def get_all_intents(self) -> list[str]:
        """Return list of all available intent types.

        Returns:
            List of intent type names

        """
        return [
            "code",
            "pattern",
            "knowledge",
            "correction",
            "decision",
            "commitment",
            "task",
            "checkpoint",
            "general",
        ]

    def _detect_query_type(self, query: str) -> str:
        """Detect query type based on keywords.

        Args:
            query: Query text to analyze

        Returns:
            Query type: "technical", "balanced", or "preference"

        """
        query_lower = query.lower()

        # Check for technical keywords
        if any(kw in query_lower for kw in QUERY_TYPE_KEYWORDS["technical"]):
            return "technical"

        # Check for preference keywords
        if any(kw in query_lower for kw in QUERY_TYPE_KEYWORDS["preference"]):
            return "preference"

        # Default to balanced
        return "balanced"

    def _get_adaptive_threshold(
        self,
        query_type: str,
        result_count: int,
        min_threshold: float = 0.20,
    ) -> float:
        """Get adaptive threshold based on result count.

        Priority 2: Lowers threshold when result count is low to improve recall.
        Helps find relevant results that have lower similarity scores.

        Args:
            query_type: The query type ("technical", "balanced", "preference")
            result_count: Number of results found so far
            min_threshold: Minimum threshold to use (default 0.20)

        Returns:
            Adaptive threshold value

        """
        # Get default threshold for query type
        default_threshold = QUERY_TYPE_THRESHOLDS.get(query_type, 0.30)

        # If we have good results, use default
        if result_count >= 3:
            return default_threshold

        # If we have some results, lower threshold slightly
        if result_count >= 1:
            return max(default_threshold * 0.85, min_threshold)

        # If no results, use minimum threshold to maximize recall
        return min_threshold

    # ========================================================================
    # Phase 2 Smart Defaults Helpers
    # ========================================================================

    # Lazy-loaded spell corrector instance
    _spell_corrector = None

    # Common abbreviations that benefit from query expansion
    _ABBREVIATIONS = {
        "db",
        "cks",
        "api",
        "sql",
        "jwt",
        "oauth",
        "http",
        "https",
        "tls",
        "ssl",
        "tcp",
        "udp",
        "dns",
        "cdn",
        "aws",
        "gcp",
        "azure",
        "json",
        "xml",
        "yaml",
        "csv",
        "nosql",
        "auth",
        "config",
        "env",
        "dev",
        "prod",
        "staging",
        "test",
        "ui",
        "ux",
        "rest",
        "graphql",
        "grpc",
        "cli",
        "gui",
        "ide",
        "sdk",
        "dll",
        "so",
        "async",
        "sync",
        "req",
        "resp",
        "err",
        "msg",
    }

    # Common typo patterns for quick detection
    _TYPO_PATTERNS = [
        r"ie$",  # recieve, recieved (should be receive, received)
        r"aaa+",
        r"eee+",
        r"iii+",
        r"ooo+",
        r"uuu+",  # repeated letters
        r"ss+",
        r"tt+",
        r"pp+",
        r"ll+",  # double consonants
        r"([^aeiou]){2,}",  # 3+ consecutive consonants
    ]

    def _has_typos(self, query: str) -> bool:
        """Quick check if query contains potential typos.

        Uses pattern matching for fast detection before running
        full spell correction (which is more expensive).

        Args:
            query: Query text to check

        Returns:
            True if potential typos detected

        """
        if not PHASE2_AVAILABLE:
            return False

        # Environment variable to disable spell correction (for hooks with tight timeouts)
        # Spell correction initialization loads 10,000+ terms which takes ~13s
        if os.environ.get("CKS_SPELL_CORRECTION_ENABLED", "true").lower() == "false":
            return False

        # Quick pattern check for common typos
        query_lower = query.lower()

        # Check for repeated characters (indicative of typos)
        import re

        for pattern in self._TYPO_PATTERNS:
            if re.search(pattern, query_lower):
                return True

        # Check if spell corrector would make any corrections
        # (only initialize if we suspect typos to avoid overhead)
        try:
            if self._spell_corrector is None:
                from .spell_correction import QuerySpellCorrector

                self._spell_corrector = QuerySpellCorrector()
                self._spell_corrector.initialize(str(self.db_path))

            # Test if correction would change the query
            corrected = self._spell_corrector.correct_query(query)
            return corrected.lower() != query.lower()
        except Exception:
            return False

    def _auto_correct_spelling(self, query: str) -> str:
        """Auto-correct spelling using QuerySpellCorrector.

        Args:
            query: Query text to correct

        Returns:
            Corrected query (or original if correction fails)

        """
        if not PHASE2_AVAILABLE:
            return query

        # Environment variable to disable spell correction (for hooks with tight timeouts)
        # Spell correction initialization loads 10,000+ terms which takes ~13s
        if os.environ.get("CKS_SPELL_CORRECTION_ENABLED", "true").lower() == "false":
            return query

        try:
            if self._spell_corrector is None:
                from .spell_correction import QuerySpellCorrector

                self._spell_corrector = QuerySpellCorrector()
                self._spell_corrector.initialize(str(self.db_path))

            corrected = self._spell_corrector.correct_query(query)

            # Only log if correction was actually made
            if corrected.lower() != query.lower():
                # Optional: print correction notice (disabled by default)
                # print(f"[CKS] Auto-corrected: '{query}' -> '{corrected}'")
                pass

            return corrected

        except Exception as e:
            # Fail gracefully - return original query
            print(f"⚠️ Spell correction failed: {e}")
            return query

    def _has_abbreviations(self, query: str) -> bool:
        """Check if query contains common abbreviations that would benefit
        from query expansion.

        Args:
            query: Query text to check

        Returns:
            True if abbreviations detected

        """
        if not PHASE1_AVAILABLE:
            return False

        # Simple word extraction (split by whitespace)
        words = set(query.lower().split())

        # Check for intersection with abbreviations list
        return bool(words & self._ABBREVIATIONS)

    def _detect_entry_type(self, query: str) -> str | None:
        """Auto-detect entry type filter based on query keywords.

        Uses QUERY_INTENT_BOOSTS patterns to identify which entry types
        are most relevant to the query. Returns a single best-match type
        or None if no clear signal.

        Args:
            query: Query text to analyze

        Returns:
            Suggested entry type (correction, decision, pattern, etc.) or None

        """
        query_lower = query.lower()

        # Count matches for each entry type
        type_scores = {}
        import re

        for keywords, types in QUERY_INTENT_BOOSTS.items():
            # Check if any keyword matches
            if re.search(r"\b(" + keywords + r")\b", query_lower):
                # Boost each type in the list
                for entry_type in types:
                    type_scores[entry_type] = type_scores.get(entry_type, 0) + 1

        # Return the highest-scoring type if it has a clear signal
        if type_scores:
            best_type = max(type_scores, key=type_scores.get)
            # Only return if it has a meaningful score (at least 1 keyword match)
            if type_scores[best_type] >= 1:
                return best_type

        return None

    def _should_enable_diversity(self, query: str) -> float:
        """Detect if query would benefit from result diversification.

        Broad/exploratory queries benefit from MMR diversity to avoid
        redundant results. Returns suggested diversity lambda (0.0-1.0)
        or 0.0 if diversity not recommended.

        Args:
            query: Query text to analyze

        Returns:
            Suggested diversity lambda (0.3-0.5) or 0.0

        """
        query_lower = query.lower()

        # Keywords indicating broad/exploratory intent
        diversity_keywords = {
            # High diversity desired (0.4)
            "all of": 0.4,
            "every": 0.4,
            "each": 0.4,
            "all types of": 0.4,
            "various": 0.4,
            "different": 0.4,
            "multiple": 0.4,
            "several": 0.4,
            # Medium diversity desired (0.3)
            "overview": 0.3,
            "summary": 0.3,
            "list": 0.3,
            "examples of": 0.3,
            "kinds of": 0.3,
            "types of": 0.3,
            "ways to": 0.3,
            "approaches": 0.3,
            "options": 0.3,
            "alternatives": 0.3,
        }

        # Check for diversity keywords
        import re

        max_diversity = 0.0
        for keyword, diversity_value in diversity_keywords.items():
            # Use word boundary matching
            if re.search(r"\b" + re.escape(keyword) + r"\b", query_lower):
                max_diversity = max(max_diversity, diversity_value)

        return max_diversity

    def _calculate_final_score(
        self,
        similarity: float,
        boost: float,
        created_at: str,
        usage_count: int,
        intent_boost: float = 1.0,
    ) -> float:
        """Calculate final ranking score from multiple signals.

        Combines:
        - Similarity (semantic match) × boost (success factor) × intent_boost: 60%
        - Recency decay (exponential over 4 weeks): 10%
        - Usage frequency (log scale to avoid overfitting): 10%
        - Usage-weighted similarity: 20%

        Args:
            similarity: Cosine similarity score (0-1)
            boost: Success boost factor (0.5-1.5)
            created_at: ISO timestamp of creation
            usage_count: Number of times this entry was used
            intent_boost: Intent-based boost factor (default 1.0)

        Returns:
            Final ranking score (higher = better)

        """
        # Base: similarity × boost × intent_boost
        base_score = similarity * boost * intent_boost

        # Recency decay (exponential over 4 weeks)
        # Parse timestamp with timezone handling
        try:
            if "Z" in created_at:
                created_at_parsed = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            elif "+" in created_at:
                created_at_parsed = datetime.fromisoformat(created_at)
            else:
                created_at_parsed = datetime.fromisoformat(created_at).replace(tzinfo=UTC)
            days_old = (datetime.now(UTC) - created_at_parsed).days
        except Exception:
            # If parsing fails, assume recent
            days_old = 0

        recency_decay = max(0.5, 0.97**days_old)  # 3% decay per day, min 0.5

        # Usage count weighting (log scale to avoid overfitting)
        usage_weight = min(1.2, 1.0 + math.log10(usage_count + 1) * 0.1)

        # Combine signals
        return (
            base_score * 0.60  # Similarity + boost
            + recency_decay * 0.10  # Recency
            + (usage_count / 100) * 0.10  # Usage frequency (normalized)
            + base_score * usage_weight * 0.20  # Usage-weighted similarity
        )

    # ========================================================================
    # Validation Helpers
    # ========================================================================

    def _validate_entry_type(self, entry_type: str) -> bool:
        """Validate entry type against allowed types.

        Args:
            entry_type: Type string to validate

        Returns:
            True if valid, False otherwise

        """
        return entry_type in VALID_ENTRY_TYPES

    def _validate_entry_content(
        self,
        title: str | None = None,
        content: str | None = None,
        question: str | None = None,
        answer: str | None = None,
        strict_mode: bool | None = None,
    ) -> None:
        """Validate entry content meets minimum quality requirements.

        This method validates that CKS entries have meaningful, non-empty content
        to prevent low-quality data from being stored. Validation can be
        configured via environment variable CKS_VALIDATION_STRICT.

        Args:
            title: Title for pattern/code entries (min 1 char)
            content: Main content for pattern/code entries (min 10 chars)
            question: Question for memory entries (min 3 chars)
            answer: Answer for memory entries (min 5 chars)
            strict_mode: Override default strict mode (None = use env var)

        Raises:
            ValueError: If validation fails and strict_mode is True

        Environment Variables:
            CKS_VALIDATION_STRICT: If "true", validation raises ValueError.
                                  If "false" or unset, validation only logs warnings.

        """
        # Determine strict mode from parameter or environment
        if strict_mode is None:
            strict_mode = os.getenv("CKS_VALIDATION_STRICT", "false").lower() == "true"

        # Validation rules with minimum lengths
        MIN_TITLE_LENGTH = 1
        MIN_CONTENT_LENGTH = 10
        MIN_QUESTION_LENGTH = 3
        MIN_ANSWER_LENGTH = 5

        errors = []

        # Validate title (for pattern/code entries)
        if title is not None:
            if not title or not title.strip():
                errors.append("title cannot be empty")
            elif len(title.strip()) < MIN_TITLE_LENGTH:
                errors.append(f"title must be at least {MIN_TITLE_LENGTH} character(s)")

        # Validate content (for pattern/code entries)
        if content is not None:
            if not content or not content.strip():
                errors.append("content cannot be empty")
            elif len(content.strip()) < MIN_CONTENT_LENGTH:
                errors.append(f"content must be at least {MIN_CONTENT_LENGTH} characters")

        # Validate question (for memory entries)
        if question is not None:
            if not question or not question.strip():
                errors.append("question cannot be empty")
            elif len(question.strip()) < MIN_QUESTION_LENGTH:
                errors.append(f"question must be at least {MIN_QUESTION_LENGTH} characters")

        # Validate answer (for memory entries)
        if answer is not None:
            if not answer or not answer.strip():
                errors.append("answer cannot be empty")
            elif len(answer.strip()) < MIN_ANSWER_LENGTH:
                errors.append(f"answer must be at least {MIN_ANSWER_LENGTH} characters")

        if errors:
            error_msg = "; ".join(errors)
            if strict_mode:
                raise ValueError(f"Entry validation failed: {error_msg}")
            # Log warning but don't raise
            logger.warning(f"Entry quality issue (non-strict mode): {error_msg}")

    # ========================================================================
    # Memory Operations
    # ========================================================================

    def ingest_memory(
        self,
        question: str,
        answer: str,
        source_chunk: str | None = None,
        **metadata,
    ) -> str:
        """Store a conversation memory with optional embedding.

        Args:
            question: The question/task description
            answer: The answer/solution content
            source_chunk: Original user language for better semantic matching (optional, uses answer if not provided)
            **metadata: Additional metadata to store

        Returns:
            Entry ID of the stored memory

        Raises:
            ValueError: If validation fails in strict mode (CKS_VALIDATION_STRICT=true)

        """
        # Validate entry content quality
        self._validate_entry_content(question=question, answer=answer)

        entry_id = f"mem_{uuid4().hex[:16]}"

        # Use source_chunk for embedding if provided, otherwise fall back to answer
        embedding_text = source_chunk if source_chunk else answer

        full_metadata = {
            "question": question,
            "source": "cks_unified",
            "ingested_at": datetime.now(UTC).isoformat(),
            **metadata,
        }

        # Generate embedding for the content (prefer source_chunk for better semantic matching)
        embedding = self._generate_embedding(embedding_text) if self.enable_semantic else None

        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO entries (id, type, title, content, metadata, embedding, source_chunk)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                entry_id,
                "memory",
                question[:200],
                answer,
                json.dumps(full_metadata),
                embedding,
                source_chunk,
            ),
        )

        self.conn.commit()
        return entry_id

    def search_memories(self, query: str, limit: int = 5) -> list[dict]:
        """Search conversation memories."""
        return self.search(query, entry_type="memory", limit=limit)

    def search_keyword_fts5(
        self,
        query: str,
        limit: int = 10,
        entry_type: str | None = None,
    ) -> list[dict]:
        """Fast FTS5 keyword search for hooks and quick lookups.

        Uses the FTS5 full-text index for <10ms searches. Falls back
        to semantic search if FTS5 is not available.

        Args:
            query: Search query (keywords)
            limit: Maximum results
            entry_type: Optional type filter (memory, pattern, etc.)

        Returns:
            List of matching entries with BM25 ranking

        """
        # Check if FTS5 table exists
        cursor = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' " "AND name='entries_fts'",
        )
        if not cursor.fetchone():
            # Fall back to semantic search
            return self.search(query, entry_type=entry_type, limit=limit)

        # Prepare FTS5 query - clean words and OR-join
        import re

        # Remove FTS5 special chars: " * ? ( ) : ^
        clean_query = re.sub(r'["\*\?\(\)\:\^]', "", query)
        words = [w for w in clean_query.strip().split() if len(w) > 2]
        if not words:
            return []
        fts_query = " OR ".join(f'"{w}"' for w in words)

        try:
            if entry_type:
                sql = """
                    SELECT e.*, bm25(entries_fts) as rank
                    FROM entries_fts fts
                    JOIN entries e ON fts.rowid = e.rowid
                    WHERE entries_fts MATCH ? AND e.type = ?
                    ORDER BY rank LIMIT ?
                """
                cursor = self.conn.execute(sql, (fts_query, entry_type, limit))
            else:
                sql = """
                    SELECT e.*, bm25(entries_fts) as rank
                    FROM entries_fts fts
                    JOIN entries e ON fts.rowid = e.rowid
                    WHERE entries_fts MATCH ?
                    ORDER BY rank LIMIT ?
                """
                cursor = self.conn.execute(sql, (fts_query, limit))

            results = []
            for row in cursor.fetchall():
                entry = dict(
                    zip([col[0] for col in cursor.description], row, strict=False),
                )
                entry["search_method"] = "fts5"
                results.append(entry)

            return results

        except Exception as e:
            # FTS5 query failed, fall back to semantic
            print(f"FTS5 search failed, falling back: {e}")
            return self.search(query, entry_type=entry_type, limit=limit)

    # ========================================================================
    # Pattern Operations
    # ========================================================================

    def ingest_pattern(
        self,
        title: str,
        content: str,
        entry_type: str = "pattern",
        source_chunk: str | None = None,
        **metadata,
    ) -> str:
        """Store a pattern document with optional embedding.

        Args:
            title: Title of the pattern
            content: Content of the pattern
            entry_type: Type of entry (default: "pattern")
                Valid types: memory, pattern, code, knowledge,
                            correction, decision, commitment, insight, learning
            source_chunk: Original user language for better semantic matching (optional, uses content if not provided)
            **metadata: Additional metadata fields

        Returns:
            Entry ID if successful

        Raises:
            ValueError: If entry_type is not in VALID_ENTRY_TYPES
            ValueError: If validation fails in strict mode (CKS_VALIDATION_STRICT=true)

        """
        # Validate entry type
        if not self._validate_entry_type(entry_type):
            raise ValueError(
                f"Invalid entry_type '{entry_type}'. "
                f"Must be one of: {', '.join(VALID_ENTRY_TYPES)}",
            )

        # Validate entry content quality
        self._validate_entry_content(title=title, content=content)

        entry_id = f"pat_{uuid4().hex[:16]}"

        # Use source_chunk for embedding if provided, otherwise fall back to content
        embedding_text = source_chunk if source_chunk else content

        full_metadata = {
            "title": title,
            "source": "cks_unified",
            "ingested_at": datetime.now(UTC).isoformat(),
            **metadata,
        }

        # Generate embedding for content (prefer source_chunk for better semantic matching)
        embedding = self._generate_embedding(embedding_text) if self.enable_semantic else None

        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO entries (id, type, title, content, metadata, embedding, source_chunk)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                entry_id,
                entry_type,
                title,
                content,
                json.dumps(full_metadata),
                embedding,
                source_chunk,
            ),
        )

        self.conn.commit()
        return entry_id

    def search_patterns(self, query: str, limit: int = 5) -> list[dict]:
        """Search pattern documentation."""
        return self.search(query, entry_type="pattern", limit=limit)

    # ========================================================================
    # New Memory Type Operations (Enhancement 4)
    # ========================================================================

    def ingest_correction(self, title: str, content: str, **metadata) -> str:
        """Store a correction (mistake and fix).

        Args:
            title: Title describing the mistake
            content: The fix and explanation
            **metadata: Additional metadata fields

        Returns:
            Entry ID if successful

        """
        return self.ingest_pattern(title, content, entry_type="correction", **metadata)

    def ingest_decision(self, title: str, content: str, **metadata) -> str:
        """Store a decision (choice made and rationale).

        Args:
            title: Title of the decision
            content: The decision rationale and context
            **metadata: Additional metadata fields

        Returns:
            Entry ID if successful

        """
        return self.ingest_pattern(title, content, entry_type="decision", **metadata)

    def ingest_commitment(self, title: str, content: str, **metadata) -> str:
        """Store a commitment (promise or resolution).

        Args:
            title: Title of the commitment
            content: The commitment details
            **metadata: Additional metadata fields

        Returns:
            Entry ID if successful

        """
        return self.ingest_pattern(title, content, entry_type="commitment", **metadata)

    def ingest_insight(self, title: str, content: str, **metadata) -> str:
        """Store an insight (realization or aha moment).

        Args:
            title: Title of the insight
            content: The insight and its implications
            **metadata: Additional metadata fields

        Returns:
            Entry ID if successful

        """
        return self.ingest_pattern(title, content, entry_type="insight", **metadata)

    def ingest_learning(self, title: str, content: str, **metadata) -> str:
        """Store a learning (lesson learned).

        Args:
            title: Title of the learning
            content: The lesson and how to apply it
            **metadata: Additional metadata fields

        Returns:
            Entry ID if successful

        """
        return self.ingest_pattern(title, content, entry_type="learning", **metadata)

    # ========================================================================
    # Decision Extraction (Oppia 5-Step from transcripts)
    # ========================================================================

    def extract_and_ingest_decisions(
        self,
        transcript: str,
        min_confidence: float = 0.60,
        session_id: str | None = None,
    ) -> dict:
        """Extract decisions from transcript and ingest to CKS.

        Uses Oppia 5-Step structure:
        1. Problem Definition
        2. Code Investigation
        3. Hypothesis Testing
        4. Solution Documentation
        5. Outcome Verification

        Args:
            transcript: Full session transcript text
            min_confidence: Minimum extraction confidence (0.0-1.0)
            session_id: Optional session identifier for metadata

        Returns:
            Dict with extraction results:
            {
                "count": number of decisions extracted,
                "entry_ids": list of CKS entry IDs,
                "avg_confidence": average confidence score,
                "hypothesis_coverage": % with hypothesis testing,
                "oppia_complete": % with complete Oppia structure,
            }

        """
        from .decision_extractor import DecisionExtractor

        if not transcript or len(transcript) < 100:
            return {
                "count": 0,
                "entry_ids": [],
                "avg_confidence": 0.0,
                "hypothesis_coverage": 0.0,
                "oppia_complete": 0.0,
            }

        extractor = DecisionExtractor(min_confidence=min_confidence)
        decisions = extractor.extract_from_transcript(transcript)

        if not decisions:
            return {
                "count": 0,
                "entry_ids": [],
                "avg_confidence": 0.0,
                "hypothesis_coverage": 0.0,
                "oppia_complete": 0.0,
            }

        entry_ids = []
        total_confidence = 0.0
        with_hypotheses = 0
        oppia_complete_count = 0

        for decision in decisions:
            # Decide entry type based on decision content
            if decision.decision_type == "DEBUGGING" and decision.outcome_verified:
                entry_type = "learning"  # Verified debugging = lesson learned
            else:
                entry_type = "decision"

            # Build metadata
            metadata = decision.to_cks_metadata()
            if session_id:
                metadata["session_id"] = session_id

            # Ingest to CKS
            entry_id = self.ingest_pattern(
                title=decision.title,
                content=decision.to_cks_content(),
                entry_type=entry_type,
                **metadata,
            )
            entry_ids.append(entry_id)

            # Track metrics
            total_confidence += decision.confidence
            if decision.hypotheses_tested:
                with_hypotheses += 1
            if decision._oppia_completeness() >= 0.6:
                oppia_complete_count += 1

        return {
            "count": len(entry_ids),
            "entry_ids": entry_ids,
            "avg_confidence": total_confidence / len(decisions) if decisions else 0.0,
            "hypothesis_coverage": with_hypotheses / len(decisions) if decisions else 0.0,
            "oppia_complete": oppia_complete_count / len(decisions) if decisions else 0.0,
        }

    # ========================================================================
    # ========================================================================
    # Batch Operations (3-5x faster for bulk imports)
    # ========================================================================

    def ingest_memories_batch(
        self,
        items: list[dict[str, str]],
        batch_size: int = 32,
        **common_metadata,
    ) -> list[str]:
        """Ingest multiple memories in a single batch.

        3-5x faster than individual ingest_memory calls for bulk imports.

        Args:
            items: List of dicts with 'question' and 'answer' keys.
                Example: [{"question": "Q1", "answer": "A1"}, ...]
            batch_size: Number of embeddings to generate at once (default: 32)
            **common_metadata: Metadata applied to all entries

        Returns:
            List of entry IDs created

        """
        if not items:
            return []

        entry_ids = []
        texts_to_embed = []
        item_indices = []

        # Prepare data
        for idx, item in enumerate(items):
            if "question" not in item or "answer" not in item:
                continue

            entry_id = f"mem_{uuid4().hex[:16]}"
            entry_ids.append(entry_id)

            # Use answer for embedding (will be batch processed)
            texts_to_embed.append(item["answer"])
            item_indices.append((idx, entry_id, item))

        # Generate embeddings in a single batch
        embeddings = None
        if self.enable_semantic and texts_to_embed:
            embeddings = self._generate_embeddings_batch(texts_to_embed, batch_size)

        # Bulk insert to database
        cursor = self.conn.cursor()
        for idx, (orig_idx, entry_id, item) in enumerate(item_indices):
            question = item["question"]
            answer = item["answer"]
            source_chunk = item.get("source_chunk")

            embedding = embeddings[idx] if embeddings is not None else None

            full_metadata = {
                "question": question,
                "source": "cks_unified_batch",
                "ingested_at": datetime.now(UTC).isoformat(),
                **common_metadata,
                **{
                    k: v for k, v in item.items() if k not in {"question", "answer", "source_chunk"}
                },
            }

            cursor.execute(
                """
                INSERT INTO entries (id, type, title, content, metadata, embedding, source_chunk)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    entry_id,
                    "memory",
                    question[:200],
                    answer,
                    json.dumps(full_metadata),
                    embedding,
                    source_chunk,
                ),
            )

        self.conn.commit()
        return entry_ids

    def ingest_patterns_batch(
        self,
        items: list[dict[str, str]],
        entry_type: str = "pattern",
        batch_size: int = 32,
        **common_metadata,
    ) -> list[str]:
        """Ingest multiple patterns/knowledge items in a single batch.

        Args:
            items: List of dicts with 'title' and 'content' keys.
                Example: [{"title": "T1", "content": "C1"}, ...]
            entry_type: Type for all entries (default: "pattern")
            batch_size: Number of embeddings to generate at once
            **common_metadata: Metadata applied to all entries

        Returns:
            List of entry IDs created

        """
        # Validate entry type
        if not self._validate_entry_type(entry_type):
            raise ValueError(
                f"Invalid entry_type '{entry_type}'. "
                f"Must be one of: {', '.join(VALID_ENTRY_TYPES)}",
            )

        if not items:
            return []

        entry_ids = []
        texts_to_embed = []
        item_indices = []

        # Prepare data
        for idx, item in enumerate(items):
            if "title" not in item or "content" not in item:
                continue

            entry_id = f"{entry_type[0]}_{uuid4().hex[:16]}"
            entry_ids.append(entry_id)

            # Use content for embedding
            texts_to_embed.append(item["content"])
            item_indices.append((idx, entry_id, item))

        # Generate embeddings in a single batch
        embeddings = None
        if self.enable_semantic and texts_to_embed:
            embeddings = self._generate_embeddings_batch(texts_to_embed, batch_size)

        # Bulk insert to database
        cursor = self.conn.cursor()
        for idx, (orig_idx, entry_id, item) in enumerate(item_indices):
            title = item["title"]
            content = item["content"]
            source_chunk = item.get("source_chunk")
            embedding = embeddings[idx] if embeddings is not None else None

            full_metadata = {
                "title": title,
                "source": "cks_unified_batch",
                "ingested_at": datetime.now(UTC).isoformat(),
                **common_metadata,
                **{k: v for k, v in item.items() if k not in {"title", "content", "source_chunk"}},
            }

            cursor.execute(
                """
                INSERT INTO entries (id, type, title, content, metadata, embedding, source_chunk)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    entry_id,
                    entry_type,
                    title,
                    content,
                    json.dumps(full_metadata),
                    embedding,
                    source_chunk,
                ),
            )

        self.conn.commit()
        return entry_ids

    def _generate_embeddings_batch(
        self,
        texts: list[str],
        batch_size: int = 32,
    ) -> list[bytes]:
        """Generate embeddings for multiple texts in batches.

        Args:
            texts: List of text strings to embed
            batch_size: Number of texts to process at once

        Returns:
            List of serialized embedding blobs

        """
        if not self.enable_semantic or not texts:
            return [None] * len(texts)

        # Ensure model is loaded
        if not self._model_loaded:
            self._initialize_embedding_model()

        if not self._model:
            return [None] * len(texts)

        import numpy as np

        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            batch_embeddings = self._model.encode(
                batch_texts,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )
            all_embeddings.append(batch_embeddings)

        # Combine and serialize
        combined = np.vstack(all_embeddings)
        return [combined[i].astype(np.float32).tobytes() for i in range(len(combined))]

    # Universal Operations
    # ========================================================================

    def _sanitize_fts_query(self, query: str) -> str:
        """Sanitize query for FTS5 to handle special characters.

        FTS5 special characters and patterns that cause syntax errors:
        - / (forward slash) - syntax error
        - : (colon) - column specification syntax (e.g., 'column:term')
        - . (period/dot) - can cause syntax errors in certain contexts
        - * (asterisk) - prefix operator
        - ? (question mark) - causes syntax error
        - " (double quote) - phrase operator
        - ( ) (parentheses) - grouping
        - - (hyphen) - column operator
        - < > (angle brackets) - NEAR operator
        - | (pipe) - OR operator

        Strategy: Replace problematic characters with spaces to avoid FTS5 syntax errors
        while maintaining searchability.
        """
        import re

        # First, handle colon-based column syntax (e.g., 'P:' in 'P:/path')
        # FTS5 interprets 'word:' as 'search in column named word'
        sanitized = re.sub(r":", " ", query)

        # Characters that cause FTS5 syntax errors - replace with space
        # Include period (.), question mark (?), and other FTS5 special chars
        fts5_special_chars = r'[/\.*?"()<>|-]'

        # Replace each special character with a space
        sanitized = re.sub(fts5_special_chars, " ", sanitized)

        # Collapse multiple spaces into single space
        sanitized = re.sub(r"\s+", " ", sanitized)

        # Strip leading/trailing whitespace
        return sanitized.strip()

    def search(self, query: str, entry_type: str | None = None, limit: int = 5) -> list[dict]:
        """Search all entries or filter by type using FTS5 full-text search."""
        cursor = self.conn.cursor()

        # Check if FTS table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='entries_fts'",
        )
        fts_exists = cursor.fetchone() is not None

        if fts_exists:
            # Use FTS5 for fast full-text search
            sanitized_query = self._sanitize_fts_query(query)
            if entry_type:
                cursor.execute(
                    """
                    SELECT e.id, e.type, e.title, e.content, e.metadata, e.created_at
                    FROM entries e
                    WHERE e.rowid IN (SELECT rowid FROM entries_fts WHERE entries_fts MATCH ?)
                      AND e.type = ?
                    ORDER BY e.created_at DESC
                    LIMIT ?
                    """,
                    (sanitized_query, entry_type, limit),
                )
            else:
                cursor.execute(
                    """
                    SELECT e.id, e.type, e.title, e.content, e.metadata, e.created_at
                    FROM entries e
                    WHERE e.rowid IN (SELECT rowid FROM entries_fts WHERE entries_fts MATCH ?)
                    ORDER BY e.created_at DESC
                    LIMIT ?
                    """,
                    (sanitized_query, limit),
                )
        else:
            # Fallback to LIKE queries if FTS not available
            if entry_type:
                cursor.execute(
                    """
                    SELECT id, type, title, content, metadata, created_at
                    FROM entries
                    WHERE type = ? AND (content LIKE ? OR title LIKE ? OR metadata LIKE ?)
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (entry_type, f"%{query}%", f"%{query}%", f"%{query}%", limit),
                )
            else:
                cursor.execute(
                    """
                    SELECT id, type, title, content, metadata, created_at
                    FROM entries
                    WHERE content LIKE ? OR title LIKE ? OR metadata LIKE ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (f"%{query}%", f"%{query}%", f"%{query}%", limit),
                )

        results = []
        for row in cursor.fetchall():
            try:
                metadata = json.loads(row["metadata"]) if row["metadata"] else {}
            except:
                metadata = {}

            results.append(
                {
                    "id": row["id"],
                    "type": row["type"],
                    "title": row["title"],
                    "content": row["content"],
                    "metadata": metadata,
                    "created_at": row["created_at"],
                },
            )

        # Record usage for returned entries
        self._record_usage_for_results(results, success=True)

        return results

    # ========================================================================
    # Consolidation Phase 1: Project Context Entity Operations
    # ========================================================================

    def ingest_task(
        self,
        name: str,
        status: str = "pending",
        progress_pct: int = 0,
        description: str = "",
        priority: str = "medium",
        strategic_context: dict[str, Any] | None = None,
        **metadata,
    ) -> str:
        """Store a task entity for project context management."""
        import hashlib

        task_id = f"task_{name.lower()}_{hashlib.md5(name.encode()).hexdigest()[:8]}"

        task_metadata = {
            "task_name": name,
            "status": status,
            "progress_pct": progress_pct,
            "priority": priority,
            **metadata,
        }
        if strategic_context:
            task_metadata["strategic_context"] = strategic_context

        content_parts = [description]
        if strategic_context:
            if strategic_context.get("goal"):
                content_parts.append(f"Goal: {strategic_context['goal']}")
            if strategic_context.get("success_criteria"):
                content_parts.append(f"Success Criteria: {strategic_context['success_criteria']}")
            if strategic_context.get("approach"):
                content_parts.append(f"Approach: {strategic_context['approach']}")

        content = " | ".join(content_parts) if content_parts else description or name

        return self.ingest_pattern(
            title=name,
            content=content,
            entry_type="task",
            entry_id=task_id,
            **task_metadata,
        )

    def ingest_checkpoint(
        self,
        task_name: str,
        session_id: str,
        progress_pct: int,
        blocker: dict[str, Any] | None = None,
        files_modified: list[str] | None = None,
        next_steps: list[str] | None = None,
        session_summary: str = "",
        **metadata,
    ) -> str:
        """Store a session checkpoint entity."""
        timestamp = datetime.now().isoformat()
        checkpoint_id = f"checkpoint_{task_name.lower()}_{session_id}"

        checkpoint_metadata = {
            "task_name": task_name,
            "session_id": session_id,
            "timestamp": timestamp,
            "progress_pct": progress_pct,
            "blocker": blocker,
            "files_modified": files_modified or [],
            "next_steps": next_steps or [],
            **metadata,
        }

        content_parts = [f"Progress: {progress_pct}%"]
        if session_summary:
            content_parts.append(session_summary)
        if blocker:
            content_parts.append(f"Blocker: {blocker.get('description', 'Unknown blocker')}")
        if next_steps:
            content_parts.append(f"Next Steps: {', '.join(next_steps[:3])}")

        content = " | ".join(content_parts)

        entry_id = self.ingest_pattern(
            title=f"Checkpoint: {task_name}",
            content=content,
            entry_type="checkpoint",
            entry_id=checkpoint_id,
            **checkpoint_metadata,
        )

        if entry_id:
            self.add_relationship(
                from_entry_id=entry_id,
                to_entry_id=f"task_{task_name.lower()}",
                relationship_type="belongs_to_task",
            )

        return entry_id

    def ingest_blocker(
        self,
        task_name: str,
        description: str,
        severity: str = "medium",
        investigation: str = "",
        workaround: str = "",
        **metadata,
    ) -> str:
        """Store a blocker entity."""
        timestamp = datetime.now().isoformat()
        import hashlib

        blocker_id = (
            f"blocker_{task_name.lower()}_{hashlib.md5(description.encode()).hexdigest()[:8]}"
        )

        blocker_metadata = {
            "task_name": task_name,
            "severity": severity,
            "created_date": timestamp,
            "status": "unresolved",
            "investigation": investigation,
            "workaround": workaround,
            **metadata,
        }

        content_parts = [description]
        if investigation:
            content_parts.append(f"Investigation: {investigation}")
        if workaround:
            content_parts.append(f"Workaround: {workaround}")

        content = " | ".join(content_parts)

        entry_id = self.ingest_pattern(
            title=f"Blocker: {description[:50]}..."
            if len(description) > 50
            else f"Blocker: {description}",
            content=content,
            entry_type="blocker",
            entry_id=blocker_id,
            **blocker_metadata,
        )

        if entry_id:
            self.add_relationship(
                from_entry_id=entry_id,
                to_entry_id=f"task_{task_name.lower()}",
                relationship_type="blocks_task",
            )

        return entry_id

    def add_relationship(
        self,
        from_entry_id: str,
        to_entry_id: str,
        relationship_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Add a relationship between two entries."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO entity_relationships
                (from_entry_id, to_entry_id, relationship_type, metadata)
                VALUES (?, ?, ?, ?)
            """,
                (
                    from_entry_id,
                    to_entry_id,
                    relationship_type,
                    json.dumps(metadata) if metadata else None,
                ),
            )
            self.conn.commit()
            return True
        except Exception as e:
            import logging

            logging.getLogger(__name__).exception(f"Error adding relationship: {e}")
            return False

    def get_relationships(
        self,
        entry_id: str,
        relationship_type: str | None = None,
        direction: str = "both",
    ) -> list[dict[str, Any]]:
        """Get relationships for an entry."""
        try:
            cursor = self.conn.cursor()
            results = []

            if direction in ("outgoing", "both"):
                params = [entry_id]
                sql = """
                    SELECT from_entry_id, to_entry_id, relationship_type, metadata
                    FROM entity_relationships
                    WHERE from_entry_id = ?
                """
                if relationship_type:
                    sql += " AND relationship_type = ?"
                    params.append(relationship_type)

                for row in cursor.execute(sql, params):
                    results.append(
                        {
                            "from_entry_id": row[0],
                            "to_entry_id": row[1],
                            "relationship_type": row[2],
                            "metadata": json.loads(row[3]) if row[3] else {},
                            "direction": "outgoing",
                        },
                    )

            if direction in ("incoming", "both"):
                params = [entry_id]
                sql = """
                    SELECT from_entry_id, to_entry_id, relationship_type, metadata
                    FROM entity_relationships
                    WHERE to_entry_id = ?
                """
                if relationship_type:
                    sql += " AND relationship_type = ?"
                    params.append(relationship_type)

                for row in cursor.execute(sql, params):
                    results.append(
                        {
                            "from_entry_id": row[0],
                            "to_entry_id": row[1],
                            "relationship_type": row[2],
                            "metadata": json.loads(row[3]) if row[3] else {},
                            "direction": "incoming",
                        },
                    )

            return results
        except Exception as e:
            import logging

            logging.getLogger(__name__).exception(f"Error getting relationships: {e}")
            return []

    def get_tasks(
        self,
        status: str | None = None,
        priority: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get tasks with optional filtering."""
        query = "SELECT * FROM entries WHERE type = 'task'"
        params = []

        if status:
            query += " AND json_extract(metadata, '$.status') = ?"
            params.append(status)

        if priority:
            query += " AND json_extract(metadata, '$.priority') = ?"
            params.append(priority)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor = self.conn.cursor()
        cursor.execute(query, params)

        results = []
        for row in cursor.fetchall():
            try:
                metadata = json.loads(row["metadata"]) if row["metadata"] else {}
            except:
                metadata = {}

            results.append(
                {
                    "id": row["id"],
                    "type": row["type"],
                    "title": row["title"],
                    "content": row["content"],
                    "metadata": metadata,
                    "created_at": row["created_at"],
                },
            )

        return results
        if entry_type:
            cursor.execute(
                """
                SELECT id, type, title, content, metadata, created_at
                FROM entries
                WHERE type = ? AND (content LIKE ? OR title LIKE ? OR metadata LIKE ?)
                ORDER BY created_at DESC
                LIMIT ?
            """,
                (entry_type, f"%{query}%", f"%{query}%", f"%{query}%", limit),
            )
        else:
            cursor.execute(
                """
                SELECT id, type, title, content, metadata, created_at
                FROM entries
                WHERE content LIKE ? OR title LIKE ? OR metadata LIKE ?
                ORDER BY created_at DESC
                LIMIT ?
            """,
                (f"%{query}%", f"%{query}%", f"%{query}%", limit),
            )

        results = []
        for row in cursor.fetchall():
            try:
                metadata = json.loads(row["metadata"]) if row["metadata"] else {}
            except:
                metadata = {}

            results.append(
                {
                    "id": row["id"],
                    "type": row["type"],
                    "title": row["title"],
                    "content": row["content"],
                    "metadata": metadata,
                    "created_at": row["created_at"],
                },
            )

        return results

    def search_semantic(
        self,
        query: str,
        entry_type: str | None = None,
        limit: int = 5,
        expand_query: bool = False,
        fusion_method: str | None = None,
        diversity: float | None = None,
        entity_slug: str | None = None,
        spell_correct: bool | None = None,
    ) -> list[dict]:
        """Search entries using semantic similarity with multi-signal re-ranking.

        Phase 1 Enhancements:
        - Query expansion: Expand query with synonyms/abbreviations
        - Fusion method: 'rrf' for Reciprocal Rank Fusion
        - Diversity: MMR lambda (0=relevance, 1=diversity)
        - Entity slug: Use entity-specific terminology

        Phase 2 Smart Defaults:
        - Spell correction: Auto-enabled when typos detected
        - Entry type: Auto-detected from query keywords (error, decision, pattern, etc.)
        - Diversity: Auto-enabled for broad/exploratory queries (all, overview, etc.)
        - Fusion method: Defaults to 'adaptive' for intelligent selection

        Args:
            query: Search query text
            entry_type: Filter by type (optional, auto-detected if not specified)
            limit: Max results to return
            expand_query: Enable query expansion (default: False, auto-detected for abbreviations)
            fusion_method: Result fusion method ('rrf', 'adaptive', None)
            diversity: MMR diversity parameter (0.0-1.0, auto-detected for broad queries)
            entity_slug: Entity for domain-specific expansion
            spell_correct: Auto-correct typos (default: None for auto-detect)

        Returns:
            List of matching entries with similarity scores, sorted by relevance

        """
        # Check query cache first (for cached queries only - without Phase 1/2 features)
        # Skip cache if using advanced features that modify query behavior
        use_cache = (
            not expand_query
            and fusion_method is None
            and diversity is None
            and entity_slug is None
            and spell_correct is None
        )
        if use_cache:
            cache_key = self._cache_key(query, entry_type, limit)
            cached_result = self._get_cached_result(cache_key)
            if cached_result is not None:
                return cached_result

        original_query = query  # Store for tracking/debugging

        # Track original parameter values to distinguish explicit vs auto-detected
        _explicit_expand_query = expand_query
        _explicit_fusion_method = fusion_method
        _explicit_entity_slug = entity_slug

        # Phase 2: Smart defaults - auto-detect and apply optimizations

        # Auto spell correction (Phase 2) - only if globally enabled
        if self.enable_spell_correction:
            if spell_correct is None:
                # Auto-correct if typos detected
                if PHASE2_AVAILABLE and self._has_typos(query):
                    query = self._auto_correct_spelling(query)
            elif spell_correct:
                # Explicitly requested
                query = self._auto_correct_spelling(query)

        # Auto-detect abbreviations for expansion (Phase 1 + 2)
        if not expand_query and PHASE1_AVAILABLE and self._has_abbreviations(query):
            expand_query = True

        # Auto-detect entry type for filtering (Phase 2)
        # DISABLED: Too aggressive - filters out relevant results
        # e.g., "debug error" -> type="pattern" (only 6 entries, none relevant)
        # if entry_type is None and PHASE1_AVAILABLE:
        #     detected_type = self._detect_entry_type(query)
        #     if detected_type:
        #         entry_type = detected_type

        # Auto-detect diversity for broad queries (Phase 2)
        if diversity is None and PHASE1_AVAILABLE:
            detected_diversity = self._should_enable_diversity(query)
            if detected_diversity > 0:
                diversity = detected_diversity

        # Recalculate cacheability after smart defaults
        cacheable = (
            not expand_query
            and fusion_method is None
            and diversity is None
            and entity_slug is None
            and spell_correct is None
        )

        # PRIORITY 1: Hybrid temporal search (recent + compressed index)
        # Use if memory-efficient RAG is available AND Phase 1 features were NOT explicitly requested
        # (Auto-detected abbreviations/diversity don't disable hybrid)
        if (
            self.enable_memory_efficient_rag
            and self.memory_efficient_rag
            and not (_explicit_expand_query or _explicit_fusion_method or _explicit_entity_slug)
        ):
            results = self._search_hybrid_temporal(
                query=query,
                entry_type=entry_type,
                limit=limit,
                recent_days=7,  # Entries < 7 days use direct search, older use compressed index
                diversity=diversity,
            )
            return self._cache_and_return(
                self._apply_auto_learning_if_enabled(results, original_query),
                query,
                entry_type,
                limit,
                cacheable and diversity is None,
            )

        # PRIORITY 2: Phase 1 Query expansion and fusion (if explicitly requested)
        if PHASE1_AVAILABLE and (expand_query or fusion_method):
            results = self._search_semantic_phase1(
                query=query,
                original_query=original_query,
                entry_type=entry_type,
                limit=limit,
                expand_query=expand_query,
                fusion_method=fusion_method
                or "adaptive",  # Default to adaptive if Phase 1 requested
                diversity=diversity,
                entity_slug=entity_slug,
            )
            return self._cache_and_return(
                self._apply_auto_learning_if_enabled(results, original_query),
                query,
                entry_type,
                limit,
                cacheable and not spell_correct,
            )

        if not self.enable_semantic:
            # Fallback to LIKE search if semantic not available
            print("⚠️ Semantic search not available, using LIKE search")
            return self.search(query, entry_type=entry_type, limit=limit)

        # Detect query type and get adaptive threshold
        query_type = self._detect_query_type(query)
        adaptive_threshold = QUERY_TYPE_THRESHOLDS[query_type]

        # Lazy-load model on first semantic search
        if not self._model_loaded:
            self._initialize_embedding_model()
            self._model_loaded = True

        # Generate query embedding
        query_embedding = self._generate_embedding(query)
        if query_embedding is None:
            return self.search(query, entry_type=entry_type, limit=limit)

        query_vec = self._deserialize_embedding(query_embedding)
        if query_vec is None:
            return self.search(query, entry_type=entry_type, limit=limit)

        # Get all entries with embeddings and usage stats
        cursor = self.conn.cursor()

        if entry_type:
            cursor.execute(
                """
                SELECT id, type, title, content, metadata, created_at, embedding, usage_count, source_chunk
                FROM entries
                WHERE type = ? AND embedding IS NOT NULL
            """,
                (entry_type,),
            )
        else:
            cursor.execute("""
                SELECT id, type, title, content, metadata, created_at, embedding, usage_count, source_chunk
                FROM entries
                WHERE embedding IS NOT NULL
            """)

        # Vectorized cosine similarity computation (10-50x faster)
        rows = cursor.fetchall()
        if not rows:
            return []

        # Batch load all embeddings into matrix
        valid_indices = []
        embeddings_list = []
        for i, row in enumerate(rows):
            entry_vec = self._deserialize_embedding(row["embedding"])
            if entry_vec is not None:
                valid_indices.append(i)
                embeddings_list.append(entry_vec)

        if not embeddings_list:
            return []

        # Stack into matrix for vectorized computation
        embeddings_matrix = self._np.stack(embeddings_list)

        # Vectorized cosine similarity: (query_vec @ entries.T) / (||query|| * ||entries||)
        query_norm = self._np.linalg.norm(query_vec)
        if query_norm == 0:
            return []

        # Compute all similarities at once using matrix operations
        dot_products = embeddings_matrix @ query_vec  # Shape: (n_entries,)
        entry_norms = self._np.linalg.norm(embeddings_matrix, axis=1)
        similarities = dot_products / (query_norm * entry_norms + 1e-8)

        # Priority 2: Two-pass filtering with adaptive threshold
        # First pass: Use default threshold
        results_with_scores = []
        for idx, similarity in zip(valid_indices, similarities, strict=False):
            # Filter by default threshold
            if similarity < adaptive_threshold:
                continue

            row = rows[idx]

            # Apply success boost factor
            success_boost = self.get_success_boost(row["id"])

            # Apply intent boost factor based on query keywords and entry type
            intent_boost = self._detect_intent_boost(query, row["type"])

            # Combine boosts
            boost = success_boost * intent_boost
            boosted_similarity = similarity * boost

            # Calculate final multi-signal score
            usage_count = row["usage_count"] or 0
            final_score = self._calculate_final_score(
                similarity=similarity,
                boost=success_boost,
                created_at=row["created_at"],
                usage_count=usage_count,
                intent_boost=intent_boost,
            )

            try:
                metadata = json.loads(row["metadata"]) if row["metadata"] else {}
            except:
                metadata = {}

            # Prioritize source_chunk in results for better user language matching
            display_content = row["source_chunk"] if row["source_chunk"] else row["content"]

            result_entry = {
                "id": row["id"],
                "type": row["type"] or "unknown",
                "title": row["title"] or "",
                "content": row["content"] or "",
                "display_content": display_content,
                "preview": display_content[:150] if display_content else "",
                "metadata": metadata,
                "created_at": row["created_at"],
                "similarity": similarity,
                "boost": boost,
                "success_boost": success_boost,
                "intent_boost": intent_boost,
                "boosted_similarity": boosted_similarity,
                "usage_count": usage_count,
                "final_score": final_score,
                "source_chunk": row["source_chunk"],
                "query_type": query_type,
                "threshold_used": adaptive_threshold,
            }
            results_with_scores.append(result_entry)

        # Second pass: If result count is low, use lower threshold
        if len(results_with_scores) < 3:
            min_threshold = 0.20
            seen_ids = {r["id"] for r in results_with_scores}

            for idx, similarity in zip(valid_indices, similarities, strict=False):
                # Skip if already in results or below minimum threshold
                if idx in seen_ids or similarity < min_threshold:
                    continue

                row = rows[idx]

                # Apply boosts
                success_boost = self.get_success_boost(row["id"])
                intent_boost = self._detect_intent_boost(query, row["type"])
                boost = success_boost * intent_boost
                boosted_similarity = similarity * boost

                usage_count = row["usage_count"] or 0
                final_score = self._calculate_final_score(
                    similarity=similarity,
                    boost=success_boost,
                    created_at=row["created_at"],
                    usage_count=usage_count,
                    intent_boost=intent_boost,
                )

                try:
                    metadata = json.loads(row["metadata"]) if row["metadata"] else {}
                except:
                    metadata = {}

                display_content = row["source_chunk"] if row["source_chunk"] else row["content"]

                result_entry = {
                    "id": row["id"],
                    "type": row["type"] or "unknown",
                    "title": row["title"] or "",
                    "content": row["content"] or "",
                    "display_content": display_content,
                    "preview": display_content[:150] if display_content else "",
                    "metadata": metadata,
                    "created_at": row["created_at"],
                    "similarity": similarity,
                    "boost": boost,
                    "success_boost": success_boost,
                    "intent_boost": intent_boost,
                    "boosted_similarity": boosted_similarity,
                    "usage_count": usage_count,
                    "final_score": final_score,
                    "source_chunk": row["source_chunk"],
                    "query_type": query_type,
                    "threshold_used": min_threshold,
                }
                results_with_scores.append(result_entry)
                seen_ids.add(idx)

                # Stop if we have enough results
                if len(results_with_scores) >= limit:
                    break

        # Sort by final score and limit
        results_with_scores.sort(key=lambda x: x["final_score"], reverse=True)
        return results_with_scores[:limit]

    def _search_with_memory_efficient_rag(
        self,
        query: str,
        entry_type: str | None = None,
        limit: int = 5,
        diversity: float | None = None,
    ) -> list[dict]:
        """Search using memory-efficient IVF+PQ compressed index.

        Fast semantic search with 75% memory reduction and 90-95% recall.

        Args:
            query: Search query text
            entry_type: Filter by entry type
            limit: Max results to return
            diversity: MMR diversity parameter (not implemented for compressed index yet)

        Returns:
            List of matching entries with similarity scores

        """
        if not self.enable_semantic or not self._model:
            # Ensure model is loaded
            self._initialize_embedding_model()
            if not self._model:
                return self.search(query, entry_type=entry_type, limit=limit)

        # Generate query embedding
        query_embedding = self._generate_embedding(query)
        if query_embedding is None:
            return self.search(query, entry_type=entry_type, limit=limit)

        query_vec = self._deserialize_embedding(query_embedding)
        if query_vec is None:
            return self.search(query, entry_type=entry_type, limit=limit)

        # Search compressed index
        raw_results = self.memory_efficient_rag.search(
            query_vec,
            k=limit,
            entry_type=entry_type,
        )

        if not raw_results:
            return []

        # Apply CKS-specific scoring (success boost, intent boost, etc.)
        results_with_scores = []
        for result in raw_results:
            entry_id = result["id"]
            similarity = result["similarity"]

            # Apply success boost factor
            success_boost = self.get_success_boost(entry_id)

            # Apply intent boost factor based on query keywords and entry type
            intent_boost = self._detect_intent_boost(query, result["type"])

            # Combine boosts
            boost = success_boost * intent_boost
            boosted_similarity = similarity * boost

            # Calculate final multi-signal score
            usage_count = result.get("usage_count", 0)
            final_score = self._calculate_final_score(
                similarity=similarity,
                boost=boost,
                created_at=result.get("created_at", ""),
                usage_count=usage_count,
                intent_boost=intent_boost,
            )

            # Parse metadata
            try:
                metadata = json.loads(result["metadata"]) if result.get("metadata") else {}
            except:
                metadata = {}

            # Build result object
            results_with_scores.append(
                {
                    "id": entry_id,
                    "type": result["type"],
                    "title": result["title"],
                    "content": result["content"],
                    "source_chunk": result.get("source_chunk", ""),
                    "display_content": result.get("source_chunk") or result["content"],
                    "metadata": metadata,
                    "created_at": result.get("created_at", ""),
                    "similarity": similarity,
                    "boost": boost,
                    "success_boost": success_boost,
                    "intent_boost": intent_boost,
                    "boosted_similarity": boosted_similarity,
                    "usage_count": usage_count,
                    "final_score": final_score,
                    "query_type": "semantic_compressed",
                    "threshold_used": 0.0,  # No threshold for compressed index
                },
            )

        # Sort by final_score and limit
        results_with_scores.sort(key=lambda x: x["final_score"], reverse=True)
        limited_results = results_with_scores[:limit]

        # Record usage for returned entries
        self._record_usage_for_results(limited_results, success=True)

        return limited_results

    def _search_hybrid_temporal(
        self,
        query: str,
        entry_type: str | None = None,
        limit: int = 5,
        recent_days: int = 7,
        diversity: float | None = None,
    ) -> list[dict]:
        """Hybrid search combining recent entries (FTS5) and older entries (compressed index).

        Temporal hybrid approach:
        - Recent entries (< N days): Direct embedding search (always current, fast due to small set)
        - Older entries (>= N days): Compressed IVF+PQ index (fast, memory efficient)
        - Results merged using reciprocal rank fusion

        This ensures newly ingested entries are immediately searchable without index rebuild.

        Args:
            query: Search query text
            entry_type: Filter by entry type
            limit: Max results to return
            recent_days: Days threshold for "recent" entries (default: 7)
            diversity: MMR diversity parameter

        Returns:
            List of matching entries with similarity scores

        """
        from datetime import timedelta

        results_recent: list[dict] = []
        results_older: list[dict] = []

        # Calculate cutoff date
        cutoff_date = (
            datetime.now(UTC).replace(tzinfo=None) - timedelta(days=recent_days)
        ).isoformat()

        # Get recent entries count (to decide if direct search is feasible)
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) as count
            FROM entries
            WHERE embedding IS NOT NULL AND created_at >= ?
            """,
            (cutoff_date,),
        )
        recent_count = cursor.fetchone()["count"]

        # Search recent entries if available
        if recent_count > 0:
            results_recent = self._search_recent_embeddings(
                query=query,
                entry_type=entry_type,
                cutoff_date=cutoff_date,
                limit=limit * 2,  # Fetch more for better fusion
            )

        # Search older entries with compressed index
        if self.enable_memory_efficient_rag and self.memory_efficient_rag:
            results_older = self._search_older_compressed(
                query=query,
                entry_type=entry_type,
                cutoff_date=cutoff_date,
                limit=limit * 2,
            )

        # Merge results using reciprocal rank fusion
        merged = self._merge_hybrid_results(
            results_recent=results_recent,
            results_older=results_older,
            limit=limit,
        )

        # Record usage for returned entries
        self._record_usage_for_results(merged, success=True)

        return merged

    def _search_recent_embeddings(
        self,
        query: str,
        entry_type: str | None,
        cutoff_date: str,
        limit: int = 10,
    ) -> list[dict]:
        """Search recent entries using direct embedding computation.

        Fast enough for recent entries because the set is small (< 1000 typically).
        Ensures newly ingested entries are immediately searchable.

        Args:
            query: Search query text
            entry_type: Filter by entry type
            cutoff_date: ISO date string for "recent" threshold
            limit: Max results to return

        Returns:
            List of matching entries with similarity scores

        """
        if not self.enable_semantic or not self._model:
            self._initialize_embedding_model()
            if not self._model:
                return []

        # Generate query embedding
        query_embedding = self._generate_embedding(query)
        if query_embedding is None:
            return []

        query_vec = self._deserialize_embedding(query_embedding)
        if query_vec is None:
            return []

        # Get recent entries with embeddings
        cursor = self.conn.cursor()
        if entry_type:
            cursor.execute(
                """
                SELECT id, type, title, content, metadata, created_at, embedding, usage_count, source_chunk
                FROM entries
                WHERE type = ? AND embedding IS NOT NULL AND created_at >= ?
                """,
                (entry_type, cutoff_date),
            )
        else:
            cursor.execute(
                """
                SELECT id, type, title, content, metadata, created_at, embedding, usage_count, source_chunk
                FROM entries
                WHERE embedding IS NOT NULL AND created_at >= ?
                """,
                (cutoff_date,),
            )

        rows = cursor.fetchall()
        if not rows:
            return []

        # Compute cosine similarity for recent entries
        query_norm = self._np.linalg.norm(query_vec)
        if query_norm == 0:
            return []

        results_with_scores = []
        for row in rows:
            entry_vec = self._deserialize_embedding(row["embedding"])
            if entry_vec is None:
                continue

            # Cosine similarity
            similarity = self._np.dot(query_vec, entry_vec) / (
                query_norm * self._np.linalg.norm(entry_vec) + 1e-8
            )

            # Filter by threshold
            if similarity < 0.20:  # Lower threshold for recent entries (inclusive)
                continue

            # Apply boosts
            entry_id = row["id"]
            success_boost = self.get_success_boost(entry_id)
            intent_boost = self._detect_intent_boost(query, row["type"])
            boost = success_boost * intent_boost
            boosted_similarity = similarity * boost

            # Calculate final score
            usage_count = row["usage_count"] or 0
            final_score = self._calculate_final_score(
                similarity=similarity,
                boost=boost,
                created_at=row["created_at"],
                usage_count=usage_count,
                intent_boost=intent_boost,
            )

            # Parse metadata
            try:
                metadata = json.loads(row["metadata"]) if row["metadata"] else {}
            except:
                metadata = {}

            results_with_scores.append(
                {
                    "id": entry_id,
                    "type": row["type"],
                    "title": row["title"],
                    "content": row["content"],
                    "source_chunk": row["source_chunk"] or "",
                    "display_content": row["source_chunk"] or row["content"],
                    "metadata": metadata,
                    "created_at": row["created_at"],
                    "similarity": similarity,
                    "boost": boost,
                    "success_boost": success_boost,
                    "intent_boost": intent_boost,
                    "boosted_similarity": boosted_similarity,
                    "usage_count": usage_count,
                    "final_score": final_score,
                    "query_type": "semantic_recent",
                    "threshold_used": 0.20,
                },
            )

        # Sort and limit
        results_with_scores.sort(key=lambda x: x["final_score"], reverse=True)
        return results_with_scores[:limit]

    def _search_older_compressed(
        self,
        query: str,
        entry_type: str | None,
        cutoff_date: str,
        limit: int = 10,
    ) -> list[dict]:
        """Search older entries using compressed IVF+PQ index.

        Args:
            query: Search query text
            entry_type: Filter by entry type
            cutoff_date: ISO date string for "recent" threshold (older = < cutoff_date)
            limit: Max results to return

        Returns:
            List of matching entries with similarity scores

        """
        if not self.enable_semantic or not self._model:
            self._initialize_embedding_model()
            if not self._model:
                return []

        # Generate query embedding
        query_embedding = self._generate_embedding(query)
        if query_embedding is None:
            return []

        query_vec = self._deserialize_embedding(query_embedding)
        if query_vec is None:
            return []

        # Search compressed index
        raw_results = self.memory_efficient_rag.search(
            query_vec,
            k=limit * 5,  # Fetch more, then filter by date
            entry_type=entry_type,
        )

        if not raw_results:
            return []

        # Filter to only older entries and apply CKS scoring
        results_with_scores = []
        for result in raw_results:
            created_at = result.get("created_at", "")
            # Skip if entry is recent (belongs to recent search)
            if created_at >= cutoff_date:
                continue

            entry_id = result["id"]
            similarity = result["similarity"]

            # Apply boosts
            success_boost = self.get_success_boost(entry_id)
            intent_boost = self._detect_intent_boost(query, result["type"])
            boost = success_boost * intent_boost
            boosted_similarity = similarity * boost

            # Calculate final score
            usage_count = result.get("usage_count", 0)
            final_score = self._calculate_final_score(
                similarity=similarity,
                boost=boost,
                created_at=created_at,
                usage_count=usage_count,
                intent_boost=intent_boost,
            )

            # Parse metadata
            try:
                metadata = json.loads(result["metadata"]) if result.get("metadata") else {}
            except:
                metadata = {}

            results_with_scores.append(
                {
                    "id": entry_id,
                    "type": result["type"],
                    "title": result["title"],
                    "content": result["content"],
                    "source_chunk": result.get("source_chunk", ""),
                    "display_content": result.get("source_chunk") or result["content"],
                    "metadata": metadata,
                    "created_at": created_at,
                    "similarity": similarity,
                    "boost": boost,
                    "success_boost": success_boost,
                    "intent_boost": intent_boost,
                    "boosted_similarity": boosted_similarity,
                    "usage_count": usage_count,
                    "final_score": final_score,
                    "query_type": "semantic_compressed",
                    "threshold_used": 0.0,
                },
            )

        # Sort and limit
        results_with_scores.sort(key=lambda x: x["final_score"], reverse=True)
        return results_with_scores[:limit]

    def _merge_hybrid_results(
        self,
        results_recent: list[dict],
        results_older: list[dict],
        limit: int = 5,
    ) -> list[dict]:
        """Merge results from recent and older searches using reciprocal rank fusion.

        Args:
            results_recent: Results from recent entry search
            results_older: Results from older entry search (compressed index)
            limit: Max results to return

        Returns:
            Merged and re-ranked results

        """
        # Reciprocal Rank Fusion constant
        k = 60

        # Score aggregation
        scores: dict[str, float] = {}
        entry_data: dict[str, dict] = {}

        # Score recent results
        for rank, result in enumerate(results_recent, 1):
            entry_id = result["id"]
            rrf_score = 1.0 / (k + rank)
            scores[entry_id] = scores.get(entry_id, 0) + rrf_score
            entry_data[entry_id] = result
            entry_data[entry_id]["rrf_score"] = rrf_score
            entry_data[entry_id]["source"] = "recent"

        # Score older results
        for rank, result in enumerate(results_older, 1):
            entry_id = result["id"]
            rrf_score = 1.0 / (k + rank)
            scores[entry_id] = scores.get(entry_id, 0) + rrf_score
            if entry_id not in entry_data:
                entry_data[entry_id] = result
            entry_data[entry_id]["rrf_score"] = scores[entry_id]
            if entry_id in results_recent:
                entry_data[entry_id]["source"] = "both"
            else:
                entry_data[entry_id]["source"] = "older"

        # Sort by RRF score
        sorted_entries = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # Build final results
        final_results = []
        for entry_id, rrf_score in sorted_entries[:limit]:
            result = entry_data[entry_id].copy()
            result["rrf_score"] = rrf_score
            result["final_score"] = rrf_score  # Use RRF score as final for hybrid
            result["query_type"] = "semantic_hybrid"
            final_results.append(result)

        return final_results

    def _apply_auto_learning_if_enabled(
        self,
        results: list[dict],
        query: str,
    ) -> list[dict]:
        """Apply auto-learning to search results if enabled.

        Detects unknown terms, extracts definitions from results,
        and persists new abbreviation mappings to query_expansion.py.

        Args:
            results: Search results with similarity scores
            query: Original search query

        Returns:
            Results with additional auto_learning metadata if learning occurred

        """
        if not self.enable_auto_learning:
            return results

        # Only trigger auto-learning if search results are poor (low average similarity)
        if not results:
            return results

        avg_similarity = sum(r.get("similarity", 0) for r in results) / len(results)
        if avg_similarity >= self.auto_learning_threshold:  # Good results, no learning needed
            return results

        # Initialize auto-learning expander lazily
        if self._auto_learning_expander is None:
            self._auto_learning_expander = AutoLearningQueryExpander(
                dry_run=False,
                cks_path=Path(__file__).parent,
            )

        # Run auto-learning
        learning_response = self._auto_learning_expander.search_and_learn(
            query=query,
            results=results,
            cks_client=self,
        )

        # Add learning metadata to results if anything was learned
        if learning_response.get("learned_mappings"):
            results = list(results)  # Make a mutable copy
            if results:
                # Add metadata to the first result
                results[0]["auto_learning"] = {
                    "unknown_terms": learning_response.get("unknown_terms", []),
                    "learned_mappings": learning_response.get("learned_mappings", []),
                    "suggestions": learning_response.get("suggestions", []),
                }

        return results

    def _search_semantic_phase1(
        self,
        query: str,
        original_query: str,
        entry_type: str | None = None,
        limit: int = 5,
        expand_query: bool = False,
        fusion_method: str | None = None,
        diversity: float | None = None,
        entity_slug: str | None = None,
    ) -> list[dict]:
        """Phase 1 enhanced semantic search with query expansion and fusion.

        Args:
            query: Search query text
            entry_type: Filter by type (optional)
            limit: Max results to return
            expand_query: Enable query expansion
            fusion_method: 'rrf' for Reciprocal Rank Fusion
            diversity: MMR diversity parameter (0=relevance, 1=diversity)
            entity_slug: Entity for domain-specific expansion

        Returns:
            Enhanced list of matching entries

        """
        if not self.enable_semantic:
            return self.search(query, entry_type=entry_type, limit=limit)

        # Step 1: Query expansion
        if expand_query and PHASE1_AVAILABLE:
            expander = QueryExpander()
            queries = expander.expand_query(
                query,
                entity_slug=entity_slug,
                max_variations=5,
            )
        else:
            queries = [query]

        # Step 2: Search for each query variation
        all_result_sets = []
        for q in queries:
            # Use the base search_semantic logic for each query
            # Temporarily disable Phase 1 to avoid recursion
            results = self._search_semantic_base(q, entry_type, limit * 2)
            all_result_sets.append(results)

        # Step 3: Fusion with RRF
        if fusion_method == "rrf" and len(all_result_sets) > 1:
            merged = reciprocal_rank_fusion(all_result_sets, k=60, limit=limit * 2)
        elif len(all_result_sets) == 1:
            merged = all_result_sets[0]
        else:
            # Simple merge without fusion
            merged = SearchResultsMerger.merge_results(all_result_sets, merge_strategy="score")

        # Step 4: Apply MMR diversity if requested
        if diversity is not None and PHASE1_AVAILABLE:
            merged = maximal_marginal_relevance(
                query=query,
                results=merged,
                lambda_param=diversity,
                limit=limit * 2,
            )

        # Step 5: Apply enhanced temporal boosting if available
        if PHASE1_AVAILABLE:
            for result in merged:
                if "created_at" in result:
                    boost = calculate_temporal_boost(result, base_boost=1.0)
                    result["final_score"] = (
                        result.get("final_score", result.get("similarity", 0)) * boost
                    )

        # Sort by final_score and limit
        merged.sort(key=lambda x: x.get("final_score", x.get("similarity", 0)), reverse=True)
        return merged[:limit]

    def _search_semantic_base(
        self,
        query: str,
        entry_type: str | None = None,
        limit: int = 5,
    ) -> list[dict]:
        """Base semantic search without Phase 1 features (internal helper).

        This is the original search_semantic logic extracted to avoid recursion.
        """
        # Detect query type and get adaptive threshold
        query_type = self._detect_query_type(query)
        adaptive_threshold = QUERY_TYPE_THRESHOLDS[query_type]

        # Lazy-load model on first semantic search
        if not self._model_loaded:
            self._initialize_embedding_model()
            self._model_loaded = True

        # Generate query embedding
        query_embedding = self._generate_embedding(query)
        if query_embedding is None:
            return self.search(query, entry_type=entry_type, limit=limit)

        query_vec = self._deserialize_embedding(query_embedding)
        if query_vec is None:
            return self.search(query, entry_type=entry_type, limit=limit)

        # Get all entries with embeddings and usage stats
        cursor = self.conn.cursor()

        if entry_type:
            cursor.execute(
                """
                SELECT id, type, title, content, metadata, created_at, embedding, usage_count, source_chunk
                FROM entries
                WHERE type = ? AND embedding IS NOT NULL
            """,
                (entry_type,),
            )
        else:
            cursor.execute("""
                SELECT id, type, title, content, metadata, created_at, embedding, usage_count, source_chunk
                FROM entries
                WHERE embedding IS NOT NULL
            """)

        # Vectorized cosine similarity computation (10-50x faster)
        rows = cursor.fetchall()
        if not rows:
            return []

        # Batch load all embeddings into matrix
        valid_indices = []
        embeddings_list = []
        for i, row in enumerate(rows):
            entry_vec = self._deserialize_embedding(row["embedding"])
            if entry_vec is not None:
                valid_indices.append(i)
                embeddings_list.append(entry_vec)

        if not embeddings_list:
            return []

        # Stack into matrix for vectorized computation
        embeddings_matrix = self._np.stack(embeddings_list)

        # Vectorized cosine similarity: (query_vec @ entries.T) / (||query|| * ||entries||)
        query_norm = self._np.linalg.norm(query_vec)
        if query_norm == 0:
            return []

        # Compute all similarities at once using matrix operations
        dot_products = embeddings_matrix @ query_vec  # Shape: (n_entries,)
        entry_norms = self._np.linalg.norm(embeddings_matrix, axis=1)
        similarities = dot_products / (query_norm * entry_norms + 1e-8)

        # Priority 2: Two-pass filtering with adaptive threshold
        # First pass: Use default threshold
        results_with_scores = []
        for idx, similarity in zip(valid_indices, similarities, strict=False):
            # Filter by default threshold
            if similarity < adaptive_threshold:
                continue

            row = rows[idx]

            # Apply success boost factor
            success_boost = self.get_success_boost(row["id"])

            # Apply intent boost factor based on query keywords and entry type
            intent_boost = self._detect_intent_boost(query, row["type"])

            # Combine boosts
            boost = success_boost * intent_boost
            boosted_similarity = similarity * boost

            # Calculate final multi-signal score
            usage_count = row["usage_count"] or 0
            final_score = self._calculate_final_score(
                similarity=similarity,
                boost=success_boost,
                created_at=row["created_at"],
                usage_count=usage_count,
                intent_boost=intent_boost,
            )

            try:
                metadata = json.loads(row["metadata"]) if row["metadata"] else {}
            except:
                metadata = {}

            # Prioritize source_chunk in results for better user language matching
            display_content = row["source_chunk"] if row["source_chunk"] else row["content"]

            result_entry = {
                "id": row["id"],
                "type": row["type"] or "unknown",
                "title": row["title"] or "",
                "content": row["content"] or "",
                "display_content": display_content,
                "preview": display_content[:150] if display_content else "",
                "metadata": metadata,
                "created_at": row["created_at"],
                "similarity": similarity,
                "boost": boost,
                "success_boost": success_boost,
                "intent_boost": intent_boost,
                "boosted_similarity": boosted_similarity,
                "usage_count": usage_count,
                "final_score": final_score,
                "source_chunk": row["source_chunk"],
                "query_type": query_type,
                "threshold_used": adaptive_threshold,
            }
            results_with_scores.append(result_entry)

        # Second pass: If result count is low, use lower threshold
        if len(results_with_scores) < 3:
            min_threshold = 0.20
            seen_ids = {r["id"] for r in results_with_scores}

            for idx, similarity in zip(valid_indices, similarities, strict=False):
                # Skip if already in results or below minimum threshold
                if idx in seen_ids or similarity < min_threshold:
                    continue

                row = rows[idx]

                # Apply boosts
                success_boost = self.get_success_boost(row["id"])
                intent_boost = self._detect_intent_boost(query, row["type"])
                boost = success_boost * intent_boost
                boosted_similarity = similarity * boost

                usage_count = row["usage_count"] or 0
                final_score = self._calculate_final_score(
                    similarity=similarity,
                    boost=success_boost,
                    created_at=row["created_at"],
                    usage_count=usage_count,
                    intent_boost=intent_boost,
                )

                try:
                    metadata = json.loads(row["metadata"]) if row["metadata"] else {}
                except:
                    metadata = {}

                display_content = row["source_chunk"] if row["source_chunk"] else row["content"]

                result_entry = {
                    "id": row["id"],
                    "type": row["type"] or "unknown",
                    "title": row["title"] or "",
                    "content": row["content"] or "",
                    "display_content": display_content,
                    "preview": display_content[:150] if display_content else "",
                    "metadata": metadata,
                    "created_at": row["created_at"],
                    "similarity": similarity,
                    "boost": boost,
                    "success_boost": success_boost,
                    "intent_boost": intent_boost,
                    "boosted_similarity": boosted_similarity,
                    "usage_count": usage_count,
                    "final_score": final_score,
                    "source_chunk": row["source_chunk"],
                    "query_type": query_type,
                    "threshold_used": min_threshold,
                }
                results_with_scores.append(result_entry)
                seen_ids.add(idx)

                # Stop if we have enough results
                if len(results_with_scores) >= limit:
                    break

        # Sort by final score and limit
        results_with_scores.sort(key=lambda x: x["final_score"], reverse=True)
        return results_with_scores[:limit]

    def _record_usage_for_results(self, results: list[dict], success: bool = True) -> None:
        """Record usage for all returned results.

        Args:
            results: List of entry results
            success: Whether the usage was successful

        """
        if not results:
            return

        entry_ids = [r.get("id") for r in results if r.get("id")]
        if not entry_ids:
            return

        try:
            cursor = self.conn.cursor()
            # Batch update for efficiency
            placeholders = ",".join(["(?)"] * len(entry_ids))
            success_increment = 1 if success else 0

            cursor.execute(
                f"""
                UPDATE entries
                SET usage_count = usage_count + 1,
                    success_count = success_count + ?
                WHERE id IN ({placeholders})
                """,
                [success_increment, *entry_ids],
            )
            self.conn.commit()
        except Exception as e:
            # Log but don't fail the search
            print(f"⚠️ Failed to record usage: {e}")

    def record_usage(self, entry_id: str, success: bool = True) -> bool:
        """Record usage of an entry for self-improvement tracking.

        Args:
            entry_id: ID of the entry to record usage for
            success: Whether the usage was successful (default: True)

        Returns:
            True if usage recorded successfully, False otherwise

        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                UPDATE entries
                SET usage_count = usage_count + 1,
                    success_count = success_count + ?
                WHERE id = ?
            """,
                (1 if success else 0, entry_id),
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"⚠️ Failed to record usage for {entry_id}: {e}")
            return False

    def record_feedback(self, entry_id: str, feedback: str) -> bool:
        """Record feedback on an entry (Enhancement 5).

        Args:
            entry_id: ID of the entry
            feedback: "up" or "down"

        Returns:
            True if feedback recorded, False otherwise

        """
        if feedback not in ("up", "down"):
            return False

        column = "thumbs_up" if feedback == "up" else "thumbs_down"

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                f"""
                UPDATE entries
                SET {column} = {column} + 1
                WHERE id = ?
            """,
                (entry_id,),
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"⚠️ Failed to record feedback for {entry_id}: {e}")
            return False

    def update_usage_count(self, entry_id: str) -> bool:
        """Increment usage_count for an entry (for feedback loop tracking).

        Called when a memory is injected into a prompt, to track usage
        independent of success/failure outcomes.

        Args:
            entry_id: ID of the entry to update

        Returns:
            True if updated successfully, False otherwise

        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                UPDATE entries
                SET usage_count = usage_count + 1
                WHERE id = ?
            """,
                (entry_id,),
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"⚠️ Failed to update usage_count for {entry_id}: {e}")
            return False

    def get_success_boost(self, entry_id: str) -> float:
        """Calculate success boost factor for an entry based on usage history (Enhancement 5).

        Combines implicit success rate (70%) with explicit feedback (30%).

        Args:
            entry_id: ID of the entry

        Returns:
            Boost factor (1.0 = neutral, >1.0 = successful, <1.0 = unsuccessful)

        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT usage_count, success_count, thumbs_up, thumbs_down
                FROM entries
                WHERE id = ?
            """,
                (entry_id,),
            )

            row = cursor.fetchone()
            if not row:
                return 1.0

            usage_count = row["usage_count"] or 0
            success_count = row["success_count"] or 0
            thumbs_up = row["thumbs_up"] or 0
            thumbs_down = row["thumbs_down"] or 0

            if usage_count == 0:
                return 1.0

            # Calculate implicit success rate (70% weight)
            implicit_rate = success_count / usage_count

            # Calculate explicit feedback score (30% weight)
            total_feedback = thumbs_up + thumbs_down
            if total_feedback > 0:
                feedback_score = thumbs_up / total_feedback
            else:
                feedback_score = 0.5  # Neutral when no feedback

            # Blend implicit and explicit signals
            success_rate = (implicit_rate * 0.7) + (feedback_score * 0.3)

            # Boost formula: +10% per successful use, max +50%
            # Penalty: -10% per failure, max -50%
            boost = 1.0 + (success_rate - 0.5) * 0.1 * usage_count
            return max(0.5, min(1.5, boost))  # Clamp between 0.5x and 1.5x

        except Exception as e:
            print(f"⚠️ Failed to calculate boost for {entry_id}: {e}")
            return 1.0

    def backfill_embeddings(self, batch_size: int = 100) -> dict[str, int]:
        """Generate embeddings for existing entries that don't have them.

        Args:
            batch_size: Number of entries to process per batch

        Returns:
            Dictionary with counts: {total, backfilled, skipped, errors}

        """
        if not self.enable_semantic:
            print("⚠️ Semantic search not enabled, cannot backfill embeddings")
            return {"total": 0, "backfilled": 0, "skipped": 0, "errors": 0}

        cursor = self.conn.cursor()

        # Count entries without embeddings
        cursor.execute("SELECT COUNT(*) FROM entries WHERE embedding IS NULL")
        total_to_backfill = cursor.fetchone()[0]

        if total_to_backfill == 0:
            print("✅ All entries already have embeddings")
            return {"total": 0, "backfilled": 0, "skipped": 0, "errors": 0}

        print(f"🔄 Backfilling embeddings for {total_to_backfill} entries...")

        # Get entries without embeddings (include source_chunk for better embeddings)
        cursor.execute(
            """
            SELECT id, content, source_chunk FROM entries WHERE embedding IS NULL
            LIMIT ?
        """,
            (batch_size,),
        )

        backfilled = 0
        skipped = 0
        errors = 0

        for row in cursor.fetchall():
            entry_id = row["id"]
            # Use source_chunk for embedding if available, otherwise fall back to content
            text_to_embed = row["source_chunk"] if row["source_chunk"] else row["content"]

            # Generate embedding
            embedding = self._generate_embedding(text_to_embed)

            if embedding is not None:
                try:
                    # Update entry with embedding
                    cursor.execute(
                        """
                        UPDATE entries SET embedding = ? WHERE id = ?
                    """,
                        (embedding, entry_id),
                    )
                    backfilled += 1
                except Exception as e:
                    print(f"⚠️ Error updating {entry_id}: {e}")
                    errors += 1
            else:
                skipped += 1

        self.conn.commit()

        result = {
            "total": total_to_backfill,
            "backfilled": backfilled,
            "skipped": skipped,
            "errors": errors,
            "remaining": max(0, total_to_backfill - backfilled),
        }

        print(f"✅ Backfilled {backfilled} entries ({result['remaining']} remaining)")
        return result

    def get_statistics(self) -> dict[str, Any]:
        """Get CKS statistics."""
        cursor = self.conn.cursor()

        stats = {}
        cursor.execute("SELECT type, COUNT(*) FROM entries GROUP BY type")
        stats["by_type"] = dict(cursor.fetchall())
        cursor.execute("SELECT COUNT(*) FROM entries")
        stats["total_entries"] = cursor.fetchone()[0]
        stats["database_size_bytes"] = self.db_path.stat().st_size

        return stats

    # ========================================================================
    # Temporal Query Methods
    # ========================================================================

    def query_by_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
        limit: int = 100,
    ) -> list[dict]:
        """Query entries within a specific time range.

        Args:
            start_time: Start of time range (inclusive)
            end_time: End of time range (inclusive)
            limit: Maximum number of results to return

        Returns:
            List of entry dictionaries within the specified time range

        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, type, title, content, metadata, created_at, updated_at
            FROM entries
            WHERE created_at >= ? AND created_at <= ?
            ORDER BY created_at ASC
            LIMIT ?
            """,
            (start_time.isoformat(), end_time.isoformat(), limit),
        )

        results = []
        for row in cursor.fetchall():
            results.append(
                {
                    "id": row["id"],
                    "type": row["type"],
                    "title": row["title"],
                    "content": row["content"],
                    "metadata": row["metadata"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                },
            )
        return results

    def query_evolution_by_topic(
        self,
        topic: str,
        limit: int = 100,
    ) -> list[dict]:
        """Query how understanding evolved for a specific topic over time.

        Args:
            topic: Topic to search for (searched in title, content, metadata)
            limit: Maximum number of results to return

        Returns:
            List of entry dictionaries showing chronological evolution

        """
        cursor = self.conn.cursor()
        search_pattern = f"%{topic}%"
        cursor.execute(
            """
            SELECT id, type, title, content, metadata, created_at, updated_at
            FROM entries
            WHERE title LIKE ? OR content LIKE ? OR metadata LIKE ?
            ORDER BY created_at ASC
            LIMIT ?
            """,
            (search_pattern, search_pattern, search_pattern, limit),
        )

        results = []
        for row in cursor.fetchall():
            results.append(
                {
                    "id": row["id"],
                    "type": row["type"],
                    "title": row["title"],
                    "content": row["content"],
                    "metadata": row["metadata"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                },
            )
        return results

    def query_beliefs_at_time(
        self,
        target_time: datetime,
        limit: int = 100,
    ) -> list[dict]:
        """Query what was believed at a specific point in time.

        Returns all entries that existed at or before the target time.

        Args:
            target_time: Point in time to query beliefs for
            limit: Maximum number of results to return

        Returns:
            List of entry dictionaries that existed at or before target time

        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, type, title, content, metadata, created_at, updated_at
            FROM entries
            WHERE created_at <= ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (target_time.isoformat(), limit),
        )

        results = []
        for row in cursor.fetchall():
            results.append(
                {
                    "id": row["id"],
                    "type": row["type"],
                    "title": row["title"],
                    "content": row["content"],
                    "metadata": row["metadata"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                },
            )
        return results

    def query_conflicts_over_time(
        self,
        topic: str,
        limit: int = 100,
    ) -> list[dict]:
        """Query for conflicts/contradictions on a topic over time.

        Searches for entries related to a topic to identify potential
        contradictions or evolving positions.

        Args:
            topic: Topic to search for conflicts in
            limit: Maximum number of results to return

        Returns:
            List of entry dictionaries showing potential conflicts over time

        """
        cursor = self.conn.cursor()
        search_pattern = f"%{topic}%"
        cursor.execute(
            """
            SELECT id, type, title, content, metadata, created_at, updated_at
            FROM entries
            WHERE title LIKE ? OR content LIKE ? OR metadata LIKE ?
            ORDER BY created_at ASC
            LIMIT ?
            """,
            (search_pattern, search_pattern, search_pattern, limit),
        )

        results = []
        for row in cursor.fetchall():
            results.append(
                {
                    "id": row["id"],
                    "type": row["type"],
                    "title": row["title"],
                    "content": row["content"],
                    "metadata": row["metadata"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                },
            )
        return results

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# ========================================================================
# Hybrid Search Integration (Anthropic Contextual Retrieval)
# ========================================================================

# Apply hybrid search patch if Phase 2 is available
# This makes hybrid search (FTS5 + semantic fusion) the default
if PHASE2_AVAILABLE:
    try:
        CKS = patch_hybrid_search(CKS)
    except Exception as e:
        print(f"⚠️ Hybrid search patch failed: {e}")

# Apply optimized search patch (adds query expansion and MMR)
# This enhances the default search with all available optimizations
if PHASE2_AVAILABLE:
    try:
        CKS = patch_optimized_search(CKS)
    except Exception as e:
        print(f"⚠️ Optimized search patch failed: {e}")


# ========================================================================
# Migration Functions
# ========================================================================


def migrate_from_legacy(source_db_paths: list[Path]) -> dict[str, int]:
    """Migrate data from legacy CKS databases to unified CKS.

    Args:
        source_db_paths: List of paths to legacy databases

    Returns:
        Dictionary with migration counts by type

    """
    cks = CKS()

    counts = {"memory": 0, "pattern": 0, "knowledge": 0, "code": 0, "total": 0}

    for source_path in source_db_paths:
        if not source_path.exists():
            print(f"⚠️ Skipping non-existent database: {source_path}")
            continue

        print(f"📦 Migrating from: {source_path}")

        try:
            # Connect to source database
            source_conn = sqlite3.connect(str(source_path))
            source_conn.row_factory = sqlite3.Row
            source_cursor = source_conn.cursor()

            # Check for memories table (legacy cks.db)
            source_cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='memories'",
            )
            if source_cursor.fetchone():
                print("  → Found memories table")
                source_cursor.execute("SELECT * FROM memories")
                for row in source_cursor.fetchall():
                    # Extract metadata
                    try:
                        metadata = json.loads(row["metadata"]) if row["metadata"] else {}
                    except:
                        metadata = {}

                    # Ingest as memory
                    cks.ingest_memory(
                        question=row["question"] or "N/A",
                        answer=row["answer"] or "",
                        **metadata,
                    )
                    counts["memory"] += 1
                    counts["total"] += 1

                print(f"    Migrated {counts['memory']} memories")

            # Check for knowledge_nodes table (cks_hypergraph)
            source_cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='knowledge_nodes'",
            )
            if source_cursor.fetchone():
                print("  → Found knowledge_nodes table")
                source_cursor.execute("SELECT * FROM knowledge_nodes")

                for row in source_cursor.fetchall():
                    # Extract metadata
                    try:
                        metadata = json.loads(row["metadata"]) if row["metadata"] else {}
                    except:
                        metadata = {}

                    # Determine type based on category
                    category = metadata.get("category", "").lower()
                    title_from_meta = metadata.get("title", row["type"] or "Knowledge")
                    content = row["content"]

                    if "pattern" in category:
                        cks.ingest_pattern(
                            title=title_from_meta,
                            content=content,
                        )
                        counts["pattern"] += 1
                    else:
                        cks.ingest_pattern(
                            title=title_from_meta,
                            content=content,
                            type="knowledge",
                        )
                        counts["knowledge"] += 1

                    counts["total"] += 1

                print(f"    Migrated {counts['pattern'] + counts['knowledge']} knowledge entries")

            source_conn.close()

        except Exception as e:
            print(f"❌ Error migrating {source_path}: {e}")

    cks.close()

    return counts


# ========================================================================
# Convenience Functions
# ========================================================================


def get_cks() -> CKS:
    """Get CKS instance with default path."""
    return CKS()


def ingest_memory(question: str, answer: str, source_chunk: str | None = None, **metadata) -> str:
    """Quick memory ingestion."""
    with get_cks() as cks:
        return cks.ingest_memory(question, answer, source_chunk=source_chunk, **metadata)


def ingest_pattern(title: str, content: str, source_chunk: str | None = None, **metadata) -> str:
    """Quick pattern ingestion."""
    with get_cks() as cks:
        return cks.ingest_pattern(title, content, source_chunk=source_chunk, **metadata)


def search(query: str, entry_type: str | None = None, limit: int = 5) -> list[dict]:
    """Quick search."""
    with get_cks() as cks:
        return cks.search(query, entry_type=entry_type, limit=limit)


def search_semantic(
    query: str,
    entry_type: str | None = None,
    limit: int = 5,
    expand_query: bool = False,
    fusion_method: str | None = None,
    diversity: float | None = None,
) -> list[dict]:
    """Semantic search (similarity-based, not keyword matching).

    Finds relevant results even when words don't match.

    Args:
        query: Search query
        entry_type: Optional entry type filter
        limit: Max results
        expand_query: Expand query with synonyms/abbreviations
        fusion_method: Fusion method (e.g., 'rrf' for reciprocal rank fusion)
        diversity: Diversity penalty for MMR (0-1, higher = more diversity)

    Returns:
        List of matching entries with similarity scores

    """
    with get_cks() as cks:
        return cks.search_semantic(
            query=query,
            entry_type=entry_type,
            limit=limit,
            expand_query=expand_query,
            fusion_method=fusion_method,
            diversity=diversity,
        )


def ingest_correction(title: str, content: str, **metadata) -> str:
    """Quick correction ingestion (mistake and fix)."""
    with get_cks() as cks:
        return cks.ingest_correction(title, content, **metadata)


def ingest_decision(title: str, content: str, **metadata) -> str:
    """Quick decision ingestion (choice made and rationale)."""
    with get_cks() as cks:
        return cks.ingest_decision(title, content, **metadata)


def ingest_commitment(title: str, content: str, **metadata) -> str:
    """Quick commitment ingestion (promise or resolution)."""
    with get_cks() as cks:
        return cks.ingest_commitment(title, content, **metadata)


def ingest_insight(title: str, content: str, **metadata) -> str:
    """Quick insight ingestion (realization or aha moment)."""
    with get_cks() as cks:
        return cks.ingest_insight(title, content, **metadata)


def ingest_learning(title: str, content: str, **metadata) -> str:
    """Quick learning ingestion (lesson learned)."""
    with get_cks() as cks:
        return cks.ingest_learning(title, content, **metadata)


# ========================================================================
# Apply Search Optimizations
# ========================================================================

try:
    from .optimized_search import patch_optimized_search

    # Patch CKS to use optimized search by default
    # This adds: query expansion, hybrid search, MMR diversification
    CKS = patch_optimized_search(CKS)
except ImportError as e:
    import warnings

    warnings.warn(f"CKS search optimizations unavailable: {e}")
