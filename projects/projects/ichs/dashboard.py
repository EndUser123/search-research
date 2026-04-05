"""
Real-time monitoring dashboard for iCHS
"""

import threading
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class ProgressInfo:
    """Progress information for the dashboard"""

    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    current_task: str = ""
    start_time: float = 0
    estimated_completion: float | None = None
    current_command: str = ""
    current_tool: str = ""
    success_rate: float = 0.0


class RealTimeDashboard:
    """Real-time monitoring dashboard for iCHS operations"""

    def __init__(self, enable_progress_bar: bool = True):
        """
        Initialize the dashboard

        Args:
            enable_progress_bar: Whether to show the progress bar
        """
        self.progress_info = ProgressInfo()
        self._stop_event = threading.Event()
        self._dashboard_thread = None
        self._enable_progress_bar = enable_progress_bar
        self._last_update_time = 0
        self._update_interval = 0.5  # Update every 500ms

        # Tool-specific counters
        self.tool_counts: dict[str, int] = {}
        self.tool_success_counts: dict[str, int] = {}
        self.tool_failure_counts: dict[str, int] = {}

        # Performance metrics
        self.command_start_times: dict[str, float] = {}
        self.command_durations: list[float] = []

        # Task queue
        self.task_queue: list[str] = []
        self.completed_tasks: list[str] = []
        self.failed_tasks: list[str] = []

    def start(self):
        """Start the dashboard display"""
        self._stop_event.clear()
        self.progress_info.start_time = time.time()
        self._dashboard_thread = threading.Thread(target=self._run_dashboard)
        self._dashboard_thread.daemon = True
        self._dashboard_thread.start()

    def stop(self):
        """Stop the dashboard display"""
        self._stop_event.set()
        if self._dashboard_thread:
            self._dashboard_thread.join()
        self._display_final_summary()

    def update_progress(
        self,
        total_tasks: int,
        completed_tasks: int,
        failed_tasks: int,
        current_task: str = "",
    ):
        """Update progress information"""
        self.progress_info.total_tasks = total_tasks
        self.progress_info.completed_tasks = completed_tasks
        self.progress_info.failed_tasks = failed_tasks
        self.progress_info.current_task = current_task

        # Calculate success rate
        if total_tasks > 0:
            self.progress_info.success_rate = (completed_tasks / total_tasks) * 100

        # Calculate estimated completion time
        if completed_tasks > 0 and total_tasks > completed_tasks:
            elapsed_time = time.time() - self.progress_info.start_time
            avg_time_per_task = elapsed_time / completed_tasks
            remaining_tasks = total_tasks - completed_tasks
            estimated_remaining_time = avg_time_per_task * remaining_tasks
            self.progress_info.estimated_completion = (
                time.time() + estimated_remaining_time
            )
        else:
            self.progress_info.estimated_completion = None

    def update_current_command(self, command: str, tool: str):
        """Update the current command being executed"""
        self.progress_info.current_command = command
        self.progress_info.current_tool = tool
        self.command_start_times[command] = time.time()

    def mark_command_completed(self, command: str, success: bool = True):
        """Mark a command as completed"""
        if command in self.command_start_times:
            duration = time.time() - self.command_start_times[command]
            self.command_durations.append(duration)
            del self.command_start_times[command]

        tool = self.progress_info.current_tool
        if tool:
            self.tool_counts[tool] = self.tool_counts.get(tool, 0) + 1
            if success:
                self.tool_success_counts[tool] = (
                    self.tool_success_counts.get(tool, 0) + 1
                )
            else:
                self.tool_failure_counts[tool] = (
                    self.tool_failure_counts.get(tool, 0) + 1
                )

    def add_task_to_queue(self, task: str):
        """Add a task to the queue"""
        self.task_queue.append(task)

    def mark_task_completed(self, task: str, success: bool = True):
        """Mark a task as completed"""
        if task in self.task_queue:
            self.task_queue.remove(task)

        if success:
            self.completed_tasks.append(task)
        else:
            self.failed_tasks.append(task)

    def _run_dashboard(self):
        """Main dashboard loop"""
        while not self._stop_event.is_set():
            current_time = time.time()

            # Update display at specified intervals
            if current_time - self._last_update_time >= self._update_interval:
                self._display_progress()
                self._last_update_time = current_time

            time.sleep(0.1)  # Small sleep to prevent CPU overuse

    def _display_progress(self):
        """Display the current progress"""
        # Clear screen
        print("\033[H\033[J", end="")

        # Header
        print("╔" + "═" * 78 + "╗")
        print("║" + " " * 36 + "iCHS Real-time Dashboard" + " " * 36 + "║")
        print("╠" + "═" * 78 + "╣")

        # Progress summary
        print("║ Progress Summary:")
        print(f"║  Total Tasks: {self.progress_info.total_tasks}")
        print(f"║  Completed: {self.progress_info.completed_tasks}")
        print(f"║  Failed: {self.progress_info.failed_tasks}")
        print(f"║  Success Rate: {self.progress_info.success_rate:.1f}%")

        # Current task
        if self.progress_info.current_task:
            print(f"║  Current Task: {self.progress_info.current_task}")

        # Current command
        if self.progress_info.current_command:
            # Truncate long commands
            cmd_display = self.progress_info.current_command
            if len(cmd_display) > 50:
                cmd_display = cmd_display[:47] + "..."
            print(f"║  Current Command: {cmd_display}")
            print(f"║  Using Tool: {self.progress_info.current_tool}")

        # Time information
        elapsed_time = time.time() - self.progress_info.start_time
        print(f"║  Elapsed Time: {self._format_time(elapsed_time)}")

        if self.progress_info.estimated_completion:
            remaining_time = self.progress_info.estimated_completion - time.time()
            print(f"║  Estimated Completion: {self._format_time(remaining_time)}")

        # Progress bar
        if self._enable_progress_bar and self.progress_info.total_tasks > 0:
            print("║")
            print("║  Progress Bar:")
            progress = (
                self.progress_info.completed_tasks / self.progress_info.total_tasks
            ) * 100
            bar_length = 50
            filled = int(bar_length * progress / 100)
            bar = "█" * filled + "░" * (bar_length - filled)
            print(f"║  [{bar}] {progress:.1f}%")

        # Tool statistics
        if self.tool_counts:
            print("║")
            print("║  Tool Statistics:")
            for tool, count in sorted(self.tool_counts.items()):
                success_count = self.tool_success_counts.get(tool, 0)
                failure_count = self.tool_failure_counts.get(tool, 0)
                success_rate = (success_count / count) * 100 if count > 0 else 0
                print(
                    f"║    {tool}: {count} total, {success_count} success, {failure_count} failed ({success_rate:.1f}%)"
                )

        # Performance metrics
        if self.command_durations:
            print("║")
            print("║  Performance Metrics:")
            avg_duration = sum(self.command_durations) / len(self.command_durations)
            max_duration = max(self.command_durations)
            min_duration = min(self.command_durations)
            print(f"║    Average Command Duration: {avg_duration:.2f}s")
            print(f"║    Max Command Duration: {max_duration:.2f}s")
            print(f"║    Min Command Duration: {min_duration:.2f}s")

        # Task queue
        if self.task_queue:
            print("║")
            print("║  Task Queue (next 5):")
            for i, task in enumerate(self.task_queue[:5]):
                print(f"║    {i + 1}. {task}")

        # Footer
        print("╚" + "═" * 78 + "╝")
        print("  Press Ctrl+C to stop monitoring", end="", flush=True)

    def _display_final_summary(self):
        """Display final summary when dashboard stops"""
        print("\033[H\033[J", end="")  # Clear screen

        print("╔" + "═" * 78 + "╗")
        print("║" + " " * 32 + "iCHS Final Summary" + " " * 32 + "║")
        print("╠" + "═" * 78 + "╣")

        total_time = time.time() - self.progress_info.start_time

        print(f"║ Total Execution Time: {self._format_time(total_time)}")
        print(f"║ Total Tasks: {self.progress_info.total_tasks}")
        print(f"║ Completed Tasks: {self.progress_info.completed_tasks}")
        print(f"║ Failed Tasks: {self.progress_info.failed_tasks}")

        if self.progress_info.total_tasks > 0:
            success_rate = (
                self.progress_info.completed_tasks / self.progress_info.total_tasks
            ) * 100
            print(f"║ Overall Success Rate: {success_rate:.1f}%")

        if self.command_durations:
            avg_duration = sum(self.command_durations) / len(self.command_durations)
            print(f"║ Average Command Duration: {avg_duration:.2f}s")

        if self.tool_counts:
            print("║")
            print("║ Tool Usage Summary:")
            for tool, count in sorted(self.tool_counts.items()):
                success_count = self.tool_success_counts.get(tool, 0)
                failure_count = self.tool_failure_counts.get(tool, 0)
                print(
                    f"║   {tool}: {count} executions ({success_count} success, {failure_count} failed)"
                )

        print("╚" + "═" * 78 + "╝")

    def _format_time(self, seconds: float) -> str:
        """Format time in seconds to HH:MM:SS format"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            remaining_seconds = int(seconds % 60)
            return f"{minutes}m {remaining_seconds}s"
        else:
            hours = int(seconds // 3600)
            remaining_minutes = int((seconds % 3600) // 60)
            remaining_seconds = int(seconds % 60)
            return f"{hours}h {remaining_minutes}m {remaining_seconds}s"

    def get_performance_report(self) -> dict[str, Any]:
        """Get performance statistics"""
        if not self.command_durations:
            return {"error": "No performance data collected"}

        return {
            "total_commands": len(self.command_durations),
            "average_duration": sum(self.command_durations)
            / len(self.command_durations),
            "max_duration": max(self.command_durations),
            "min_duration": min(self.command_durations),
            "total_duration": sum(self.command_durations),
            "tool_counts": self.tool_counts.copy(),
            "tool_success_rates": {
                tool: (self.tool_success_counts.get(tool, 0) / count) * 100
                for tool, count in self.tool_counts.items()
            },
            "total_tasks": self.progress_info.total_tasks,
            "completed_tasks": self.progress_info.completed_tasks,
            "failed_tasks": self.progress_info.failed_tasks,
            "success_rate": self.progress_info.success_rate,
        }


class SimpleProgressMonitor:
    """Simple progress monitor for environments without full terminal support"""

    def __init__(self):
        self.start_time = time.time()
        self.completed_tasks = 0
        self.total_tasks = 0
        self.current_task = ""

    def start(self, total_tasks: int):
        """Start monitoring"""
        self.total_tasks = total_tasks
        self.start_time = time.time()
        self.completed_tasks = 0
        print(f"Starting monitoring of {total_tasks} tasks...")

    def update(self, completed_tasks: int, current_task: str = ""):
        """Update progress"""
        self.completed_tasks = completed_tasks
        self.current_task = current_task

        if self.total_tasks > 0:
            progress = (completed_tasks / self.total_tasks) * 100
            elapsed = time.time() - self.start_time

            print(
                f"Progress: {completed_tasks}/{self.total_tasks} ({progress:.1f}%) - "
                f"Current: {current_task} - Elapsed: {self._format_time(elapsed)}",
                end="\r",
            )

    def finish(self):
        """Finish monitoring"""
        total_time = time.time() - self.start_time
        print(f"\nCompleted in {self._format_time(total_time)}")

    def _format_time(self, seconds: float) -> str:
        """Format time in seconds to HH:MM:SS format"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            remaining_seconds = int(seconds % 60)
            return f"{minutes}m {remaining_seconds}s"
        else:
            hours = int(seconds // 3600)
            remaining_minutes = int((seconds % 3600) // 60)
            remaining_seconds = int(seconds % 60)
            return f"{hours}h {remaining_minutes}m {remaining_seconds}s"
