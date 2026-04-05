"""
Workflow system adapters for evidence validation.

This module provides specialized adapters for workflow engines,
task runners, and orchestration systems.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from .base import HTTPAdapter, WebSocketAdapter, DirectAdapter
from ..models.schemas import EvidenceType, CacheStrategy


class WorkflowEngineAdapter:
    """
    Adapter for workflow engines like Apache Airflow, Luigi, or Prefect.

    Integrates evidence validation into workflow execution with
    automatic task evidence collection and validation.
    """

    def __init__(
        self,
        workflow_engine: str,
        base_url: str,
        api_key: Optional[str] = None,
        auto_validate_tasks: bool = True,
        validation_rules: Optional[List[str]] = None
    ):
        """Initialize workflow engine adapter.

        Args:
            workflow_engine: Name of the workflow engine
            base_url: Evidence validation API base URL
            api_key: Optional API key
            auto_validate_tasks: Automatically validate task completions
            validation_rules: Default validation rules to apply
        """
        self.workflow_engine = workflow_engine
        self.auto_validate_tasks = auto_validate_tasks
        self.default_validation_rules = validation_rules or []

        # Initialize HTTP adapter
        self.http_adapter = HTTPAdapter(
            component_name=f"{workflow_engine}_adapter",
            component_version="1.0.0")
            base_url=base_url,
            api_key=api_key
        )

    async def validate_task_execution(
        self,
        task_id: str,
        dag_id: Optional[str] = None,
        execution_date: Optional[datetime] = None,
        task_result: Optional[Dict[str, Any]] = None,
        task_logs: Optional[str] = None,
        execution_time: Optional[float] = None,
        validation_rules: Optional[List[str]] = None
    ):
        """Validate task execution evidence.

        Args:
            task_id: Task identifier
            dag_id: DAG/workflow identifier
            execution_date: Task execution date
            task_result: Task execution result
            task_logs: Task execution logs
            execution_time: Task execution time in seconds
            validation_rules: Specific validation rules to apply
        """
        evidence_data = {
            "task_id": task_id,
            "dag_id": dag_id,
            "execution_date": execution_date.isoformat() if execution_date else None,
            "task_result": task_result,
            "task_logs": task_logs,
            "execution_time": execution_time,
            "workflow_engine": self.workflow_engine,
        }

        metadata = {
            "workflow_id": dag_id,
            "task_id": task_id,
            "priority": 7,  # High priority for workflow tasks
            "tags": ["workflow", "task_execution", self.workflow_engine],
        }

        rules = validation_rules or self.default_validation_rules

        return await self.http_adapter.validate_evidence(
            evidence_data=evidence_data,
            evidence_type=EvidenceType.TASK_EXECUTION,
            metadata=metadata,
            validation_rules=rules,
            async_validation=True,  # Workflow validations should be async
            cache_strategy=CacheStrategy.MEDIUM_TERM
        )

    async def validate_workflow_metrics(
        self,
        workflow_id: str,
        metrics: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ):
        """Validate workflow performance metrics.

        Args:
            workflow_id: Workflow identifier
            metrics: Performance metrics data
            timestamp: Metrics collection timestamp
        """
        evidence_data = {
            "workflow_id": workflow_id,
            "metrics": metrics,
            "timestamp": timestamp.isoformat() if timestamp else datetime.now(timezone.utc).isoformat(),
            "workflow_engine": self.workflow_engine,
        }

        metadata = {
            "workflow_id": workflow_id,
            "tags": ["workflow", "metrics", self.workflow_engine],
            "priority": 5,
        }

        return await self.http_adapter.validate_evidence(
            evidence_data=evidence_data,
            evidence_type=EvidenceType.PERFORMANCE_METRIC,
            metadata=metadata,
            validation_rules=["content_integrity", "metric_validity"],
            async_validation=True,
            cache_strategy=CacheStrategy.SHORT_TERM
        )

    async def validate_workflow_artifact(
        self,
        workflow_id: str,
        artifact_path: str,
        artifact_type: str,
        artifact_hash: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Validate workflow artifact evidence.

        Args:
            workflow_id: Workflow identifier
            artifact_path: Path to the artifact
            artifact_type: Type of artifact (data_file, model, report, etc.)
            artifact_hash: SHA-256 hash of the artifact
            metadata: Additional artifact metadata
        """
        evidence_data = {
            "workflow_id": workflow_id,
            "artifact_path": artifact_path,
            "artifact_type": artifact_type,
            "artifact_hash": artifact_hash,
            "metadata": metadata or {},
            "workflow_engine": self.workflow_engine,
        }

        request_metadata = {
            "workflow_id": workflow_id,
            "tags": ["workflow", "artifact", artifact_type, self.workflow_engine],
            "priority": 6,
        }

        return await self.http_adapter.validate_evidence(
            evidence_data=evidence_data,
            evidence_type=EvidenceType.FILE_OPERATION,
            metadata=request_metadata,
            validation_rules=["file_integrity", "artifact_validity"],
            async_validation=True,
            cache_strategy=CacheStrategy.LONG_TERM
        )

    async def close(self):
        """Close adapter connections."""
        await self.http_adapter.close()


