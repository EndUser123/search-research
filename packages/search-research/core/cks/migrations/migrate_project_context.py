#!/usr/bin/env python3
"""
Migration Script: Project Context CKS to Unified CKS

MIGRATION COMPLETE (2025-12-28): Was: P:\\\\.cks/storage/cks.db (DEPRECATED)
to data/cks.db (Unified CKS) as part of the CKS consolidation.

Entity Types Migrated:
- Task -> task entry type
- SessionCheckpoint -> checkpoint entry type
- Blocker -> blocker entry type (if exists)
- Decision -> decision entry type (if exists)
- ProjectContext -> task entry type (special case)

Relationships Preserved:
- belongs_to_task (checkpoint -> task)
- blocks_task (blocker -> task)
- decision_for_task (decision -> task)
"""

import json
import logging
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add src to path for imports

from ..unified import CKS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def get_source_entities(
    source_db_path: str,
    entity_type: str | None = None
) -> list[dict[str, Any]]:
    """Get entities from source database.

    Args:
        source_db_path: Path to Project Context CKS database
        entity_type: Filter by entity type (optional)

    Returns:
        List of entity dictionaries
    """
    try:
        conn = sqlite3.connect(source_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT * FROM entities"
        params = []

        if entity_type:
            query += " WHERE entity_type = ?"
            params.append(entity_type)

        query += " ORDER BY created_at"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        entities = []
        for row in rows:
            entity = dict(row)
            # Parse JSON attributes
            if entity.get("attributes"):
                try:
                    entity["attributes"] = json.loads(entity["attributes"])
                except json.JSONDecodeError:
                    entity["attributes"] = {}
            # Parse JSON relationships
            if entity.get("relationships"):
                try:
                    entity["relationships"] = json.loads(entity["relationships"])
                except json.JSONDecodeError:
                    entity["relationships"] = {}
            entities.append(entity)

        conn.close()
        return entities

    except Exception as e:
        logger.error(f"Error reading source database: {e}")
        return []


def migrate_task_entity(cks: CKS, entity: dict[str, Any]) -> str | None:
    """Migrate a Task entity to unified CKS.

    Args:
        cks: Unified CKS instance
        entity: Source Task entity

    Returns:
        Entry ID if successful, None otherwise
    """
    try:
        attrs = entity.get("attributes", {})

        return cks.ingest_task(
            name=attrs.get("name", "Unknown Task"),
            status=attrs.get("status", "pending"),
            progress_pct=attrs.get("progress_pct", 0),
            description=attrs.get("description", ""),
            priority=attrs.get("priority", "medium"),
            strategic_context=attrs.get("strategic_context"),
            # Preserve metadata
            source_entity_id=entity.get("entity_id"),
            created_at=entity.get("created_at"),
            updated_at=entity.get("updated_at")
        )
    except Exception as e:
        logger.error(f"Error migrating task {entity.get('entity_id')}: {e}")
        return None


def migrate_project_context_entity(cks: CKS, entity: dict[str, Any]) -> str | None:
    """Migrate a ProjectContext entity to unified CKS as a task.

    Args:
        cks: Unified CKS instance
        entity: Source ProjectContext entity

    Returns:
        Entry ID if successful, None otherwise
    """
    try:
        attrs = entity.get("attributes", {})

        return cks.ingest_task(
            name=attrs.get("name", "Project Context"),
            status="pending",
            progress_pct=0,
            description=attrs.get("focus", ""),
            priority="medium",
            strategic_context={
                "goal": attrs.get("goal", ""),
                "base_repository": attrs.get("base_repository", ""),
            },
            # Preserve metadata
            source_entity_type="ProjectContext",
            source_entity_id=entity.get("entity_id"),
            tsk_id=attrs.get("tsk_id"),
            created_at=entity.get("created_at")
        )
    except Exception as e:
        logger.error(f"Error migrating project context {entity.get('entity_id')}: {e}")
        return None


def migrate_checkpoint_entity(cks: CKS, entity: dict[str, Any]) -> str | None:
    """Migrate a SessionCheckpoint entity to unified CKS.

    Args:
        cks: Unified CKS instance
        entity: Source SessionCheckpoint entity

    Returns:
        Entry ID if successful, None otherwise
    """
    try:
        attrs = entity.get("attributes", {})

        # Extract task name from features.checkpoint or entity_id
        task_name = attrs.get("task", "Unknown")
        if "checkpoint_" in entity.get("entity_id", ""):
            # Extract from entity_id pattern: checkpoint_<task_name>_<session_id>
            parts = entity["entity_id"].split("_")
            if len(parts) >= 2:
                task_name = parts[1]

        entry_id = cks.ingest_checkpoint(
            task_name=task_name,
            session_id=attrs.get("session_id", ""),
            progress_pct=attrs.get("progress_pct", 0),
            blocker=attrs.get("blocker"),
            files_modified=attrs.get("files_modified", []),
            next_steps=attrs.get("next_steps", []),
            session_summary=attrs.get("session_summary", ""),
            # Preserve metadata
            source_entity_id=entity.get("entity_id"),
            created_at=attrs.get("timestamp") or entity.get("created_at")
        )

        return entry_id
    except Exception as e:
        logger.error(f"Error migrating checkpoint {entity.get('entity_id')}: {e}")
        return None


def migrate_blocker_entity(cks: CKS, entity: dict[str, Any]) -> str | None:
    """Migrate a Blocker entity to unified CKS.

    Args:
        cks: Unified CKS instance
        entity: Source Blocker entity

    Returns:
        Entry ID if successful, None otherwise
    """
    try:
        attrs = entity.get("attributes", {})

        return cks.ingest_blocker(
            task_name=attrs.get("task", "Unknown"),
            description=attrs.get("description", ""),
            severity=attrs.get("severity", "medium"),
            investigation=attrs.get("investigation", ""),
            workaround=attrs.get("workaround", ""),
            # Preserve metadata
            source_entity_id=entity.get("entity_id"),
            created_at=attrs.get("created_date") or entity.get("created_at")
        )
    except Exception as e:
        logger.error(f"Error migrating blocker {entity.get('entity_id')}: {e}")
        return None


def migrate_decision_entity(cks: CKS, entity: dict[str, Any]) -> str | None:
    """Migrate a Decision entity to unified CKS.

    Args:
        cks: Unified CKS instance
        entity: Source Decision entity

    Returns:
        Entry ID if successful, None otherwise
    """
    try:
        attrs = entity.get("attributes", {})

        # Use the existing ingest_decision method
        entry_id = cks.ingest_decision(
            title=f"Decision: {attrs.get('what', 'Unknown Decision')}",
            content=f"Answer: {attrs.get('answer', '')}\n\nReasoning: {attrs.get('reasoning', '')}",
            # Preserve metadata
            source_entity_id=entity.get("entity_id"),
            task_name=attrs.get("task"),
            alternatives_considered=attrs.get("alternatives_considered", []),
            created_at=attrs.get("date") or entity.get("created_at")
        )

        # Create relationship to task
        task_name = attrs.get("task", "").lower()
        if entry_id and task_name:
            cks.add_relationship(
                from_entry_id=entry_id,
                to_entry_id=f"task_{task_name}",
                relationship_type="decision_for_task"
            )

        return entry_id
    except Exception as e:
        logger.error(f"Error migrating decision {entity.get('entity_id')}: {e}")
        return None


def run_migration(
    source_db_path: str = "P:\\\\.cks/storage/cks.db",
    target_db_path: str = None,
    dry_run: bool = False
) -> dict[str, int]:
    """Run the migration from Project Context CKS to Unified CKS.

    Args:
        source_db_path: Path to source database
        target_db_path: Path to target database (default: CKS default)
        dry_run: If True, don't actually write to target database

    Returns:
        Dictionary with migration counts by type
    """
    source_path = Path(source_db_path)

    if not source_path.exists():
        logger.error(f"Source database not found: {source_db_path}")
        return {}

    logger.info(f"Source database: {source_db_path}")
    logger.info(f"Source size: {source_path.stat().st_size / 1024:.1f} KB")

    # Initialize target CKS
    if target_db_path:
        cks = CKS(db_path=target_db_path)
    else:
        cks = CKS()

    logger.info(f"Target database: {cks.db_path}")
    logger.info(f"Target size: {cks.db_path.stat().st_size / 1024 / 1024:.1f} MB")

    # Migration counters
    counts = {
        "task": 0,
        "checkpoint": 0,
        "blocker": 0,
        "decision": 0,
        "project_context": 0,
        "total": 0,
        "errors": 0
    }

    if dry_run:
        logger.info("DRY RUN - No data will be written")

    # Get all entities from source
    logger.info("Scanning source database...")
    all_entities = get_source_entities(source_db_path)
    logger.info(f"Found {len(all_entities)} entities")

    # Group by entity type
    by_type: dict[str, list[dict]] = {}
    for entity in all_entities:
        entity_type = entity.get("entity_type", "Unknown")
        if entity_type not in by_type:
            by_type[entity_type] = []
        by_type[entity_type].append(entity)

    logger.info(f"Entity types: {list(by_type.keys())}")

    # Migrate each type
    for entity_type, entities in by_type.items():
        logger.info(f"\nMigrating {len(entities)} {entity_type} entities...")

        for entity in entities:
            if dry_run:
                logger.info(f"  Would migrate: {entity['entity_id']}")
                counts["total"] += 1
                continue

            entry_id = None

            if entity_type == "Task":
                entry_id = migrate_task_entity(cks, entity)
                counts["task"] += 1
            elif entity_type == "ProjectContext":
                entry_id = migrate_project_context_entity(cks, entity)
                counts["project_context"] += 1
            elif entity_type == "SessionCheckpoint":
                entry_id = migrate_checkpoint_entity(cks, entity)
                counts["checkpoint"] += 1
            elif entity_type == "Blocker":
                entry_id = migrate_blocker_entity(cks, entity)
                counts["blocker"] += 1
            elif entity_type == "Decision":
                entry_id = migrate_decision_entity(cks, entity)
                counts["decision"] += 1
            else:
                logger.warning(f"Unknown entity type: {entity_type}")
                continue

            if entry_id:
                counts["total"] += 1
                logger.debug(f"  Migrated {entity['entity_id']} -> {entry_id}")
            else:
                counts["errors"] += 1

    cks.close()

    # Print summary
    logger.info("\n" + "=" * 50)
    logger.info("Migration Summary:")
    logger.info(f"  Tasks: {counts['task']}")
    logger.info(f"  Project Context: {counts['project_context']}")
    logger.info(f"  Checkpoints: {counts['checkpoint']}")
    logger.info(f"  Blockers: {counts['blocker']}")
    logger.info(f"  Decisions: {counts['decision']}")
    logger.info(f"  Total: {counts['total']}")
    if counts["errors"] > 0:
        logger.warning(f"  Errors: {counts['errors']}")
    logger.info("=" * 50)

    return counts


def main():
    """Main entry point for migration script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Migrate Project Context CKS to Unified CKS"
    )
    parser.add_argument(
        "--source",
        default="P:\\\\.cks/storage/cks.db",
        help="Path to source database"
    )
    parser.add_argument(
        "--target",
        default=None,
        help="Path to target database (default: CKS default)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without writing"
    )

    args = parser.parse_args()

    run_migration(
        source_db_path=args.source,
        target_db_path=args.target,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()
