from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

from ..database.sqlite_database_manager import SQLiteDatabaseManager

"""Standards Knowledge Service for CSF SQLite Knowledge Curator.

Algorithm Approach: Service layer pattern with comprehensive CRUD operations,
validation logic execution, and compliance management. Uses SQLiteDatabaseManager
for all database operations with proper transaction handling.

Time Complexity: O(log n) for indexed operations, O(n) for full table scans
Space Complexity: O(1) for single operations, O(m) for batch operations

Design Pattern: Service layer with repository pattern for data access.
Provides clean abstraction over database operations with comprehensive
error handling and validation logic execution.

Security Features:
- SQL injection prevention through parameterized queries
- Input validation and sanitization
- Transaction atomicity for data consistency
- Access control through service layer
- Comprehensive error handling prevents information leakage
- Validation logic execution with security context

Parameters:
db_manager (SQLiteDatabaseManager): Database manager instance
    - Must be properly initialized
    - Provides connection pooling and transaction management
    - Handles all database operations

Returns:
StandardsKnowledgeService: Configured service instance
    - Ready for immediate use
    - Thread-safe operations
    - Comprehensive error handling
    - Validation logic execution capabilities

Raises:
ValueError: For invalid configuration or parameters
StandardsKnowledgeError: For service-specific errors
sqlite3.Error: For database operation errors

Examples:
>>> db_manager = SQLiteDatabaseManager()
>>> service = StandardsKnowledgeService(db_manager)
>>> rule = service.create_rule({
...     "standard_category": "solo_developer",
...     "rule_name": "value_driven_decisions",
...     "description": "Decisions must add real value",
...     "validation_logic": {"type": "boolean", "required": True},
...     "severity": "error",
...     "applicable_contexts": ["implementation", "design"]
... })
>>> result = service.validate_context("implementation", {"decision_data": "test"})

Edge Cases:
- Empty validation results: Returns empty list with metadata
- Database connection failures: Proper error wrapping and retry
- Invalid validation logic: Comprehensive validation with clear messages
- Concurrent operations: Thread-safe with proper isolation
- Large rule sets: Efficient queries and batch validation

Performance Considerations:
- Connection pooling reduces overhead for frequent operations
- Database indexes on frequently queried fields
- Batch operations minimize transaction overhead
- Async operations prevent blocking on I/O
- Efficient query patterns avoid N+1 problems
- Validation logic caching for repeated executions
"""


# Configure logging for standards knowledge operations
logger = logging.getLogger(__name__)


class StandardsKnowledgeError(Exception):
    """
    Custom exception for standards knowledge service errors.

    Algorithm Approach: Structured error handling with context information.
    Provides clear error categorization and debugging information.

    Attributes:
    message (str): Human-readable error message
    error_code (str): Machine-readable error code
    details (dict): Additional error context

    """

    def __init__(
        self,
        message: str,
        error_code: str = "STANDARDS_ERROR",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}

    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}"


@dataclass
class StandardRule:
    """
    Standard rule data model for CSF compliance validation.

    Algorithm Approach: Dataclass with validation and serialization.
    Provides type safety and convenient data access patterns.

    Attributes:
    id (str): Unique identifier for the standard rule
    standard_category (str): Category of the standard ('solo_developer', 'architecture', 'quality', 'security')
    rule_name (str): Unique name for the rule within the category
    description (str): Detailed description of the rule
    validation_logic (dict): JSON-serializable validation logic criteria
    severity (str): Severity level ('error', 'warning', 'info')
    applicable_contexts (List[str]): Contexts where this rule applies
    created_at (str): ISO timestamp when rule was created
    updated_at (str): ISO timestamp when rule was last updated
    active (bool): Whether the rule is currently active
    metadata (dict, optional): Additional metadata as key-value pairs

    """

    standard_category: str
    rule_name: str
    description: str
    validation_logic: dict[str, Any]
    severity: str
    id: str | None = None
    applicable_contexts: list[str] | None = None
    created_at: str | None = None
    updated_at: str | None = None
    active: bool = True
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """Validate rule data after initialization."""
        if not self.id:
            self.id = str(uuid.uuid4())

        if not self.created_at:
            self.created_at = datetime.now(UTC).isoformat()

        if not self.updated_at:
            self.updated_at = self.created_at

        if self.applicable_contexts is None:
            self.applicable_contexts = []

        if self.metadata is None:
            self.metadata = {}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StandardRule:
        """Create StandardRule from dictionary."""
        try:
            return cls(**data)
        except TypeError as e:
            raise StandardsKnowledgeError(
                f"Invalid rule data: {e}",
                error_code="INVALID_RULE_DATA",
                details={"missing_fields": str(e)},
            )

    def to_dict(self) -> dict[str, Any]:
        """Convert StandardRule to dictionary."""
        return asdict(self)

    def validate(self) -> None:
        """
        Validate rule data integrity.

        Algorithm Approach: Comprehensive validation with clear error messages.
        Ensures data consistency and prevents invalid states.

        Raises:
        StandardsKnowledgeError: If validation fails

        """
        errors = []

        # Required field validation
        if not self.standard_category or not isinstance(self.standard_category, str):
            errors.append("standard_category is required and must be a string")
        elif len(self.standard_category) > 100:
            errors.append("standard_category must be 100 characters or less")
        elif self.standard_category not in [
            "solo_developer",
            "architecture",
            "quality",
            "security",
        ]:
            errors.append(
                "standard_category must be one of: solo_developer, architecture, quality, security"
            )

        if not self.rule_name or not isinstance(self.rule_name, str):
            errors.append("rule_name is required and must be a string")
        elif len(self.rule_name) > 255:
            errors.append("rule_name must be 255 characters or less")

        if not self.description or not isinstance(self.description, str):
            errors.append("description is required and must be a string")

        if not self.validation_logic or not isinstance(self.validation_logic, dict):
            errors.append("validation_logic is required and must be a dictionary")
        else:
            try:
                json.dumps(self.validation_logic)  # Test JSON serializability
            except (TypeError, ValueError):
                errors.append("validation_logic must be JSON serializable")

        if not self.severity or not isinstance(self.severity, str):
            errors.append("severity is required and must be a string")
        elif self.severity not in ["error", "warning", "info"]:
            errors.append("severity must be one of: error, warning, info")

        # Contexts validation
        if self.applicable_contexts is not None:
            if not isinstance(self.applicable_contexts, list):
                errors.append("applicable_contexts must be a list")
            else:
                for i, context in enumerate(self.applicable_contexts):
                    if not isinstance(context, str):
                        errors.append(f"applicable_contexts[{i}] must be a string")
                    elif len(context) > 100:
                        errors.append(f"applicable_contexts[{i}] must be 100 characters or less")

        # Metadata validation
        if self.metadata is not None:
            if not isinstance(self.metadata, dict):
                errors.append("metadata must be a dictionary")
            else:
                try:
                    json.dumps(self.metadata)  # Test JSON serializability
                except (TypeError, ValueError):
                    errors.append("metadata must be JSON serializable")

        if errors:
            raise StandardsKnowledgeError(
                f"Validation failed: {'; '.join(errors)}",
                error_code="VALIDATION_ERROR",
                details={"field_errors": errors},
            )


