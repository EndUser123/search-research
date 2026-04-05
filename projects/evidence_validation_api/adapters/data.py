"""
Data system adapters for evidence validation.

This module provides specialized adapters for databases,
data pipelines, and storage systems.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from ..models.schemas import CacheStrategy, EvidenceType
from .base import HTTPAdapter, WebSocketAdapter


class DatabaseAdapter:
    """
    Adapter for database systems like PostgreSQL, MySQL, MongoDB.

    Integrates evidence validation into database operations,
    migrations, and data quality checks.
    """

    def __init__(
        self,
        database_type: str,
        base_url: str,
        api_key: str | None = None,
        validate_queries: bool = True,
        validate_migrations: bool = True,
    ):
        """Initialize database adapter.

        Args:
            database_type: Type of database (postgresql, mysql, mongodb, etc.)
            base_url: Evidence validation API base URL
            api_key: Optional API key
            validate_queries: Validate query execution evidence
            validate_migrations: Validate database migration evidence
        """
        self.database_type = database_type
        self.validate_queries = validate_queries
        self.validate_migrations = validate_migrations

        # Initialize HTTP adapter
        self.http_adapter = HTTPAdapter(
            component_name=f"{database_type}_adapter",
            component_version="1.0.0")
            base_url=base_url,
            api_key=api_key,
        )

    async def validate_query_execution(
        self,
        query: str,
        database_name: str,
        execution_time: float | None = None,
        rows_affected: int | None = None,
        result_size: int | None = None,
        error_message: str | None = None,
        user: str | None = None,
        connection_id: str | None = None,
    ):
        """Validate database query execution evidence.

        Args:
            query: SQL query that was executed
            database_name: Database name
            execution_time: Query execution time in milliseconds
            rows_affected: Number of rows affected
            result_size: Size of result set in bytes
            error_message: Error message if query failed
            user: User who executed the query
            connection_id: Database connection identifier
        """
        evidence_data = {
            "query": query,
            "database_name": database_name,
            "execution_time": execution_time,
            "rows_affected": rows_affected,
            "result_size": result_size,
            "error_message": error_message,
            "user": user,
            "connection_id": connection_id,
            "database_type": self.database_type,
        }

        # Determine evidence type based on whether query succeeded
        evidence_type = (
            EvidenceType.DATABASE_OPERATION
            if not error_message
            else EvidenceType.ERROR_LOG
        )

        metadata = {
            "workflow_id": database_name,
            "task_id": connection_id or "unknown",
            "tags": ["database", "query", self.database_type],
            "priority": 6 if not error_message else 7,
            "severity": "low" if not error_message else "medium",
        }

        validation_rules = []
        if self.validate_queries:
            if error_message:
                validation_rules = ["error_analysis", "query_validity"]
            else:
                validation_rules = ["query_performance", "result_validity"]

        return await self.http_adapter.validate_evidence(
            evidence_data=evidence_data,
            evidence_type=evidence_type,
            metadata=metadata,
            validation_rules=validation_rules,
            async_validation=True,
            cache_strategy=CacheStrategy.MEDIUM_TERM,
        )

    async def validate_database_migration(
        self,
        migration_id: str,
        migration_version: str,
        database_name: str,
        direction: str,  # "up" or "down"
        tables_affected: list[str] | None = None,
        execution_time: float | None = None,
        checksum: str | None = None,
        success: bool = True,
        error_message: str | None = None,
    ):
        """Validate database migration evidence.

        Args:
            migration_id: Migration identifier
            migration_version: Migration version
            database_name: Database name
            direction: Migration direction (up/down)
            tables_affected: List of affected tables
            execution_time: Migration execution time in seconds
            checksum: Migration script checksum
            success: Whether migration succeeded
            error_message: Error message if migration failed
        """
        evidence_data = {
            "migration_id": migration_id,
            "migration_version": migration_version,
            "database_name": database_name,
            "direction": direction,
            "tables_affected": tables_affected,
            "execution_time": execution_time,
            "checksum": checksum,
            "success": success,
            "error_message": error_message,
            "database_type": self.database_type,
        }

        evidence_type = (
            EvidenceType.DATABASE_OPERATION if success else EvidenceType.ERROR_LOG
        )

        metadata = {
            "workflow_id": database_name,
            "task_id": migration_id,
            "tags": ["database", "migration", self.database_type],
            "priority": 9,  # High priority for migrations
            "severity": "low" if success else "high",
        }

        validation_rules = []
        if self.validate_migrations:
            if success:
                validation_rules = [
                    "migration_integrity",
                    "schema_validity",
                    "rollback_capability",
                ]
            else:
                validation_rules = ["migration_failure_analysis", "rollback_procedure"]

        return await self.http_adapter.validate_evidence(
            evidence_data=evidence_data,
            evidence_type=evidence_type,
            metadata=metadata,
            validation_rules=validation_rules,
            async_validation=True,
            cache_strategy=CacheStrategy.LONG_TERM,
        )

    async def validate_data_quality(
        self,
        table_name: str,
        database_name: str,
        quality_metrics: dict[str, Any],
        timestamp: datetime | None = None,
    ):
        """Validate data quality metrics.

        Args:
            table_name: Table name
            database_name: Database name
            quality_metrics: Data quality metrics (null_count, duplicate_count, etc.)
            timestamp: Quality check timestamp
        """
        evidence_data = {
            "table_name": table_name,
            "database_name": database_name,
            "quality_metrics": quality_metrics,
            "timestamp": timestamp.isoformat()
            if timestamp
            else datetime.now(UTC).isoformat(),
            "database_type": self.database_type,
        }

        metadata = {
            "workflow_id": database_name,
            "task_id": table_name,
            "tags": ["database", "data_quality", table_name, self.database_type],
            "priority": 5,
        }

        return await self.http_adapter.validate_evidence(
            evidence_data=evidence_data,
            evidence_type=EvidenceType.QUALITY_METRIC,
            metadata=metadata,
            validation_rules=["quality_standards", "data_integrity"],
            async_validation=True,
            cache_strategy=CacheStrategy.MEDIUM_TERM,
        )

    async def close(self):
        """Close adapter connections."""
        await self.http_adapter.close()


class DataPipelineAdapter:
    """
    Adapter for data pipeline systems like Apache Airflow, Dagster,
    or Apache Beam.

    Integrates evidence validation into data pipeline execution
    with automatic data lineage and quality validation.
    """

    def __init__(
        self,
        pipeline_system: str,
        base_url: str,
        api_key: str | None = None,
        validate_data_lineage: bool = True,
        validate_quality_checks: bool = True,
    ):
        """Initialize data pipeline adapter.

        Args:
            pipeline_system: Name of the pipeline system
            base_url: Evidence validation API base URL
            api_key: Optional API key
            validate_data_lineage: Validate data lineage evidence
            validate_quality_checks: Validate data quality checks
        """
        self.pipeline_system = pipeline_system
        self.validate_data_lineage = validate_data_lineage
        self.validate_quality_checks = validate_quality_checks

        # Initialize WebSocket adapter for real-time pipeline monitoring
        self.ws_adapter = WebSocketAdapter(
            component_name=f"{pipeline_system}_adapter",
            component_version="1.0.0")
            base_url=base_url,
            api_key=api_key,
        )

    async def connect(self):
        """Connect to validation service with WebSocket."""
        await self.ws_adapter.connect()

    async def validate_pipeline_run(
        self,
        run_id: str,
        pipeline_name: str,
        status: str,
        start_time: datetime,
        end_time: datetime | None = None,
        input_datasets: list[str] | None = None,
        output_datasets: list[str] | None = None,
        config_hash: str | None = None,
        error_message: str | None = None,
    ):
        """Validate pipeline run evidence.

        Args:
            run_id: Pipeline run identifier
            pipeline_name: Name of the pipeline
            status: Pipeline run status
            start_time: Pipeline start time
            end_time: Pipeline end time
            input_datasets: List of input dataset paths/identifiers
            output_datasets: List of output dataset paths/identifiers
            config_hash: Hash of pipeline configuration
            error_message: Error message if pipeline failed
        """
        evidence_data = {
            "run_id": run_id,
            "pipeline_name": pipeline_name,
            "status": status,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat() if end_time else None,
            "input_datasets": input_datasets,
            "output_datasets": output_datasets,
            "config_hash": config_hash,
            "error_message": error_message,
            "pipeline_system": self.pipeline_system,
        }

        evidence_type = (
            EvidenceType.TASK_EXECUTION
            if status == "success"
            else EvidenceType.ERROR_LOG
        )

        metadata = {
            "workflow_id": pipeline_name,
            "task_id": run_id,
            "tags": ["pipeline", "run", pipeline_name, self.pipeline_system],
            "priority": 7,
            "severity": "low" if status == "success" else "high",
        }

        validation_rules = ["pipeline_integrity", "data_lineage"]
        if status != "success":
            validation_rules.extend(["failure_analysis", "error_recovery"])

        response = await self.ws_adapter.validate_evidence(
            evidence_data=evidence_data,
            evidence_type=evidence_type,
            metadata=metadata,
            validation_rules=validation_rules,
            async_validation=True,
            cache_strategy=CacheStrategy.LONG_TERM,
        )

        # Subscribe to real-time updates for long-running pipelines
        if end_time is None:  # Pipeline still running
            await self.ws_adapter.subscribe_to_validation(
                response.request_id,
                lambda data: self._handle_pipeline_validation(data, run_id),
            )

        return response

    async def validate_data_transformation(
        self,
        transformation_id: str,
        input_schema: dict[str, Any],
        output_schema: dict[str, Any],
        transformation_type: str,
        input_count: int,
        output_count: int,
        validation_results: dict[str, Any] | None = None,
    ):
        """Validate data transformation evidence.

        Args:
            transformation_id: Transformation step identifier
            input_schema: Input data schema
            output_schema: Output data schema
            transformation_type: Type of transformation (filter, map, join, etc.)
            input_count: Number of input records
            output_count: Number of output records
            validation_results: Data validation results
        """
        evidence_data = {
            "transformation_id": transformation_id,
            "input_schema": input_schema,
            "output_schema": output_schema,
            "transformation_type": transformation_type,
            "input_count": input_count,
            "output_count": output_count,
            "validation_results": validation_results,
            "pipeline_system": self.pipeline_system,
        }

        metadata = {
            "task_id": transformation_id,
            "tags": [
                "pipeline",
                "transformation",
                transformation_type,
                self.pipeline_system,
            ],
            "priority": 6,
        }

        validation_rules = [
            "schema_compatibility",
            "data_integrity",
            "transformation_logic",
            "volume_consistency",
        ]

        return await self.ws_adapter.validate_evidence(
            evidence_data=evidence_data,
            evidence_type=EvidenceType.DATABASE_OPERATION,
            metadata=metadata,
            validation_rules=validation_rules,
            async_validation=True,
            cache_strategy=CacheStrategy.MEDIUM_TERM,
        )

    async def _handle_pipeline_validation(self, data: dict[str, Any], run_id: str):
        """Handle pipeline-specific validation updates."""
        print(f"Pipeline validation update for run {run_id}: {data}")

    async def close(self):
        """Close adapter connections."""
        await self.ws_adapter.disconnect()
        await self.ws_adapter.close()


class StorageAdapter:
    """
    Adapter for storage systems like Amazon S3, Google Cloud Storage,
    or Azure Blob Storage.

    Integrates evidence validation into storage operations
    with file integrity and access validation.
    """

    def __init__(
        self,
        storage_system: str,
        base_url: str,
        api_key: str | None = None,
        validate_file_integrity: bool = True,
        validate_access_logs: bool = True,
    ):
        """Initialize storage adapter.

        Args:
            storage_system: Name of the storage system
            base_url: Evidence validation API base URL
            api_key: Optional API key
            validate_file_integrity: Validate file integrity evidence
            validate_access_logs: Validate access log evidence
        """
        self.storage_system = storage_system
        self.validate_file_integrity = validate_file_integrity
        self.validate_access_logs = validate_access_logs

        # Initialize HTTP adapter
        self.http_adapter = HTTPAdapter(
            component_name=f"{storage_system}_adapter",
            component_version="1.0.0")
            base_url=base_url,
            api_key=api_key,
        )

    async def validate_file_operation(
        self,
        operation: str,  # upload, download, delete, copy
        file_path: str,
        bucket_name: str | None = None,
        file_size: int | None = None,
        file_hash: str | None = None,
        content_type: str | None = None,
        user: str | None = None,
        access_time: datetime | None = None,
        error_message: str | None = None,
    ):
        """Validate file operation evidence.

        Args:
            operation: Type of file operation
            file_path: File path or key
            bucket_name: Bucket/container name
            file_size: File size in bytes
            file_hash: SHA-256 hash of file content
            content_type: MIME type of file
            user: User who performed operation
            access_time: When operation occurred
            error_message: Error message if operation failed
        """
        evidence_data = {
            "operation": operation,
            "file_path": file_path,
            "bucket_name": bucket_name,
            "file_size": file_size,
            "file_hash": file_hash,
            "content_type": content_type,
            "user": user,
            "access_time": access_time.isoformat()
            if access_time
            else datetime.now(UTC).isoformat(),
            "error_message": error_message,
            "storage_system": self.storage_system,
        }

        evidence_type = (
            EvidenceType.FILE_OPERATION if not error_message else EvidenceType.ERROR_LOG
        )

        metadata = {
            "workflow_id": bucket_name or "default",
            "task_id": file_path,
            "tags": ["storage", "file", operation, self.storage_system],
            "priority": 5 if not error_message else 7,
            "severity": "low" if not error_message else "medium",
        }

        validation_rules = []
        if self.validate_file_integrity:
            validation_rules.extend(["file_integrity", "content_validation"])
        if operation in ["upload", "copy"] and file_hash:
            validation_rules.append("hash_verification")

        return await self.http_adapter.validate_evidence(
            evidence_data=evidence_data,
            evidence_type=evidence_type,
            metadata=metadata,
            validation_rules=validation_rules,
            async_validation=True,
            cache_strategy=CacheStrategy.LONG_TERM,
        )

    async def validate_storage_metrics(
        self,
        bucket_name: str,
        metrics: dict[str, Any],
        timestamp: datetime | None = None,
    ):
        """Validate storage performance metrics.

        Args:
            bucket_name: Bucket/container name
            metrics: Storage metrics (request_count, bandwidth, error_rate, etc.)
            timestamp: Metrics collection timestamp
        """
        evidence_data = {
            "bucket_name": bucket_name,
            "metrics": metrics,
            "timestamp": timestamp.isoformat()
            if timestamp
            else datetime.now(UTC).isoformat(),
            "storage_system": self.storage_system,
        }

        metadata = {
            "workflow_id": bucket_name,
            "tags": ["storage", "metrics", bucket_name, self.storage_system],
            "priority": 4,
        }

        return await self.http_adapter.validate_evidence(
            evidence_data=evidence_data,
            evidence_type=EvidenceType.PERFORMANCE_METRIC,
            metadata=metadata,
            validation_rules=["performance_standards", "availability_metrics"],
            async_validation=True,
            cache_strategy=CacheStrategy.SHORT_TERM,
        )

    async def close(self):
        """Close adapter connections."""
        await self.http_adapter.close()
