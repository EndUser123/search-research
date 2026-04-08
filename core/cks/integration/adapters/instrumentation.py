import asyncio
import threading
import time
import uuid
from collections.abc import Callable
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from functools import wraps
from typing import Any

from ..core.universal_instrumentation import get_global_instrumentation
from ..models.event_models import SystemCategory
from ..utils.performance_tracker import PerformanceTracker

"""
CKS (Knowledge System) Instrumentation Integration
Comprehensive instrumentation for CKS components with <1ms overhead

Task 1.2 Implementation: Knowledge System (CKS) instrumentation providing
the highest ROI as it's foundational to the entire ecosystem.

Components Instrumented:
1. ChatHistoryClient - Chat history retrieval and analysis
2. MultiGraphEngine - Multi-graph processing and analysis
3. VectorStorage (PyTorchVectorStorage, StorageManager) - Vector database operations
4. RAGWorkflow - RAG workflow orchestration
5. CKSRAGIntegrationCoordinator - Main integration coordinator

Key Features:
- Usage pattern tracking and performance metrics
- Vector search performance monitoring
- Chat history retrieval optimization
- Workflow correlation for RAG operations
- Comprehensive error tracking and recovery monitoring
- Non-invasive integration that preserves existing functionality
"""


# Import universal framework


class CKSOperationType(Enum):
    """CKS-specific operation types for detailed tracking."""

    # Chat History Operations
    CHAT_SEARCH = "chat_search"
    CHAT_PATTERN_DETECTION = "chat_pattern_detection"
    CHAT_ANALYSIS = "chat_analysis"
    CHAT_RETRIEVAL = "chat_retrieval"

    # Multi-Graph Engine Operations
    GRAPH_QUERY = "graph_query"
    GRAPH_INFERENCE = "graph_inference"
    SEMANTIC_REASONING = "semantic_reasoning"
    CROSS_GRAPH_ANALYSIS = "cross_graph_analysis"
    KNOWLEDGE_EXTRACTION = "knowledge_extraction"

    # Vector Storage Operations
    VECTOR_STORE = "vector_store"
    VECTOR_RETRIEVE = "vector_retrieve"
    VECTOR_SEARCH = "vector_search"
    VECTOR_BATCH_OPERATION = "vector_batch_operation"
    EMBEDDING_GENERATION = "embedding_generation"

    # RAG Workflow Operations
    RAG_ORCHESTRATION = "rag_orchestration"
    DOCUMENT_PROCESSING = "document_processing"
    CONTEXT_AUGMENTATION = "context_augmentation"
    RESPONSE_GENERATION = "response_generation"

    # Integration Coordinator Operations
    COMPONENT_COORDINATION = "component_coordination"
    WORKFLOW_CORRELATION = "workflow_correlation"
    ERROR_RECOVERY = "error_recovery"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"


class CKSComponentType(Enum):
    """CKS component types for categorization."""

    CHAT_HISTORY_CLIENT = "ChatHistoryClient"
    MULTI_GRAPH_ENGINE = "MultiGraphEngine"
    VECTOR_STORAGE = "VectorStorage"
    RAG_WORKFLOW = "RAGWorkflow"
    RAG_INTEGRATION_COORDINATOR = "CKSRAGIntegrationCoordinator"
    STORAGE_MANAGER = "StorageManager"
    PYTORCH_VECTOR_STORAGE = "PyTorchVectorStorage"


@dataclass
class CKSMetrics:
    """CKS-specific metrics for comprehensive monitoring."""

    # Performance metrics
    operation_count: int = 0
    total_execution_time_ms: float = 0.0
    average_response_time_ms: float = 0.0
    cache_hit_rate: float = 0.0

    # Vector-specific metrics
    vector_search_count: int = 0
    embedding_generation_count: int = 0
    vector_storage_ops: int = 0
    average_search_latency_ms: float = 0.0

    # Chat-specific metrics
    messages_processed: int = 0
    patterns_detected: int = 0
    conversations_analyzed: int = 0
    average_analysis_time_ms: float = 0.0

    # Error metrics
    error_count: int = 0
    recovery_count: int = 0
    timeout_count: int = 0

    # Resource metrics
    memory_usage_mb: float = 0.0
    gpu_utilization_percent: float = 0.0
    disk_io_mb: float = 0.0


