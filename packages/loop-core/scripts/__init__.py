"""
loop-core: Terminal-local state management for Ralph-style autonomous loops.

This package provides file-based state management that avoids Git race conditions
in multi-terminal environments.
"""

__version__ = "0.1.0"

from scripts.loop_observability import log_decision, update_metrics
from scripts.plan_parser import parse_plan_tasks
from scripts.state_manager import TerminalStateManager

__all__ = [
    "TerminalStateManager",
    "parse_plan_tasks",
    "log_decision",
    "update_metrics",
]
