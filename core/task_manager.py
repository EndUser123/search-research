"""
Windows Scheduled Task Manager

Provides interface for querying and managing Windows scheduled tasks
used by the CSF (Constitutional Solo Framework) system.

Uses schtasks.exe (Windows built-in) for task management.
"""

from __future__ import annotations

import json
import subprocess
from cli.subprocess_helper import run_subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class TaskInfo:
    """Information about a Windows scheduled task."""
    name: str
    state: str  # Ready, Running, Disabled, etc.
    last_run_time: str | None
    next_run_time: str | None
    last_run_result: int | None  # 0 = success
    author: str | None
    description: str | None

    @property
    def is_enabled(self) -> bool:
        return self.state.lower() not in ["disabled", "unknown"]

    @property
    def is_running(self) -> bool:
        return self.state.lower() == "running"


class TaskManager:
    """
    Manager for Windows scheduled tasks.

    Provides methods to query, enable, disable, and trigger tasks.
    Uses schtasks.exe command-line utility.
    """

    # CSF task definitions (with Windows task prefix)
    CSF_TASKS = {
        "\\CHS One-Time Rebuild": "CHS One-Time Rebuild",
        "\\CSF_CHS_Incremental_Update": "CHS Incremental Update",
        "\\CKS_Dreaming_Daemon": "CKS Dreaming Daemon",
        "\\CSF_LogRotation": "CSF Log Rotation",
        "\\CSF_DatabaseMaintenance": "CSF Database Maintenance",
        "\\CSF_MLTraining": "CSF ML Training",
    }

    # Short names for CLI convenience
    CSF_TASK_SHORT_NAMES = {
        "chs-rebuild": "\\CHS One-Time Rebuild",
        "chs-inc": "\\CSF_CHS_Incremental_Update",
        "cks": "\\CKS_Dreaming_Daemon",
        "log": "\\CSF_LogRotation",
        "db": "\\CSF_DatabaseMaintenance",
        "ml": "\\CSF_MLTraining",
    }

    def __init__(self, task_folder: str = "\\"):
        """Initialize task manager.

        Args:
            task_folder: Task folder path (default: root task folder)
        """
        self.task_folder = task_folder

    def _run_schtasks(self, args: list[str]) -> tuple[int, str, str]:
        """Run schtasks.exe command.

        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        cmd = ["schtasks.exe"] + args
        try:
            result = run_subprocess(
                cmd,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return 1, "", f"Failed to run schtasks: {e}"

    def get_task_info(self, task_name: str) -> TaskInfo | None:
        """Get information about a specific task.

        Args:
            task_name: Name of the task (can include folder path like \\TaskName)

        Returns:
            TaskInfo object or None if task not found
        """
        # Use verbose list format to get all information including state
        # XML format doesn't include Status/State information
        # Note: /TN and task_name must be separate arguments
        code, stdout, stderr = self._run_schtasks([
            "/query", "/TN", task_name, "/FO", "LIST", "/V"
        ])

        if code != 0:
            return None

        # Parse the text-based output
        state = "Unknown"
        last_run = None
        next_run = None
        last_result = None
        author = None
        description = None

        for line in stdout.split('\n'):
            line = line.strip()
            if line.startswith("Status:"):
                state = line.split(":", 1)[1].strip()
            elif line.startswith("Last Run Time:"):
                last_run = line.split(":", 1)[1].strip()
            elif line.startswith("Next Run Time:"):
                next_run = line.split(":", 1)[1].strip()
            elif line.startswith("Last Result:"):
                result_str = line.split(":", 1)[1].strip()
                try:
                    last_result = int(result_str)
                except ValueError:
                    last_result = None
            elif line.startswith("Author:"):
                author = line.split(":", 1)[1].strip()
                if author == "N/A":
                    author = None
            elif line.startswith("Comment:"):
                description = line.split(":", 1)[1].strip()
            elif line.startswith("Scheduled Task State:"):
                task_state = line.split(":", 1)[1].strip()
                if task_state == "Disabled":
                    state = "Disabled"

        return TaskInfo(
            name=task_name,
            state=state,
            last_run_time=last_run,
            next_run_time=next_run,
            last_run_result=last_result,
            author=author,
            description=description,
        )

    def get_all_tasks(self) -> dict[str, TaskInfo]:
        """Get information about all CSF tasks.

        Returns:
            Dictionary mapping task names to TaskInfo objects
        """
        tasks = {}

        for short_name, display_name in self.CSF_TASKS.items():
            info = self.get_task_info(short_name)
            if info is None:
                # Create a placeholder for missing tasks
                info = TaskInfo(
                    name=short_name,
                    state="Not Found",
                    last_run_time=None,
                    next_run_time=None,
                    last_run_result=None,
                    author=None,
                    description=display_name,
                )
            tasks[short_name] = info

        return tasks

    def enable_task(self, task_name: str) -> tuple[bool, str]:
        """Enable a scheduled task.

        Args:
            task_name: Name of the task to enable

        Returns:
            Tuple of (success, message)
        """
        code, stdout, stderr = self._run_schtasks([
            "/change", "/TN", task_name, "/enable"
        ])

        if code == 0:
            return True, f"Task '{task_name}' enabled successfully"
        else:
            return False, f"Failed to enable task: {stderr or stdout}"

    def disable_task(self, task_name: str) -> tuple[bool, str]:
        """Disable a scheduled task.

        Args:
            task_name: Name of the task to disable

        Returns:
            Tuple of (success, message)
        """
        code, stdout, stderr = self._run_schtasks([
            "/change", "/TN", task_name, "/disable"
        ])

        if code == 0:
            return True, f"Task '{task_name}' disabled successfully"
        else:
            return False, f"Failed to disable task: {stderr or stdout}"

    def trigger_task(self, task_name: str) -> tuple[bool, str]:
        """Trigger (run) a scheduled task immediately.

        Args:
            task_name: Name of the task to trigger

        Returns:
            Tuple of (success, message)
        """
        code, stdout, stderr = self._run_schtasks([
            "/run", "/TN", task_name
        ])

        if code == 0:
            return True, f"Task '{task_name}' triggered successfully"
        else:
            return False, f"Failed to trigger task: {stderr or stdout}"

    def end_task(self, task_name: str) -> tuple[bool, str]:
        """End a running task.

        Args:
            task_name: Name of the task to end

        Returns:
            Tuple of (success, message)
        """
        code, stdout, stderr = self._run_schtasks([
            "/end", "/TN", task_name
        ])

        if code == 0:
            return True, f"Task '{task_name}' ended successfully"
        else:
            return False, f"Failed to end task: {stderr or stdout}"

    def format_status(self, tasks: dict[str, TaskInfo] | None = None) -> str:
        """Format task status as human-readable text.

        Args:
            tasks: Optional dictionary of tasks (uses get_all_tasks if None)

        Returns:
            Formatted status string
        """
        if tasks is None:
            tasks = self.get_all_tasks()

        lines = [
            "CSF Scheduled Tasks Status",
            "=" * 70,
        ]

        for short_name, display_name in self.CSF_TASKS.items():
            task = tasks.get(short_name)
            if task is None:
                continue

            status_icon = {
                "ready": "[OK]",
                "running": "[RUN]",
                "disabled": "[OFF]",
                "not found": "[?]",
            }.get(task.state.lower(), "[?]")

            lines.append(f"{status_icon} {display_name}")

            if task.state != "Not Found":
                lines.append(f"    State: {task.state}")
                if task.last_run_time and task.last_run_time != "N/A":
                    lines.append(f"    Last run: {task.last_run_time}")
                if task.next_run_time and task.next_run_time != "N/A":
                    lines.append(f"    Next run: {task.next_run_time}")
            else:
                lines.append("    Task not found on this system")

            lines.append("")

        return "\n".join(lines)

    def get_incremental_status(self) -> dict[str, Any]:
        """Get CHS incremental update status from state file.

        Returns:
            Dictionary with incremental update status
        """
        # State file location
        _csf_root = Path(__file__).parent.parent.parent.parent
        state_file = _csf_root / ".data" / "chs" / "incremental_state.json"

        if state_file.exists():
            try:
                state = json.loads(state_file.read_text(encoding="utf-8"))
                return {
                    "last_update": state.get("last_update"),
                    "total_updates": state.get("total_updates", 0),
                    "last_status": state.get("last_status", "unknown"),
                    "last_message_count": state.get("last_message_count", 0),
                    "last_update_duration": state.get("last_update_duration"),
                }
            except Exception:
                pass

        return {
            "last_update": None,
            "total_updates": 0,
            "last_status": "never_run",
            "last_message_count": 0,
            "last_update_duration": None,
        }