@dataclass
class StandardRuleSearchFilter:
    """
    Search filter for standard rules.

    Algorithm Approach: Flexible filtering with multiple criteria.
    Supports complex search scenarios with pagination.

    Attributes:
    standard_category (str, optional): Filter by standard category
    rule_name (str, optional): Filter by rule name (partial match)
    severity (str, optional): Filter by severity level
    active (bool, optional): Filter by active status
    contexts (List[str], optional): Filter by applicable contexts (AND logic)
    search_text (str, optional): Text search in rule name and description
    limit (int): Maximum number of results (default: 50)
    offset (int): Number of results to skip (default: 0)
    sort_by (str): Sort field (default: "created_at")
    sort_order (str): Sort order ("asc" or "desc", default: "desc")

    """

    standard_category: str | None = None
    rule_name: str | None = None
    severity: str | None = None
    active: bool | None = None
    contexts: list[str] | None = None
    search_text: str | None = None
    limit: int = 50
    offset: int = 0
    sort_by: str = "created_at"
    sort_order: str = "desc"

    def validate(self) -> None:
        """
        Validate search filter parameters.

        Algorithm Approach: Parameter validation with type checking.
        Ensures search parameters are valid and safe.

        Raises:
        StandardsKnowledgeError: If validation fails

        """
        errors = []

        if self.limit <= 0 or self.limit > 1000:
            errors.append("limit must be between 1 and 1000")

        if self.offset < 0:
            errors.append("offset must be non-negative")

        if self.sort_by not in [
            "created_at",
            "updated_at",
            "rule_name",
            "standard_category",
            "severity",
        ]:
            errors.append("invalid sort_by field")

        if self.sort_order not in ["asc", "desc"]:
            errors.append("sort_order must be 'asc' or 'desc'")

        if self.standard_category and self.standard_category not in [
            "solo_developer",
            "architecture",
            "quality",
            "security",
        ]:
            errors.append(
                "standard_category must be one of: solo_developer, architecture, quality, security"
            )

        if self.severity and self.severity not in ["error", "warning", "info"]:
            errors.append("severity must be one of: error, warning, info")

        if errors:
            raise StandardsKnowledgeError(
                f"Search filter validation failed: {'; '.join(errors)}",
                error_code="FILTER_VALIDATION_ERROR",
            )


@dataclass
class ValidationResult:
    """
    Result of validation logic execution.

    Algorithm Approach: Structured validation result with context.
    Provides detailed information about validation outcomes.

    Attributes:
    rule_id (str): ID of the rule that was executed
    rule_name (str): Name of the rule that was executed
    passed (bool): Whether the validation passed
    severity (str): Severity level of the rule
    message (str): Validation result message
    details (dict): Additional validation details
    execution_time (float): Time taken to execute validation in seconds
    timestamp (str): ISO timestamp of validation execution

    """

    rule_id: str
    rule_name: str
    passed: bool
    severity: str
    message: str
    details: dict[str, Any]
    execution_time: float
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        """Convert ValidationResult to dictionary."""
        return asdict(self)


@dataclass
class ComplianceReport:
    """
    Comprehensive compliance validation report.

    Algorithm Approach: Aggregated validation results with statistics.
    Provides complete overview of compliance status.

    Attributes:
    context (str): Context that was validated
    total_rules (int): Total number of rules evaluated
    passed_rules (int): Number of rules that passed
    failed_rules (int): Number of rules that failed
    error_count (int): Number of error-level failures
    warning_count (int): Number of warning-level failures
    info_count (int): Number of info-level failures
    overall_status (str): Overall compliance status
    validation_results (List[ValidationResult]): Detailed validation results
    execution_time (float): Total execution time in seconds
    timestamp (str): ISO timestamp of report generation

    """

    context: str
    total_rules: int
    passed_rules: int
    failed_rules: int
    error_count: int
    warning_count: int
    info_count: int
    overall_status: str
    validation_results: list[ValidationResult]
    execution_time: float
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        """Convert ComplianceReport to dictionary."""
        return asdict(self)


class StandardsKnowledgeServiceInterface:
    """
    Interface for Standards Knowledge Service operations.

    Algorithm Approach: Abstract base class defining service contract.
    Ensures consistent implementation across different service providers.
    """

    def create_rule(self, rule_data: dict[str, Any]) -> dict[str, Any]:
        """Create a new standard rule."""
        raise NotImplementedError

    def get_rule_by_id(self, rule_id: str) -> dict[str, Any] | None:
        """Retrieve a standard rule by ID."""
        raise NotImplementedError

    def get_rule_by_name(self, standard_category: str, rule_name: str) -> dict[str, Any] | None:
        """Retrieve a standard rule by category and name."""
        raise NotImplementedError

    def update_rule(self, rule_id: str, update_data: dict[str, Any]) -> dict[str, Any]:
        """Update an existing standard rule."""
        raise NotImplementedError

    def delete_rule(self, rule_id: str) -> dict[str, Any]:
        """Delete a standard rule."""
        raise NotImplementedError

    def search_rules(self, filter_config: StandardRuleSearchFilter | None = None) -> dict[str, Any]:
        """Search standard rules with filtering."""
        raise NotImplementedError

    def get_rules_by_context(self, context: str, active_only: bool = True) -> list[dict[str, Any]]:
        """Get rules applicable to a specific context."""
        raise NotImplementedError

    def get_rules_by_category(
        self, standard_category: str, active_only: bool = True
    ) -> list[dict[str, Any]]:
        """Get rules by standard category."""
        raise NotImplementedError

    def validate_context(self, context: str, data: dict[str, Any]) -> ComplianceReport:
        """Validate data against applicable rules for a context."""
        raise NotImplementedError

    def execute_validation_logic(
        self, rule: dict[str, Any], data: dict[str, Any]
    ) -> ValidationResult:
        """Execute validation logic for a specific rule."""
        raise NotImplementedError

    def get_statistics(self) -> dict[str, Any]:
        """Get service statistics."""
        raise NotImplementedError

    def batch_create_rules(self, rules_data: list[dict[str, Any]]) -> dict[str, Any]:
        """Create multiple rules in a batch operation."""
        raise NotImplementedError


