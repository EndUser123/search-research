#!/usr/bin/env python3
"""CKS-Integrated SessionContextManager
Stores project contexts in Unified CKS (Consolidation Phase 1).
"""

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path

# Add parent to path for imports
current_dir = Path(__file__).parent

from ...unified import CKS


@dataclass
class ProjectContext:
    """Represents active project context."""

    tsk_id: str
    name: str
    base_repository: str
    focus: str
    worktree_path: str
    last_activity: float
    session_id: str


class SessionContextManagerCKS:
    """CKS-integrated session context manager.
    Stores contexts in CKS hyper-graph entities instead of JSON files.
    """

    def __init__(
        self, cks_db_path: str | None = None, memory_base: str = ".speckit/memory"
    ) -> None:
        # CKS Consolidation Phase 1: Use unified CKS
        self.cks = CKS()  # db_path ignored, always uses unified CKS
        # Adapter wrapper for CKSHyperGraphClient compatibility
        self._hyper_graph_query = self._cks_hyper_graph_query
        self._update_entity_attributes = self._cks_update_entity_attributes
        self.memory_base = Path(memory_base)
        self.session_id = f"session_{int(time.time())}"
        self.current_context = None
        self._load_context()

    def _load_context(self) -> None:
        """Load active session context from CKS."""
        # Query for active ProjectContext entity
        contexts = self._cks_hyper_graph_query(
            entity_type="ProjectContext",
            filter={"active": "true"},
            limit=1,
        )

        if contexts:
            ctx = contexts[0]
            attrs = ctx["attributes"]

            # Check if context is stale (older than 2 hours)
            last_activity = attrs.get("last_activity", 0)
            if time.time() - last_activity > 7200:
                self.current_context = None
                # Mark as inactive
                self._cks_update_entity_attributes(
                    entity_type="ProjectContext",
                    entity_id=ctx["entity_id"],
                    attributes={"active": "false"},
                )
            else:
                self.current_context = ProjectContext(
                    tsk_id=attrs["tsk_id"],
                    name=attrs["name"],
                    base_repository=attrs["base_repository"],
                    focus=attrs["focus"],
                    worktree_path=attrs["worktree_path"],
                    last_activity=last_activity,
                    session_id=attrs["session_id"],
                )

    def _save_context(self) -> None:
        """Save current session context to CKS."""
        if not self.current_context:
            return

        # Update last activity
        self.current_context.last_activity = time.time()

        # CRITICAL FIX: Deactivate ALL other contexts first
        all_contexts = self._cks_hyper_graph_query(
            entity_type="ProjectContext",
            filter={"active": "true"},
            limit=100,
        )

        for ctx in all_contexts:
            ctx_attrs = ctx["attributes"]
            ctx_tsk_id = ctx_attrs.get("tsk_id", "")
            # Deactivate all contexts except the current one
            if ctx_tsk_id != self.current_context.tsk_id:
                self._cks_update_entity_attributes(
                    entity_type="ProjectContext",
                    entity_id=ctx["entity_id"],
                    attributes={"active": "false"},
                )

        # Check if entity already exists
        existing = self._cks_hyper_graph_query(
            entity_type="ProjectContext",
            filter={"tsk_id": self.current_context.tsk_id},
            limit=1,
        )

        attrs = {
            "tsk_id": self.current_context.tsk_id,
            "name": self.current_context.name,
            "base_repository": self.current_context.base_repository,
            "focus": self.current_context.focus,
            "worktree_path": self.current_context.worktree_path,
            "last_activity": self.current_context.last_activity,
            "session_id": self.current_context.session_id,
            "active": "true",
        }

        if existing:
            # Update existing entity
            self._cks_update_entity_attributes(
                entity_type="ProjectContext",
                entity_id=existing[0]["entity_id"],
                attributes=attrs,
            )
        else:
            # Create new entity
            from csf.cks_client import Entity

            entity = Entity(
                entity_type="ProjectContext",
                entity_id=f"context_{self.current_context.tsk_id}_{int(time.time())}",
                attributes=attrs,
                relationships={},
            )
            self.cks.add_entity(entity)

    def _cks_hyper_graph_query(self, entity_type=None, filter=None, limit=100):
        """Adapter for CKSHyperGraphClient.hyper_graph_query using unified CKS."""
        entry_type = None
        if entity_type in ("ProjectContext", "Task"):
            entry_type = "task"
        elif entity_type == "SessionCheckpoint":
            entry_type = "checkpoint"
        elif entity_type == "Blocker":
            entry_type = "blocker"

        if entry_type == "task":
            results = self.cks.get_tasks(limit=limit)
        else:
            results = self.cks.search("", entry_type=entry_type, limit=limit)

        if filter:
            filtered = []
            for r in results:
                m = r.get("metadata", {})
                if all(m.get(k) == v for k, v in filter.items()):
                    filtered.append(r)
            results = filtered

        return [
            {
                "entity_id": r.get("id", ""),
                "entity_type": entry_type or r.get("type", ""),
                "attributes": r.get("metadata", {}),
                "title": r.get("title", ""),
                "content": r.get("content", ""),
                "created_at": r.get("created_at", ""),
            }
            for r in results
        ]

    def _cks_update_entity_attributes(self, entity_type, entity_id, attributes) -> bool:
        """Adapter for CKSHyperGraphClient.update_entity_attributes using unified CKS."""
        import sqlite3

        conn = sqlite3.connect(str(self.cks.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT metadata FROM entries WHERE id = ?", (entity_id,))
        row = cursor.fetchone()
        if row:
            try:
                existing = json.loads(row[0]) if row[0] else {}
            except:
                existing = {}
            existing.update(attributes)
            cursor.execute(
                "UPDATE entries SET metadata = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (json.dumps(existing), entity_id),
            )
            conn.commit()
            conn.close()
            return True
        conn.close()
        return False

    def detect_active_tsk_projects(self) -> list[dict]:
        """Scan for active TSK projects in memory system."""
        active_projects = []

        # Scan TSK directories for project.json files or recent activity
        for tsk_dir in self.memory_base.glob("TSK-*"):
            if not tsk_dir.is_dir():
                continue

            # Check for project.json first
            project_file = tsk_dir / "project.json"
            if project_file.exists():
                try:
                    with open(project_file) as f:
                        project_data = json.load(f)
                        if project_data.get("active", False):
                            active_projects.append(
                                {
                                    "tsk_id": project_data.get("tsk_id", tsk_dir.name),
                                    "name": project_data.get("name", "Unknown Project"),
                                    "path": str(tsk_dir),
                                    "base_repository": project_data.get("context", {}).get(
                                        "base_repository", "unknown"
                                    ),
                                    "focus": project_data.get("context", {}).get(
                                        "focus", "general"
                                    ),
                                    "source": "project.json",
                                }
                            )
                except (json.JSONDecodeError, KeyError):
                    continue

            else:
                # Fallback: check for recent activity in directory
                try:
                    latest_file = max(tsk_dir.glob("**/*"), key=os.path.getctime, default=None)
                    if latest_file:
                        file_age = time.time() - latest_file.stat().st_mtime
                        if file_age < 86400:  # Activity in last 24 hours
                            active_projects.append(
                                {
                                    "tsk_id": tsk_dir.name,
                                    "name": f"Project {tsk_dir.name}",
                                    "path": str(tsk_dir),
                                    "base_repository": "unknown",
                                    "focus": "general",
                                    "source": "directory_activity",
                                }
                            )
                except (OSError, ValueError):
                    continue

        return active_projects

    def get_worktree_context(self) -> str | None:
        """Determine project context from current working directory."""
        cwd = Path.cwd().resolve()

        # Check if we're in a known worktree structure
        if "yt-fts-alt-platforms" in str(cwd):
            return "TSK-ALT-PLATFORM-DOWNLOADING"
        if "__csf" in str(cwd):
            # Check for GPU-related context
            if "GPUWorkloadDataExtractor" in str(cwd) or "gpu_workload" in str(cwd).lower():
                return "TSK-122225-GPUWorkloadIntegration-1457"
        elif "projects" in str(cwd):
            # Generic project directory
            return "generic_project"

        return None

    def set_active_context(self, tsk_id: str, force: bool = False) -> bool:
        """Set active project context."""
        active_projects = self.detect_active_tsk_projects()

        # Find the requested project
        target_project = None
        for project in active_projects:
            if project["tsk_id"] == tsk_id:
                target_project = project
                break

        if not target_project:
            # Also allow context setting based on worktree detection
            worktree_ctx = self.get_worktree_context()
            if worktree_ctx and worktree_ctx == tsk_id:
                target_project = {
                    "tsk_id": tsk_id,
                    "name": f"Auto-detected: {tsk_id}",
                    "base_repository": "auto-detected",
                    "focus": "general",
                    "worktree_path": str(Path.cwd()),
                }
            else:
                raise ValueError(f"TSK project {tsk_id} not found or not active")

        # Check for potential context conflict
        if self.current_context and not force and self.current_context.tsk_id != tsk_id:
            print("⚠️  CONTEXT SWITCH DETECTED:")
            print(f"   Previous: {self.current_context.tsk_id} ({self.current_context.name})")
            print(f"   Requested: {tsk_id} ({target_project['name']})")

        self.current_context = ProjectContext(
            tsk_id=target_project["tsk_id"],
            name=target_project["name"],
            base_repository=target_project.get("base_repository", "unknown"),
            focus=target_project.get("focus", "general"),
            worktree_path=target_project.get("worktree_path", str(Path.cwd())),
            last_activity=time.time(),
            session_id=self.session_id,
        )

        self._save_context()
        print(f"✅ Context set to: {tsk_id} - {target_project['name']}")
        return True

    def validate_current_operation(
        self, operation_description: str = ""
    ) -> tuple[bool, str | None]:
        """Validate if current operation matches active project context.
        Returns (is_valid, warning_message).
        """
        if not self.current_context:
            return True, None  # No context set, allow operation

        # Detect current worktree context
        worktree_context = self.get_worktree_context()

        # Check for context mismatches
        if worktree_context and worktree_context != self.current_context.tsk_id:
            return (
                False,
                f"Context mismatch: working directory suggests {worktree_context} but active context is {self.current_context.tsk_id}",
            )

        # Check for operation-specific conflicts
        op_lower = operation_description.lower()

        # GPU-related operations when not in GPU context
        if (
            "gpu" in op_lower or "workload" in op_lower
        ) and "GPUWorkload" not in self.current_context.tsk_id:
            if "GPU" in self.current_context.tsk_id:
                return True, None  # Allow GPU work in GPU context
            return (
                False,
                f"GPU operation detected but active context is {self.current_context.tsk_id}",
            )

        # Platform-related operations when not in platform context
        if (
            "platform" in op_lower or "odysee" in op_lower or "rumble" in op_lower
        ) and "PLATFORM" not in self.current_context.tsk_id:
            return (
                False,
                f"Platform operation detected but active context is {self.current_context.tsk_id}",
            )

        return True, None

    def pre_operation_check(self, operation_description: str) -> bool:
        """Perform pre-operation validation. Returns True if operation should proceed."""
        is_valid, warning = self.validate_current_operation(operation_description)

        if not is_valid:
            print("❌ CONTEXT VALIDATION FAILED")
            print(f"   Operation: {operation_description}")
            print(f"   Issue: {warning}")
            print(
                f"   Active Context: {self.current_context.tsk_id if self.current_context else 'None'}"
            )

            # Suggest context correction
            worktree_context = self.get_worktree_context()
            if worktree_context:
                print(f"   Suggested Context: {worktree_context}")
                print(f"   Run: context-set {worktree_context}")

            return False

        if warning:
            print(f"⚠️  {warning}")

        return True

    def get_context_summary(self) -> str:
        """Get formatted summary of current context."""
        if not self.current_context:
            return "No active context set"

        active_projects = self.detect_active_tsk_projects()
        context_age = int(time.time() - self.current_context.last_activity)

        summary = f"""
📍 ACTIVE SESSION CONTEXT (CKS Storage)
   TSK ID: {self.current_context.tsk_id}
   Name: {self.current_context.name}
   Repository: {self.current_context.base_repository}
   Focus: {self.current_context.focus}
   Session: {self.current_context.session_id}
   Age: {context_age}s ago
   Worktree: {self.current_context.worktree_path}

🔍 AVAILABLE ACTIVE PROJECTS ({len(active_projects)}):
"""
        for project in active_projects[:5]:  # Show top 5
            status = (
                "✅ ACTIVE" if project["tsk_id"] == self.current_context.tsk_id else "   available"
            )
            summary += f"   {status} {project['tsk_id']} - {project['name']}\n"

        return summary

    def clear_context(self) -> None:
        """Clear current session context."""
        if self.current_context:
            # Mark entity as inactive in CKS
            existing = self._cks_hyper_graph_query(
                entity_type="ProjectContext",
                filter={"tsk_id": self.current_context.tsk_id, "active": "true"},
                limit=1,
            )

            if existing:
                self._cks_update_entity_attributes(
                    entity_type="ProjectContext",
                    entity_id=existing[0]["entity_id"],
                    attributes={"active": "false"},
                )

        self.current_context = None
        print("✅ Session context cleared")
