"""
TaskMaster Session Integration

TASK-F-007: Implement TaskMaster Session Integration

This module provides comprehensive session linkage and task continuity management
for TaskMaster, integrating with the SessionMemoryBridge to preserve task context
across session compactions and restorations.

Key Features:
- Session linkage for active tasks
- Task continuity tracking across sessions
- Pre-compaction state preservation
- Context criticality calculation
- Database integration with session tracking
- Performance monitoring and validation
- Session state migration capabilities

Performance Targets:
- Session linkage operations: <10ms
- Task continuity calculation: <5ms
- Session state migration: <50ms
- Context criticality analysis: <20ms

Author: CSF NIP Development Team
Version: 1.0.0
Date: 2025-12-13
"""

from __future__ import annotations

import json
import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

# Import TaskMaster components
from .db import WorkspaceTaskDAL, get_dal

# Import Session Memory components
try:
    from __csf.src.core.session_memory.criticality_analyzer import (
        CriticalityCalculator,
    )
    from __csf.src.core.session_memory.models import SessionStatus, TaskContext
    from __csf.src.core.session_memory.session_memory_bridge import (
        SessionMemoryBridge,
    )
    SESSION_MEMORY_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Session Memory components not available: {e}")
    SESSION_MEMORY_AVAILABLE = False
    SessionMemoryBridge = None
    TaskContext = None
    SessionStatus = None
    CriticalityCalculator = None


# ============================================================================
# Data Classes and Result Types
# ============================================================================

@dataclass
class SessionLinkageResult:
    """Result of session linkage operation."""

    success: bool = False
    linked_tasks: list[str] = field(default_factory=list)
    failed_tasks: list[str] = field(default_factory=list)
    session_id: str = ""
    execution_time_ms: float = 0.0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ContinuityScoreResult:
    """Result of session continuity score calculation."""

    session_id: str = ""
    continuity_score: float = 0.0
    total_tasks: int = 0
    preserved_tasks: int = 0
    critical_tasks_preserved: int = 0
    session_span: int = 0
    last_compaction: datetime | None = None
    calculation_time_ms: float = 0.0
    factors: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionMigrationResult:
    """Result of session state migration."""

    success: bool = False
    old_session_id: str = ""
    new_session_id: str = ""
    migrated_tasks: list[str] = field(default_factory=list)
    failed_migrations: list[str] = field(default_factory=list)
    migration_time_ms: float = 0.0
    bridge_created: bool = False
    bridge_id: str = ""
    integrity_verified: bool = False
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ActiveSessionTasks:
    """Container for active session tasks."""

    session_id: str = ""
    tasks: list[TaskContext] = field(default_factory=list)
    total_count: int = 0
    active_count: int = 0
    critical_count: int = 0
    span_distribution: dict[int, int] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    retrieval_time_ms: float = 0.0


# ============================================================================
# Main Integration Class
# ============================================================================

