"""
Test Suite for TaskMaster Session Integration

TASK-F-007: Test TaskMaster Session Integration

This test suite provides comprehensive testing of the TaskMasterSessionIntegration
class, including all session linkage, task continuity, and migration functionality.

Test Coverage:
- Session linkage operations
- Continuity score calculations
- Session state migrations
- Active session task retrieval
- Performance validation
- Error handling and edge cases
- Integration with SessionMemoryBridge

Performance Requirements:
- Session linkage: <10ms per operation
- Continuity calculation: <5ms per operation
- Session migration: <50ms per operation
- Task retrieval: <20ms per operation

Author: CSF NIP Development Team
Version: 1.0.0
Date: 2025-12-13
"""

import json
import logging
import sqlite3
import tempfile
import time
import uuid
from pathlib import Path
from unittest.mock import Mock

import pytest
from db import WorkspaceTaskDAL

# Import the module to test
from session_integration import (
    TaskMasterSessionIntegration,
    create_session_integration,
    get_session_integration,
)

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestTaskMasterSessionIntegration:
    """Test class for TaskMasterSessionIntegration."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        # Initialize database
        dal = WorkspaceTaskDAL()
        dal.db_path = Path(db_path)
        dal._ensure_database()

        # Add session columns if needed
        with dal.connect() as conn:
            try:
                conn.execute("ALTER TABLE task ADD COLUMN session_id TEXT")
            except sqlite3.OperationalError:
                pass  # Column might already exist

            try:
                conn.execute("ALTER TABLE task ADD COLUMN session_span INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass

            try:
                conn.execute("ALTER TABLE task ADD COLUMN pre_compaction_state TEXT")
            except sqlite3.OperationalError:
                pass

            try:
                conn.execute("ALTER TABLE task ADD COLUMN context_criticality REAL DEFAULT 0.0")
            except sqlite3.OperationalError:
                pass

            try:
                conn.execute("ALTER TABLE task ADD COLUMN compaction_session_id TEXT")
            except sqlite3.OperationalError:
                pass

            # Create session_tracking table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS session_tracking (
                    session_id TEXT PRIMARY KEY,
                    task_master_session_id TEXT,
                    started_at TIMESTAMP,
                    last_compaction TIMESTAMP,
                    compaction_count INTEGER DEFAULT 0,
                    total_context_tokens INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'active',
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

        yield db_path

        # Cleanup
        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    def test_dal(self, temp_db):
        """Create test DAL instance."""
        dal = WorkspaceTaskDAL()
        dal.db_path = Path(temp_db)
        return dal

    @pytest.fixture
    def mock_session_bridge(self):
        """Create mock SessionMemoryBridge."""
        mock_bridge = Mock()
        mock_bridge.preserve_session_context.return_value = Mock(
            bridge_id=str(uuid.uuid4()),
            pre_compaction_session_id="old_session",
            post_compaction_session_id="new_session"
        )
        return mock_bridge

    @pytest.fixture
    def integration(self, test_dal, mock_session_bridge):
        """Create TaskMasterSessionIntegration instance for testing."""
        return TaskMasterSessionIntegration(
            dal=test_dal,
            session_memory_bridge=mock_session_bridge,
            performance_monitoring=True
        )

    @pytest.fixture
    def sample_tasks(self):
        """Create sample task data."""
        return [
            {
                'id': str(uuid.uuid4()),
                'title': 'Test Task 1',
                'description': 'First test task',
                'status': 'active',
                'priority': 'high',
                'estimated_duration': 2.0,
                'completion_percentage': 25
            },
            {
                'id': str(uuid.uuid4()),
                'title': 'Test Task 2',
                'description': 'Second test task',
                'status': 'pending',
                'priority': 'medium',
                'estimated_duration': 1.5,
                'completion_percentage': 0
            },
            {
                'id': str(uuid.uuid4()),
                'title': 'Test Task 3',
                'description': 'Third test task',
                'status': 'completed',
                'priority': 'low',
                'estimated_duration': 3.0,
                'completion_percentage': 100
            }
        ]

    def test_initialization(self, test_dal):
        """Test TaskMasterSessionIntegration initialization."""
        # Test with default parameters
        integration = TaskMasterSessionIntegration(dal=test_dal)
        assert integration.dal == test_dal
        assert integration.performance_monitoring is True
        assert integration._lock is not None

        # Test with custom parameters
        mock_bridge = Mock()
        integration = TaskMasterSessionIntegration(
            dal=test_dal,
            session_memory_bridge=mock_bridge,
            performance_monitoring=False
        )
        assert integration.session_memory_bridge == mock_bridge
        assert integration.performance_monitoring is False

    def test_link_tasks_to_session_success(self, integration, sample_tasks):
        """Test successful task linking to session."""
        # Add sample tasks to database
        session_id = str(uuid.uuid4())
        task_ids = []

        for task_data in sample_tasks:
            task_id = integration.dal.add_task(task_data)
            task_ids.append(task_id)

        # Link tasks to session
        result = integration.link_tasks_to_session(task_ids, session_id)

        # Verify result
        assert result.success is True
        assert result.session_id == session_id
        assert len(result.linked_tasks) == len(task_ids)
        assert len(result.failed_tasks) == 0
        assert result.execution_time_ms < 10 * len(task_ids)  # Performance requirement

        # Verify database updates
        for task_id in task_ids:
            tasks = integration.dal.get_all_tasks()
            task = next((t for t in tasks if t['id'] == task_id), None)
            assert task is not None
            assert task.get('session_id') == session_id
            assert task.get('session_span') == 1

    def test_link_tasks_to_session_partial_failure(self, integration, sample_tasks):
        """Test task linking with partial failures."""
        session_id = str(uuid.uuid4())
        task_ids = []

        # Add sample tasks
        for task_data in sample_tasks:
            task_id = integration.dal.add_task(task_data)
            task_ids.append(task_id)

        # Add invalid task ID
        task_ids.append(str(uuid.uuid4()))

        # Link tasks
        result = integration.link_tasks_to_session(task_ids, session_id)

        # Verify result
        assert result.success is False  # Not all tasks linked
        assert len(result.linked_tasks) == len(sample_tasks)  # Only valid tasks linked
        assert len(result.failed_tasks) == 1  # Invalid task failed
        assert len(result.warnings) > 0  # Should have partial success warning

    def test_link_tasks_to_session_validation(self, integration):
        """Test input validation for task linking."""
        # Test empty task list
        result = integration.link_tasks_to_session([], str(uuid.uuid4()))
        assert result.success is False
        assert len(result.errors) > 0

        # Test empty session ID
        result = integration.link_tasks_to_session([str(uuid.uuid4())], "")
        assert result.success is False
        assert len(result.errors) > 0

    def test_get_session_continuity_score(self, integration, sample_tasks):
        """Test continuity score calculation."""
        session_id = str(uuid.uuid4())

        # Add and link tasks with different properties
        task_ids = []
        for i, task_data in enumerate(sample_tasks):
            task_id = integration.dal.add_task(task_data)
            task_ids.append(task_id)

            # Link to session
            integration.dal.update_task(task_id, {'session_id': session_id})

            # Add pre-compaction state for some tasks
            if i < 2:  # First two tasks have pre-compaction state
                integration.dal.update_task(task_id, {
                    'pre_compaction_state': json.dumps({'test': 'state'}),
                    'context_criticality': 0.8 if i == 0 else 0.5  # First task is critical
                })

        # Calculate continuity score
        result = integration.get_session_continuity_score(session_id)

        # Verify result
        assert result.session_id == session_id
        assert result.total_tasks == len(sample_tasks)
        assert 0.0 <= result.continuity_score <= 1.0
        assert result.preserved_tasks == 2
        assert result.critical_tasks_preserved == 1
        assert result.calculation_time_ms < 5  # Performance requirement

        # Verify factors
        assert 'preservation' in result.factors
        assert 'critical' in result.factors
        assert 'span' in result.factors
        assert 'recency' in result.factors

    def test_get_session_continuity_score_empty_session(self, integration):
        """Test continuity score for empty session."""
        session_id = str(uuid.uuid4())
        result = integration.get_session_continuity_score(session_id)

        # Empty session should have perfect continuity
        assert result.continuity_score == 1.0
        assert result.total_tasks == 0
        assert result.preserved_tasks == 0

    def test_migrate_session_state_success(self, integration, sample_tasks):
        """Test successful session state migration."""
        old_session = str(uuid.uuid4())
        new_session = str(uuid.uuid4())
        task_ids = []

        # Add and link tasks to old session
        for task_data in sample_tasks:
            task_id = integration.dal.add_task(task_data)
            task_ids.append(task_id)
            integration.dal.update_task(task_id, {
                'session_id': old_session,
                'context_criticality': 0.5
            })

        # Migrate session state
        result = integration.migrate_session_state(old_session, new_session)

        # Verify result
        assert result.success is True
        assert result.old_session_id == old_session
        assert result.new_session_id == new_session
        assert len(result.migrated_tasks) == len(sample_tasks)
        assert len(result.failed_migrations) == 0
        assert result.bridge_created is True
        assert result.migration_time_ms < 50  # Performance requirement

        # Verify database updates
        for task_id in task_ids:
            tasks = integration.dal.get_all_tasks()
            task = next((t for t in tasks if t['id'] == task_id), None)
            assert task is not None
            assert task.get('session_id') == new_session
            assert task.get('session_span') == 2  # Incremented from 1
            assert task.get('compaction_session_id') == old_session
            assert task.get('pre_compaction_state') is not None

    def test_migrate_session_state_validation(self, integration):
        """Test input validation for session migration."""
        # Test same session IDs
        session_id = str(uuid.uuid4())
        result = integration.migrate_session_state(session_id, session_id)
        assert result.success is False
        assert len(result.errors) > 0

        # Test empty session IDs
        result = integration.migrate_session_state("", str(uuid.uuid4()))
        assert result.success is False
        assert len(result.errors) > 0

    def test_get_active_session_tasks(self, integration, sample_tasks):
        """Test retrieval of active session tasks."""
        session_id = str(uuid.uuid4())

        # Add and link tasks with different statuses
        task_ids = []
        for i, task_data in enumerate(sample_tasks):
            task_id = integration.dal.add_task(task_data)
            task_ids.append(task_id)
            integration.dal.update_task(task_id, {
                'session_id': session_id,
                'context_criticality': 0.8 if i < 2 else 0.3,  # First two are critical
                'session_span': i + 1
            })

        # Get active session tasks
        result = integration.get_active_session_tasks(session_id)

        # Verify result
        assert result.session_id == session_id
        assert result.total_count == len(sample_tasks)
        assert len(result.tasks) == len(sample_tasks)
        assert result.active_count > 0  # At least one active task
        assert result.critical_count == 2  # Two critical tasks
        assert result.retrieval_time_ms < 20  # Performance requirement

        # Verify span distribution
        assert len(result.span_distribution) > 0
        assert sum(result.span_distribution.values()) == len(sample_tasks)

    def test_get_active_session_tasks_caching(self, integration, sample_tasks):
        """Test caching of active session tasks."""
        session_id = str(uuid.uuid4())

        # Add sample tasks
        for task_data in sample_tasks:
            task_id = integration.dal.add_task(task_data)
            integration.dal.update_task(task_id, {'session_id': session_id})

        # First call - should hit database
        start_time = time.time()
        result1 = integration.get_active_session_tasks(session_id)
        first_call_time = (time.time() - start_time) * 1000

        # Second call - should hit cache
        start_time = time.time()
        result2 = integration.get_active_session_tasks(session_id)
        second_call_time = (time.time() - start_time) * 1000

        # Verify caching worked
        assert result1.session_id == result2.session_id
        assert result1.total_count == result2.total_count
        assert second_call_time < first_call_time  # Cached call should be faster

    def test_performance_monitoring(self, integration, sample_tasks):
        """Test performance monitoring functionality."""
        # Perform some operations
        session_id = str(uuid.uuid4())
        task_ids = []

        for task_data in sample_tasks:
            task_id = integration.dal.add_task(task_data)
            task_ids.append(task_id)

        integration.link_tasks_to_session(task_ids, session_id)
        integration.get_session_continuity_score(session_id)
        integration.get_active_session_tasks(session_id)

        # Get performance metrics
        metrics = integration.get_performance_metrics()

        # Verify metrics are tracked
        assert 'link_tasks_to_session' in metrics
        assert 'get_session_continuity_score' in metrics
        assert 'get_active_session_tasks' in metrics

        # Verify metric structure
        for operation, metric in metrics.items():
            assert 'count' in metric
            assert 'avg_time_ms' in metric
            assert 'min_time_ms' in metric
            assert 'max_time_ms' in metric
            assert 'last_10_avg_ms' in metric
            assert metric['count'] > 0

    def test_cache_management(self, integration, sample_tasks):
        """Test cache management functionality."""
        session_id = str(uuid.uuid4())

        # Add sample tasks and populate cache
        for task_data in sample_tasks:
            task_id = integration.dal.add_task(task_data)
            integration.dal.update_task(task_id, {'session_id': session_id})

        integration.get_active_session_tasks(session_id)

        # Verify cache exists
        assert session_id in integration._session_cache
        assert session_id in integration._cache_expiry

        # Clear cache
        integration.clear_cache()

        # Verify cache is cleared
        assert len(integration._session_cache) == 0
        assert len(integration._cache_expiry) == 0

    def test_session_memory_bridge_integration(self, integration, sample_tasks):
        """Test integration with SessionMemoryBridge."""
        session_id = str(uuid.uuid4())
        task_ids = []

        # Add and link tasks
        for task_data in sample_tasks:
            task_id = integration.dal.add_task(task_data)
            task_ids.append(task_id)
            integration.dal.update_task(task_id, {
                'session_id': session_id,
                'context_criticality': 0.6  # Above threshold for bridge creation
            })

        # Migrate session (should create bridge)
        result = integration.migrate_session_state(session_id, str(uuid.uuid4()))

        # Verify bridge was created
        assert result.bridge_created is True
        assert result.bridge_id is not None

        # Verify bridge was called with correct parameters
        integration.session_memory_bridge.preserve_session_context.assert_called_once()
        call_args = integration.session_memory_bridge.preserve_session_context.call_args
        assert call_args[0][0] == session_id  # First argument should be session_id

    def test_thread_safety(self, integration, sample_tasks):
        """Test thread safety of operations."""
        import threading

        session_id = str(uuid.uuid4())
        task_ids = []
        results = []
        errors = []

        # Add tasks
        for task_data in sample_tasks:
            task_id = integration.dal.add_task(task_data)
            task_ids.append(task_id)

        def worker():
            try:
                result = integration.link_tasks_to_session(task_ids, session_id)
                results.append(result)
            except Exception as e:
                errors.append(e)

        # Create multiple threads
        threads = [threading.Thread(target=worker) for _ in range(5)]

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify no errors occurred
        assert len(errors) == 0, f"Thread safety errors: {errors}"
        assert len(results) == 5

        # All operations should succeed
        for result in results:
            assert result.success is True
            assert len(result.linked_tasks) == len(task_ids)

    def test_error_handling(self, integration):
        """Test error handling for various scenarios."""
        # Test with invalid session ID
        result = integration.get_session_continuity_score("invalid_session")
        assert result.session_id == "invalid_session"
        # Should handle gracefully without crashing

        # Test with non-existent session
        result = integration.get_active_session_tasks(str(uuid.uuid4()))
        assert result.total_count == 0
        assert len(result.tasks) == 0

    def test_data_integrity(self, integration, sample_tasks):
        """Test data integrity throughout operations."""
        session_id = str(uuid.uuid4())
        original_tasks = []

        # Add tasks and preserve original state
        for task_data in sample_tasks:
            task_id = integration.dal.add_task(task_data)
            task_data['id'] = task_id
            original_tasks.append(task_data.copy())

        # Link tasks
        integration.link_tasks_to_session([t['id'] for t in original_tasks], session_id)

        # Verify data integrity after linking
        all_tasks = integration.dal.get_all_tasks()
        for original in original_tasks:
            current = next((t for t in all_tasks if t['id'] == original['id']), None)
            assert current is not None

            # Verify original fields are preserved
            assert current['title'] == original['title']
            assert current['description'] == original['description']
            assert current['priority'] == original['priority']

            # Verify new session fields are added
            assert current['session_id'] == session_id
            assert current['session_span'] == 1


class TestFactoryFunctions:
    """Test factory functions for TaskMasterSessionIntegration."""

    def test_get_session_integration_singleton(self):
        """Test get_session_integration returns singleton instance."""
        # Reset global instance
        import session_integration
        session_integration._integration_instance = None

        # First call should create instance
        integration1 = get_session_integration()
        assert integration1 is not None

        # Second call should return same instance
        integration2 = get_session_integration()
        assert integration1 is integration2

    def test_create_session_integration_new_instance(self):
        """Test create_session_integration returns new instance."""
        integration1 = create_session_integration()
        integration2 = create_session_integration()

        assert integration1 is not integration2
        assert isinstance(integration1, TaskMasterSessionIntegration)
        assert isinstance(integration2, TaskMasterSessionIntegration)


# Performance benchmarks
class TestPerformanceBenchmarks:
    """Performance benchmark tests."""

    def test_link_tasks_performance(self, integration):
        """Benchmark task linking performance."""
        session_id = str(uuid.uuid4())
        task_count = 100
        task_ids = []

        # Create tasks
        for i in range(task_count):
            task_data = {
                'title': f'Performance Test Task {i}',
                'description': f'Task number {i}',
                'status': 'active',
                'priority': 'medium',
                'estimated_duration': 1.0
            }
            task_id = integration.dal.add_task(task_data)
            task_ids.append(task_id)

        # Measure performance
        start_time = time.time()
        result = integration.link_tasks_to_session(task_ids, session_id)
        execution_time = (time.time() - start_time) * 1000

        # Verify performance requirement
        assert result.success is True
        assert execution_time < 10 * task_count  # <10ms per task
        print(f"Linked {task_count} tasks in {execution_time:.1f}ms "
              f"({execution_time/task_count:.2f}ms per task)")

    def test_continuity_score_performance(self, integration):
        """Benchmark continuity score calculation performance."""
        session_count = 50
        tasks_per_session = 20

        # Create sessions and tasks
        for session_idx in range(session_count):
            session_id = str(uuid.uuid4())
            for task_idx in range(tasks_per_session):
                task_data = {
                    'title': f'Session {session_idx} Task {task_idx}',
                    'description': f'Task in session {session_id}',
                    'session_id': session_id,
                    'pre_compaction_state': json.dumps({'test': 'state'}) if task_idx < 10 else None,
                    'context_criticality': 0.8 if task_idx < 5 else 0.3
                }
                integration.dal.add_task(task_data)

        # Measure performance
        start_time = time.time()
        for session_idx in range(session_count):
            session_id = str(uuid.uuid4())
            result = integration.get_session_continuity_score(session_id)
            assert result.calculation_time_ms < 5  # <5ms per operation

        total_time = (time.time() - start_time) * 1000
        avg_time = total_time / session_count
        print(f"Calculated {session_count} continuity scores in {total_time:.1f}ms "
              f"({avg_time:.2f}ms per calculation)")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
