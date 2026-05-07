#!/usr/bin/env python3
"""Migration Script: SQLite Repository → CKS Hyper-Graph.

Migrates existing data from SQLite repository tables to CKS hyper-graph entities.

Tables to migrate:
- tasks → Task entities
- session_checkpoints → SessionCheckpoint entities
- project_contexts → ProjectContext entities
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

# Add current directory to path for imports
current_dir = Path(__file__).parent

from csf.cks_client import (
    CKSHyperGraphClient,
    create_checkpoint_entity,
    create_task_entity,
)


class MigrationToCKS:
    """Migrate SQLite repository data to CKS hyper-graph."""

    def __init__(
        self,
        source_db: str | Path = "P:\\\\.cks/storage/cks.db",
        target_db: str | Path = "P:\\\\__csf/data/cks.db",
    ) -> None:
        self.source_db = Path(source_db)
        self.target_db = Path(target_db)
        self.cks = CKSHyperGraphClient(self.target_db)

    def migrate_tasks(self) -> int:
        """Migrate tasks table to Task entities."""
        conn = sqlite3.connect(str(self.source_db))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check if tasks table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'",
        )
        if not cursor.fetchone():
            print("[Migration] No tasks table found")
            return 0

        cursor.execute("SELECT * FROM tasks")
        rows = cursor.fetchall()

        migrated = 0
        for row in rows:
            try:
                # Convert sqlite3.Row to dict
                row_dict = dict(row)

                # Parse strategic_context JSON
                strategic_context = row_dict.get("strategic_context")
                strategic_context = json.loads(strategic_context) if strategic_context else {}

                # Create Task entity
                task = create_task_entity(
                    name=row_dict["name"],
                    status=row_dict["status"],
                    progress_pct=row_dict["progress_pct"],
                    description=row_dict.get("description", ""),
                    priority=row_dict.get("priority", "medium"),
                    strategic_context=strategic_context,
                )

                # Preserve original timestamps
                task.created_at = row_dict["created_at"]
                task.updated_at = row_dict["updated_at"]

                success = self.cks.add_entity(task)
                if success:
                    migrated += 1
                    print(f"[Migration] Task migrated: {row_dict['name']}")
                else:
                    print(f"[Migration] Failed to migrate task: {row_dict['name']}")

            except Exception as e:
                row_dict = dict(row) if not isinstance(row, dict) else row
                print(f"[Migration] Error migrating task {row_dict.get('name', 'unknown')}: {e}")

        conn.close()
        return migrated

    def migrate_session_checkpoints(self) -> int:
        """Migrate session_checkpoints table to SessionCheckpoint entities."""
        conn = sqlite3.connect(str(self.source_db))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check if session_checkpoints table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='session_checkpoints'",
        )
        if not cursor.fetchone():
            print("[Migration] No session_checkpoints table found")
            return 0

        cursor.execute("SELECT * FROM session_checkpoints")
        rows = cursor.fetchall()

        migrated = 0
        for row in rows:
            try:
                # Convert sqlite3.Row to dict
                row_dict = dict(row)

                # Parse JSON fields
                blocker = row_dict.get("blocker")
                if blocker:
                    blocker = json.loads(blocker)

                files_modified = row_dict.get("files_modified")
                if files_modified:
                    files_modified = json.loads(files_modified)

                next_steps = row_dict.get("next_steps")
                if next_steps:
                    next_steps = json.loads(next_steps)

                # Create SessionCheckpoint entity
                checkpoint = create_checkpoint_entity(
                    task_name=row_dict["task_name"],
                    session_id=row_dict["session_id"],
                    progress_pct=row_dict["progress_pct"],
                    blocker=blocker,
                    files_modified=files_modified,
                    next_steps=next_steps,
                    session_summary=row_dict.get("session_summary", ""),
                )

                # Preserve original timestamp
                checkpoint.attributes["timestamp"] = row_dict["timestamp"]

                success = self.cks.add_entity(checkpoint)
                if success:
                    migrated += 1
                    print(f"[Migration] Checkpoint migrated: {row_dict['task_name']}")
                else:
                    print(f"[Migration] Failed to migrate checkpoint: {row_dict['task_name']}")

            except Exception as e:
                row_dict = dict(row) if not isinstance(row, dict) else row
                print(
                    f"[Migration] Error migrating checkpoint {row_dict.get('task_name', 'unknown')}: {e}"
                )

        conn.close()
        return migrated

    def migrate_project_contexts(self) -> int:
        """Migrate project_contexts table to ProjectContext entities."""
        conn = sqlite3.connect(str(self.source_db))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check if project_contexts table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='project_contexts'",
        )
        if not cursor.fetchone():
            print("[Migration] No project_contexts table found")
            return 0

        cursor.execute("SELECT * FROM project_contexts")
        rows = cursor.fetchall()

        migrated = 0
        for row in rows:
            try:
                # Convert sqlite3.Row to dict
                row_dict = dict(row)

                # Parse path_patterns JSON
                path_patterns = row_dict.get("path_patterns")
                path_patterns = json.loads(path_patterns) if path_patterns else []

                # Create ProjectContext entity
                from csf.cks_client import Entity

                context = Entity(
                    entity_type="ProjectContext",
                    entity_id=row_dict["tsk_id"],
                    attributes={
                        "tsk_id": row_dict["tsk_id"],
                        "worktree_path": row_dict["worktree_path"],
                        "path_patterns": path_patterns,
                        "description": row_dict.get("description", ""),
                        "active": row_dict.get("active", 0),
                    },
                )

                # Preserve original timestamps
                context.created_at = row_dict["created_at"]
                context.updated_at = row_dict["updated_at"]

                success = self.cks.add_entity(context)
                if success:
                    migrated += 1
                    print(f"[Migration] ProjectContext migrated: {row_dict['tsk_id']}")
                else:
                    print(f"[Migration] Failed to migrate ProjectContext: {row_dict['tsk_id']}")

            except Exception as e:
                row_dict = dict(row) if not isinstance(row, dict) else row
                print(
                    f"[Migration] Error migrating ProjectContext {row_dict.get('tsk_id', 'unknown')}: {e}"
                )

        conn.close()
        return migrated

    def run(self):
        """Execute full migration."""
        print("=" * 60)
        print("MIGRATION: SQLite Repository → CKS Hyper-Graph")
        print("=" * 60)

        print(f"\nSource: {self.source_db}")
        print(f"Target: {self.target_db}\n")

        total = 0

        # Migrate tasks
        print("[1/3] Migrating tasks...")
        tasks = self.migrate_tasks()
        print(f"✅ Migrated {tasks} tasks\n")
        total += tasks

        # Migrate checkpoints
        print("[2/3] Migrating session checkpoints...")
        checkpoints = self.migrate_session_checkpoints()
        print(f"✅ Migrated {checkpoints} checkpoints\n")
        total += checkpoints

        # Migrate project contexts
        print("[3/3] Migrating project contexts...")
        contexts = self.migrate_project_contexts()
        print(f"✅ Migrated {contexts} project contexts\n")
        total += contexts

        print("=" * 60)
        print(f"Migration complete: {total} entities migrated")
        print("=" * 60)

        return total


def main() -> int:
    """Main entry point."""
    migration = MigrationToCKS()
    migration.run()

    # Verify migration
    print("\n[Verification] Checking migrated entities...")
    cks = CKSHyperGraphClient("P:\\\\__csf/data/cks.db")

    for entity_type in ["Task", "SessionCheckpoint", "ProjectContext"]:
        entities = cks.hyper_graph_query(entity_type=entity_type, limit=1000)
        print(f"  {entity_type}: {len(entities)} entities")

    return 0


if __name__ == "__main__":
    sys.exit(main())
