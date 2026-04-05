#!/usr/bin/env python3
"""
SessionContextManager - Prevents project context switching confusion
Tracks active TSK projects and validates operations before execution
"""

import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class ProjectContext:
    """Represents active project context"""
    tsk_id: str
    name: str
    base_repository: str
    focus: str
    worktree_path: str
    last_activity: float
    session_id: str

class SessionContextManager:
    """
    Manages session context to prevent project switching confusion.
    Validates active project before major operations.
    """

    def __init__(self, memory_base: str = ".speckit/memory"):
        self.memory_base = Path(memory_base)
        self.context_file = self.memory_base / "session_context.json"
        self.session_id = f"session_{int(time.time())}"
        self.current_context = None
        self._load_context()

    def _load_context(self) -> None:
        """Load existing session context if available"""
        if self.context_file.exists():
            try:
                with open(self.context_file) as f:
                    data = json.load(f)
                    self.current_context = ProjectContext(**data)
                    # Check if context is stale (older than 2 hours)
                    if time.time() - self.current_context.last_activity > 7200:
                        self.current_context = None
            except (json.JSONDecodeError, TypeError, KeyError):
                self.current_context = None

    def _save_context(self) -> None:
        """Save current session context"""
        if self.current_context:
            self.current_context.last_activity = time.time()
            with open(self.context_file, 'w') as f:
                json.dump(asdict(self.current_context), f, indent=2)

    def detect_active_tsk_projects(self) -> list[dict]:
        """Scan for active TSK projects in memory system"""
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
                        if project_data.get('active', False):
                            active_projects.append({
                                'tsk_id': project_data.get('tsk_id', tsk_dir.name),
                                'name': project_data.get('name', 'Unknown Project'),
                                'path': str(tsk_dir),
                                'base_repository': project_data.get('context', {}).get('base_repository', 'unknown'),
                                'focus': project_data.get('context', {}).get('focus', 'general'),
                                'source': 'project.json'
                            })
                except (json.JSONDecodeError, KeyError):
                    continue

            else:
                # Fallback: check for recent activity in directory
                try:
                    latest_file = max(tsk_dir.glob('**/*'), key=os.path.getctime, default=None)
                    if latest_file:
                        file_age = time.time() - latest_file.stat().st_mtime
                        if file_age < 86400:  # Activity in last 24 hours
                            active_projects.append({
                                'tsk_id': tsk_dir.name,
                                'name': f"Project {tsk_dir.name}",
                                'path': str(tsk_dir),
                                'base_repository': 'unknown',
                                'focus': 'general',
                                'source': 'directory_activity'
                            })
                except (OSError, ValueError):
                    continue

        return active_projects

    def get_worktree_context(self) -> str | None:
        """Determine project context from current working directory"""
        cwd = Path.cwd().resolve()

        # Check if we're in a known worktree structure
        if 'yt-fts-alt-platforms' in str(cwd):
            return 'TSK-ALT-PLATFORM-DOWNLOADING'
        elif '__csf' in str(cwd):
            # Check for GPU-related context
            if 'GPUWorkloadDataExtractor' in str(cwd) or 'gpu_workload' in str(cwd).lower():
                return 'TSK-122225-GPUWorkloadIntegration-1457'
        elif 'projects' in str(cwd):
            # Generic project directory
            return 'generic_project'

        return None

    def set_active_context(self, tsk_id: str, force: bool = False) -> bool:
        """Set active project context"""
        active_projects = self.detect_active_tsk_projects()

        # Find the requested project
        target_project = None
        for project in active_projects:
            if project['tsk_id'] == tsk_id:
                target_project = project
                break

        if not target_project:
            raise ValueError(f"TSK project {tsk_id} not found or not active")

        # Check for potential context conflict
        if self.current_context and not force:
            if self.current_context.tsk_id != tsk_id:
                print("⚠️  CONTEXT SWITCH DETECTED:")
                print(f"   Previous: {self.current_context.tsk_id} ({self.current_context.name})")
                print(f"   Requested: {tsk_id} ({target_project['name']})")

        self.current_context = ProjectContext(
            tsk_id=target_project['tsk_id'],
            name=target_project['name'],
            base_repository=target_project['base_repository'],
            focus=target_project['focus'],
            worktree_path=Path.cwd().as_posix(),
            last_activity=time.time(),
            session_id=self.session_id
        )

        self._save_context()
        print(f"✅ Context set to: {tsk_id} - {target_project['name']}")
        return True

    def validate_current_operation(self, operation_description: str = "") -> tuple[bool, str | None]:
        """
        Validate if current operation matches active project context.
        Returns (is_valid, warning_message)
        """
        if not self.current_context:
            return True, None  # No context set, allow operation

        # Detect current worktree context
        worktree_context = self.get_worktree_context()

        # Check for context mismatches
        if worktree_context and worktree_context != self.current_context.tsk_id:
            return False, f"Context mismatch: working directory suggests {worktree_context} but active context is {self.current_context.tsk_id}"

        # Check for operation-specific conflicts
        op_lower = operation_description.lower()

        # GPU-related operations when not in GPU context
        if ('gpu' in op_lower or 'workload' in op_lower) and 'GPUWorkload' not in self.current_context.tsk_id:
            if 'GPU' in self.current_context.tsk_id:
                return True, None  # Allow GPU work in GPU context
            else:
                return False, f"GPU operation detected but active context is {self.current_context.tsk_id}"

        # Platform-related operations when not in platform context
        if ('platform' in op_lower or 'odysee' in op_lower or 'rumble' in op_lower) and 'PLATFORM' not in self.current_context.tsk_id:
            return False, f"Platform operation detected but active context is {self.current_context.tsk_id}"

        return True, None

    def pre_operation_check(self, operation_description: str) -> bool:
        """
        Perform pre-operation validation. Returns True if operation should proceed.
        """
        is_valid, warning = self.validate_current_operation(operation_description)

        if not is_valid:
            print("❌ CONTEXT VALIDATION FAILED")
            print(f"   Operation: {operation_description}")
            print(f"   Issue: {warning}")
            print(f"   Active Context: {self.current_context.tsk_id if self.current_context else 'None'}")

            # Suggest context correction
            worktree_context = self.get_worktree_context()
            if worktree_context:
                print(f"   Suggested Context: {worktree_context}")
                print(f"   Run: context-set {worktree_context}")

            return False

        elif warning:
            print(f"⚠️  {warning}")

        return True

    def get_context_summary(self) -> str:
        """Get formatted summary of current context"""
        if not self.current_context:
            return "No active context set"

        active_projects = self.detect_active_tsk_projects()
        context_age = int(time.time() - self.current_context.last_activity)

        summary = f"""
📍 ACTIVE SESSION CONTEXT
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
            status = "✅ ACTIVE" if project['tsk_id'] == self.current_context.tsk_id else "   available"
            summary += f"   {status} {project['tsk_id']} - {project['name']}\n"

        return summary

    def clear_context(self) -> None:
        """Clear current session context"""
        self.current_context = None
        if self.context_file.exists():
            self.context_file.unlink()
        print("✅ Session context cleared")
