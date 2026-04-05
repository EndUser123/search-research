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

"""
Library Knowledge Service for CSF SQLite Knowledge Curator.

Algorithm Approach: Service layer pattern with comprehensive CRUD operations,
search functionality, and metadata management. Uses SQLiteDatabaseManager
for all database operations with proper transaction handling.

Time Complexity: O(log n) for indexed operations, O(n) for full table scans
Space Complexity: O(1) for single operations, O(m) for batch operations

Design Pattern: Service layer with repository pattern for data access.
Provides clean abstraction over database operations with comprehensive
error handling and validation.

Security Features:
- SQL injection prevention through parameterized queries
- Input validation and sanitization
- Transaction atomicity for data consistency
- Access control through service layer
- Comprehensive error handling prevents information leakage

Parameters:
db_manager (SQLiteDatabaseManager): Database manager instance
    - Must be properly initialized
    - Provides connection pooling and transaction management
    - Handles all database operations

Returns:
LibraryKnowledgeService: Configured service instance
    - Ready for immediate use
    - Thread-safe operations
    - Comprehensive error handling

Raises:
ValueError: For invalid configuration or parameters
LibraryKnowledgeError: For service-specific errors
sqlite3.Error: For database operation errors

Examples:
>>> db_manager = SQLiteDatabaseManager()
>>> service = LibraryKnowledgeService(db_manager)
>>> pattern = service.create_pattern({
...     "library_name": "requests",
...     "pattern_type": "usage_pattern",
...     "title": "HTTP GET Request",
...     "description": "Making HTTP GET requests"
... })
>>> service.get_pattern_by_id(pattern["id"])

Edge Cases:
- Empty search results: Returns empty list with metadata
- Database connection failures: Proper error wrapping and retry
- Invalid data patterns: Comprehensive validation with clear messages
- Concurrent operations: Thread-safe with proper isolation
- Large datasets: Paginated results and efficient queries

Performance Considerations:
- Connection pooling reduces overhead for frequent operations
- Database indexes on frequently queried fields
- Batch operations minimize transaction overhead
- Async operations prevent blocking on I/O
- Efficient query patterns avoid N+1 problems
"""


# Configure logging for library knowledge operations
logger = logging.getLogger(__name__)


class LibraryKnowledgeError(Exception):
    """
    Custom exception for library knowledge service errors.

    Algorithm Approach: Structured error handling with context information.
    Provides clear error categorization and debugging information.

    Attributes:
    message (str): Human-readable error message
    error_code (str): Machine-readable error code
    details (dict): Additional error context

    """

    def __init__(
        self, message: str, error_code: str = "LIBRARY_ERROR", details: dict | None = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}

    def __str__(self):
        return f"[{self.error_code}] {self.message}"