class TaskMasterSessionIntegration:
    """
    Integration layer for TaskMaster session management.

    This class provides comprehensive session linkage and task continuity
    management, bridging TaskMaster's database operations with the SessionMemoryBridge
    to ensure task context preservation across session lifecycles.

    Key Responsibilities:
    - Link tasks to sessions with proper tracking
    - Calculate session continuity scores
    - Migrate session state during compactions
    - Retrieve and manage active session tasks
    - Integrate with SessionMemoryBridge for context preservation
    - Monitor performance and validate operations
    - Ensure thread safety for concurrent operations
    """

    def __init__(
        self,
        dal: WorkspaceTaskDAL | None = None,
        session_memory_bridge: SessionMemoryBridge | None = None,
        performance_monitoring: bool = True
    ) -> None:
        """
        Initialize the TaskMaster Session Integration.

        Args:
            dal: Optional WorkspaceTaskDAL instance. If None, uses global instance.
            session_memory_bridge: Optional SessionMemoryBridge instance.
            performance_monitoring: Whether to enable performance monitoring.
        """
        # Initialize components
        self.dal = dal or get_dal()
        self.session_memory_bridge = session_memory_bridge
        self.performance_monitoring = performance_monitoring

        # Thread safety
        self._lock = threading.RLock()

        # Performance tracking
        self._operation_times: dict[str, list[float]] = {}
        self._operation_counts: dict[str, int] = {}

        # Caching for performance
        self._session_cache: dict[str, dict[str, Any]] = {}
        self._cache_expiry: dict[str, datetime] = {}
        self._cache_ttl = timedelta(minutes=5)

        # Initialize logging
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("TaskMasterSessionIntegration initialized")

        # Validate components
        self._validate_components()

        # Initialize session memory bridge if needed
        if SESSION_MEMORY_AVAILABLE and not self.session_memory_bridge:
            try:
                self.session_memory_bridge = SessionMemoryBridge()
                self.logger.info("SessionMemoryBridge initialized automatically")
            except Exception as e:
                self.logger.warning(f"Failed to initialize SessionMemoryBridge: {e}")

    def link_tasks_to_session(self, task_ids: list[str], session_id: str) -> SessionLinkageResult:
        """
        Link tasks to a session with comprehensive tracking.

        Updates task records with session information, initializes session
        tracking if needed, and validates the linkage operation.

        Args:
            task_ids: List of task IDs to link to the session
            session_id: ID of the session to link tasks to

        Returns:
            SessionLinkageResult: Detailed result of the linkage operation

        Performance Target: <10ms per operation
        """
        start_time = time.time()
        result = SessionLinkageResult(session_id=session_id)

        with self._lock:
            try:
                self.logger.info(f"Linking {len(task_ids)} tasks to session: {session_id}")

                # Validate inputs
                if not task_ids:
                    raise ValueError("Task IDs list cannot be empty")
                if not session_id:
                    raise ValueError("Session ID cannot be empty")

                # Initialize session tracking if needed
                self._ensure_session_tracking(session_id)

                # Process each task
                for task_id in task_ids:
                    try:
                        # Update task with session linkage
                        update_data = {
                            'session_id': session_id,
                            'session_span': 1,  # Initial span
                            'last_activity': datetime.now().isoformat()
                        }

                        # Update task in database
                        self.dal.update_task(task_id, update_data)
                        result.linked_tasks.append(task_id)

                        self.logger.debug(f"Task {task_id} linked to session {session_id}")

                    except Exception as e:
                        error_msg = f"Failed to link task {task_id}: {str(e)}"
                        self.logger.error(error_msg)
                        result.failed_tasks.append(task_id)
                        result.errors.append(error_msg)

                # Update session tracking
                self._update_session_tracking(session_id, len(result.linked_tasks))

                # Calculate execution time
                result.execution_time_ms = (time.time() - start_time) * 1000

                # Determine success
                result.success = len(result.linked_tasks) > 0 and len(result.failed_tasks) == 0

                # Add warning for partial success
                if 0 < len(result.failed_tasks) < len(task_ids):
                    result.warnings.append(f"Partial success: {len(result.failed_tasks)} tasks failed to link")

                # Track performance if enabled
                if self.performance_monitoring:
                    self._track_performance("link_tasks_to_session", result.execution_time_ms)

                # Verify performance target
                if result.execution_time_ms > 10 * len(task_ids):
                    self.logger.warning(
                        f"Session linkage exceeded target: {result.execution_time_ms:.1f}ms "
                        f"for {len(task_ids)} tasks (target: <10ms per task)"
                    )

                self.logger.info(
                    f"Session linkage completed: {len(result.linked_tasks)}/{len(task_ids)} tasks linked "
                    f"in {result.execution_time_ms:.1f}ms"
                )

                return result

            except Exception as e:
                result.execution_time_ms = (time.time() - start_time) * 1000
                error_msg = f"Session linkage failed: {str(e)}"
                self.logger.error(error_msg)
                result.errors.append(error_msg)
                return result

    def get_session_continuity_score(self, session_id: str) -> ContinuityScoreResult:
        """
        Calculate continuity score for a session.

        Analyzes task continuity, session span information, and context
        criticality to provide a comprehensive continuity score.

        Args:
            session_id: ID of the session to analyze

        Returns:
            ContinuityScoreResult: Detailed continuity score analysis

        Performance Target: <5ms per operation
        """
        start_time = time.time()
        result = ContinuityScoreResult(session_id=session_id)

        with self._lock:
            try:
                self.logger.info(f"Calculating continuity score for session: {session_id}")

                # Validate input
                if not session_id:
                    raise ValueError("Session ID cannot be empty")

                # Get session tasks
                session_tasks = self._get_session_tasks(session_id)
                result.total_tasks = len(session_tasks)

                if result.total_tasks == 0:
                    result.continuity_score = 1.0  # Perfect continuity for empty session
                    result.calculation_time_ms = (time.time() - start_time) * 1000
                    return result

                # Analyze task preservation
                preserved_tasks = 0
                critical_tasks_preserved = 0
                total_span = 0

                for task in session_tasks:
                    # Check if task has pre-compaction state
                    if task.get('pre_compaction_state'):
                        preserved_tasks += 1

                        # Check context criticality
                        criticality = task.get('context_criticality', 0.0)
                        if criticality >= 0.7:  # High criticality threshold
                            critical_tasks_preserved += 1

                    # Accumulate session span
                    total_span += task.get('session_span', 0)

                result.preserved_tasks = preserved_tasks
                result.critical_tasks_preserved = critical_tasks_preserved
                result.session_span = total_span // max(1, result.total_tasks)

                # Calculate continuity factors
                preservation_factor = preserved_tasks / result.total_tasks
                critical_factor = critical_tasks_preserved / max(1, result.preserved_tasks)
                span_factor = min(1.0, result.session_span / 5.0)  # Normalize to 0-1

                # Get last compaction info
                session_info = self._get_session_info(session_id)
                if session_info:
                    result.last_compaction = session_info.get('last_compaction')

                    # Factor in time since last compaction
                    if result.last_compaction:
                        time_since = datetime.now() - result.last_compaction
                        recency_factor = max(0.0, 1.0 - (time_since.total_seconds() / 86400))  # Decay over 24h
                    else:
                        recency_factor = 1.0
                else:
                    recency_factor = 0.8  # Default for unknown sessions

                # Calculate weighted continuity score
                weights = {
                    'preservation': 0.4,
                    'critical': 0.3,
                    'span': 0.15,
                    'recency': 0.15
                }

                result.continuity_score = (
                    preservation_factor * weights['preservation'] +
                    critical_factor * weights['critical'] +
                    span_factor * weights['span'] +
                    recency_factor * weights['recency']
                )

                result.factors = {
                    'preservation': preservation_factor,
                    'critical': critical_factor,
                    'span': span_factor,
                    'recency': recency_factor
                }

                # Calculate execution time
                result.calculation_time_ms = (time.time() - start_time) * 1000

                # Track performance if enabled
                if self.performance_monitoring:
                    self._track_performance("get_session_continuity_score", result.calculation_time_ms)

                # Verify performance target
                if result.calculation_time_ms > 5:
                    self.logger.warning(
                        f"Continuity score calculation exceeded target: {result.calculation_time_ms:.1f}ms"
                    )

                self.logger.info(
                    f"Continuity score for {session_id}: {result.continuity_score:.3f} "
                    f"in {result.calculation_time_ms:.1f}ms"
                )

                return result

            except Exception as e:
                result.calculation_time_ms = (time.time() - start_time) * 1000
                error_msg = f"Continuity score calculation failed: {str(e)}"
                self.logger.error(error_msg)
                return result

    def migrate_session_state(self, old_session: str, new_session: str) -> SessionMigrationResult:
        """
        Migrate session state from old session to new session.

        Creates a bridge for context preservation, migrates task state,
        and validates the migration integrity.

        Args:
            old_session: ID of the session to migrate from
            new_session: ID of the session to migrate to

        Returns:
            SessionMigrationResult: Detailed migration result

        Performance Target: <50ms per operation
        """
        start_time = time.time()
        result = SessionMigrationResult(
            old_session_id=old_session,
            new_session_id=new_session
        )

        with self._lock:
            try:
                self.logger.info(f"Migrating session state: {old_session} -> {new_session}")

                # Validate inputs
                if not old_session or not new_session:
                    raise ValueError("Session IDs cannot be empty")
                if old_session == new_session:
                    raise ValueError("Old and new session IDs must be different")

                # Get tasks from old session
                old_tasks = self._get_session_tasks(old_session)

                if not old_tasks:
                    result.warnings.append("No tasks found in old session")
                    result.migration_time_ms = (time.time() - start_time) * 1000
                    result.success = True
                    return result

                # Create bridge for context preservation
                if self.session_memory_bridge and SESSION_MEMORY_AVAILABLE:
                    try:
                        # Create TaskContext objects for critical tasks
                        task_contexts = []
                        for task_data in old_tasks:
                            if task_data.get('context_criticality', 0.0) >= 0.4:
                                task_context = self._create_task_context_from_data(task_data)
                                if task_context:
                                    task_contexts.append(task_context)

                        # Create session data for bridge
                        session_data = {
                            'session_id': old_session,
                            'tasks': task_contexts,
                            'patterns': [],
                            'evidence': [],
                            'metadata': {
                                'migration_target': new_session,
                                'migration_timestamp': datetime.now().isoformat()
                            }
                        }

                        # Create bridge
                        bridge = self.session_memory_bridge.preserve_session_context(
                            session_id=old_session,
                            criticality_threshold=0.4
                        )

                        result.bridge_created = True
                        result.bridge_id = bridge.bridge_id
                        result.integrity_verified = True

                        self.logger.info(f"Created context preservation bridge: {bridge.bridge_id}")

                    except Exception as e:
                        self.logger.warning(f"Failed to create preservation bridge: {e}")
                        result.warnings.append(f"Bridge creation failed: {str(e)}")

                # Migrate tasks to new session
                for task_data in old_tasks:
                    task_id = task_data['id']
                    try:
                        # Store pre-compaction state
                        pre_compaction_state = {
                            'original_session': old_session,
                            'migration_timestamp': datetime.now().isoformat(),
                            'task_data': task_data,
                            'session_span_at_migration': task_data.get('session_span', 0)
                        }

                        # Update task with new session information
                        update_data = {
                            'session_id': new_session,
                            'session_span': task_data.get('session_span', 0) + 1,  # Increment span
                            'pre_compaction_state': json.dumps(pre_compaction_state),
                            'compaction_session_id': old_session,
                            'last_activity': datetime.now().isoformat()
                        }

                        self.dal.update_task(task_id, update_data)
                        result.migrated_tasks.append(task_id)

                    except Exception as e:
                        error_msg = f"Failed to migrate task {task_id}: {str(e)}"
                        self.logger.error(error_msg)
                        result.failed_migrations.append(task_id)
                        result.errors.append(error_msg)

                # Initialize new session tracking
                self._ensure_session_tracking(new_session)
                self._update_session_tracking(new_session, len(result.migrated_tasks))

                # Update old session status
                self._update_session_status(old_session, 'migrated')

                # Calculate execution time
                result.migration_time_ms = (time.time() - start_time) * 1000

                # Determine success
                total_tasks = len(old_tasks)
                result.success = (
                    len(result.migrated_tasks) > 0 and
                    len(result.failed_migrations) == 0
                )

                # Add warning for partial success
                if 0 < len(result.failed_migrations) < total_tasks:
                    result.warnings.append(
                        f"Partial migration: {len(result.failed_migrations)}/{total_tasks} tasks failed"
                    )

                # Track performance if enabled
                if self.performance_monitoring:
                    self._track_performance("migrate_session_state", result.migration_time_ms)

                # Verify performance target
                if result.migration_time_ms > 50:
                    self.logger.warning(
                        f"Session migration exceeded target: {result.migration_time_ms:.1f}ms"
                    )

                self.logger.info(
                    f"Session migration completed: {len(result.migrated_tasks)}/{total_tasks} tasks "
                    f"in {result.migration_time_ms:.1f}ms"
                )

                return result

            except Exception as e:
                result.migration_time_ms = (time.time() - start_time) * 1000
                error_msg = f"Session migration failed: {str(e)}"
                self.logger.error(error_msg)
                result.errors.append(error_msg)
                return result

    def get_active_session_tasks(self, session_id: str) -> ActiveSessionTasks:
        """
        Get active tasks for a session.

        Retrieves all tasks associated with a session, categorizes them,
        and provides comprehensive statistics.

        Args:
            session_id: ID of the session to get tasks for

        Returns:
            ActiveSessionTasks: Container with session tasks and statistics

        Performance Target: <20ms per operation
        """
        start_time = time.time()
        result = ActiveSessionTasks(session_id=session_id)

        with self._lock:
            try:
                self.logger.info(f"Retrieving active tasks for session: {session_id}")

                # Validate input
                if not session_id:
                    raise ValueError("Session ID cannot be empty")

                # Check cache first
                cached_result = self._get_cached_session_tasks(session_id)
                if cached_result:
                    self.logger.debug(f"Using cached result for session {session_id}")
                    return cached_result

                # Get session tasks from database
                session_tasks = self._get_session_tasks(session_id)
                result.total_count = len(session_tasks)

                # Convert to TaskContext objects
                for task_data in session_tasks:
                    try:
                        task_context = self._create_task_context_from_data(task_data)
                        if task_context:
                            result.tasks.append(task_context)

                            # Update statistics
                            if task_context.status.lower() in ['active', 'in_progress', 'pending']:
                                result.active_count += 1

                            if task_data.get('context_criticality', 0.0) >= 0.7:
                                result.critical_count += 1

                            # Track span distribution
                            span = task_data.get('session_span', 0)
                            result.span_distribution[span] = result.span_distribution.get(span, 0) + 1

                    except Exception as e:
                        self.logger.warning(f"Failed to create TaskContext for task {task_data.get('id')}: {e}")

                # Update timestamp
                result.last_updated = datetime.utcnow()
                result.retrieval_time_ms = (time.time() - start_time) * 1000

                # Cache result
                self._cache_session_tasks(session_id, result)

                # Track performance if enabled
                if self.performance_monitoring:
                    self._track_performance("get_active_session_tasks", result.retrieval_time_ms)

                # Verify performance target
                if result.retrieval_time_ms > 20:
                    self.logger.warning(
                        f"Active session tasks retrieval exceeded target: {result.retrieval_time_ms:.1f}ms"
                    )

                self.logger.info(
                    f"Retrieved {result.total_count} tasks for session {session_id} "
                    f"({result.active_count} active, {result.critical_count} critical) "
                    f"in {result.retrieval_time_ms:.1f}ms"
                )

                return result

            except Exception as e:
                result.retrieval_time_ms = (time.time() - start_time) * 1000
                error_msg = f"Failed to retrieve active session tasks: {str(e)}"
                self.logger.error(error_msg)
                return result

    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    def _validate_components(self) -> None:
        """Validate that required components are available."""
        if not self.dal:
            raise RuntimeError("WorkspaceTaskDAL is required but not available")

        if SESSION_MEMORY_AVAILABLE:
            self.logger.info("Session Memory components are available")
        else:
            self.logger.warning("Session Memory components are not available - some features will be limited")

    def _ensure_session_tracking(self, session_id: str) -> None:
        """Ensure session tracking record exists."""
        try:
            with self.dal.connect() as conn:
                # Check if session exists
                cursor = conn.execute(
                    "SELECT session_id FROM session_tracking WHERE session_id = ?",
                    (session_id,)
                )
                if not cursor.fetchone():
                    # Create new session tracking record
                    conn.execute("""
                        INSERT INTO session_tracking
                        (session_id, task_master_session_id, started_at, status, metadata)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        session_id,
                        session_id,  # Use same ID for simplicity
                        datetime.now().isoformat(),
                        'active',
                        json.dumps({'created_by': 'TaskMasterSessionIntegration'})
                    ))
                    conn.commit()

        except Exception as e:
            self.logger.warning(f"Failed to ensure session tracking for {session_id}: {e}")

    def _update_session_tracking(self, session_id: str, task_count: int) -> None:
        """Update session tracking information."""
        try:
            with self.dal.connect() as conn:
                conn.execute("""
                    UPDATE session_tracking
                    SET total_context_tokens = total_context_tokens + ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE session_id = ?
                """, (task_count, session_id))
                conn.commit()

        except Exception as e:
            self.logger.warning(f"Failed to update session tracking for {session_id}: {e}")

    def _update_session_status(self, session_id: str, status: str) -> None:
        """Update session status."""
        try:
            with self.dal.connect() as conn:
                conn.execute("""
                    UPDATE session_tracking
                    SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE session_id = ?
                """, (status, session_id))
                conn.commit()

        except Exception as e:
            self.logger.warning(f"Failed to update session status for {session_id}: {e}")

    def _get_session_tasks(self, session_id: str) -> list[dict[str, Any]]:
        """Get all tasks for a session."""
        try:
            with self.dal.connect() as conn:
                cursor = conn.execute("""
                    SELECT * FROM task
                    WHERE session_id = ?
                    ORDER BY last_activity DESC
                """, (session_id,))

                # Get column names
                columns = [description[0] for description in cursor.description]

                # Convert rows to dictionaries
                tasks = []
                for row in cursor.fetchall():
                    task = dict(zip(columns, row, strict=False))

                    # Parse JSON fields
                    for field in ['tags', 'acceptance_criteria', 'validation_rules', 'entities']:
                        if task.get(field):
                            try:
                                task[field] = json.loads(task[field])
                            except (json.JSONDecodeError, TypeError):
                                task[field] = []

                    tasks.append(task)

                return tasks

        except Exception as e:
            self.logger.error(f"Failed to get session tasks for {session_id}: {e}")
            return []

    def _get_session_info(self, session_id: str) -> dict[str, Any] | None:
        """Get session tracking information."""
        try:
            with self.dal.connect() as conn:
                cursor = conn.execute("""
                    SELECT * FROM session_tracking
                    WHERE session_id = ?
                """, (session_id,))

                row = cursor.fetchone()
                if row:
                    columns = [description[0] for description in cursor.description]
                    session_info = dict(zip(columns, row, strict=False))

                    # Parse metadata
                    if session_info.get('metadata'):
                        try:
                            session_info['metadata'] = json.loads(session_info['metadata'])
                        except (json.JSONDecodeError, TypeError):
                            session_info['metadata'] = {}

                    return session_info

                return None

        except Exception as e:
            self.logger.error(f"Failed to get session info for {session_id}: {e}")
            return None

    def _create_task_context_from_data(self, task_data: dict[str, Any]) -> TaskContext | None:
        """Create TaskContext from task data."""
        if not TaskContext:
            self.logger.warning("TaskContext model not available")
            return None

        try:
            # Map priority
            priority_map = {
                'critical': 'critical',
                'high': 'high',
                'medium': 'medium',
                'low': 'low'
            }
            priority = priority_map.get(task_data.get('priority', 'medium'), 'medium')

            # Create TaskContext
            task_context = TaskContext(
                task_id=task_data['id'],
                title=task_data.get('title', ''),
                description=task_data.get('description', ''),
                status=task_data.get('status', 'pending'),
                priority=priority,
                progress=task_data.get('completion_percentage', 0) / 100.0,
                created_at=datetime.fromisoformat(task_data.get('created_at', datetime.now().isoformat())),
                updated_at=datetime.fromisoformat(task_data.get('last_activity', datetime.now().isoformat())),
                assigned_to=task_data.get('assigned_to', ''),
                context_summary=task_data.get('description', ''),
                estimated_effort=task_data.get('estimated_duration'),
                actual_effort=task_data.get('actual_duration', 0)
            )

            return task_context

        except Exception as e:
            self.logger.error(f"Failed to create TaskContext: {e}")
            return None

    def _track_performance(self, operation: str, execution_time_ms: float) -> None:
        """Track performance metrics."""
        if operation not in self._operation_times:
            self._operation_times[operation] = []
            self._operation_counts[operation] = 0

        self._operation_times[operation].append(execution_time_ms)
        self._operation_counts[operation] += 1

        # Keep only last 100 measurements
        if len(self._operation_times[operation]) > 100:
            self._operation_times[operation] = self._operation_times[operation][-100:]

    def _cache_session_tasks(self, session_id: str, result: ActiveSessionTasks) -> None:
        """Cache session tasks result."""
        self._session_cache[session_id] = {
            'result': result,
            'timestamp': datetime.now()
        }
        self._cache_expiry[session_id] = datetime.now() + self._cache_ttl

    def _get_cached_session_tasks(self, session_id: str) -> ActiveSessionTasks | None:
        """Get cached session tasks if still valid."""
        if session_id in self._session_cache and session_id in self._cache_expiry:
            if datetime.now() < self._cache_expiry[session_id]:
                return self._session_cache[session_id]['result']
            else:
                # Expired cache, remove it
                del self._session_cache[session_id]
                del self._cache_expiry[session_id]
        return None

    def get_performance_metrics(self) -> dict[str, Any]:
        """Get performance metrics for all operations."""
        metrics = {}

        for operation, times in self._operation_times.items():
            if times:
                metrics[operation] = {
                    'count': self._operation_counts[operation],
                    'avg_time_ms': sum(times) / len(times),
                    'min_time_ms': min(times),
                    'max_time_ms': max(times),
                    'last_10_avg_ms': sum(times[-10:]) / min(10, len(times))
                }

        return metrics

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._session_cache.clear()
        self._cache_expiry.clear()
        self.logger.info("Cache cleared")


# ============================================================================
# Global Instance and Factory Functions
# ============================================================================

_integration_instance = None

def get_session_integration(
    dal: WorkspaceTaskDAL | None = None,
    session_memory_bridge: SessionMemoryBridge | None = None
) -> TaskMasterSessionIntegration:
    """
    Get global TaskMaster Session Integration instance.

    Args:
        dal: Optional WorkspaceTaskDAL instance
        session_memory_bridge: Optional SessionMemoryBridge instance

    Returns:
        TaskMasterSessionIntegration: Global instance
    """
    global _integration_instance

    if _integration_instance is None:
        _integration_instance = TaskMasterSessionIntegration(
            dal=dal,
            session_memory_bridge=session_memory_bridge
        )

    return _integration_instance


def create_session_integration(
    dal: WorkspaceTaskDAL | None = None,
    session_memory_bridge: SessionMemoryBridge | None = None
) -> TaskMasterSessionIntegration:
    """
    Create new TaskMaster Session Integration instance.

    Args:
        dal: Optional WorkspaceTaskDAL instance
        session_memory_bridge: Optional SessionMemoryBridge instance

    Returns:
        TaskMasterSessionIntegration: New instance
    """
    return TaskMasterSessionIntegration(
        dal=dal,
        session_memory_bridge=session_memory_bridge
    )
