import os
import tempfile
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from ..core.storage_manager import StorageConfig, StorageManager

"""
Test suite for CKS Storage Manager.

Test Case ID: TC-CKS-001
Priority: High
Test Type: Unit Testing + Integration Testing

Purpose:
Comprehensive test suite for CKS Storage Manager following TDD approach.
Tests multi-graph storage, FAISS integration, SQLite operations, and
constitutional compliance requirements.

Test Data:
- Various graph types: Knowledge, Vector, Causal, Social, System
- Test embeddings and vectors
- Cross-graph relationship data
- Constitutional constraint data

Expected Results:
- All storage operations work correctly
- FAISS GPU/CPU fallback functions
- SQLite schema maintains data integrity
- Constitutional validation passes
- Memory management prevents leaks
"""


# Import the module we're testing


class TestStorageConfig:
    """Test configuration validation for storage components."""

    def test_storage_config_defaults(self):
        """
        Test default configuration values.

        Test Case ID: TC-CKS-001-01
        Purpose: Verify default configuration is constitutional compliant
        """
        config = StorageConfig()

        # Constitutional: Solo developer optimized defaults
        assert config.db_path.endswith(".db")
        assert config.faiss_index_path.endswith(".index")
        assert config.enable_gpu is True  # GPU with CPU fallback
        assert config.max_memory_mb <= 4096  # Conservative memory limit
        assert config.vector_dimension == 768  # Standard embedding size

    def test_storage_config_validation(self):
        """
        Test configuration validation.

        Test Case ID: TC-CKS-001-02
        Purpose: Verify invalid configurations are rejected
        """
        # Test invalid memory limit
        with pytest.raises(ValueError):
            StorageConfig(max_memory_mb=-1)

        # Test invalid vector dimension
        with pytest.raises(ValueError):
            StorageConfig(vector_dimension=0)

    def test_storage_config_paths(self):
        """
        Test path configuration and creation.

        Test Case ID: TC-CKS-001-03
        Purpose: Verify directory creation and path handling
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            config = StorageConfig(db_path=db_path)

            assert config.db_path == db_path
            assert os.path.isdir(os.path.dirname(db_path))


class TestStorageManager:
    """Test main storage manager functionality."""

    @pytest.fixture
    def temp_storage_manager(self):
        """Create a temporary storage manager for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test_cks.db")
            faiss_path = os.path.join(temp_dir, "test_vectors.index")
            config = StorageConfig(
                db_path=db_path,
                faiss_index_path=faiss_path,
                enable_gpu=False,  # Disable GPU for testing
                max_memory_mb=512,
            )
            manager = StorageManager(config)
            manager.initialize()
            yield manager
            manager.cleanup()

    def test_storage_manager_initialization(self, temp_storage_manager):
        """
        Test storage manager initialization.

        Test Case ID: TC-CKS-001-04
        Purpose: Verify all components initialize correctly
        """
        manager = temp_storage_manager

        # Verify database connection
        assert manager.db_connection is not None
        assert manager.faiss_index is not None

        # Verify graph schemas are created
        cursor = manager.db_connection.cursor()
        tables = cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table'",
        ).fetchall()

        table_names = [row[0] for row in tables]
        expected_tables = [
            "knowledge_nodes",
            "knowledge_edges",
            "causal_nodes",
            "causal_edges",
            "social_nodes",
            "social_edges",
            "system_nodes",
            "system_edges",
            "cross_graph_relationships",
            "metadata",
            "audit_trail",
        ]

        for table in expected_tables:
            assert table in table_names

    def test_knowledge_graph_operations(self, temp_storage_manager):
        """
        Test knowledge graph CRUD operations.

        Test Case ID: TC-CKS-001-05
        Purpose: Verify knowledge graph data management
        """
        manager = temp_storage_manager

        # Create knowledge node
        node_data = {
            "type": "concept",
            "content": "Python programming",
            "metadata": {"domain": "software_engineering"},
        }
        node_id = manager.create_knowledge_node(node_data)
        assert node_id is not None
        assert isinstance(node_id, str)

        # Retrieve knowledge node
        retrieved = manager.get_knowledge_node(node_id)
        assert retrieved is not None
        assert retrieved["type"] == "concept"
        assert retrieved["content"] == "Python programming"

        # Update knowledge node
        update_data = {"content": "Advanced Python programming"}
        success = manager.update_knowledge_node(node_id, update_data)
        assert success is True

        # Verify update
        updated = manager.get_knowledge_node(node_id)
        assert updated["content"] == "Advanced Python programming"

        # Create relationship
        node_data2 = {"type": "concept", "content": "Data structures"}
        node_id2 = manager.create_knowledge_node(node_data2)

        edge_data = {
            "source": node_id,
            "target": node_id2,
            "relationship": "includes",
            "metadata": {"strength": 0.9},
        }
        edge_id = manager.create_knowledge_edge(edge_data)
        assert edge_id is not None

    def test_vector_operations(self, temp_storage_manager):
        """
        Test vector storage and retrieval with FAISS.

        Test Case ID: TC-CKS-001-06
        Purpose: Verify vector embeddings storage and similarity search
        """
        manager = temp_storage_manager

        # Create test vectors
        test_vectors = np.random.rand(5, 768).astype(np.float32)
        vector_ids = [f"vector_{i}" for i in range(5)]

        # Store vectors
        for i, (vector, vector_id) in enumerate(zip(test_vectors, vector_ids, strict=False)):
            success = manager.store_vector(vector_id, vector)
            assert success is True

        # Test similarity search
        query_vector = test_vectors[2].reshape(1, -1)
        results = manager.search_similar_vectors(query_vector, k=3)

        assert len(results) <= 3
        assert all(isinstance(r[0], str) for r in results)  # vector_ids
        assert all(isinstance(r[1], (float, np.floating)) for r in results)  # distances

    @patch("faiss.index_factory")
    def test_gpu_fallback_handling(self, mock_faiss_index, temp_storage_manager):
        """
        Test GPU support with CPU fallback.

        Test Case ID: TC-CKS-001-07
        Purpose: Verify GPU initialization falls back to CPU gracefully
        """
        # Mock GPU failure
        mock_gpu_index = MagicMock()
        mock_gpu_index.is_gpu = False
        mock_faiss_index.return_value = mock_gpu_index

        # Re-initialize with GPU enabled
        config = StorageConfig(enable_gpu=True)
        manager = StorageManager(config)

        # Should not raise exception even with GPU failure
        try:
            manager.initialize()
            assert manager.faiss_index is not None
        finally:
            manager.cleanup()

    def test_cross_graph_relationships(self, temp_storage_manager):
        """
        Test cross-graph relationship tracking.

        Test Case ID: TC-CKS-001-08
        Purpose: Verify relationships between different graph types
        """
        manager = temp_storage_manager

        # Create nodes in different graphs
        knowledge_id = manager.create_knowledge_node(
            {
                "type": "concept",
                "content": "Machine Learning",
            },
        )

        causal_id = manager.create_causal_node(
            {
                "type": "event",
                "content": "Model Training",
            },
        )

        # Create cross-graph relationship
        relationship_data = {
            "source_graph": "knowledge",
            "source_id": knowledge_id,
            "target_graph": "causal",
            "target_id": causal_id,
            "relationship_type": "enables",
            "metadata": {"confidence": 0.85},
        }

        rel_id = manager.create_cross_graph_relationship(relationship_data)
        assert rel_id is not None

        # Retrieve cross-graph relationships
        relationships = manager.get_cross_graph_relationships(
            source_graph="knowledge",
            source_id=knowledge_id,
        )
        assert len(relationships) == 1
        assert relationships[0]["target_graph"] == "causal"
        assert relationships[0]["relationship_type"] == "enables"

    def test_constitutional_compliance(self, temp_storage_manager):
        """
        Test constitutional compliance validation.

        Test Case ID: TC-CKS-001-09
        Purpose: Verify all operations comply with constitutional constraints
        """
        manager = temp_storage_manager

        # Test solo developer optimization
        assert manager.get_memory_usage() <= manager.config.max_memory_mb

        # Test evidence-based operations
        node_id = manager.create_knowledge_node({"type": "test", "content": "test"})
        assert node_id is not None  # Should provide concrete evidence

        # Test audit trail creation
        operations = manager.get_audit_trail()
        assert isinstance(operations, list)
        # Should have creation operation in audit trail

        # Test quality gate compliance
        compliance_score = manager.get_constitutional_compliance_score()
        assert compliance_score >= 0.95  # Constitutional minimum

    def test_memory_management(self, temp_storage_manager):
        """
        Test memory management and cleanup.

        Test Case ID: TC-CKS-001-10
        Purpose: Verify memory doesn't leak and cleanup works
        """
        manager = temp_storage_manager

        # Add data to increase memory usage
        for i in range(100):
            manager.create_knowledge_node(
                {
                    "type": "test",
                    "content": f"test_node_{i}",
                },
            )

            # Store vectors
            vector = np.random.rand(768).astype(np.float32)
            manager.store_vector(f"vector_{i}", vector)

        # Check memory usage
        initial_memory = manager.get_memory_usage()
        assert 0 < initial_memory <= manager.config.max_memory_mb

        # Test cleanup
        manager.cleanup()
        assert manager.db_connection is None

        # Memory should be released after cleanup
        final_memory = manager.get_memory_usage()
        assert final_memory < initial_memory

    def test_error_handling_and_recovery(self, temp_storage_manager):
        """
        Test error handling and recovery mechanisms.

        Test Case ID: TC-CKS-001-11
        Purpose: Verify robust error handling and recovery
        """
        manager = temp_storage_manager

        # Test invalid node creation
        with pytest.raises(ValueError):
            manager.create_knowledge_node({})  # Missing required fields

        # Test invalid vector dimensions
        with pytest.raises(ValueError):
            manager.store_vector("test", np.random.rand(100))  # Wrong dimension

        # Test non-existent node retrieval
        result = manager.get_knowledge_node("non_existent_id")
        assert result is None

        # Database connection recovery
        manager.db_connection.close()
        # Operations should still work (connection should be recovered)
        node_id = manager.create_knowledge_node(
            {"type": "test", "content": "recovery_test"},
        )
        assert node_id is not None

    def test_batch_operations(self, temp_storage_manager):
        """
        Test batch operations for efficiency.

        Test Case ID: TC-CKS-001-12
        Purpose: Verify batch operations work and are efficient
        """
        manager = temp_storage_manager

        # Batch create nodes
        node_data_list = [{"type": "concept", "content": f"concept_{i}"} for i in range(10)]

        node_ids = manager.batch_create_knowledge_nodes(node_data_list)
        assert len(node_ids) == 10
        assert all(isinstance(nid, str) for nid in node_ids)

        # Batch store vectors
        vectors = np.random.rand(10, 768).astype(np.float32)
        vector_ids = [f"batch_vector_{i}" for i in range(10)]

        success = manager.batch_store_vectors(vector_ids, vectors)
        assert success is True

        # Verify all vectors are stored
        for vector_id in vector_ids:
            retrieved = manager.get_vector(vector_id)
            assert retrieved is not None
            assert retrieved.shape == (768,)