class TaskQueueAdapter:
    """
    Adapter for task queue systems like Celery, RQ, or Dramatiq.

    Integrates evidence validation into distributed task processing
    with automatic task result validation.
    """

    def __init__(
        self,
        task_queue_system: str,
        base_url: str,
        api_key: Optional[str] = None,
        validate_results: bool = True,
        validate_failures: bool = True
    ):
        """Initialize task queue adapter.

        Args:
            task_queue_system: Name of the task queue system
            base_url: Evidence validation API base URL
            api_key: Optional API key
            validate_results: Validate successful task results
            validate_failures: Validate task failures for analysis
        """
        self.task_queue_system = task_queue_system
        self.validate_results = validate_results
        self.validate_failures = validate_failures

        # Initialize HTTP adapter
        self.http_adapter = HTTPAdapter(
            component_name=f"{task_queue_system}_adapter",
            component_version="1.0.0")
            base_url=base_url,
            api_key=api_key
        )

    async def validate_task_result(
        self,
        task_id: str,
        task_name: str,
        worker_id: Optional[str] = None,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        result: Optional[Any] = None,
        success: bool = True,
        exception: Optional[str] = None,
        traceback: Optional[str] = None,
        runtime: Optional[float] = None
    ):
        """Validate task execution result.

        Args:
            task_id: Task identifier
            task_name: Name of the task function
            worker_id: Worker that executed the task
            args: Task arguments
            kwargs: Task keyword arguments
            result: Task result
            success: Whether task succeeded
            exception: Exception message if failed
            traceback: Exception traceback
            runtime: Task runtime in seconds
        """
        evidence_data = {
            "task_id": task_id,
            "task_name": task_name,
            "worker_id": worker_id,
            "args": args,
            "kwargs": kwargs,
            "result": result,
            "success": success,
            "exception": exception,
            "traceback": traceback,
            "runtime": runtime,
            "task_queue_system": self.task_queue_system,
        }

        # Determine evidence type based on success
        evidence_type = EvidenceType.TASK_EXECUTION if success else EvidenceType.ERROR_LOG

        metadata = {
            "task_id": task_id,
            "tags": ["task_queue", "task_execution", self.task_queue_system],
            "priority": 7 if success else 8,  # Higher priority for failures
            "severity": "low" if success else "high",
        }

        # Select validation rules based on result type
        if success and self.validate_results:
            validation_rules = ["content_integrity", "task_result_validity"]
        elif not success and self.validate_failures:
            validation_rules = ["error_analysis", "failure_validity"]
        else:
            validation_rules = []

        return await self.http_adapter.validate_evidence(
            evidence_data=evidence_data,
            evidence_type=evidence_type,
            metadata=metadata,
            validation_rules=validation_rules,
            async_validation=True,
            cache_strategy=CacheStrategy.MEDIUM_TERM
        )

    async def validate_queue_metrics(
        self,
        queue_name: str,
        metrics: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ):
        """Validate queue performance metrics.

        Args:
            queue_name: Queue name
            metrics: Queue metrics (queue_size, processing_rate, etc.)
            timestamp: Metrics collection timestamp
        """
        evidence_data = {
            "queue_name": queue_name,
            "metrics": metrics,
            "timestamp": timestamp.isoformat() if timestamp else datetime.now(timezone.utc).isoformat(),
            "task_queue_system": self.task_queue_system,
        }

        metadata = {
            "tags": ["task_queue", "metrics", queue_name, self.task_queue_system],
            "priority": 5,
        }

        return await self.http_adapter.validate_evidence(
            evidence_data=evidence_data,
            evidence_type=EvidenceType.PERFORMANCE_METRIC,
            metadata=metadata,
            validation_rules=["metric_validity", "performance_analysis"],
            async_validation=True,
            cache_strategy=CacheStrategy.SHORT_TERM
        )

    async def close(self):
        """Close adapter connections."""
        await self.http_adapter.close()