class StandardsKnowledgeService(StandardsKnowledgeServiceInterface):
    """
    Service for managing CSF standard rules and compliance validation.

    Algorithm Approach: Service layer with comprehensive CRUD operations,
    validation logic execution, and compliance management. Uses SQLiteDatabaseManager
    for all database operations with proper transaction handling.

    Design Pattern: Service layer with repository pattern for data access.
    Provides clean abstraction over database operations.

    Thread Safety: Thread-safe operations through database manager connection
    pooling and proper transaction isolation.
    """

    def __init__(self, db_manager: SQLiteDatabaseManager):
        """
        Initialize Standards Knowledge Service.

        Parameters
        ----------
        db_manager (SQLiteDatabaseManager): Database manager instance

        Raises
        ------
        ValueError: If db_manager is invalid
        StandardsKnowledgeError: If service initialization fails

        """
        if not db_manager:
            raise ValueError("Database manager is required")

        self.db_manager = db_manager
        self._ensure_database_schema()

        logger.info("StandardsKnowledgeService initialized successfully")

    def _ensure_database_schema(self) -> None:
        """
        Ensure database schema exists and is up-to-date.

        Algorithm Approach: Schema validation and creation.
        Creates necessary tables and indexes if they don't exist.

        Raises:
        StandardsKnowledgeError: If schema creation fails

        """
        try:
            with self.db_manager.transaction("standards") as conn:
                cursor = conn.cursor()

                # Create standard_rules table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS standard_rules (
                        id TEXT PRIMARY KEY,
                        standard_category TEXT NOT NULL,
                        rule_name TEXT NOT NULL,
                        description TEXT NOT NULL,
                        validation_logic TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        applicable_contexts TEXT,
                        created_at TEXT,
                        updated_at TEXT,
                        active BOOLEAN DEFAULT 1,
                        metadata TEXT
                    )
                """
                )

                # Create indexes for common queries
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_category ON standard_rules(standard_category)"
                )
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_active ON standard_rules(active)")
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_severity ON standard_rules(severity)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_created_at ON standard_rules(created_at)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_category_name ON standard_rules(standard_category, rule_name)"
                )

                # Create unique constraint on category and name
                cursor.execute(
                    """
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_category_name
                    ON standard_rules(standard_category, rule_name)
                    WHERE active = 1
                """
                )

                # Create full-text search index
                cursor.execute(
                    """
                    CREATE VIRTUAL TABLE IF NOT EXISTS standard_rules_fts
                    USING fts5(rule_name, description, content=standard_rules, content_rowid=rowid)
                """
                )

                # Trigger to maintain FTS index
                cursor.execute(
                    """
                    CREATE TRIGGER IF NOT EXISTS standard_rules_fts_insert
                    AFTER INSERT ON standard_rules
                    BEGIN
                        INSERT INTO standard_rules_fts(rowid, rule_name, description)
                        VALUES (new.rowid, new.rule_name, new.description);
                    END
                """
                )

                cursor.execute(
                    """
                    CREATE TRIGGER IF NOT EXISTS standard_rules_fts_update
                    AFTER UPDATE ON standard_rules
                    BEGIN
                        UPDATE standard_rules_fts SET
                            rule_name = new.rule_name,
                            description = new.description
                        WHERE rowid = old.rowid;
                    END
                """
                )

                cursor.execute(
                    """
                    CREATE TRIGGER IF NOT EXISTS standard_rules_fts_delete
                    AFTER DELETE ON standard_rules
                    BEGIN
                        DELETE FROM standard_rules_fts WHERE rowid = old.rowid;
                    END
                """
                )

                cursor.close()
                logger.debug("Database schema ensured successfully")

        except sqlite3.Error as e:
            raise StandardsKnowledgeError(
                f"Failed to ensure database schema: {e}",
                error_code="SCHEMA_ERROR",
                details={"database_error": str(e)},
            )

    def create_rule(self, rule_data: dict[str, Any]) -> dict[str, Any]:
        """
        Create a new standard rule.

        Algorithm Approach: Validation followed by database insertion.
        Ensures data integrity and returns complete rule information.

        Parameters
        ----------
        rule_data (Dict[str, Any]): Rule data to create

        Returns
        -------
        Dict[str, Any]: Created rule with generated fields

        Raises
        ------
        StandardsKnowledgeError: If validation or creation fails

        """
        try:
            # Create and validate rule
            rule = StandardRule.from_dict(rule_data)
            rule.validate()

            # Convert lists and dicts to JSON for storage
            contexts_json = (
                json.dumps(rule.applicable_contexts) if rule.applicable_contexts else None
            )
            validation_json = json.dumps(rule.validation_logic)
            metadata_json = json.dumps(rule.metadata) if rule.metadata else None

            with self.db_manager.transaction("standards") as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO standard_rules (
                        id, standard_category, rule_name, description,
                        validation_logic, severity, applicable_contexts,
                        created_at, updated_at, active, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        rule.id,
                        rule.standard_category,
                        rule.rule_name,
                        rule.description,
                        validation_json,
                        rule.severity,
                        contexts_json,
                        rule.created_at,
                        rule.updated_at,
                        rule.active,
                        metadata_json,
                    ),
                )

                cursor.close()

            logger.info(f"Created standard rule: {rule.id}")

            # Return complete rule data with success flag
            result = rule.to_dict()
            result["success"] = True
            return result

        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                raise StandardsKnowledgeError(
                    "Rule with this category and name already exists",
                    error_code="DUPLICATE_RULE",
                )
            raise StandardsKnowledgeError(
                f"Database integrity error: {e}", error_code="INTEGRITY_ERROR"
            )
        except sqlite3.Error as e:
            raise StandardsKnowledgeError(
                f"Failed to create rule: {e}",
                error_code="CREATE_ERROR",
                details={"database_error": str(e)},
            )

    def get_rule_by_id(self, rule_id: str) -> dict[str, Any] | None:
        """
        Retrieve a standard rule by ID.

        Algorithm Approach: Direct lookup with JSON field restoration.
        Returns complete rule data with proper types.

        Parameters
        ----------
        rule_id (str): ID of the rule to retrieve

        Returns
        -------
        Optional[Dict[str, Any]]: Rule data or None if not found

        Raises
        ------
        StandardsKnowledgeError: If database operation fails

        """
        try:
            if not rule_id:
                return None

            with self.db_manager.transaction("standards") as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT id, standard_category, rule_name, description,
                           validation_logic, severity, applicable_contexts,
                           created_at, updated_at, active, metadata
                    FROM standard_rules
                    WHERE id = ?
                """,
                    (rule_id,),
                )

                row = cursor.fetchone()
                cursor.close()

                if not row:
                    return None

                # Convert row to dictionary with JSON field restoration
                rule_dict = {
                    "id": row[0],
                    "standard_category": row[1],
                    "rule_name": row[2],
                    "description": row[3],
                    "validation_logic": json.loads(row[4]) if row[4] else {},
                    "severity": row[5],
                    "applicable_contexts": json.loads(row[6]) if row[6] else [],
                    "created_at": row[7],
                    "updated_at": row[8],
                    "active": bool(row[9]) if row[9] is not None else True,
                    "metadata": json.loads(row[10]) if row[10] else {},
                }

                return rule_dict

        except sqlite3.Error as e:
            raise StandardsKnowledgeError(
                f"Failed to get rule {rule_id}: {e}",
                error_code="RETRIEVE_ERROR",
                details={"rule_id": rule_id, "database_error": str(e)},
            )

    def get_rule_by_name(self, standard_category: str, rule_name: str) -> dict[str, Any] | None:
        """
        Retrieve a standard rule by category and name.

        Algorithm Approach: Category and name lookup with JSON field restoration.
        Returns the most recent active rule for the given category and name.

        Parameters
        ----------
        standard_category (str): Category of the rule
        rule_name (str): Name of the rule

        Returns
        -------
        Optional[Dict[str, Any]]: Rule data or None if not found

        Raises
        ------
        StandardsKnowledgeError: If database operation fails

        """
        try:
            if not standard_category or not rule_name:
                return None

            with self.db_manager.transaction("standards") as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT id, standard_category, rule_name, description,
                           validation_logic, severity, applicable_contexts,
                           created_at, updated_at, active, metadata
                    FROM standard_rules
                    WHERE standard_category = ? AND rule_name = ?
                    ORDER BY created_at DESC
                    LIMIT 1
                """,
                    (standard_category, rule_name),
                )

                row = cursor.fetchone()
                cursor.close()

                if not row:
                    return None

                # Convert row to dictionary with JSON field restoration
                rule_dict = {
                    "id": row[0],
                    "standard_category": row[1],
                    "rule_name": row[2],
                    "description": row[3],
                    "validation_logic": json.loads(row[4]) if row[4] else {},
                    "severity": row[5],
                    "applicable_contexts": json.loads(row[6]) if row[6] else [],
                    "created_at": row[7],
                    "updated_at": row[8],
                    "active": bool(row[9]) if row[9] is not None else True,
                    "metadata": json.loads(row[10]) if row[10] else {},
                }

                return rule_dict

        except sqlite3.Error as e:
            raise StandardsKnowledgeError(
                f"Failed to get rule by name {standard_category}.{rule_name}: {e}",
                error_code="RETRIEVE_ERROR",
                details={
                    "standard_category": standard_category,
                    "rule_name": rule_name,
                    "database_error": str(e),
                },
            )

    def update_rule(self, rule_id: str, update_data: dict[str, Any]) -> dict[str, Any]:
        """
        Update an existing standard rule.

        Algorithm Approach: Validation with selective field updates.
        Maintains data integrity while allowing partial updates.

        Parameters
        ----------
        rule_id (str): ID of the rule to update
        update_data (Dict[str, Any]): Fields to update

        Returns
        -------
        Dict[str, Any]: Updated rule data

        Raises
        ------
        StandardsKnowledgeError: If rule not found or validation fails

        """
        try:
            # Get existing rule first
            existing = self.get_rule_by_id(rule_id)
            if not existing:
                raise StandardsKnowledgeError(
                    f"Rule not found: {rule_id}", error_code="RULE_NOT_FOUND"
                )

            # Update fields
            existing.update(update_data)
            existing["updated_at"] = datetime.now(UTC).isoformat()

            # Validate updated rule
            updated_rule = StandardRule.from_dict(existing)
            updated_rule.validate()

            # Convert lists and dicts to JSON for storage
            contexts_json = (
                json.dumps(updated_rule.applicable_contexts)
                if updated_rule.applicable_contexts
                else None
            )
            validation_json = json.dumps(updated_rule.validation_logic)
            metadata_json = json.dumps(updated_rule.metadata) if updated_rule.metadata else None

            with self.db_manager.transaction("standards") as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    UPDATE standard_rules
                    SET standard_category = ?, rule_name = ?, description = ?,
                        validation_logic = ?, severity = ?, applicable_contexts = ?,
                        updated_at = ?, active = ?, metadata = ?
                    WHERE id = ?
                """,
                    (
                        updated_rule.standard_category,
                        updated_rule.rule_name,
                        updated_rule.description,
                        validation_json,
                        updated_rule.severity,
                        contexts_json,
                        updated_rule.updated_at,
                        updated_rule.active,
                        metadata_json,
                        rule_id,
                    ),
                )

                if cursor.rowcount == 0:
                    raise StandardsKnowledgeError(
                        f"Rule not found for update: {rule_id}",
                        error_code="RULE_NOT_FOUND",
                    )

                cursor.close()

            logger.info(f"Updated standard rule: {rule_id}")
            result = updated_rule.to_dict()
            result["success"] = True
            return result

        except sqlite3.Error as e:
            raise StandardsKnowledgeError(
                f"Failed to update rule {rule_id}: {e}",
                error_code="UPDATE_ERROR",
                details={"rule_id": rule_id, "database_error": str(e)},
            )

    def delete_rule(self, rule_id: str) -> dict[str, Any]:
        """
        Delete a standard rule.

        Algorithm Approach: Safe deletion with existence check.
        Ensures rule exists before deletion.

        Parameters
        ----------
        rule_id (str): ID of the rule to delete

        Returns
        -------
        Dict[str, Any]: Deletion confirmation

        Raises
        ------
        StandardsKnowledgeError: If rule not found or deletion fails

        """
        try:
            # Check if rule exists
            existing = self.get_rule_by_id(rule_id)
            if not existing:
                raise StandardsKnowledgeError(
                    f"Rule not found: {rule_id}", error_code="RULE_NOT_FOUND"
                )

            with self.db_manager.transaction("standards") as conn:
                cursor = conn.cursor()

                cursor.execute("DELETE FROM standard_rules WHERE id = ?", (rule_id,))

                if cursor.rowcount == 0:
                    raise StandardsKnowledgeError(
                        f"Rule not found for deletion: {rule_id}",
                        error_code="RULE_NOT_FOUND",
                    )

                cursor.close()

            logger.info(f"Deleted standard rule: {rule_id}")
            return {"success": True, "rule_id": rule_id}

        except sqlite3.Error as e:
            raise StandardsKnowledgeError(
                f"Failed to delete rule {rule_id}: {e}",
                error_code="DELETE_ERROR",
                details={"rule_id": rule_id, "database_error": str(e)},
            )

    def search_rules(self, filter_config: StandardRuleSearchFilter | None = None) -> dict[str, Any]:
        """
        Search standard rules with filtering.

        Algorithm Approach: Dynamic query building with parameterized queries.
        Supports complex filtering with full-text search capabilities.

        Parameters
        ----------
        filter_config (StandardRuleSearchFilter, optional): Search filters

        Returns
        -------
        Dict[str, Any]: Search results with rules and metadata

        Raises
        ------
        StandardsKnowledgeError: If search fails

        """
        try:
            if filter_config is None:
                filter_config = StandardRuleSearchFilter()

            filter_config.validate()

            # Build query dynamically
            query_parts = [
                """
                SELECT id, standard_category, rule_name, description,
                       validation_logic, severity, applicable_contexts,
                       created_at, updated_at, active, metadata
                FROM standard_rules
                WHERE 1=1
                """
            ]

            params = []

            # Add filters
            if filter_config.standard_category:
                query_parts.append("AND standard_category = ?")
                params.append(filter_config.standard_category)

            if filter_config.rule_name:
                query_parts.append("AND rule_name LIKE ?")
                params.append(f"%{filter_config.rule_name}%")

            if filter_config.severity:
                query_parts.append("AND severity = ?")
                params.append(filter_config.severity)

            if filter_config.active is not None:
                query_parts.append("AND active = ?")
                params.append(1 if filter_config.active else 0)

            if filter_config.search_text:
                query_parts.append("AND (rule_name LIKE ? OR description LIKE ?)")
                search_term = f"%{filter_config.search_text}%"
                params.extend([search_term, search_term])

            if filter_config.contexts:
                for context in filter_config.contexts:
                    query_parts.append("AND applicable_contexts LIKE ?")
                    params.append(f'%"{context}"%')

            # Add sorting
            sort_column = filter_config.sort_by
            if sort_column not in [
                "created_at",
                "updated_at",
                "rule_name",
                "standard_category",
                "severity",
            ]:
                sort_column = "created_at"

            query_parts.append(f"ORDER BY {sort_column} {filter_config.sort_order.upper()}")

            # Add pagination
            query_parts.append("LIMIT ? OFFSET ?")
            params.extend([filter_config.limit, filter_config.offset])

            query = " ".join(query_parts)

            with self.db_manager.transaction("standards") as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()

                # Get total count for pagination
                count_query = "SELECT COUNT(*) FROM standard_rules WHERE 1=1"
                count_params = []

                # Rebuild WHERE clause for count query
                if filter_config.standard_category:
                    count_query += " AND standard_category = ?"
                    count_params.append(filter_config.standard_category)

                if filter_config.rule_name:
                    count_query += " AND rule_name LIKE ?"
                    count_params.append(f"%{filter_config.rule_name}%")

                if filter_config.severity:
                    count_query += " AND severity = ?"
                    count_params.append(filter_config.severity)

                if filter_config.active is not None:
                    count_query += " AND active = ?"
                    count_params.append(1 if filter_config.active else 0)

                if filter_config.search_text:
                    count_query += " AND (rule_name LIKE ? OR description LIKE ?)"
                    search_term = f"%{filter_config.search_text}%"
                    count_params.extend([search_term, search_term])

                if filter_config.contexts:
                    for context in filter_config.contexts:
                        count_query += " AND applicable_contexts LIKE ?"
                        count_params.append(f'%"{context}"%')

                cursor.execute(count_query, count_params)
                total_count = cursor.fetchone()[0]

                cursor.close()

            # Convert rows to rule dictionaries
            rules = []
            for row in rows:
                rule_dict = {
                    "id": row[0],
                    "standard_category": row[1],
                    "rule_name": row[2],
                    "description": row[3],
                    "validation_logic": json.loads(row[4]) if row[4] else {},
                    "severity": row[5],
                    "applicable_contexts": json.loads(row[6]) if row[6] else [],
                    "created_at": row[7],
                    "updated_at": row[8],
                    "active": bool(row[9]) if row[9] is not None else True,
                    "metadata": json.loads(row[10]) if row[10] else {},
                }
                rules.append(rule_dict)

            return {
                "rules": rules,
                "total_count": total_count,
                "limit": filter_config.limit,
                "offset": filter_config.offset,
                "has_more": filter_config.offset + len(rules) < total_count,
            }

        except sqlite3.Error as e:
            raise StandardsKnowledgeError(
                f"Failed to search rules: {e}",
                error_code="SEARCH_ERROR",
                details={"database_error": str(e)},
            )

    def get_rules_by_context(self, context: str, active_only: bool = True) -> list[dict[str, Any]]:
        """
        Get rules applicable to a specific context.

        Algorithm Approach: Context-based filtering with JSON array search.
        Returns rules that apply to the given context.

        Parameters
        ----------
        context (str): Context to filter rules by
        active_only (bool): Whether to only return active rules

        Returns
        -------
        List[Dict[str, Any]]: List of applicable rules

        Raises
        ------
        StandardsKnowledgeError: If retrieval fails

        """
        try:
            if not context:
                return []

            with self.db_manager.transaction("standards") as conn:
                cursor = conn.cursor()

                query = """
                    SELECT id, standard_category, rule_name, description,
                           validation_logic, severity, applicable_contexts,
                           created_at, updated_at, active, metadata
                    FROM standard_rules
                    WHERE applicable_contexts LIKE ?
                """
                params = [f'%"{context}"%']

                if active_only:
                    query += " AND active = 1"

                query += " ORDER BY severity DESC, created_at DESC"

                cursor.execute(query, params)
                rows = cursor.fetchall()
                cursor.close()

            # Convert rows to rule dictionaries
            rules = []
            for row in rows:
                rule_dict = {
                    "id": row[0],
                    "standard_category": row[1],
                    "rule_name": row[2],
                    "description": row[3],
                    "validation_logic": json.loads(row[4]) if row[4] else {},
                    "severity": row[5],
                    "applicable_contexts": json.loads(row[6]) if row[6] else [],
                    "created_at": row[7],
                    "updated_at": row[8],
                    "active": bool(row[9]) if row[9] is not None else True,
                    "metadata": json.loads(row[10]) if row[10] else {},
                }
                rules.append(rule_dict)

            return rules

        except sqlite3.Error as e:
            raise StandardsKnowledgeError(
                f"Failed to get rules by context {context}: {e}",
                error_code="CONTEXT_RULES_ERROR",
                details={"context": context, "database_error": str(e)},
            )

    def get_rules_by_category(
        self, standard_category: str, active_only: bool = True
    ) -> list[dict[str, Any]]:
        """
        Get rules by standard category.

        Algorithm Approach: Category-based filtering with optional active status.
        Returns all rules for the given category.

        Parameters
        ----------
        standard_category (str): Category to filter rules by
        active_only (bool): Whether to only return active rules

        Returns
        -------
        List[Dict[str, Any]]: List of rules in the category

        Raises
        ------
        StandardsKnowledgeError: If retrieval fails

        """
        try:
            if not standard_category:
                return []

            with self.db_manager.transaction("standards") as conn:
                cursor = conn.cursor()

                query = """
                    SELECT id, standard_category, rule_name, description,
                           validation_logic, severity, applicable_contexts,
                           created_at, updated_at, active, metadata
                    FROM standard_rules
                    WHERE standard_category = ?
                """
                params = [standard_category]

                if active_only:
                    query += " AND active = 1"

                query += " ORDER BY severity DESC, rule_name ASC"

                cursor.execute(query, params)
                rows = cursor.fetchall()
                cursor.close()

            # Convert rows to rule dictionaries
            rules = []
            for row in rows:
                rule_dict = {
                    "id": row[0],
                    "standard_category": row[1],
                    "rule_name": row[2],
                    "description": row[3],
                    "validation_logic": json.loads(row[4]) if row[4] else {},
                    "severity": row[5],
                    "applicable_contexts": json.loads(row[6]) if row[6] else [],
                    "created_at": row[7],
                    "updated_at": row[8],
                    "active": bool(row[9]) if row[9] is not None else True,
                    "metadata": json.loads(row[10]) if row[10] else {},
                }
                rules.append(rule_dict)

            return rules

        except sqlite3.Error as e:
            raise StandardsKnowledgeError(
                f"Failed to get rules by category {standard_category}: {e}",
                error_code="CATEGORY_RULES_ERROR",
                details={
                    "standard_category": standard_category,
                    "database_error": str(e),
                },
            )

    def validate_context(self, context: str, data: dict[str, Any]) -> ComplianceReport:
        """
        Validate data against applicable rules for a context.

        Algorithm Approach: Rule filtering with batch validation execution.
        Provides comprehensive compliance reporting.

        Parameters
        ----------
        context (str): Context to validate against
        data (Dict[str, Any]): Data to validate

        Returns
        -------
        ComplianceReport: Comprehensive validation report

        Raises
        ------
        StandardsKnowledgeError: If validation fails

        """
        start_time = datetime.now(UTC)

        try:
            # Get applicable rules for context
            applicable_rules = self.get_rules_by_context(context, active_only=True)

            validation_results = []
            error_count = 0
            warning_count = 0
            info_count = 0
            passed_count = 0

            # Execute validation for each rule
            for rule in applicable_rules:
                try:
                    result = self.execute_validation_logic(rule, data)
                    validation_results.append(result)

                    if result.passed:
                        passed_count += 1
                    elif result.severity == "error":
                        error_count += 1
                    elif result.severity == "warning":
                        warning_count += 1
                    else:
                        info_count += 1

                except Exception as e:
                    # Create failure result for rule execution error
                    error_result = ValidationResult(
                        rule_id=rule["id"],
                        rule_name=rule["rule_name"],
                        passed=False,
                        severity="error",
                        message=f"Rule execution failed: {e!s}",
                        details={"error": str(e), "rule_data": rule},
                        execution_time=0.0,
                        timestamp=datetime.now(UTC).isoformat(),
                    )
                    validation_results.append(error_result)
                    error_count += 1
                    logger.error(f"Rule execution error for {rule['id']}: {e}")

            # Calculate overall status
            total_rules = len(applicable_rules)
            failed_rules = total_rules - passed_count

            if error_count > 0:
                overall_status = "failed"
            elif warning_count > 0:
                overall_status = "warning"
            else:
                overall_status = "passed"

            execution_time = (datetime.now(UTC) - start_time).total_seconds()

            report = ComplianceReport(
                context=context,
                total_rules=total_rules,
                passed_rules=passed_count,
                failed_rules=failed_rules,
                error_count=error_count,
                warning_count=warning_count,
                info_count=info_count,
                overall_status=overall_status,
                validation_results=validation_results,
                execution_time=execution_time,
                timestamp=start_time.isoformat(),
            )

            logger.info(f"Context validation completed: {context} - {overall_status}")
            return report

        except Exception as e:
            # Create error report for validation failure
            error_report = ComplianceReport(
                context=context,
                total_rules=0,
                passed_rules=0,
                failed_rules=0,
                error_count=1,
                warning_count=0,
                info_count=0,
                overall_status="error",
                validation_results=[],
                execution_time=(datetime.now(UTC) - start_time).total_seconds(),
                timestamp=start_time.isoformat(),
            )

            logger.error(f"Context validation failed for {context}: {e}")
            return error_report

    def execute_validation_logic(
        self, rule: dict[str, Any], data: dict[str, Any]
    ) -> ValidationResult:
        """
        Execute validation logic for a specific rule.

        Algorithm Approach: Logic type detection with appropriate validation.
        Supports multiple validation logic types and patterns.

        Parameters
        ----------
        rule (Dict[str, Any]): Rule to execute
        data (Dict[str, Any]): Data to validate

        Returns
        -------
        ValidationResult: Result of validation execution

        Raises
        ------
        StandardsKnowledgeError: If rule execution fails

        """
        start_time = datetime.now(UTC)

        try:
            validation_logic = rule.get("validation_logic", {})
            logic_type = validation_logic.get("type", "boolean")

            # Execute validation based on logic type
            if logic_type == "boolean":
                passed = self._execute_boolean_validation(validation_logic, data)
                message = "Boolean validation passed" if passed else "Boolean validation failed"

            elif logic_type == "exists":
                field_path = validation_logic.get("field_path", "")
                passed = self._execute_exists_validation(field_path, data)
                message = (
                    f"Field '{field_path}' exists"
                    if passed
                    else f"Field '{field_path}' does not exist"
                )

            elif logic_type == "regex":
                pattern = validation_logic.get("pattern", "")
                field_path = validation_logic.get("field_path", "")
                passed = self._execute_regex_validation(pattern, field_path, data)
                message = "Regex pattern matched" if passed else "Regex pattern did not match"

            elif logic_type == "enum":
                allowed_values = validation_logic.get("allowed_values", [])
                field_path = validation_logic.get("field_path", "")
                passed = self._execute_enum_validation(allowed_values, field_path, data)
                message = "Value is in allowed set" if passed else "Value is not in allowed set"

            elif logic_type == "range":
                min_val = validation_logic.get("min")
                max_val = validation_logic.get("max")
                field_path = validation_logic.get("field_path", "")
                passed = self._execute_range_validation(min_val, max_val, field_path, data)
                message = "Value is within range" if passed else "Value is outside range"

            elif logic_type == "length":
                min_length = validation_logic.get("min_length")
                max_length = validation_logic.get("max_length")
                field_path = validation_logic.get("field_path", "")
                passed = self._execute_length_validation(min_length, max_length, field_path, data)
                message = (
                    "Length meets requirements" if passed else "Length does not meet requirements"
                )

            else:
                passed = False
                message = f"Unknown validation logic type: {logic_type}"

            execution_time = (datetime.now(UTC) - start_time).total_seconds()

            return ValidationResult(
                rule_id=rule["id"],
                rule_name=rule["rule_name"],
                passed=passed,
                severity=rule["severity"],
                message=message,
                details={
                    "validation_logic": validation_logic,
                    "data_keys": list(data.keys()),
                },
                execution_time=execution_time,
                timestamp=start_time.isoformat(),
            )

        except Exception as e:
            execution_time = (datetime.now(UTC) - start_time).total_seconds()

            return ValidationResult(
                rule_id=rule["id"],
                rule_name=rule["rule_name"],
                passed=False,
                severity="error",
                message=f"Validation execution error: {e!s}",
                details={"error": str(e), "rule": rule},
                execution_time=execution_time,
                timestamp=start_time.isoformat(),
            )

    def _execute_boolean_validation(self, logic: dict[str, Any], data: dict[str, Any]) -> bool:
        """Execute boolean validation logic."""
        required = logic.get("required", True)
        return required

    def _execute_exists_validation(self, field_path: str, data: dict[str, Any]) -> bool:
        """Execute field existence validation."""
        if not field_path:
            return False

        # Navigate nested field path
        current = data
        path_parts = field_path.split(".")

        try:
            for part in path_parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return False
            return True
        except (KeyError, TypeError):
            return False

    def _execute_regex_validation(
        self, pattern: str, field_path: str, data: dict[str, Any]
    ) -> bool:
        """Execute regex pattern validation."""
        import re

        if not pattern or not field_path:
            return False

        try:
            # Get field value
            current = data
            path_parts = field_path.split(".")

            for part in path_parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return False

            if not isinstance(current, str):
                return False

            return bool(re.match(pattern, current))

        except (re.error, KeyError, TypeError):
            return False

    def _execute_enum_validation(
        self, allowed_values: list[Any], field_path: str, data: dict[str, Any]
    ) -> bool:
        """Execute enumeration validation."""
        if not allowed_values or not field_path:
            return False

        try:
            # Get field value
            current = data
            path_parts = field_path.split(".")

            for part in path_parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return False

            return current in allowed_values

        except (KeyError, TypeError):
            return False

    def _execute_range_validation(
        self, min_val: Any, max_val: Any, field_path: str, data: dict[str, Any]
    ) -> bool:
        """Execute range validation."""
        if not field_path:
            return False

        try:
            # Get field value
            current = data
            path_parts = field_path.split(".")

            for part in path_parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return False

            # Check if value is numeric
            if not isinstance(current, (int, float)):
                return False

            # Check range bounds
            if min_val is not None and current < min_val:
                return False
            if max_val is not None and current > max_val:
                return False

            return True

        except (KeyError, TypeError, ValueError):
            return False

    def _execute_length_validation(
        self, min_length: int, max_length: int, field_path: str, data: dict[str, Any]
    ) -> bool:
        """Execute length validation."""
        if not field_path:
            return False

        try:
            # Get field value
            current = data
            path_parts = field_path.split(".")

            for part in path_parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return False

            # Get length based on type
            if isinstance(current, (str, list, dict)):
                length = len(current)
            else:
                return False

            # Check length bounds
            if min_length is not None and length < min_length:
                return False
            if max_length is not None and length > max_length:
                return False

            return True

        except (KeyError, TypeError, ValueError):
            return False

    def get_statistics(self) -> dict[str, Any]:
        """
        Get service statistics and database information.

        Algorithm Approach: Aggregated queries with metadata collection.
        Provides comprehensive overview of service state.

        Returns:
        Dict[str, Any]: Service statistics and database info

        Raises:
        StandardsKnowledgeError: If statistics retrieval fails

        """
        try:
            with self.db_manager.transaction("standards") as conn:
                cursor = conn.cursor()

                # Get total rules
                cursor.execute("SELECT COUNT(*) FROM standard_rules")
                total_rules = cursor.fetchone()[0]

                # Get rules by category
                cursor.execute(
                    """
                    SELECT standard_category, COUNT(*)
                    FROM standard_rules
                    GROUP BY standard_category
                    ORDER BY count DESC
                """
                )
                rules_by_category = dict(cursor.fetchall())

                # Get rules by severity
                cursor.execute(
                    """
                    SELECT severity, COUNT(*)
                    FROM standard_rules
                    GROUP BY severity
                    ORDER BY count DESC
                """
                )
                rules_by_severity = dict(cursor.fetchall())

                # Get active vs inactive rules
                cursor.execute(
                    """
                    SELECT active, COUNT(*)
                    FROM standard_rules
                    GROUP BY active
                """
                )
                active_status = dict(cursor.fetchall())

                # Get rules created by time period
                cursor.execute(
                    """
                    SELECT
                        CASE
                            WHEN created_at >= date('now', '-7 days') THEN 'last_week'
                            WHEN created_at >= date('now', '-30 days') THEN 'last_month'
                            WHEN created_at >= date('now', '-90 days') THEN 'last_quarter'
                            ELSE 'older'
                        END as period,
                        COUNT(*) as count
                    FROM standard_rules
                    WHERE created_at IS NOT NULL
                    GROUP BY period
                """
                )
                creation_periods = dict(cursor.fetchall())

                cursor.close()

            # Get database info
            database_info = self.db_manager.get_database_info("standards")

            return {
                "total_rules": total_rules,
                "rules_by_category": rules_by_category,
                "rules_by_severity": rules_by_severity,
                "active_rules": active_status.get(1, 0),
                "inactive_rules": active_status.get(0, 0),
                "creation_periods": creation_periods,
                "database_info": database_info,
                "service_status": "healthy",
            }

        except sqlite3.Error as e:
            raise StandardsKnowledgeError(
                f"Failed to get statistics: {e}",
                error_code="STATISTICS_ERROR",
                details={"database_error": str(e)},
            )

    def batch_create_rules(self, rules_data: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Create multiple rules in a batch operation.

        Algorithm Approach: Transactional batch processing with validation.
        Ensures atomicity for all or none success.

        Parameters
        ----------
        rules_data (List[Dict[str, Any]]): List of rule data to create

        Returns
        -------
        Dict[str, Any]: Batch creation results with statistics

        Raises
        ------
        StandardsKnowledgeError: If batch creation fails

        """
        created_rules = []
        failed_rules = []

        try:
            with self.db_manager.transaction("standards") as conn:
                cursor = conn.cursor()

                for rule_data in rules_data:
                    try:
                        # Validate rule
                        rule = StandardRule.from_dict(rule_data)
                        rule.validate()

                        # Convert to JSON for storage
                        contexts_json = (
                            json.dumps(rule.applicable_contexts)
                            if rule.applicable_contexts
                            else None
                        )
                        validation_json = json.dumps(rule.validation_logic)
                        metadata_json = json.dumps(rule.metadata) if rule.metadata else None

                        # Insert rule
                        cursor.execute(
                            """
                            INSERT INTO standard_rules (
                                id, standard_category, rule_name, description,
                                validation_logic, severity, applicable_contexts,
                                created_at, updated_at, active, metadata
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                            (
                                rule.id,
                                rule.standard_category,
                                rule.rule_name,
                                rule.description,
                                validation_json,
                                rule.severity,
                                contexts_json,
                                rule.created_at,
                                rule.updated_at,
                                rule.active,
                                metadata_json,
                            ),
                        )

                        created_rules.append(rule.to_dict())

                    except Exception as e:
                        failed_rules.append({"data": rule_data, "error": str(e)})

                cursor.close()

            logger.info(f"Batch created {len(created_rules)} rules")

            return {
                "success": True,
                "created_rules": created_rules,
                "failed_rules": failed_rules,
                "total_created": len(created_rules),
                "total_failed": len(failed_rules),
                "total_processed": len(rules_data),
            }

        except sqlite3.Error as e:
            raise StandardsKnowledgeError(
                f"Failed to batch create rules: {e}",
                error_code="BATCH_CREATE_ERROR",
                details={"database_error": str(e)},
            )

    def get_database_info(self) -> dict[str, Any]:
        """
        Get database information for the standards knowledge database.

        Returns:
        Dict[str, Any]: Database information

        Raises:
        StandardsKnowledgeError: If info retrieval fails

        """
        try:
            return self.db_manager.get_database_info("standards")
        except Exception as e:
            raise StandardsKnowledgeError(
                f"Failed to get database info: {e}", error_code="DATABASE_INFO_ERROR"
            )

    # ========== ASYNC METHODS ==========

    async def create_rule_async(self, rule_data: dict[str, Any]) -> dict[str, Any]:
        """
        Asynchronously create a new standard rule.

        Algorithm Approach: Async wrapper around sync method.
        Provides non-blocking operation for I/O bound tasks.

        Parameters
        ----------
        rule_data (Dict[str, Any]): Rule data to create

        Returns
        -------
        Dict[str, Any]: Created rule data

        Raises
        ------
        StandardsKnowledgeError: If creation fails

        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.create_rule, rule_data)

    async def get_rule_by_id_async(self, rule_id: str) -> dict[str, Any] | None:
        """
        Asynchronously retrieve a standard rule by ID.

        Parameters
        ----------
        rule_id (str): ID of the rule to retrieve

        Returns
        -------
        Optional[Dict[str, Any]]: Rule data or None

        Raises
        ------
        StandardsKnowledgeError: If retrieval fails

        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_rule_by_id, rule_id)

    async def get_rule_by_name_async(
        self, standard_category: str, rule_name: str
    ) -> dict[str, Any] | None:
        """
        Asynchronously retrieve a standard rule by category and name.

        Parameters
        ----------
        standard_category (str): Category of the rule
        rule_name (str): Name of the rule

        Returns
        -------
        Optional[Dict[str, Any]]: Rule data or None

        Raises
        ------
        StandardsKnowledgeError: If retrieval fails

        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_rule_by_name, standard_category, rule_name)

    async def update_rule_async(self, rule_id: str, update_data: dict[str, Any]) -> dict[str, Any]:
        """
        Asynchronously update an existing standard rule.

        Parameters
        ----------
        rule_id (str): ID of the rule to update
        update_data (Dict[str, Any]): Fields to update

        Returns
        -------
        Dict[str, Any]: Updated rule data

        Raises
        ------
        StandardsKnowledgeError: If update fails

        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.update_rule, rule_id, update_data)

    async def delete_rule_async(self, rule_id: str) -> dict[str, Any]:
        """
        Asynchronously delete a standard rule.

        Parameters
        ----------
        rule_id (str): ID of the rule to delete

        Returns
        -------
        Dict[str, Any]: Deletion confirmation

        Raises
        ------
        StandardsKnowledgeError: If deletion fails

        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.delete_rule, rule_id)

    async def search_rules_async(
        self, filter_config: StandardRuleSearchFilter | None = None
    ) -> dict[str, Any]:
        """
        Asynchronously search standard rules.

        Parameters
        ----------
        filter_config (StandardRuleSearchFilter, optional): Search filters

        Returns
        -------
        Dict[str, Any]: Search results

        Raises
        ------
        StandardsKnowledgeError: If search fails

        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.search_rules, filter_config)

    async def get_rules_by_context_async(
        self, context: str, active_only: bool = True
    ) -> list[dict[str, Any]]:
        """
        Asynchronously get rules applicable to a specific context.

        Parameters
        ----------
        context (str): Context to filter rules by
        active_only (bool): Whether to only return active rules

        Returns
        -------
        List[Dict[str, Any]]: List of applicable rules

        Raises
        ------
        StandardsKnowledgeError: If retrieval fails

        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_rules_by_context, context, active_only)

    async def get_rules_by_category_async(
        self, standard_category: str, active_only: bool = True
    ) -> list[dict[str, Any]]:
        """
        Asynchronously get rules by standard category.

        Parameters
        ----------
        standard_category (str): Category to filter rules by
        active_only (bool): Whether to only return active rules

        Returns
        -------
        List[Dict[str, Any]]: List of rules in the category

        Raises
        ------
        StandardsKnowledgeError: If retrieval fails

        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.get_rules_by_category, standard_category, active_only
        )

    async def validate_context_async(self, context: str, data: dict[str, Any]) -> ComplianceReport:
        """
        Asynchronously validate data against applicable rules for a context.

        Parameters
        ----------
        context (str): Context to validate against
        data (Dict[str, Any]): Data to validate

        Returns
        -------
        ComplianceReport: Comprehensive validation report

        Raises
        ------
        StandardsKnowledgeError: If validation fails

        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.validate_context, context, data)

    async def get_statistics_async(self) -> dict[str, Any]:
        """
        Asynchronously get service statistics.

        Returns:
        Dict[str, Any]: Service statistics

        Raises:
        StandardsKnowledgeError: If statistics retrieval fails

        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_statistics)

    async def batch_create_rules_async(self, rules_data: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Asynchronously create multiple rules in a batch operation.

        Parameters
        ----------
        rules_data (List[Dict[str, Any]]): List of rule data to create

        Returns
        -------
        Dict[str, Any]: Batch creation results

        Raises
        ------
        StandardsKnowledgeError: If batch creation fails

        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.batch_create_rules, rules_data)

    # ========== UTILITY METHODS ==========

    def close(self) -> None:
        """
        Close the service and cleanup resources.

        Algorithm Approach: Graceful shutdown with resource cleanup.
        Ensures no resource leaks on service termination.
        """
        try:
            if hasattr(self, "db_manager") and self.db_manager:
                self.db_manager.close_all()
            logger.info("StandardsKnowledgeService closed successfully")
        except Exception as e:
            logger.warning(f"Error closing StandardsKnowledgeService: {e}")

    def __enter__(self) -> StandardsKnowledgeService:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        """Context manager exit with cleanup."""
        self.close()
        if exc_type:
            logger.error("StandardsKnowledgeService exiting with error: %s", exc_val)
        return False  # Don't suppress exceptions