class TestIntegration:
    """Integration tests with external dependencies."""

    def test_sqlite_persistence(self):
        """
        Test data persistence across sessions.

        Test Case ID: TC-CKS-001-13
        Purpose: Verify data survives database closure/reopening
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "persistence_test.db")
            config = StorageConfig(db_path=db_path, enable_gpu=False)

            # First session: create data
            manager1 = StorageManager(config)
            manager1.initialize()

            node_id = manager1.create_knowledge_node(
                {
                    "type": "persistent_test",
                    "content": "This should persist",
                },
            )
            manager1.cleanup()

            # Second session: verify data persistence
            manager2 = StorageManager(config)
            manager2.initialize()

            retrieved = manager2.get_knowledge_node(node_id)
            assert retrieved is not None
            assert retrieved["content"] == "This should persist"

            manager2.cleanup()

    @pytest.mark.skipif(
        not os.environ.get("RUN_GPU_TESTS"),
        reason="GPU tests require explicit enable",
    )
    def test_gpu_acceleration(self):
        """
        Test GPU acceleration when available.

        Test Case ID: TC-CKS-001-14
        Purpose: Verify GPU acceleration works when hardware available
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            config = StorageConfig(
                db_path=os.path.join(temp_dir, "gpu_test.db"),
                enable_gpu=True,
                max_memory_mb=1024,
            )

            manager = StorageManager(config)
            manager.initialize()

            # Store large number of vectors to test GPU performance
            vectors = np.random.rand(1000, 768).astype(np.float32)
            vector_ids = [f"gpu_test_{i}" for i in range(1000)]

            success = manager.batch_store_vectors(vector_ids, vectors)
            assert success is True

            # Test search performance
            query_vector = vectors[0].reshape(1, -1)
            results = manager.search_similar_vectors(query_vector, k=10)

            assert len(results) == 10
            # GPU should be faster than CPU for this workload

            manager.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