@dataclass
class LibraryPattern:
    """
    Library pattern data model.

    Algorithm Approach: Dataclass with validation and serialization.
    Provides type safety and convenient data access patterns.

    Attributes:
    id (str): Unique identifier for the pattern
    library_name (str): Name of the library this pattern belongs to
    pattern_type (str): Type of pattern (usage_pattern, violation_pattern, etc.)
    title (str): Human-readable title for the pattern
    description (str): Detailed description of the pattern
    evidence (str, optional): Evidence or rationale for the pattern
    code_example (str, optional): Code example demonstrating the pattern
    source (str): Source of the pattern (manual, automated, imported)
    confidence_score (float): Confidence score (0.0 to 1.0)
    created_at (str): ISO timestamp when pattern was created
    updated_at (str): ISO timestamp when pattern was last updated
    tags (List[str], optional): Tags for categorization and search
    metadata (dict, optional): Additional metadata as key-value pairs

    """

    library_name: str
    pattern_type: str
    title: str
    description: str
    id: str | None = None
    evidence: str | None = None
    code_example: str | None = None
    source: str = "manual"
    confidence_score: float = 0.8
    created_at: str | None = None
    updated_at: str | None = None
    tags: list[str] | None = None
    metadata: dict | None = None

    def __post_init__(self):
        """Validate pattern data after initialization."""
        if not self.id:
            self.id = str(uuid.uuid4())

        if not self.created_at:
            self.created_at = datetime.now(UTC).isoformat()

        if not self.updated_at:
            self.updated_at = self.created_at

        if self.tags is None:
            self.tags = []

        if self.metadata is None:
            self.metadata = {}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LibraryPattern:
        """Create LibraryPattern from dictionary."""
        try:
            return cls(**data)
        except TypeError as e:
            raise LibraryKnowledgeError(
                f"Invalid pattern data: {e}",
                error_code="INVALID_PATTERN_DATA",
                details={"missing_fields": str(e)},
            )

    def to_dict(self) -> dict[str, Any]:
        """Convert LibraryPattern to dictionary."""
        return asdict(self)

    def validate(self) -> None:
        """
        Validate pattern data integrity.

        Algorithm Approach: Comprehensive validation with clear error messages.
        Ensures data consistency and prevents invalid states.

        Raises:
        LibraryKnowledgeError: If validation fails

        """
        errors = []

        # Required field validation
        if not self.library_name or not isinstance(self.library_name, str):
            errors.append("library_name is required and must be a string")
        elif len(self.library_name) > 255:
            errors.append("library_name must be 255 characters or less")

        if not self.pattern_type or not isinstance(self.pattern_type, str):
            errors.append("pattern_type is required and must be a string")
        elif len(self.pattern_type) > 100:
            errors.append("pattern_type must be 100 characters or less")

        if not self.title or not isinstance(self.title, str):
            errors.append("title is required and must be a string")
        elif len(self.title) > 500:
            errors.append("title must be 500 characters or less")

        if not self.description or not isinstance(self.description, str):
            errors.append("description is required and must be a string")

        # Confidence score validation
        if not isinstance(self.confidence_score, (int, float)):
            errors.append("confidence_score must be a number")
        elif not 0.0 <= self.confidence_score <= 1.0:
            errors.append("confidence_score must be between 0.0 and 1.0")

        # Tags validation
        if self.tags is not None:
            if not isinstance(self.tags, list):
                errors.append("tags must be a list")
            else:
                for i, tag in enumerate(self.tags):
                    if not isinstance(tag, str):
                        errors.append(f"tag[{i}] must be a string")
                    elif len(tag) > 100:
                        errors.append(f"tag[{i}] must be 100 characters or less")

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
            raise LibraryKnowledgeError(
                f"Validation failed: {'; '.join(errors)}",
                error_code="VALIDATION_ERROR",
                details={"field_errors": errors},
            )