class OrchestrationAdapter:
    """
    Adapter for orchestration systems like Kubernetes, Docker Swarm,
    or Apache Mesos.

    Integrates evidence validation into container orchestration
    and service mesh operations.
    """

    def __init__(
        self,
        orchestration_platform: str,
        base_url: str,
        api_key: Optional[str] = None,
        validate_deployments: bool = True,
        validate_health_checks: bool = True
    ):
        """Initialize orchestration adapter.

        Args:
            orchestration_platform: Name of the orchestration platform
            base_url: Evidence validation API base URL
            api_key: Optional API key
            validate_deployments: Validate deployment evidence
            validate_health_checks: Validate health check evidence
        """
        self.orchestration_platform = orchestration_platform
        self.validate_deployments = validate_deployments
        self.validate_health_checks = validate_health_checks

        # Initialize WebSocket adapter for real-time updates
        self.ws_adapter = WebSocketAdapter(
            component_name=f"{orchestration_platform}_adapter",
            component_version="1.0.0")
            base_url=base_url,
            api_key=api_key
        )

    async def connect(self):
        """Connect to validation service with WebSocket."""
        await self.ws_adapter.connect()

        # Set up message handlers
        self.ws_adapter.add_message_handler(
            "validation_completed",
            self._handle_validation_completed
        )
        self.ws_adapter.add_message_handler(
            "validation_failed",
            self._handle_validation_failed
        )

    async def disconnect(self):
        """Disconnect from validation service."""
        await self.ws_adapter.disconnect()

    async def validate_deployment(
        self,
        deployment_id: str,
        namespace: str,
        service_name: str,
        image_tag: str,
        config_hash: Optional[str] = None,
        rollout_status: Optional[str] = None,
        rollout_time: Optional[float] = None
    ):
        """Validate deployment evidence.

        Args:
            deployment_id: Deployment identifier
            namespace: Kubernetes/Docker namespace
            service_name: Service being deployed
            image_tag: Docker image tag
            config_hash: Configuration hash
            rollout_status: Deployment rollout status
            rollout_time: Rollout time in seconds
        """
        evidence_data = {
            "deployment_id": deployment_id,
            "namespace": namespace,
            "service_name": service_name,
            "image_tag": image_tag,
            "config_hash": config_hash,
            "rollout_status": rollout_status,
            "rollout_time": rollout_time,
            "orchestration_platform": self.orchestration_platform,
        }

        metadata = {
            "workflow_id": namespace,
            "task_id": deployment_id,
            "tags": ["orchestration", "deployment", service_name, self.orchestration_platform],
            "priority": 8,  # High priority for deployments
        }

        validation_rules = [
            "deployment_validity",
            "image_security",
            "configuration_integrity",
            "rollout_analysis"
        ]

        response = await self.ws_adapter.validate_evidence(
            evidence_data=evidence_data,
            evidence_type=EvidenceType.TASK_EXECUTION,
            metadata=metadata,
            validation_rules=validation_rules,
            async_validation=True,
            cache_strategy=CacheStrategy.LONG_TERM
        )

        # Subscribe to real-time updates
        await self.ws_adapter.subscribe_to_validation(
            response.request_id,
            lambda data: self._handle_deployment_validation(data, deployment_id)
        )

        return response

    async def validate_health_check(
        self,
        pod_name: str,
        namespace: str,
        service_name: str,
        health_status: str,
        response_time: Optional[float] = None,
        error_message: Optional[str] = None
    ):
        """Validate health check evidence.

        Args:
            pod_name: Pod/container name
            namespace: Namespace
            service_name: Service name
            health_status: Health check status
            response_time: Health check response time
            error_message: Error message if unhealthy
        """
        evidence_data = {
            "pod_name": pod_name,
            "namespace": namespace,
            "service_name": service_name,
            "health_status": health_status,
            "response_time": response_time,
            "error_message": error_message,
            "orchestration_platform": self.orchestration_platform,
        }

        metadata = {
            "workflow_id": namespace,
            "task_id": pod_name,
            "tags": ["orchestration", "health_check", service_name, self.orchestration_platform],
            "priority": health_status == "healthy" ? 4 : 7,
            "severity": "low" if health_status == "healthy" else "medium",
        }

        evidence_type = (
            EvidenceType.PERFORMANCE_METRIC
            if health_status == "healthy"
            else EvidenceType.ERROR_LOG
        )

        validation_rules = ["health_check_validity", "performance_analysis"]

        return await self.ws_adapter.validate_evidence(
            evidence_data=evidence_data,
            evidence_type=evidence_type,
            metadata=metadata,
            validation_rules=validation_rules,
            async_validation=True,
            cache_strategy=CacheStrategy.SHORT_TERM
        )

    async def _handle_validation_completed(self, data: Dict[str, Any]):
        """Handle validation completion message."""
        # Custom logic for handling validation completions
        print(f"Validation completed: {data.get('request_id')}")

    async def _handle_validation_failed(self, data: Dict[str, Any]):
        """Handle validation failure message."""
        # Custom logic for handling validation failures
        print(f"Validation failed: {data.get('request_id')}")

    async def _handle_deployment_validation(self, data: Dict[str, Any], deployment_id: str):
        """Handle deployment-specific validation updates."""
        print(f"Deployment validation update for {deployment_id}: {data}")

    async def close(self):
        """Close adapter connections."""
        await self.disconnect()
        await self.ws_adapter.close()