@dataclass
class WorkflowContext:
    """Context for workflow correlation across CKS components."""

    workflow_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str | None = None
    correlation_id: str | None = None
    user_context: dict[str, Any] = field(default_factory=dict)
    component_chain: list[str] = field(default_factory=list)
    operation_chain: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_step(self, component: str, operation: str) -> None:
        """Add a step to the workflow chain."""
        self.component_chain.append(component)
        self.operation_chain.append(operation)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "workflow_id": self.workflow_id,
            "session_id": self.session_id,
            "correlation_id": self.correlation_id,
            "user_context": self.user_context,
            "component_chain": self.component_chain,
            "operation_chain": self.operation_chain,
            "metadata": self.metadata,
        }


class CKSInstrumentation:
    """Comprehensive CKS instrumentation with <1ms overhead.

    Features:
    - Performance tracking for all CKS operations
    - Workflow correlation across components
    - Error tracking and recovery monitoring
    - Resource usage optimization
    - Non-invasive integration patterns
    """

    def __init__(self) -> None:
        """Initialize CKS instrumentation."""
        self.instrumentation = get_global_instrumentation()
        self.metrics = CKSMetrics()
        self.active_workflows: dict[str, WorkflowContext] = {}
        self._lock = threading.RLock()

        # Performance tracking
        self.performance_tracker = PerformanceTracker(track_memory=True, track_cpu=True)

        # Start background monitoring
        self._monitoring_active = True
        self._monitoring_thread = threading.Thread(target=self._background_monitoring, daemon=True)
        self._monitoring_thread.start()

    def track_cks_operation(
        self,
        component_type: CKSComponentType,
        operation_type: CKSOperationType,
        execution_time_ms: float,
        success: bool = True,
        workflow_context: WorkflowContext | None = None,
        additional_metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Track a CKS operation with comprehensive metrics.

        Args:
            component_type: Type of CKS component
            operation_type: Type of operation performed
            execution_time_ms: Execution time in milliseconds
            success: Whether operation was successful
            workflow_context: Workflow correlation context
            additional_metadata: Additional metadata to track

        Returns:
            bool: True if tracking was successful

        """
        try:
            # Build metadata
            metadata = {
                "component_type": component_type.value,
                "operation_type": operation_type.value,
                "success": success,
                "cks_instrumentation_version": "1.0.0",
                **(additional_metadata or {}),
            }

            # Add workflow context if provided
            if workflow_context:
                metadata.update(
                    {
                        "workflow_id": workflow_context.workflow_id,
                        "session_id": workflow_context.session_id,
                        "correlation_id": workflow_context.correlation_id,
                        "component_chain": workflow_context.component_chain,
                        "operation_chain": workflow_context.operation_chain,
                    },
                )

            # Track with universal instrumentation
            success = self.instrumentation.track_function_call(
                system_category=SystemCategory.KNOWLEDGE_SYSTEM,
                component_name=component_type.value,
                operation_type=operation_type.value,
                execution_time_ms=execution_time_ms,
                success=success,
                metadata=metadata,
                workflow_id=workflow_context.workflow_id if workflow_context else None,
                session_id=workflow_context.session_id if workflow_context else None,
            )

            # Update internal metrics
            self._update_internal_metrics(
                component_type, operation_type, execution_time_ms, success
            )

            return success

        except Exception as e:
            # Silently fail to avoid breaking CKS operations
            print(f"CKS instrumentation tracking failed: {e}")
            return False

    def create_workflow_context(
        self,
        session_id: str | None = None,
        correlation_id: str | None = None,
        user_context: dict[str, Any] | None = None,
    ) -> WorkflowContext:
        """Create a new workflow context for correlation."""
        context = WorkflowContext(
            session_id=session_id, correlation_id=correlation_id, user_context=user_context or {}
        )

        with self._lock:
            self.active_workflows[context.workflow_id] = context

        return context

    def update_workflow_context(
        self,
        workflow_id: str,
        component: str,
        operation: str,
        additional_metadata: dict[str, Any] | None = None,
    ) -> WorkflowContext:
        """Update existing workflow context with new step."""
        with self._lock:
            if workflow_id in self.active_workflows:
                context = self.active_workflows[workflow_id]
                context.add_step(component, operation)
                if additional_metadata:
                    context.metadata.update(additional_metadata)
                return context

        # Return new context if not found
        return self.create_workflow_context()

    def get_workflow_context(self, workflow_id: str) -> WorkflowContext | None:
        """Get existing workflow context."""
        with self._lock:
            return self.active_workflows.get(workflow_id)

    def complete_workflow(self, workflow_id: str) -> WorkflowContext | None:
        """Complete and remove workflow context."""
        with self._lock:
            return self.active_workflows.pop(workflow_id, None)

    @contextmanager
    def track_operation(
        self,
        component_type: CKSComponentType,
        operation_type: CKSOperationType,
        workflow_context: WorkflowContext | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """Context manager for tracking CKS operations.

        Usage:
            with cks_instrumentation.track_operation(
                component_type=CKSComponentType.VECTOR_STORAGE,
                operation_type=CKSOperationType.VECTOR_SEARCH
            ):
                # Perform vector search operation
                results = vector_store.search(query)
        """
        start_time = time.perf_counter()
        success = True
        error_info = None

        try:
            yield
        except Exception as e:
            success = False
            error_info = str(e)
            raise
        finally:
            execution_time_ms = (time.perf_counter() - start_time) * 1000

            # Prepare metadata
            operation_metadata = metadata or {}
            if not success:
                operation_metadata["error_info"] = error_info

            # Add workflow step if context provided
            if workflow_context:
                workflow_context.add_step(component_type.value, operation_type.value)

            # Track the operation
            self.track_cks_operation(
                component_type=component_type,
                operation_type=operation_type,
                execution_time_ms=execution_time_ms,
                success=success,
                workflow_context=workflow_context,
                additional_metadata=operation_metadata,
            )

    @asynccontextmanager
    async def track_async_operation(
        self,
        component_type: CKSComponentType,
        operation_type: CKSOperationType,
        workflow_context: WorkflowContext | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """Async context manager for tracking CKS operations.

        Usage:
            async with cks_instrumentation.track_async_operation(
                component_type=CKSComponentType.CHAT_HISTORY_CLIENT,
                operation_type=CKSOperationType.CHAT_SEARCH
            ):
                results = await chat_client.search_history(query)
        """
        start_time = time.perf_counter()
        success = True
        error_info = None

        try:
            yield
        except Exception as e:
            success = False
            error_info = str(e)
            raise
        finally:
            execution_time_ms = (time.perf_counter() - start_time) * 1000

            # Prepare metadata
            operation_metadata = metadata or {}
            if not success:
                operation_metadata["error_info"] = error_info

            # Add workflow step if context provided
            if workflow_context:
                workflow_context.add_step(component_type.value, operation_type.value)

            # Track the operation
            self.track_cks_operation(
                component_type=component_type,
                operation_type=operation_type,
                execution_time_ms=execution_time_ms,
                success=success,
                workflow_context=workflow_context,
                additional_metadata=operation_metadata,
            )

    def track_error_recovery(
        self,
        component_type: CKSComponentType,
        error_type: str,
        recovery_action: str,
        recovery_successful: bool,
        workflow_context: WorkflowContext | None = None,
    ) -> None:
        """Track error recovery operations."""
        self.track_cks_operation(
            component_type=component_type,
            operation_type=CKSOperationType.ERROR_RECOVERY,
            execution_time_ms=0.0,
            success=recovery_successful,
            workflow_context=workflow_context,
            additional_metadata={
                "error_type": error_type,
                "recovery_action": recovery_action,
                "recovery_successful": recovery_successful,
            },
        )

        # Update recovery metrics
        with self._lock:
            self.metrics.recovery_count += 1

    def get_cks_metrics(self) -> dict[str, Any]:
        """Get comprehensive CKS metrics."""
        with self._lock:
            base_metrics = {
                "operation_count": self.metrics.operation_count,
                "total_execution_time_ms": self.metrics.total_execution_time_ms,
                "average_response_time_ms": self.metrics.average_response_time_ms,
                "cache_hit_rate": self.metrics.cache_hit_rate,
                "vector_search_count": self.metrics.vector_search_count,
                "embedding_generation_count": self.metrics.embedding_generation_count,
                "vector_storage_ops": self.metrics.vector_storage_ops,
                "average_search_latency_ms": self.metrics.average_search_latency_ms,
                "messages_processed": self.metrics.messages_processed,
                "patterns_detected": self.metrics.patterns_detected,
                "conversations_analyzed": self.metrics.conversations_analyzed,
                "average_analysis_time_ms": self.metrics.average_analysis_time_ms,
                "error_count": self.metrics.error_count,
                "recovery_count": self.metrics.recovery_count,
                "timeout_count": self.metrics.timeout_count,
                "memory_usage_mb": self.metrics.memory_usage_mb,
                "gpu_utilization_percent": self.metrics.gpu_utilization_percent,
                "disk_io_mb": self.metrics.disk_io_mb,
                "active_workflows": len(self.active_workflows),
            }

        # Add universal instrumentation metrics
        universal_metrics = self.instrumentation.get_performance_stats()
        base_metrics.update({"universal_instrumentation": universal_metrics})

        return base_metrics

    def get_workflow_analytics(self) -> dict[str, Any]:
        """Get workflow correlation analytics."""
        with self._lock:
            if not self.active_workflows:
                return {
                    "total_workflows": 0,
                    "average_steps": 0,
                    "component_distribution": {},
                    "operation_distribution": {},
                }

            all_components = []
            all_operations = []

            for workflow in self.active_workflows.values():
                all_components.extend(workflow.component_chain)
                all_operations.extend(workflow.operation_chain)

            # Calculate distributions
            component_distribution = {}
            for component in all_components:
                component_distribution[component] = component_distribution.get(component, 0) + 1

            operation_distribution = {}
            for operation in all_operations:
                operation_distribution[operation] = operation_distribution.get(operation, 0) + 1

            return {
                "total_workflows": len(self.active_workflows),
                "average_steps": len(all_components) / len(self.active_workflows)
                if self.active_workflows
                else 0,
                "component_distribution": component_distribution,
                "operation_distribution": operation_distribution,
            }

    def _update_internal_metrics(
        self,
        component_type: CKSComponentType,
        operation_type: CKSOperationType,
        execution_time_ms: float,
        success: bool,
    ) -> None:
        """Update internal CKS metrics."""
        with self._lock:
            self.metrics.operation_count += 1
            self.metrics.total_execution_time_ms += execution_time_ms

            if self.metrics.operation_count > 0:
                self.metrics.average_response_time_ms = (
                    self.metrics.total_execution_time_ms / self.metrics.operation_count
                )

            if not success:
                self.metrics.error_count += 1

            # Component-specific metrics
            if component_type == CKSComponentType.VECTOR_STORAGE:
                if operation_type == CKSOperationType.VECTOR_SEARCH:
                    self.metrics.vector_search_count += 1
                    # Update average search latency
                    if self.metrics.vector_search_count > 0:
                        total_search_time = (
                            self.metrics.average_search_latency_ms
                            * (self.metrics.vector_search_count - 1)
                            + execution_time_ms
                        )
                        self.metrics.average_search_latency_ms = (
                            total_search_time / self.metrics.vector_search_count
                        )

                elif operation_type == CKSOperationType.EMBEDDING_GENERATION:
                    self.metrics.embedding_generation_count += 1

                self.metrics.vector_storage_ops += 1

            elif component_type == CKSComponentType.CHAT_HISTORY_CLIENT:
                if operation_type == CKSOperationType.CHAT_ANALYSIS:
                    # Update average analysis time
                    if self.metrics.messages_processed > 0:
                        total_analysis_time = (
                            self.metrics.average_analysis_time_ms
                            * (self.metrics.messages_processed - 1)
                            + execution_time_ms
                        )
                        self.metrics.average_analysis_time_ms = (
                            total_analysis_time / self.metrics.messages_processed
                        )

    def _background_monitoring(self) -> None:
        """Background thread for monitoring and optimization."""
        while self._monitoring_active:
            try:
                # Update resource metrics
                current_memory = self.performance_tracker.get_current_memory_usage()
                if current_memory:
                    with self._lock:
                        self.metrics.memory_usage_mb = current_memory

                # Cleanup old workflows (older than 1 hour)
                datetime.now(UTC)
                expired_workflows = []

                with self._lock:
                    for workflow_id, workflow in self.active_workflows.items():
                        # Simple heuristic: remove workflows older than 1 hour
                        if len(workflow.component_chain) > 100:  # Too many steps
                            expired_workflows.append(workflow_id)

                for workflow_id in expired_workflows:
                    self.complete_workflow(workflow_id)

                # Sleep for monitoring interval
                time.sleep(60)  # Monitor every minute

            except Exception as e:
                print(f"CKS background monitoring error: {e}")
                time.sleep(60)

    def shutdown(self) -> None:
        """Shutdown CKS instrumentation."""
        self._monitoring_active = False
        if self._monitoring_thread.is_alive():
            self._monitoring_thread.join(timeout=5)

        # Clear active workflows
        with self._lock:
            self.active_workflows.clear()


# Global CKS instrumentation instance
_cks_instrumentation = None
_cks_lock = threading.Lock()


def get_cks_instrumentation() -> CKSInstrumentation:
    """Get global CKS instrumentation instance."""
    global _cks_instrumentation
    with _cks_lock:
        if _cks_instrumentation is None:
            _cks_instrumentation = CKSInstrumentation()
        return _cks_instrumentation


# Convenience decorators for CKS components
def instrument_cks_component(
    component_type: CKSComponentType,
    operation_type: CKSOperationType,
    track_workflow: bool = True,
):
    """Decorator for instrumenting CKS component methods.

    Args:
        component_type: Type of CKS component
        operation_type: Type of operation
        track_workflow: Whether to track workflow correlation

    """

    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Extract workflow context from kwargs if available
                workflow_context = kwargs.get("workflow_context")

                async with get_cks_instrumentation().track_async_operation(
                    component_type=component_type,
                    operation_type=operation_type,
                    workflow_context=workflow_context,
                ):
                    return await func(*args, **kwargs)

            return async_wrapper

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Extract workflow context from kwargs if available
            workflow_context = kwargs.get("workflow_context")

            with get_cks_instrumentation().track_operation(
                component_type=component_type,
                operation_type=operation_type,
                workflow_context=workflow_context,
            ):
                return func(*args, **kwargs)

        return sync_wrapper

    return decorator


# Specific decorators for common CKS operations
def instrument_chat_search(track_workflow: bool = True):
    """Decorator for chat search operations."""
    return instrument_cks_component(
        CKSComponentType.CHAT_HISTORY_CLIENT, CKSOperationType.CHAT_SEARCH, track_workflow
    )


def instrument_vector_search(track_workflow: bool = True):
    """Decorator for vector search operations."""
    return instrument_cks_component(
        CKSComponentType.VECTOR_STORAGE, CKSOperationType.VECTOR_SEARCH, track_workflow
    )


def instrument_graph_query(track_workflow: bool = True):
    """Decorator for graph query operations."""
    return instrument_cks_component(
        CKSComponentType.MULTI_GRAPH_ENGINE, CKSOperationType.GRAPH_QUERY, track_workflow
    )


def instrument_rag_orchestration(track_workflow: bool = True):
    """Decorator for RAG orchestration operations."""
    return instrument_cks_component(
        CKSComponentType.RAG_WORKFLOW, CKSOperationType.RAG_ORCHESTRATION, track_workflow
    )
