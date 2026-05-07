import gc
import json
import logging
import os
import sqlite3
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import psutil

from ..utils.constitutional_validator import ConstitutionalValidator

"""CKS Storage Manager - Multi-graph storage with SQLite + PyTorch integration.

Constitutional Requirements:
- Solo developer optimization (zero background services)
- Evidence-based implementation (TDD approach)
- Force multiplier integration (multi-graph capability)
- No enterprise bloat (simple, direct implementation)

Architecture:
Phase 1: Single PC deployment, no clustering
- On-demand processing (no background services)
- GPU acceleration with CPU fallback
- Direct Python integration (no MCP)
- Constitutional compliance mandatory

Implementation:
1. Multi-graph storage (Knowledge, Vector, Causal, Social, System)
2. SQLite for structured knowledge storage
3. PyTorch for vector embeddings with GPU support
4. Cross-graph relationship tracking
5. Memory management and cleanup
6. Constitutional validation integration
"""


# Import PyTorch adapter for FAISS compatibility
try:
    from .faiss_pytorch_adapter import FaissToPyTorchAdapter, IndexFlatIP

    FAISS_AVAILABLE = True
    PYTORCH_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    PYTORCH_AVAILABLE = False
    logging.warning("PyTorch adapter not available - vector operations will be limited")


@dataclass
class StorageConfig:
    """Configuration for CKS storage system.

    Constitutional Requirements:
    - Solo developer optimized defaults
    - Conservative resource usage
    - GPU with CPU fallback
    """

    db_path: str = field(
        default_factory=lambda: os.path.expanduser("P:\\\\__csf/data/cks.db"),
    )
    faiss_index_path: str = field(
        default_factory=lambda: os.path.expanduser("~/.cks/storage/vectors.index"),
    )
    enable_gpu: bool = True
    max_memory_mb: int = 4096  # Conservative for solo developer
    vector_dimension: int = 768  # Standard embedding size
    batch_size: int = 1000
    audit_trail_enabled: bool = True
    auto_cleanup: bool = True

    def __post_init__(self):
        """Validate configuration parameters."""
        if self.max_memory_mb <= 0:
            raise ValueError("max_memory_mb must be positive")
        if self.vector_dimension <= 0:
            raise ValueError("vector_dimension must be positive")
        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive")

        # Ensure directories exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.faiss_index_path), exist_ok=True)