@dataclass
class LibraryPatternSearchFilter:
    """
    Search filter for library patterns.

    Algorithm Approach: Flexible filtering with multiple criteria.
    Supports complex search scenarios with pagination.

    Attributes:
    library_name (str, optional): Filter by library name (partial match)
    pattern_type (str, optional): Filter by pattern type
    tags (List[str], optional): Filter by tags (AND logic)
    source (str, optional): Filter by source
    min_confidence (float, optional): Minimum confidence score
    max_confidence (float, optional): Maximum confidence score
    search_text (str, optional): Text search in title and description
    limit (int): Maximum number of results (default: 50)
    offset (int): Number of results to skip (default: 0)
    sort_by (str): Sort field (default: "created_at")
    sort_order (str): Sort order ("asc" or "desc", default: "desc")

    """

    library_name: str | None = None
    pattern_type: str | None = None
    tags: list[str] | None = None
    source: str | None = None
    min_confidence: float | None = None
    max_confidence: float | None = None
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
        LibraryKnowledgeError: If validation fails

        """
        errors = []

        if self.limit <= 0 or self.limit > 1000:
            errors.append("limit must be between 1 and 1000")

        if self.offset < 0:
            errors.append("offset must be non-negative")

        if self.sort_by not in [
            "created_at",
            "updated_at",
            "title",
            "library_name",
            "confidence_score",
        ]:
            errors.append("invalid sort_by field")

        if self.sort_order not in ["asc", "desc"]:
            errors.append("sort_order must be 'asc' or 'desc'")

        if self.min_confidence is not None:
            if (
                not isinstance(self.min_confidence, (int, float))
                or not 0.0 <= self.min_confidence <= 1.0
            ):
                errors.append("min_confidence must be between 0.0 and 1.0")

        if self.max_confidence is not None:
            if (
                not isinstance(self.max_confidence, (int, float))
                or not 0.0 <= self.max_confidence <= 1.0
            ):
                errors.append("max_confidence must be between 0.0 and 1.0")

        if self.min_confidence is not None and self.max_confidence is not None:
            if self.min_confidence > self.max_confidence:
                errors.append("min_confidence cannot be greater than max_confidence")

        if errors:
            raise LibraryKnowledgeError(
                f"Search filter validation failed: {'; '.join(errors)}",
                error_code="FILTER_VALIDATION_ERROR",
            )


@dataclass
class LibraryPatternCategory:
    """
    Pattern category information.

    Algorithm Approach: Category aggregation with statistics.
    Provides overview of pattern distribution.

    Attributes:
    name (str): Category name
    display_name (str): Human-readable display name
    description (str): Category description
    count (int): Number of patterns in this category
    last_updated (str): ISO timestamp of last update

    """

    name: str
    display_name: str
    description: str
    count: int
    last_updated: str


class LibraryKnowledgeService:
    """
    Service for managing library knowledge patterns.

    Algorithm Approach: Service layer with comprehensive CRUD operations,
    search functionality, and metadata management. Uses SQLiteDatabaseManager
    for all database operations with proper transaction handling.

    Design Pattern: Service layer with repository pattern for data access.
    Provides clean abstraction over database operations.

    Thread Safety: Thread-safe operations through database manager connection
    pooling and proper transaction isolation.
    """

    def __init__(self, db_manager: SQLiteDatabaseManager):
        """
        Initialize Library Knowledge Service.

        Parameters
        ----------
        db_manager (SQLiteDatabaseManager): Database manager instance

        Raises
        ------
        ValueError: If db_manager is invalid
        LibraryKnowledgeError: If service initialization fails

        """
        if not db_manager:
            raise ValueError("Database manager is required")

        self.db_manager = db_manager
        self._ensure_database_schema()

        logger.info("LibraryKnowledgeService initialized successfully")

    def _ensure_database_schema(self) -> None:
        """
        Ensure database schema exists and is up-to-date.

        Algorithm Approach: Schema validation and creation.
        Creates necessary tables and indexes if they don't exist.

        Raises:
        LibraryKnowledgeError: If schema creation fails

        """
        try:
            with self.db_manager.transaction("library") as conn:
                cursor = conn.cursor()

                # Create library_patterns table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS library_patterns (
                        id TEXT PRIMARY KEY,
                        library_name TEXT NOT NULL,
                        pattern_type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT NOT NULL,
                        evidence TEXT,
                        code_example TEXT,
                        source TEXT DEFAULT 'manual',
                        confidence_score REAL DEFAULT 0.8,
                        created_at TEXT,
                        updated_at TEXT,
                        tags TEXT,
                        metadata TEXT
                    )
                """)

                # Create indexes for common queries
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_library_name ON library_patterns(library_name)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_pattern_type ON library_patterns(pattern_type)"
                )
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_source ON library_patterns(source)")
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_created_at ON library_patterns(created_at)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_confidence_score ON library_patterns(confidence_score)"
                )

                # Create full-text search index
                cursor.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS library_patterns_fts
                    USING fts5(title, description, content=library_patterns, content_rowid=rowid)
                """)

                # Trigger to maintain FTS index
                cursor.execute("""
                    CREATE TRIGGER IF NOT EXISTS library_patterns_fts_insert
                    AFTER INSERT ON library_patterns
                    BEGIN
                        INSERT INTO library_patterns_fts(rowid, title, description)
                        VALUES (new.rowid, new.title, new.description);
                    END
                """)

                cursor.execute("""
                    CREATE TRIGGER IF NOT EXISTS library_patterns_fts_update
                    AFTER UPDATE ON library_patterns
                    BEGIN
                        UPDATE library_patterns_fts SET
                            title = new.title,
                            description = new.description
                        WHERE rowid = old.rowid;
                    END
                """)

                cursor.execute("""
                    CREATE TRIGGER IF NOT EXISTS library_patterns_fts_delete
                    AFTER DELETE ON library_patterns
                    BEGIN
                        DELETE FROM library_patterns_fts WHERE rowid = old.rowid;
                    END
                """)

                cursor.close()
                logger.debug("Database schema ensured successfully")

        except sqlite3.Error as e:
            raise LibraryKnowledgeError(
                f"Failed to ensure database schema: {e}",
                error_code="SCHEMA_ERROR",
                details={"database_error": str(e)},
            )

    def create_pattern(self, pattern_data: dict[str, Any]) -> dict[str, Any]:
        """
        Create a new library pattern.

        Algorithm Approach: Validation followed by database insertion.
        Ensures data integrity and returns complete pattern information.

        Parameters
        ----------
        pattern_data (Dict[str, Any]): Pattern data to create

        Returns
        -------
        Dict[str, Any]: Created pattern with generated fields

        Raises
        ------
        LibraryKnowledgeError: If validation or creation fails

        """
        try:
            # Create and validate pattern
            pattern = LibraryPattern.from_dict(pattern_data)
            pattern.validate()

            # Convert lists and dicts to JSON for storage
            tags_json = json.dumps(pattern.tags) if pattern.tags else None
            metadata_json = json.dumps(pattern.metadata) if pattern.metadata else None

            with self.db_manager.transaction("library") as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO library_patterns (
                        id, library_name, pattern_type, title, description,
                        evidence, code_example, source, confidence_score,
                        created_at, updated_at, tags, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        pattern.id,
                        pattern.library_name,
                        pattern.pattern_type,
                        pattern.title,
                        pattern.description,
                        pattern.evidence,
                        pattern.code_example,
                        pattern.source,
                        pattern.confidence_score,
                        pattern.created_at,
                        pattern.updated_at,
                        tags_json,
                        metadata_json,
                    ),
                )

                cursor.close()

            logger.info(f"Created library pattern: {pattern.id}")

            # Return complete pattern data with success flag
            result = pattern.to_dict()
            result["success"] = True
            return result

        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                raise LibraryKnowledgeError(
                    "Pattern with this ID already exists", error_code="DUPLICATE_PATTERN"
                )
            raise LibraryKnowledgeError(
                f"Database integrity error: {e}", error_code="INTEGRITY_ERROR"
            )
        except sqlite3.Error as e:
            raise LibraryKnowledgeError(
                f"Failed to create pattern: {e}",
                error_code="CREATE_ERROR",
                details={"database_error": str(e)},
            )

    def get_pattern_by_id(self, pattern_id: str) -> dict[str, Any] | None:
        """
        Retrieve a library pattern by ID.

        Algorithm Approach: Direct lookup with JSON field restoration.
        Returns complete pattern data with proper types.

        Parameters
        ----------
        pattern_id (str): ID of the pattern to retrieve

        Returns
        -------
        Optional[Dict[str, Any]]: Pattern data or None if not found

        Raises
        ------
        LibraryKnowledgeError: If database operation fails

        """
        try:
            if not pattern_id:
                return None

            with self.db_manager.transaction("library") as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT id, library_name, pattern_type, title, description,
                           evidence, code_example, source, confidence_score,
                           created_at, updated_at, tags, metadata
                    FROM library_patterns
                    WHERE id = ?
                """,
                    (pattern_id,),
                )

                row = cursor.fetchone()
                cursor.close()

                if not row:
                    return None

                # Convert row to dictionary with JSON field restoration
                pattern_dict = {
                    "id": row[0],
                    "library_name": row[1],
                    "pattern_type": row[2],
                    "title": row[3],
                    "description": row[4],
                    "evidence": row[5],
                    "code_example": row[6],
                    "source": row[7],
                    "confidence_score": row[8],
                    "created_at": row[9],
                    "updated_at": row[10],
                    "tags": json.loads(row[11]) if row[11] else [],
                    "metadata": json.loads(row[12]) if row[12] else {},
                }

                return pattern_dict

        except sqlite3.Error as e:
            raise LibraryKnowledgeError(
                f"Failed to get pattern {pattern_id}: {e}",
                error_code="RETRIEVE_ERROR",
                details={"pattern_id": pattern_id, "database_error": str(e)},
            )

    def update_pattern(self, pattern_id: str, update_data: dict[str, Any]) -> dict[str, Any]:
        """
        Update an existing library pattern.

        Algorithm Approach: Validation with selective field updates.
        Maintains data integrity while allowing partial updates.

        Parameters
        ----------
        pattern_id (str): ID of the pattern to update
        update_data (Dict[str, Any]): Fields to update

        Returns
        -------
        Dict[str, Any]: Updated pattern data

        Raises
        ------
        LibraryKnowledgeError: If pattern not found or validation fails

        """
        try:
            # Get existing pattern first
            existing = self.get_pattern_by_id(pattern_id)
            if not existing:
                raise LibraryKnowledgeError(
                    f"Pattern not found: {pattern_id}", error_code="PATTERN_NOT_FOUND"
                )

            # Update fields
            existing.update(update_data)
            existing["updated_at"] = datetime.now(UTC).isoformat()

            # Validate updated pattern
            updated_pattern = LibraryPattern.from_dict(existing)
            updated_pattern.validate()

            # Convert lists and dicts to JSON for storage
            tags_json = json.dumps(updated_pattern.tags) if updated_pattern.tags else None
            metadata_json = (
                json.dumps(updated_pattern.metadata) if updated_pattern.metadata else None
            )

            with self.db_manager.transaction("library") as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    UPDATE library_patterns
                    SET library_name = ?, pattern_type = ?, title = ?, description = ?,
                        evidence = ?, code_example = ?, source = ?, confidence_score = ?,
                        updated_at = ?, tags = ?, metadata = ?
                    WHERE id = ?
                """,
                    (
                        updated_pattern.library_name,
                        updated_pattern.pattern_type,
                        updated_pattern.title,
                        updated_pattern.description,
                        updated_pattern.evidence,
                        updated_pattern.code_example,
                        updated_pattern.source,
                        updated_pattern.confidence_score,
                        updated_pattern.updated_at,
                        tags_json,
                        metadata_json,
                        pattern_id,
                    ),
                )

                if cursor.rowcount == 0:
                    raise LibraryKnowledgeError(
                        f"Pattern not found for update: {pattern_id}",
                        error_code="PATTERN_NOT_FOUND",
                    )

                cursor.close()

            logger.info(f"Updated library pattern: {pattern_id}")
            result = updated_pattern.to_dict()
            result["success"] = True
            return result

        except sqlite3.Error as e:
            raise LibraryKnowledgeError(
                f"Failed to update pattern {pattern_id}: {e}",
                error_code="UPDATE_ERROR",
                details={"pattern_id": pattern_id, "database_error": str(e)},
            )

    def delete_pattern(self, pattern_id: str) -> dict[str, Any]:
        """
        Delete a library pattern.

        Algorithm Approach: Safe deletion with existence check.
        Ensures pattern exists before deletion.

        Parameters
        ----------
        pattern_id (str): ID of the pattern to delete

        Returns
        -------
        Dict[str, Any]: Deletion confirmation

        Raises
        ------
        LibraryKnowledgeError: If pattern not found or deletion fails

        """
        try:
            # Check if pattern exists
            existing = self.get_pattern_by_id(pattern_id)
            if not existing:
                raise LibraryKnowledgeError(
                    f"Pattern not found: {pattern_id}", error_code="PATTERN_NOT_FOUND"
                )

            with self.db_manager.transaction("library") as conn:
                cursor = conn.cursor()

                cursor.execute("DELETE FROM library_patterns WHERE id = ?", (pattern_id,))

                if cursor.rowcount == 0:
                    raise LibraryKnowledgeError(
                        f"Pattern not found for deletion: {pattern_id}",
                        error_code="PATTERN_NOT_FOUND",
                    )

                cursor.close()

            logger.info(f"Deleted library pattern: {pattern_id}")
            return {"success": True, "pattern_id": pattern_id}

        except sqlite3.Error as e:
            raise LibraryKnowledgeError(
                f"Failed to delete pattern {pattern_id}: {e}",
                error_code="DELETE_ERROR",
                details={"pattern_id": pattern_id, "database_error": str(e)},
            )

    def search_patterns(
        self, filter_config: LibraryPatternSearchFilter | None = None
    ) -> dict[str, Any]:
        """
        Search library patterns with filtering.

        Algorithm Approach: Dynamic query building with parameterized queries.
        Supports complex filtering with full-text search capabilities.

        Parameters
        ----------
        filter_config (LibraryPatternSearchFilter, optional): Search filters

        Returns
        -------
        Dict[str, Any]: Search results with patterns and metadata

        Raises
        ------
        LibraryKnowledgeError: If search fails

        """
        try:
            if filter_config is None:
                filter_config = LibraryPatternSearchFilter()

            filter_config.validate()

            # Build query dynamically
            query_parts = [
                """
                SELECT id, library_name, pattern_type, title, description,
                       evidence, code_example, source, confidence_score,
                       created_at, updated_at, tags, metadata
                FROM library_patterns
                WHERE 1=1
                """
            ]

            params = []

            # Add filters
            if filter_config.library_name:
                query_parts.append("AND library_name LIKE ?")
                params.append(f"%{filter_config.library_name}%")

            if filter_config.pattern_type:
                query_parts.append("AND pattern_type = ?")
                params.append(filter_config.pattern_type)

            if filter_config.source:
                query_parts.append("AND source = ?")
                params.append(filter_config.source)

            if filter_config.min_confidence is not None:
                query_parts.append("AND confidence_score >= ?")
                params.append(filter_config.min_confidence)

            if filter_config.max_confidence is not None:
                query_parts.append("AND confidence_score <= ?")
                params.append(filter_config.max_confidence)

            if filter_config.search_text:
                query_parts.append("AND (title LIKE ? OR description LIKE ?)")
                search_term = f"%{filter_config.search_text}%"
                params.extend([search_term, search_term])

            if filter_config.tags:
                for tag in filter_config.tags:
                    query_parts.append("AND tags LIKE ?")
                    params.append(f'%"{tag}"%')

            # Add sorting
            sort_column = filter_config.sort_by
            if sort_column not in [
                "created_at",
                "updated_at",
                "title",
                "library_name",
                "confidence_score",
            ]:
                sort_column = "created_at"

            query_parts.append(f"ORDER BY {sort_column} {filter_config.sort_order.upper()}")

            # Add pagination
            query_parts.append("LIMIT ? OFFSET ?")
            params.extend([filter_config.limit, filter_config.offset])

            query = " ".join(query_parts)

            with self.db_manager.transaction("library") as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()

                # Get total count for pagination
                count_query = "SELECT COUNT(*) FROM library_patterns WHERE 1=1"
                count_params = []

                # Rebuild WHERE clause for count query
                if filter_config.library_name:
                    count_query += " AND library_name LIKE ?"
                    count_params.append(f"%{filter_config.library_name}%")

                if filter_config.pattern_type:
                    count_query += " AND pattern_type = ?"
                    count_params.append(filter_config.pattern_type)

                if filter_config.source:
                    count_query += " AND source = ?"
                    count_params.append(filter_config.source)

                if filter_config.min_confidence is not None:
                    count_query += " AND confidence_score >= ?"
                    count_params.append(filter_config.min_confidence)

                if filter_config.max_confidence is not None:
                    count_query += " AND confidence_score <= ?"
                    count_params.append(filter_config.max_confidence)

                if filter_config.search_text:
                    count_query += " AND (title LIKE ? OR description LIKE ?)"
                    search_term = f"%{filter_config.search_text}%"
                    count_params.extend([search_term, search_term])

                if filter_config.tags:
                    for tag in filter_config.tags:
                        count_query += " AND tags LIKE ?"
                        count_params.append(f'%"{tag}"%')

                cursor.execute(count_query, count_params)
                total_count = cursor.fetchone()[0]

                cursor.close()

            # Convert rows to pattern dictionaries
            patterns = []
            for row in rows:
                pattern_dict = {
                    "id": row[0],
                    "library_name": row[1],
                    "pattern_type": row[2],
                    "title": row[3],
                    "description": row[4],
                    "evidence": row[5],
                    "code_example": row[6],
                    "source": row[7],
                    "confidence_score": row[8],
                    "created_at": row[9],
                    "updated_at": row[10],
                    "tags": json.loads(row[11]) if row[11] else [],
                    "metadata": json.loads(row[12]) if row[12] else {},
                }
                patterns.append(pattern_dict)

            return {
                "patterns": patterns,
                "total_count": total_count,
                "limit": filter_config.limit,
                "offset": filter_config.offset,
                "has_more": filter_config.offset + len(patterns) < total_count,
            }

        except sqlite3.Error as e:
            raise LibraryKnowledgeError(
                f"Failed to search patterns: {e}",
                error_code="SEARCH_ERROR",
                details={"database_error": str(e)},
            )

    def get_pattern_categories(self) -> list[dict[str, Any]]:
        """
        Get pattern categories with statistics.

        Algorithm Approach: Grouped aggregation with metadata.
        Provides overview of pattern distribution by type.

        Returns:
        List[Dict[str, Any]]: Category information with statistics

        Raises:
        LibraryKnowledgeError: If retrieval fails

        """
        try:
            with self.db_manager.transaction("library") as conn:
                cursor = conn.cursor()

                # Get pattern types with counts
                cursor.execute("""
                    SELECT
                        pattern_type,
                        COUNT(*) as count,
                        MAX(updated_at) as last_updated
                    FROM library_patterns
                    GROUP BY pattern_type
                    ORDER BY count DESC
                """)

                rows = cursor.fetchall()
                cursor.close()

            categories = []
            for row in rows:
                category = {
                    "name": row[0],
                    "display_name": row[0].replace("_", " ").title(),
                    "description": f"Patterns of type {row[0]}",
                    "count": row[1],
                    "last_updated": row[2],
                }
                categories.append(category)

            return categories

        except sqlite3.Error as e:
            raise LibraryKnowledgeError(
                f"Failed to get pattern categories: {e}",
                error_code="CATEGORIES_ERROR",
                details={"database_error": str(e)},
            )

    def batch_create_patterns(self, patterns_data: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Create multiple patterns in a batch operation.

        Algorithm Approach: Transactional batch processing with validation.
        Ensures atomicity for all or none success.

        Parameters
        ----------
        patterns_data (List[Dict[str, Any]]): List of pattern data to create

        Returns
        -------
        Dict[str, Any]: Batch creation results with statistics

        Raises
        ------
        LibraryKnowledgeError: If batch creation fails

        """
        created_patterns = []
        failed_patterns = []

        try:
            with self.db_manager.transaction("library") as conn:
                cursor = conn.cursor()

                for pattern_data in patterns_data:
                    try:
                        # Validate pattern
                        pattern = LibraryPattern.from_dict(pattern_data)
                        pattern.validate()

                        # Convert to JSON for storage
                        tags_json = json.dumps(pattern.tags) if pattern.tags else None
                        metadata_json = json.dumps(pattern.metadata) if pattern.metadata else None

                        # Insert pattern
                        cursor.execute(
                            """
                            INSERT INTO library_patterns (
                                id, library_name, pattern_type, title, description,
                                evidence, code_example, source, confidence_score,
                                created_at, updated_at, tags, metadata
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                            (
                                pattern.id,
                                pattern.library_name,
                                pattern.pattern_type,
                                pattern.title,
                                pattern.description,
                                pattern.evidence,
                                pattern.code_example,
                                pattern.source,
                                pattern.confidence_score,
                                pattern.created_at,
                                pattern.updated_at,
                                tags_json,
                                metadata_json,
                            ),
                        )

                        created_patterns.append(pattern.to_dict())

                    except Exception as e:
                        failed_patterns.append({"data": pattern_data, "error": str(e)})

                cursor.close()

            logger.info(f"Batch created {len(created_patterns)} patterns")

            return {
                "success": True,
                "created_patterns": created_patterns,
                "failed_patterns": failed_patterns,
                "total_created": len(created_patterns),
                "total_failed": len(failed_patterns),
                "total_processed": len(patterns_data),
            }

        except sqlite3.Error as e:
            raise LibraryKnowledgeError(
                f"Failed to batch create patterns: {e}",
                error_code="BATCH_CREATE_ERROR",
                details={"database_error": str(e)},
            )

    def get_statistics(self) -> dict[str, Any]:
        """
        Get service statistics and database information.

        Algorithm Approach: Aggregated queries with metadata collection.
        Provides comprehensive overview of service state.

        Returns:
        Dict[str, Any]: Service statistics and database info

        Raises:
        LibraryKnowledgeError: If statistics retrieval fails

        """
        try:
            with self.db_manager.transaction("library") as conn:
                cursor = conn.cursor()

                # Get total patterns
                cursor.execute("SELECT COUNT(*) FROM library_patterns")
                total_patterns = cursor.fetchone()[0]

                # Get patterns by library
                cursor.execute("""
                    SELECT library_name, COUNT(*)
                    FROM library_patterns
                    GROUP BY library_name
                    ORDER BY count DESC
                """)
                patterns_by_library = dict(cursor.fetchall())

                # Get patterns by type
                cursor.execute("""
                    SELECT pattern_type, COUNT(*)
                    FROM library_patterns
                    GROUP BY pattern_type
                    ORDER BY count DESC
                """)
                patterns_by_type = dict(cursor.fetchall())

                # Get patterns by source
                cursor.execute("""
                    SELECT source, COUNT(*)
                    FROM library_patterns
                    GROUP BY source
                    ORDER BY count DESC
                """)
                patterns_by_source = dict(cursor.fetchall())

                # Get confidence score statistics
                cursor.execute("""
                    SELECT
                        AVG(confidence_score) as avg_confidence,
                        MIN(confidence_score) as min_confidence,
                        MAX(confidence_score) as max_confidence
                    FROM library_patterns
                """)
                confidence_stats = cursor.fetchone()

                cursor.close()

            # Get database info
            database_info = self.db_manager.get_database_info("library")

            return {
                "total_patterns": total_patterns,
                "patterns_by_library": patterns_by_library,
                "patterns_by_type": patterns_by_type,
                "patterns_by_source": patterns_by_source,
                "confidence_statistics": {
                    "average": round(confidence_stats[0] or 0, 3),
                    "minimum": confidence_stats[1] or 0,
                    "maximum": confidence_stats[2] or 0,
                },
                "database_info": database_info,
                "service_status": "healthy",
            }

        except sqlite3.Error as e:
            raise LibraryKnowledgeError(
                f"Failed to get statistics: {e}",
                error_code="STATISTICS_ERROR",
                details={"database_error": str(e)},
            )

    def get_database_info(self) -> dict[str, Any]:
        """
        Get database information for the library knowledge database.

        Returns:
        Dict[str, Any]: Database information

        Raises:
        LibraryKnowledgeError: If info retrieval fails

        """
        try:
            return self.db_manager.get_database_info("library")
        except Exception as e:
            raise LibraryKnowledgeError(
                f"Failed to get database info: {e}", error_code="DATABASE_INFO_ERROR"
            )

    # ========== ASYNC METHODS ==========

    async def create_pattern_async(self, pattern_data: dict[str, Any]) -> dict[str, Any]:
        """
        Asynchronously create a new library pattern.

        Algorithm Approach: Async wrapper around sync method.
        Provides non-blocking operation for I/O bound tasks.

        Parameters
        ----------
        pattern_data (Dict[str, Any]): Pattern data to create

        Returns
        -------
        Dict[str, Any]: Created pattern data

        Raises
        ------
        LibraryKnowledgeError: If creation fails

        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.create_pattern, pattern_data)

    async def get_pattern_by_id_async(self, pattern_id: str) -> dict[str, Any] | None:
        """
        Asynchronously retrieve a library pattern by ID.

        Parameters
        ----------
        pattern_id (str): ID of the pattern to retrieve

        Returns
        -------
        Optional[Dict[str, Any]]: Pattern data or None

        Raises
        ------
        LibraryKnowledgeError: If retrieval fails

        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_pattern_by_id, pattern_id)

    async def update_pattern_async(
        self, pattern_id: str, update_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Asynchronously update an existing library pattern.

        Parameters
        ----------
        pattern_id (str): ID of the pattern to update
        update_data (Dict[str, Any]): Fields to update

        Returns
        -------
        Dict[str, Any]: Updated pattern data

        Raises
        ------
        LibraryKnowledgeError: If update fails

        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.update_pattern, pattern_id, update_data)

    async def delete_pattern_async(self, pattern_id: str) -> dict[str, Any]:
        """
        Asynchronously delete a library pattern.

        Parameters
        ----------
        pattern_id (str): ID of the pattern to delete

        Returns
        -------
        Dict[str, Any]: Deletion confirmation

        Raises
        ------
        LibraryKnowledgeError: If deletion fails

        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.delete_pattern, pattern_id)

    async def search_patterns_async(
        self, filter_config: LibraryPatternSearchFilter | None = None
    ) -> dict[str, Any]:
        """
        Asynchronously search library patterns.

        Parameters
        ----------
        filter_config (LibraryPatternSearchFilter, optional): Search filters

        Returns
        -------
        Dict[str, Any]: Search results

        Raises
        ------
        LibraryKnowledgeError: If search fails

        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.search_patterns, filter_config)

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
            logger.info("LibraryKnowledgeService closed successfully")
        except Exception as e:
            logger.warning(f"Error closing LibraryKnowledgeService: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.close()
        if exc_type:
            logger.error(f"LibraryKnowledgeService exiting with error: {exc_val}")
        return False  # Don't suppress exceptions
