"""Pytest configuration with TDD escalation pipeline hooks."""

# Direct import from tdd_hooks modules
import sys
from pathlib import Path
from typing import Any

# Add the root directory to path for src.* imports (enables src.duf, src.core, etc.)
root_path = Path(__file__).parent.resolve()
src_path = root_path / "src"
tdd_hooks_path = src_path / "core"

# Insert in correct order: src_path first (for knowledge.* imports), then root_path, then tdd_hooks_path
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
if str(root_path) not in sys.path:
    sys.path.insert(1, str(root_path))
if str(tdd_hooks_path) not in sys.path:
    sys.path.insert(2, str(tdd_hooks_path))

from tdd_hooks.hookspec import TDDHookSpec
from tdd_hooks.tdd_phase_hooks import TDDPhaseHooks
from tdd_hooks.test_escalation_orchestrator import TestEscalationOrchestrator


def pytest_addhooks(pluginmanager: Any) -> None:
    """Register the TDD hook specifications with pytest."""
    pluginmanager.add_hookspecs(TDDHookSpec)


def pytest_configure(config: Any) -> None:
    """Register hook implementations as pytest plugins."""
    # Register phase-level hooks
    phase_hooks = TDDPhaseHooks()
    config.pluginmanager.register(phase_hooks, name="tdd_phase_hooks")

    # Register escalation pipeline (singleton for multi-terminal support)
    orchestrator = TestEscalationOrchestrator()
    config.pluginmanager.register(orchestrator, name="tdd_escalation_pipeline")
