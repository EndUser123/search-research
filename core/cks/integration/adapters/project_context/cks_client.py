#!/usr/bin/env python3
"""CKS Hyper-Graph Client.

Entity-based storage system for task context management.
Implements hyper-graph entities with relationships and semantic search.

Entity Types:
- Task: Strategic task context (goal, success criteria, approach)
- SessionCheckpoint: Progress snapshot (progress %, blockers, next steps)
- Blocker: Current blockers (description, severity, investigation)
- Decision: Architectural decisions (what, answer, reasoning)
- LessonLearned: Lessons learned with trigger patterns

Relationships:
- Task -> SessionCheckpoint (belongs_to_task)
- Task -> Blocker (has_blocker)
- Task -> Decision (has_decision)
- SessionCheckpoint -> Blocker (contains_blocker)
"""

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Computed project root (Python 3.12+)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent.parent.parent.parent


@dataclass
class Entity:
    """Base hyper-graph entity."""

    entity_type: str
    entity_id: str
    attributes: dict[str, Any] = field(default_factory=dict)
    relationships: dict[str, str | list[str] | None] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "attributes": json.dumps(self.attributes),
            "relationships": json.dumps(self.relationships),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> Entity:
        """Create from database row."""
        return cls(
            entity_type=row["entity_type"],
            entity_id=row["entity_id"],
            attributes=json.loads(row["attributes"]) if row["attributes"] else {},
            relationships=json.loads(row["relationships"]) if row["relationships"] else {},
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


@dataclass
class TaskEntity(Entity):
    """Task entity with strategic context."""

    def __init__(
        self,
        name: str,
        status: str = "pending",
        progress_pct: int = 0,
        description: str = "",
        priority: str = "medium",
        strategic_context: dict[str, Any] | None = None,
    ) -> None:
        entity_id = f"task_{name.lower()}_{hashlib.md5(name.encode()).hexdigest()[:8]}"
        super().__init__(
            entity_type="Task",
            entity_id=entity_id,
            attributes={
                "name": name,
                "status": status,
                "progress_pct": progress_pct,
                "description": description,
                "priority": priority,
                "strategic_context": strategic_context
                or {
                    "goal": "",
                    "success_criteria": [],
                    "approach": "",
                },
            },
        )


@dataclass
class SessionCheckpointEntity(Entity):
    """Session checkpoint entity with progress snapshot."""

    def __init__(
        self,
        task_name: str,
        session_id: str,
        progress_pct: int,
        blocker: dict[str, Any] | None = None,
        files_modified: list[str] | None = None,
        next_steps: list[str] | None = None,
        session_summary: str = "",
        terminal_id: str | None = None,
    ) -> None:
        timestamp = datetime.now().isoformat()
        entity_id = f"checkpoint_{task_name.lower()}_{session_id}"

        super().__init__(
            entity_type="SessionCheckpoint",
            entity_id=entity_id,
            attributes={
                "task": task_name,
                "session_id": session_id,
                "timestamp": timestamp,
                "progress_pct": progress_pct,
                "blocker": blocker,
                "files_modified": files_modified or [],
                "next_steps": next_steps or [],
                "session_summary": session_summary,
                "terminal_id": terminal_id,
            },
            relationships={
                "belongs_to_task": f"task_{task_name.lower()}",
            },
        )


@dataclass
class BlockerEntity(Entity):
    """Blocker entity with investigation details."""

    def __init__(
        self,
        task_name: str,
        description: str,
        severity: str = "medium",
        investigation: str = "",
        workaround: str = "",
    ) -> None:
        timestamp = datetime.now().isoformat()
        entity_id = (
            f"blocker_{task_name.lower()}_{hashlib.md5(description.encode()).hexdigest()[:8]}"
        )

        super().__init__(
            entity_type="Blocker",
            entity_id=entity_id,
            attributes={
                "task": task_name,
                "description": description,
                "severity": severity,
                "created_date": timestamp,
                "status": "unresolved",
                "investigation": investigation,
                "workaround": workaround,
            },
            relationships={
                "blocks_task": f"task_{task_name.lower()}",
            },
        )


@dataclass
class DecisionEntity(Entity):
    """Decision entity with architectural rationale."""

    def __init__(
        self,
        task_name: str,
        what: str,
        answer: str,
        reasoning: str,
        alternatives_considered: list[str] | None = None,
    ) -> None:
        timestamp = datetime.now().isoformat()
        entity_id = f"decision_{task_name.lower()}_{hashlib.md5(what.encode()).hexdigest()[:8]}"

        super().__init__(
            entity_type="Decision",
            entity_id=entity_id,
            attributes={
                "task": task_name,
                "what": what,
                "answer": answer,
                "reasoning": reasoning,
                "date": timestamp,
                "alternatives_considered": alternatives_considered or [],
            },
            relationships={
                "decision_for_task": f"task_{task_name.lower()}",
            },
        )


class CKSHyperGraphClient:
    """CKS Hyper-Graph Client.

    Provides entity-based storage with:
    - CRUD operations for entities
    - Relationship tracking
    - Semantic search via vector embeddings
    - Hyper-graph traversal
    - Lessons learned management
    """

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None
        self._init_schema()

    def _get_conn(self) -> sqlite3.Connection:
        """Get database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _init_schema(self) -> None:
        """Initialize hyper-graph schema."""
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL PRIMARY KEY,
                attributes TEXT,
                relationships TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)

        # Entity embeddings for semantic search
        conn.execute("""
            CREATE TABLE IF NOT EXISTS entity_embeddings (
                entity_id TEXT PRIMARY KEY,
                embedding_vector BLOB,
                updated_at TEXT,
                FOREIGN KEY (entity_id) REFERENCES entities(entity_id)
            )
        """)

        # Indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_entity_type ON entities(entity_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON entities(created_at)")
        conn.commit()
        logger.info(f"[CKS] Schema initialized: {self.db_path}")

    def add_entity(self, entity: Entity) -> bool:
        """Add or update entity in hyper-graph."""
        try:
            conn = self._get_conn()
            entity.updated_at = datetime.now().isoformat()

            conn.execute(
                """
                INSERT OR REPLACE INTO entities
                (entity_type, entity_id, attributes, relationships, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    entity.entity_type,
                    entity.entity_id,
                    json.dumps(entity.attributes),
                    json.dumps(entity.relationships),
                    entity.created_at,
                    entity.updated_at,
                ),
            )
            conn.commit()
            logger.debug(f"[CKS] Entity added: {entity.entity_type}/{entity.entity_id}")
            return True
        except Exception as e:
            logger.exception(f"[CKS] Error adding entity: {e}")
            return False

    def get_entity(self, entity_type: str, entity_id: str) -> Entity | None:
        """Get entity by type and ID."""
        try:
            conn = self._get_conn()
            cursor = conn.execute(
                "SELECT * FROM entities WHERE entity_type = ? AND entity_id = ?",
                (entity_type, entity_id),
            )
            row = cursor.fetchone()

            if row:
                return Entity.from_row(dict(row))
            return None
        except Exception as e:
            logger.exception(f"[CKS] Error getting entity: {e}")
            return None

    def hyper_graph_query(
        self,
        entity_type: str | None = None,
        filter: dict[str, Any] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Query hyper-graph with filters.

        Args:
            entity_type: Filter by entity type
            filter: Attribute filters (e.g., {"status": "in_progress"})
            limit: Max results

        Returns:
            List of entity dictionaries

        """
        try:
            conn = self._get_conn()
            query = "SELECT * FROM entities WHERE 1=1"
            params = []

            if entity_type:
                query += " AND entity_type = ?"
                params.append(entity_type)

            # Apply JSON attribute filters
            if filter:
                for key, value in filter.items():
                    if isinstance(value, list):
                        # IN clause for lists
                        placeholders = ",".join(["?" for _ in value])
                        query += f" AND json_extract(attributes, '$.{key}') IN ({placeholders})"
                        params.extend(value)
                    else:
                        query += f" AND json_extract(attributes, '$.{key}') = ?"
                        params.append(value)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            results = []
            for row in rows:
                entity_dict = dict(row)
                entity_dict["attributes"] = (
                    json.loads(entity_dict["attributes"]) if entity_dict["attributes"] else {}
                )
                entity_dict["relationships"] = (
                    json.loads(entity_dict["relationships"]) if entity_dict["relationships"] else {}
                )
                results.append(entity_dict)

            logger.debug(f"[CKS] Query returned {len(results)} entities")
            return results

        except Exception as e:
            logger.exception(f"[CKS] Query error: {e}")
            return []

    def semantic_search(
        self,
        query: str,
        entity_type: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Semantic search for entities.

        Note: This is a simplified implementation using LIKE matching.
        Full semantic search would require vector embeddings.
        """
        try:
            conn = self._get_conn()

            # Search in attributes JSON for query string
            sql = """
                SELECT * FROM entities
                WHERE json_extract(attributes, '$') LIKE ?
            """
            params = [f"%{query}%"]

            if entity_type:
                sql += " AND entity_type = ?"
                params.append(entity_type)

            sql += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            cursor = conn.execute(sql, params)
            rows = cursor.fetchall()

            results = []
            for row in rows:
                entity_dict = dict(row)
                entity_dict["attributes"] = (
                    json.loads(entity_dict["attributes"]) if entity_dict["attributes"] else {}
                )
                entity_dict["relationships"] = (
                    json.loads(entity_dict["relationships"]) if entity_dict["relationships"] else {}
                )
                results.append(entity_dict)

            logger.debug(f"[CKS] Semantic search returned {len(results)} results")
            return results

        except Exception as e:
            logger.exception(f"[CKS] Semantic search error: {e}")
            return []

    def get_related_entities(
        self,
        entity_id: str,
        relationship_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get entities related via hyper-graph relationships.

        Args:
            entity_id: Source entity ID
            relationship_type: Filter by relationship type (e.g., "belongs_to_task")

        Returns:
            List of related entity dictionaries

        """
        try:
            # Get source entity to find relationships
            source = self.get_entity(None, entity_id)
            if not source or not source.relationships:
                return []

            related_ids = []
            for rel_type, target in source.relationships.items():
                if relationship_type and rel_type != relationship_type:
                    continue

                if target:
                    if isinstance(target, list):
                        related_ids.extend(target)
                    else:
                        related_ids.append(target)

            # Fetch related entities
            results = []
            if related_ids:
                conn = self._get_conn()
                placeholders = ",".join(["?" for _ in related_ids])
                cursor = conn.execute(
                    f"SELECT * FROM entities WHERE entity_id IN ({placeholders})",
                    related_ids,
                )
                rows = cursor.fetchall()

                for row in rows:
                    entity_dict = dict(row)
                    entity_dict["attributes"] = (
                        json.loads(entity_dict["attributes"]) if entity_dict["attributes"] else {}
                    )
                    entity_dict["relationships"] = (
                        json.loads(entity_dict["relationships"])
                        if entity_dict["relationships"]
                        else {}
                    )
                    results.append(entity_dict)

            return results

        except Exception as e:
            logger.exception(f"[CKS] Error getting related entities: {e}")
            return []

    def delete_entity(self, entity_type: str, entity_id: str) -> bool:
        """Delete entity from hyper-graph."""
        try:
            conn = self._get_conn()
            conn.execute(
                "DELETE FROM entities WHERE entity_type = ? AND entity_id = ?",
                (entity_type, entity_id),
            )
            conn.commit()
            logger.debug(f"[CKS] Entity deleted: {entity_type}/{entity_id}")
            return True
        except Exception as e:
            logger.exception(f"[CKS] Error deleting entity: {e}")
            return False

    def update_entity_attributes(
        self,
        entity_type: str,
        entity_id: str,
        attributes: dict[str, Any],
    ) -> bool:
        """Update entity attributes."""
        try:
            entity = self.get_entity(entity_type, entity_id)
            if not entity:
                return False

            entity.attributes.update(attributes)
            entity.updated_at = datetime.now().isoformat()

            return self.add_entity(entity)
        except Exception as e:
            logger.exception(f"[CKS] Error updating entity: {e}")
            return False

    def get_supported_entity_types(self) -> list[str]:
        """Get supported entity types."""
        return [
            "Task",
            "SessionCheckpoint",
            "Blocker",
            "Decision",
            "LessonLearned",
            "lessons_learned",
        ]

    def store_lesson_learned(
        self,
        trigger_phrase: str,
        context: str,
        what_to_do: str,
        severity: str = "medium",
        category: str = "general",
    ) -> bool:
        """Store a lesson learned with trigger pattern.

        Args:
            trigger_phrase: The phrase that triggers this lesson
            context: What happened / background context
            what_to_do: Corrective action to take
            severity: low/medium/high
            category: Category for grouping lessons

        Returns:
            True if stored successfully

        """
        try:
            timestamp = datetime.now().isoformat()
            entity_id = f"lesson_{hashlib.md5(trigger_phrase.encode()).hexdigest()[:8]}"

            entity = Entity(
                entity_type="LessonLearned",
                entity_id=entity_id,
                attributes={
                    "trigger_phrase": trigger_phrase,
                    "context": context,
                    "what_to_do": what_to_do,
                    "severity": severity,
                    "category": category,
                    "created_at": timestamp,
                },
            )
            return self.add_entity(entity)
        except Exception as e:
            logger.exception(f"[CKS] Error storing lesson: {e}")
            return False

    def get_lesson_by_trigger(self, trigger_phrase: str) -> dict[str, Any] | None:
        """Get lesson by exact trigger phrase match.

        Args:
            trigger_phrase: The exact trigger phrase to search for

        Returns:
            Lesson entity dict or None if not found

        """
        try:
            conn = self._get_conn()
            cursor = conn.execute(
                """
                SELECT * FROM entities
                WHERE entity_type = 'LessonLearned'
                AND json_extract(attributes, '$.trigger_phrase') = ?
                LIMIT 1
                """,
                (trigger_phrase,),
            )
            row = cursor.fetchone()

            if row:
                entity_dict = dict(row)
                entity_dict["attributes"] = (
                    json.loads(entity_dict["attributes"]) if entity_dict["attributes"] else {}
                )
                entity_dict["relationships"] = (
                    json.loads(entity_dict["relationships"]) if entity_dict["relationships"] else {}
                )
                return entity_dict
            return None
        except Exception as e:
            logger.exception(f"[CKS] Error getting lesson by trigger: {e}")
            return None

    def get_all_lessons_learned(self) -> list[dict[str, Any]]:
        """Get all stored lessons.

        Returns:
            List of lesson entity dicts

        """
        try:
            return self.hyper_graph_query(entity_type="LessonLearned", limit=1000)
        except Exception as e:
            logger.exception(f"[CKS] Error getting all lessons: {e}")
            return []

    def find_lessons_by_trigger_fuzzy(self, trigger_phrase: str) -> list[dict[str, Any]]:
        """Find lessons with similar trigger phrases (substring match).

        Args:
            trigger_phrase: The phrase to search for (substring matching)

        Returns:
            List of matching lesson entity dicts

        """
        try:
            conn = self._get_conn()
            cursor = conn.execute(
                """
                SELECT * FROM entities
                WHERE entity_type = 'LessonLearned'
                AND LOWER(json_extract(attributes, '$.trigger_phrase')) LIKE ?
                ORDER BY created_at DESC
                """,
                (f"%{trigger_phrase.lower()}%",),
            )
            rows = cursor.fetchall()

            results = []
            for row in rows:
                entity_dict = dict(row)
                entity_dict["attributes"] = (
                    json.loads(entity_dict["attributes"]) if entity_dict["attributes"] else {}
                )
                entity_dict["relationships"] = (
                    json.loads(entity_dict["relationships"]) if entity_dict["relationships"] else {}
                )
                results.append(entity_dict)

            return results
        except Exception as e:
            logger.exception(f"[CKS] Error finding lessons by fuzzy trigger: {e}")
            return []

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
            logger.debug("[CKS] Connection closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Convenience functions for common operations
def create_task_entity(
    name: str,
    status: str = "pending",
    progress_pct: int = 0,
    description: str = "",
    priority: str = "medium",
    strategic_context: dict[str, Any] | None = None,
) -> TaskEntity:
    """Create a Task entity."""
    return TaskEntity(
        name=name,
        status=status,
        progress_pct=progress_pct,
        description=description,
        priority=priority,
        strategic_context=strategic_context,
    )


def create_checkpoint_entity(
    task_name: str,
    session_id: str,
    progress_pct: int,
    blocker: dict[str, Any] | None = None,
    files_modified: list[str] | None = None,
    next_steps: list[str] | None = None,
    session_summary: str = "",
    terminal_id: str | None = None,
) -> SessionCheckpointEntity:
    """Create a SessionCheckpoint entity."""
    return SessionCheckpointEntity(
        task_name=task_name,
        session_id=session_id,
        progress_pct=progress_pct,
        blocker=blocker,
        files_modified=files_modified,
        next_steps=next_steps,
        session_summary=session_summary,
        terminal_id=terminal_id,
    )


if __name__ == "__main__":
    # Test CKS client
    logging.basicConfig(level=logging.DEBUG)

    client = CKSHyperGraphClient(
        "P:\\\\\\__csf/src/features/cks/integration/adapters/project_context/test_cks.db"
    )

    # Create task
    task = create_task_entity(
        name="CWO12",
        status="in_progress",
        progress_pct=35,
        description="Alternative Platform Support",
        priority="high",
        strategic_context={
            "goal": "Enable Claude Code on alternative platforms",
            "success_criteria": ["MacOS ARM64", "WSL2", "Linux"],
            "approach": "Abstract platform detection",
        },
    )
    client.add_entity(task)
    print(f"✅ Task created: {task.entity_id}")

    # Query tasks
    tasks = client.hyper_graph_query(
        entity_type="Task",
        filter={"status": "in_progress"},
    )
    print(f"✅ Found {len(tasks)} in_progress tasks")

    # Create checkpoint
    checkpoint = create_checkpoint_entity(
        task_name="CWO12",
        session_id="session_12345",
        progress_pct=35,
        blocker={
            "description": "AsyncBridge integration incomplete",
            "severity": "high",
        },
        next_steps=["Complete AsyncBridge", "Test on MacOS", "Update docs"],
    )
    client.add_entity(checkpoint)
    print(f"✅ Checkpoint created: {checkpoint.entity_id}")

    # Get related entities
    related = client.get_related_entities(checkpoint.entity_id, "belongs_to_task")
    print(f"✅ Related entities: {len(related)}")

    client.close()

    # Cleanup test database
    PROJECT_ROOT / "__csf" / "src" / "features" / "cks" / "integration" / "adapters" / "project_context" / "test_cks.db".unlink(
        missing_ok=True
    )