class StorageManager:
    """Core storage manager for CKS multi-graph system.

    Algorithm Approach: Multi-graph storage with SQLite + FAISS integration
    combining structured data storage with vector similarity search.

    Time Complexity:
    - Node/Edge operations: O(1) for indexed queries
    - Vector operations: O(log n) for FAISS search
    - Cross-graph queries: O(k) where k is number of relationships

    Space Complexity:
    - SQLite: O(n) where n is number of nodes/edges
    - FAISS: O(n * d) where n is vectors, d is dimension
    - Memory: Configurable with cleanup mechanisms

    Constitutional Features:
    - Solo developer optimization (no clustering, simple interfaces)
    - Evidence-based operations (audit trails, validation)
    - Force multiplier (multi-graph integration)
    - No enterprise bloat (direct Python implementation)
    """

    def __init__(self, config: StorageConfig) -> None:
        """Initialize storage manager with configuration."""
        self.config = config
        self.db_connection: sqlite3.Connection | None = None
        self.faiss_index: Any | None = None
        self.vector_id_map: dict[str, int] = {}  # Maps vector_id -> FAISS index
        self.reverse_vector_map: dict[int, str] = {}  # Maps FAISS index -> vector_id
        self._lock = threading.RLock()
        self._validator = ConstitutionalValidator()
        self._initialized = False

        # Initialize logging
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

        self.logger.info("StorageManager initialized with constitutional compliance")

    def initialize(self) -> None:
        """Initialize storage components.

        Raises:
            RuntimeError: If initialization fails

        """
        if self._initialized:
            return

        try:
            self._initialize_sqlite()
            self._initialize_faiss()
            self._initialize_validator()
            self._initialized = True

            self.logger.info("StorageManager initialization completed successfully")
            self._audit_log("system", "initialize", {"success": True})

        except Exception as e:
            self.logger.exception(f"StorageManager initialization failed: {e}")
            self._audit_log("system", "initialize", {"success": False, "error": str(e)})
            raise RuntimeError(f"Failed to initialize StorageManager: {e}")

    def _initialize_sqlite(self) -> None:
        """Initialize SQLite database with schemas."""
        self.db_connection = sqlite3.connect(
            self.config.db_path,
            check_same_thread=False,
            timeout=30.0,
        )
        self.db_connection.row_factory = sqlite3.Row

        # Enable foreign keys
        self.db_connection.execute("PRAGMA foreign_keys = ON")

        # Create schemas for all graph types
        self._create_knowledge_graph_schema()
        self._create_causal_graph_schema()
        self._create_social_graph_schema()
        self._create_system_graph_schema()
        self._create_cross_graph_schema()
        self._create_metadata_schema()

        self.db_connection.commit()

    def _create_knowledge_graph_schema(self) -> None:
        """Create knowledge graph tables."""
        cursor = self.db_connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS knowledge_nodes (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS knowledge_edges (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                relationship TEXT NOT NULL,
                metadata JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_id) REFERENCES knowledge_nodes(id),
                FOREIGN KEY (target_id) REFERENCES knowledge_nodes(id)
            )
        """,
        )

        # Create indexes for performance
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_knowledge_type ON knowledge_nodes(type)",
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_knowledge_source ON knowledge_edges(source_id)",
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_knowledge_target ON knowledge_edges(target_id)",
        )

    def _create_causal_graph_schema(self) -> None:
        """Create causal graph tables."""
        cursor = self.db_connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS causal_nodes (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS causal_edges (
                id TEXT PRIMARY KEY,
                cause_id TEXT NOT NULL,
                effect_id TEXT NOT NULL,
                strength REAL,
                confidence REAL,
                metadata JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cause_id) REFERENCES causal_nodes(id),
                FOREIGN KEY (effect_id) REFERENCES causal_nodes(id)
            )
        """,
        )

        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_causal_type ON causal_nodes(type)",
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_causal_cause ON causal_edges(cause_id)",
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_causal_effect ON causal_edges(effect_id)",
        )

    def _create_social_graph_schema(self) -> None:
        """Create social graph tables."""
        cursor = self.db_connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS social_nodes (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS social_edges (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                relationship TEXT NOT NULL,
                weight REAL DEFAULT 1.0,
                metadata JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_id) REFERENCES social_nodes(id),
                FOREIGN KEY (target_id) REFERENCES social_nodes(id)
            )
        """,
        )

        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_social_type ON social_nodes(type)",
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_social_source ON social_edges(source_id)",
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_social_target ON social_edges(target_id)",
        )

    def _create_system_graph_schema(self) -> None:
        """Create system graph tables."""
        cursor = self.db_connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS system_nodes (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS system_edges (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                relationship TEXT NOT NULL,
                priority INTEGER DEFAULT 1,
                metadata JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_id) REFERENCES system_nodes(id),
                FOREIGN KEY (target_id) REFERENCES system_nodes(id)
            )
        """,
        )

        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_system_type ON system_nodes(type)",
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_system_source ON system_edges(source_id)",
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_system_target ON system_edges(target_id)",
        )

    def _create_cross_graph_schema(self) -> None:
        """Create cross-graph relationship tables."""
        cursor = self.db_connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cross_graph_relationships (
                id TEXT PRIMARY KEY,
                source_graph TEXT NOT NULL,
                source_id TEXT NOT NULL,
                target_graph TEXT NOT NULL,
                target_id TEXT NOT NULL,
                relationship_type TEXT NOT NULL,
                confidence REAL,
                metadata JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        )

        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_cross_source ON cross_graph_relationships(source_graph, source_id)",
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_cross_target ON cross_graph_relationships(target_graph, target_id)",
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_cross_type ON cross_graph_relationships(relationship_type)",
        )

    def _create_metadata_schema(self) -> None:
        """Create metadata and audit trail tables."""
        cursor = self.db_connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value JSON,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        )

        if self.config.audit_trail_enabled:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_trail (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    operation TEXT NOT NULL,
                    graph_type TEXT,
                    entity_id TEXT,
                    details JSON
                )
            """,
            )

    def _initialize_faiss(self) -> None:
        """Initialize PyTorch vector index (FAISS-compatible)."""
        if not PYTORCH_AVAILABLE:
            self.logger.warning(
                "PyTorch adapter not available - vector operations disabled",
            )
            return

        try:
            # Create PyTorch-based FAISS-compatible index
            self.faiss_index = FaissToPyTorchAdapter(
                dimension=self.config.vector_dimension,
                enable_gpu=self.config.enable_gpu,
            )

            # Try to load existing index if available
            if os.path.exists(self.config.faiss_index_path):
                try:
                    self.faiss_index.load(self.config.faiss_index_path)
                    self.logger.info(
                        f"Loaded existing PyTorch index with {self.faiss_index.ntotal} vectors",
                    )
                except Exception as e:
                    self.logger.warning(
                        f"Failed to load existing index, starting fresh: {e}",
                    )

            device = self.faiss_index.get_device()
            self.logger.info(f"PyTorch vector index initialized on {device}")

        except Exception as e:
            self.logger.exception(f"PyTorch vector initialization failed: {e}")
            raise RuntimeError(f"Failed to initialize PyTorch vector storage: {e}")

    def _initialize_validator(self) -> None:
        """Initialize constitutional validator."""
        self._validator.validate_storage_config(self.config)

    # Knowledge Graph Operations
    def create_knowledge_node(self, node_data: dict[str, Any]) -> str:
        """Create a knowledge graph node.

        Args:
            node_data: Dictionary containing node information

        Returns:
            str: Node ID

        Raises:
            ValueError: If node_data is invalid

        """
        if not node_data or "type" not in node_data or "content" not in node_data:
            raise ValueError("node_data must contain 'type' and 'content' fields")

        with self._lock:
            node_id = f"knowledge_{int(time.time() * 1000000)}"
            cursor = self.db_connection.cursor()

            cursor.execute(
                """
                INSERT INTO knowledge_nodes (id, type, content, metadata)
                VALUES (?, ?, ?, ?)
            """,
                (
                    node_id,
                    node_data["type"],
                    node_data["content"],
                    json.dumps(node_data.get("metadata", {})),
                ),
            )

            self.db_connection.commit()
            self._audit_log("knowledge", "create_node", {"node_id": node_id})

            return node_id

    def get_knowledge_node(self, node_id: str) -> dict[str, Any] | None:
        """Retrieve a knowledge graph node.

        Args:
            node_id: ID of the node to retrieve

        Returns:
            Optional[Dict]: Node data or None if not found

        """
        cursor = self.db_connection.cursor()
        cursor.execute(
            "SELECT * FROM knowledge_nodes WHERE id = ?",
            (node_id,),
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return {
            "id": row["id"],
            "type": row["type"],
            "content": row["content"],
            "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def update_knowledge_node(self, node_id: str, update_data: dict[str, Any]) -> bool:
        """Update a knowledge graph node.

        Args:
            node_id: ID of the node to update
            update_data: Fields to update

        Returns:
            bool: True if successful, False otherwise

        """
        if not update_data:
            return False

        with self._lock:
            cursor = self.db_connection.cursor()

            # Build update query dynamically
            updates = []
            values = []

            if "type" in update_data:
                updates.append("type = ?")
                values.append(update_data["type"])

            if "content" in update_data:
                updates.append("content = ?")
                values.append(update_data["content"])

            if "metadata" in update_data:
                updates.append("metadata = ?")
                values.append(json.dumps(update_data["metadata"]))

            if not updates:
                return False

            updates.append("updated_at = CURRENT_TIMESTAMP")
            values.append(node_id)

            query = f"UPDATE knowledge_nodes SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, values)

            success = cursor.rowcount > 0
            self.db_connection.commit()

            if success:
                self._audit_log("knowledge", "update_node", {"node_id": node_id})

            return success

    def create_knowledge_edge(self, edge_data: dict[str, Any]) -> str:
        """Create a knowledge graph edge.

        Args:
            edge_data: Dictionary containing edge information

        Returns:
            str: Edge ID

        """
        required_fields = ["source", "target", "relationship"]
        if not all(field in edge_data for field in required_fields):
            raise ValueError(f"edge_data must contain {required_fields}")

        with self._lock:
            edge_id = f"knowledge_edge_{int(time.time() * 1000000)}"
            cursor = self.db_connection.cursor()

            cursor.execute(
                """
                INSERT INTO knowledge_edges (id, source_id, target_id, relationship, metadata)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    edge_id,
                    edge_data["source"],
                    edge_data["target"],
                    edge_data["relationship"],
                    json.dumps(edge_data.get("metadata", {})),
                ),
            )

            self.db_connection.commit()
            self._audit_log("knowledge", "create_edge", {"edge_id": edge_id})

            return edge_id

    # Vector Operations
    def store_vector(self, vector_id: str, vector: np.ndarray) -> bool:
        """Store a vector in the FAISS index.

        Args:
            vector_id: Unique identifier for the vector
            vector: Numpy array representing the vector

        Returns:
            bool: True if successful, False otherwise

        Raises:
            ValueError: If vector dimensions don't match config

        """
        if not FAISS_AVAILABLE or self.faiss_index is None:
            self.logger.warning("FAISS not available - vector storage disabled")
            return False

        if vector.shape[-1] != self.config.vector_dimension:
            raise ValueError(
                f"Vector dimension {vector.shape[-1]} doesn't match config {self.config.vector_dimension}",
            )

        with self._lock:
            try:
                # Ensure vector is 2D and float32
                if vector.ndim == 1:
                    vector = vector.reshape(1, -1)
                vector = vector.astype(np.float32)

                # Normalize for cosine similarity
                norm = np.linalg.norm(vector, axis=1, keepdims=True)
                vector = vector / (norm + 1e-8)

                # Get next index position
                index_pos = self.faiss_index.ntotal

                # Store in FAISS
                self.faiss_index.add(vector)

                # Update mappings
                self.vector_id_map[vector_id] = index_pos
                self.reverse_vector_map[index_pos] = vector_id

                self._audit_log("vector", "store", {"vector_id": vector_id})
                return True

            except Exception as e:
                self.logger.exception(f"Failed to store vector {vector_id}: {e}")
                return False

    def get_vector(self, vector_id: str) -> np.ndarray | None:
        """Retrieve a vector by ID.

        Args:
            vector_id: ID of the vector to retrieve

        Returns:
            Optional[np.ndarray]: Vector or None if not found

        """
        if not FAISS_AVAILABLE or self.faiss_index is None:
            return None

        if vector_id not in self.vector_id_map:
            return None

        try:
            index_pos = self.vector_id_map[vector_id]
            return self.faiss_index.reconstruct(index_pos)
        except Exception as e:
            self.logger.exception(f"Failed to retrieve vector {vector_id}: {e}")
            return None

    def search_similar_vectors(
        self,
        query_vector: np.ndarray,
        k: int = 10,
    ) -> list[tuple[str, float]]:
        """Search for similar vectors.

        Args:
            query_vector: Query vector
            k: Number of results to return

        Returns:
            List[Tuple[str, float]]: List of (vector_id, similarity_score) tuples

        """
        if not FAISS_AVAILABLE or self.faiss_index is None:
            return []

        if self.faiss_index.ntotal == 0:
            return []

        try:
            # Ensure query vector is proper shape and type
            if query_vector.ndim == 1:
                query_vector = query_vector.reshape(1, -1)
            query_vector = query_vector.astype(np.float32)

            # Normalize for cosine similarity
            norm = np.linalg.norm(query_vector, axis=1, keepdims=True)
            query_vector = query_vector / (norm + 1e-8)

            # Search
            k = min(k, self.faiss_index.ntotal)
            similarities, indices = self.faiss_index.search(query_vector, k)

            results = []
            for i in range(k):
                if indices[0][i] != -1:  # Valid result
                    index_pos = indices[0][i]
                    similarity = similarities[0][i]

                    if index_pos in self.reverse_vector_map:
                        vector_id = self.reverse_vector_map[index_pos]
                        results.append((vector_id, float(similarity)))

            return results

        except Exception as e:
            self.logger.exception(f"Vector search failed: {e}")
            return []

    # Cross-graph Operations
    def create_cross_graph_relationship(self, relationship_data: dict[str, Any]) -> str:
        """Create a relationship between different graph types.

        Args:
            relationship_data: Dictionary containing relationship information

        Returns:
            str: Relationship ID

        """
        required_fields = [
            "source_graph",
            "source_id",
            "target_graph",
            "target_id",
            "relationship_type",
        ]
        if not all(field in relationship_data for field in required_fields):
            raise ValueError(f"relationship_data must contain {required_fields}")

        with self._lock:
            rel_id = f"cross_rel_{int(time.time() * 1000000)}"
            cursor = self.db_connection.cursor()

            cursor.execute(
                """
                INSERT INTO cross_graph_relationships
                (id, source_graph, source_id, target_graph, target_id, relationship_type, confidence, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    rel_id,
                    relationship_data["source_graph"],
                    relationship_data["source_id"],
                    relationship_data["target_graph"],
                    relationship_data["target_id"],
                    relationship_data["relationship_type"],
                    relationship_data.get("confidence"),
                    json.dumps(relationship_data.get("metadata", {})),
                ),
            )

            self.db_connection.commit()
            self._audit_log("cross_graph", "create_relationship", {"rel_id": rel_id})

            return rel_id

    def get_cross_graph_relationships(
        self,
        source_graph: str | None = None,
        source_id: str | None = None,
        target_graph: str | None = None,
        target_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get cross-graph relationships with optional filtering.

        Args:
            source_graph: Filter by source graph type
            source_id: Filter by source ID
            target_graph: Filter by target graph type
            target_id: Filter by target ID

        Returns:
            List[Dict]: List of relationships

        """
        cursor = self.db_connection.cursor()

        query = "SELECT * FROM cross_graph_relationships WHERE 1=1"
        params = []

        if source_graph:
            query += " AND source_graph = ?"
            params.append(source_graph)

        if source_id:
            query += " AND source_id = ?"
            params.append(source_id)

        if target_graph:
            query += " AND target_graph = ?"
            params.append(target_graph)

        if target_id:
            query += " AND target_id = ?"
            params.append(target_id)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [
            {
                "id": row["id"],
                "source_graph": row["source_graph"],
                "source_id": row["source_id"],
                "target_graph": row["target_graph"],
                "target_id": row["target_id"],
                "relationship_type": row["relationship_type"],
                "confidence": row["confidence"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    # Batch Operations
    def batch_create_knowledge_nodes(
        self,
        node_data_list: list[dict[str, Any]],
    ) -> list[str]:
        """Create multiple knowledge nodes in batch.

        Args:
            node_data_list: List of node data dictionaries

        Returns:
            List[str]: List of created node IDs

        """
        if not node_data_list:
            return []

        node_ids = []
        with self._lock:
            cursor = self.db_connection.cursor()

            for node_data in node_data_list:
                if not node_data or "type" not in node_data or "content" not in node_data:
                    continue  # Skip invalid entries

                node_id = f"knowledge_{int(time.time() * 1000000)}_{len(node_ids)}"
                cursor.execute(
                    """
                    INSERT INTO knowledge_nodes (id, type, content, metadata)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        node_id,
                        node_data["type"],
                        node_data["content"],
                        json.dumps(node_data.get("metadata", {})),
                    ),
                )
                node_ids.append(node_id)

            self.db_connection.commit()
            self._audit_log("knowledge", "batch_create_nodes", {"count": len(node_ids)})

        return node_ids

    def batch_store_vectors(self, vector_ids: list[str], vectors: np.ndarray) -> bool:
        """Store multiple vectors in batch.

        Args:
            vector_ids: List of vector IDs
            vectors: Array of vectors (n_vectors, dimension)

        Returns:
            bool: True if successful, False otherwise

        """
        if not FAISS_AVAILABLE or self.faiss_index is None:
            return False

        if len(vector_ids) != vectors.shape[0]:
            raise ValueError("Number of vector IDs must match number of vectors")

        if vectors.shape[1] != self.config.vector_dimension:
            raise ValueError(
                f"Vector dimension {vectors.shape[1]} doesn't match config {self.config.vector_dimension}",
            )

        with self._lock:
            try:
                # Prepare vectors
                vectors = vectors.astype(np.float32)
                norm = np.linalg.norm(vectors, axis=1, keepdims=True)
                vectors = vectors / (norm + 1e-8)

                # Get starting index
                start_index = self.faiss_index.ntotal

                # Store in FAISS
                self.faiss_index.add(vectors)

                # Update mappings
                for i, vector_id in enumerate(vector_ids):
                    index_pos = start_index + i
                    self.vector_id_map[vector_id] = index_pos
                    self.reverse_vector_map[index_pos] = vector_id

                self._audit_log("vector", "batch_store", {"count": len(vector_ids)})
                return True

            except Exception as e:
                self.logger.exception(f"Batch vector storage failed: {e}")
                return False

    # Causal Graph Operations (implement similar patterns)
    def create_causal_node(self, node_data: dict[str, Any]) -> str:
        """Create a causal graph node."""
        if not node_data or "type" not in node_data or "content" not in node_data:
            raise ValueError("node_data must contain 'type' and 'content' fields")

        with self._lock:
            node_id = f"causal_{int(time.time() * 1000000)}"
            cursor = self.db_connection.cursor()

            cursor.execute(
                """
                INSERT INTO causal_nodes (id, type, content, metadata)
                VALUES (?, ?, ?, ?)
            """,
                (
                    node_id,
                    node_data["type"],
                    node_data["content"],
                    json.dumps(node_data.get("metadata", {})),
                ),
            )

            self.db_connection.commit()
            self._audit_log("causal", "create_node", {"node_id": node_id})
            return node_id

    # Social and System Graph operations would follow similar patterns
    # (omitted for brevity but would be implemented following the same constitutional patterns)

    # Memory Management and Monitoring
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB.

        Returns:
            float: Memory usage in MB

        """
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024

    def get_storage_stats(self) -> dict[str, Any]:
        """Get comprehensive storage statistics.

        Returns:
            Dict[str, Any]: Storage statistics

        """
        stats = {
            "memory_usage_mb": self.get_memory_usage(),
            "memory_limit_mb": self.config.max_memory_mb,
            "faiss_available": FAISS_AVAILABLE,
            "database_path": self.config.db_path,
        }

        if FAISS_AVAILABLE and self.faiss_index is not None:
            stats.update(
                {
                    "vectors_stored": self.faiss_index.ntotal,
                    "vector_dimension": self.config.vector_dimension,
                    "faiss_index_path": self.config.faiss_index_path,
                },
            )

        # Get node counts from database
        if self.db_connection:
            cursor = self.db_connection.cursor()
            for graph_type in ["knowledge", "causal", "social", "system"]:
                cursor.execute(f"SELECT COUNT(*) FROM {graph_type}_nodes")
                stats[f"{graph_type}_nodes"] = cursor.fetchone()[0]

        return stats

    def cleanup(self) -> None:
        """Clean up resources and save data."""
        if not self._initialized:
            return

        with self._lock:
            try:
                # Save PyTorch vector index
                if PYTORCH_AVAILABLE and self.faiss_index is not None:
                    try:
                        self.faiss_index.save(self.config.faiss_index_path)
                        self.logger.info("PyTorch vector index saved")
                    except Exception as e:
                        self.logger.warning(f"Failed to save vector index: {e}")

                # Close database
                if self.db_connection is not None:
                    self.db_connection.close()
                    self.db_connection = None

                # Clear mappings
                self.vector_id_map.clear()
                self.reverse_vector_map.clear()

                # Run garbage collection
                gc.collect()

                self._initialized = False
                self.logger.info("StorageManager cleanup completed")

            except Exception as e:
                self.logger.exception(f"Cleanup failed: {e}")

    @contextmanager
    def transaction(self):
        """Context manager for database transactions."""
        if not self.db_connection:
            raise RuntimeError("Database not initialized")

        try:
            yield
            self.db_connection.commit()
        except Exception:
            self.db_connection.rollback()
            raise

    def _audit_log(
        self,
        graph_type: str,
        operation: str,
        details: dict[str, Any],
    ) -> None:
        """Log operation to audit trail."""
        if not self.config.audit_trail_enabled or not self.db_connection:
            return

        try:
            cursor = self.db_connection.cursor()
            cursor.execute(
                """
                INSERT INTO audit_trail (operation, graph_type, entity_id, details)
                VALUES (?, ?, ?, ?)
            """,
                (
                    operation,
                    graph_type,
                    details.get("node_id") or details.get("edge_id") or details.get("rel_id"),
                    json.dumps(details),
                ),
            )
            self.db_connection.commit()
        except Exception as e:
            self.logger.exception(f"Audit logging failed: {e}")

    # Constitutional Compliance Methods
    def get_constitutional_compliance_score(self) -> float:
        """Get constitutional compliance score.

        Returns:
            float: Compliance score (0.0 to 1.0)

        """
        return self._validator.calculate_storage_compliance_score(self)

    def get_audit_trail(self) -> list[dict[str, Any]]:
        """Get audit trail entries.

        Returns:
            List[Dict]: Audit trail entries

        """
        if not self.config.audit_trail_enabled or not self.db_connection:
            return []

        cursor = self.db_connection.cursor()
        cursor.execute(
            """
            SELECT * FROM audit_trail
            ORDER BY timestamp DESC
            LIMIT 1000
        """,
        )
        rows = cursor.fetchall()

        return [
            {
                "id": row["id"],
                "timestamp": row["timestamp"],
                "operation": row["operation"],
                "graph_type": row["graph_type"],
                "entity_id": row["entity_id"],
                "details": json.loads(row["details"]) if row["details"] else {},
            }
            for row in rows
        ]

    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()
