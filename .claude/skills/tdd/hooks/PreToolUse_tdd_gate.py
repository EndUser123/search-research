#!/usr/bin/env python3
"""
PreToolUse TDD Gate - Skill-based version with terminal isolation

Enforces TDD workflow by blocking Edit/Write operations based on TDD phase:
- AWAITING_RED: Block implementation file edits (test must be written first)
- RED_CONFIRMED: Allow test edits, block implementation edits
- GREEN_CONFIRMED: Allow implementation edits, block test edits
- REFACTORING: Allow both, require tests passing

State is keyed by TEST FILE (not impl file) to prevent cross-contamination.

Changes from original:
- Removed @lru_cache on is_tdd_exempt() - prevents stale exemption decisions
- Terminal isolation via TDDState._resolve_state_file() using detect_terminal_id()
- Direct sys.path setup to access tdd_core from hooks directory
"""

import json
import os
import sys
from pathlib import Path

# Add hooks directory to path for imports
hooks_dir = Path("P:/.claude/hooks")
if str(hooks_dir) not in sys.path:
    sys.path.insert(0, str(hooks_dir))

# Import auto-logging decorator
from __lib.hook_base import hook_main
from tdd_core import TDDPhase, TDDState, debug_log, find_test_file


# NO @lru_cache - prevents stale exemption decisions across process boundaries
def is_tdd_exempt(file_path: str) -> bool:
    """Check if file is exempt from TDD enforcement.

    Exempt files:
    - Test files (tests/, test_*.py)
    - Documentation (*.md, *.rst)
    - Configuration (*.json, *.yaml, *.toml, *.ini)
    - Scripts in .staging/
    - __init__.py files
    """
    path = Path(file_path)

    # Test files
    if "tests" in path.parts or path.name.startswith("test_"):
        return True

    # Documentation
    if path.suffix in (".md", ".rst"):
        return True

    # Configuration
    if path.suffix in (".json", ".yaml", ".yml", ".toml", ".ini"):
        return True

    # Staging scripts
    if ".staging" in path.parts:
        return True

    # __init__ files
    if path.name == "__init__.py":
        return True

    # CRITICAL: Hooks NOT exempt - require tests before modification
    # Self-modification without TDD violates constitutional principles

    return False


def check_discovery_complete(state: dict, test_file: str | None) -> tuple[bool, str]:
    """Check if discovery phase is complete.

    Discovery is complete if:
    - State phase is past DISCOVER
    - OR all 4 evidence types are present (static_analysis, dynamic_analysis, coverage_baseline, test_discovery_log)

    Returns:
        tuple[bool, str]: (is_complete, reason_message)
        - is_complete: True if discovery can be skipped (already complete or not applicable)
        - reason_message: Empty string if complete, otherwise specific reason what's missing
    """
    phase = state.get("phase", "")

    # If we're past discovery phase, it's complete
    if phase and phase != TDDPhase.DISCOVER.value:
        return True, ""

    # Check discovery evidence for all 4 required types
    discovery_evidence = state.get("discovery_evidence", {})

    # If explicitly marked complete, accept it
    if discovery_evidence.get("complete", False):
        return True, ""

    # Validate all 4 evidence types
    missing_evidence = []

    # 1. static_analysis
    if "static_analysis" not in discovery_evidence:
        missing_evidence.append("static_analysis (files_read, imports_found)")

    # 2. dynamic_analysis
    if "dynamic_analysis" not in discovery_evidence:
        missing_evidence.append("dynamic_analysis (baseline_command, baseline_results)")

    # 3. coverage_baseline
    if "coverage_baseline" not in discovery_evidence:
        missing_evidence.append("coverage_baseline")

    # 4. test_discovery_log
    if "test_discovery_log" not in discovery_evidence:
        missing_evidence.append("test_discovery_log (existing_tests, test_count)")

    if missing_evidence:
        return False, f"Missing discovery evidence: {', '.join(missing_evidence)}"

    # All evidence types present
    return True, ""


def get_tdd_state_for_file(file_path: str) -> dict | None:
    """Get TDD state for a given file.

    Maps implementation file -> test file -> state.
    Returns None if no test file found or state doesn't exist.

    NO CACHE - reads from disk every time to avoid cross-process stale state.
    """
    # Check if exempt first
    if is_tdd_exempt(file_path):
        return None

    # Find the corresponding test file
    test_file = find_test_file(file_path)
    if not test_file:
        # No test file found - check if this requires TDD
        # Check if this is a tracked file under src/ (not __init__.py)
        path = Path(file_path)
        # Expand to cover implementation directories beyond just src/
        impl_dirs = ("src", "__csf", "packages", "lib", "app")
        in_impl_dir = any(dir in path.parts for dir in impl_dirs)

        if in_impl_dir and path.suffix == ".py" and path.name != "__init__.py":
            # Implementation file without test - return AWAITING_RED state to block edits
            # Create a synthetic TDD state to trigger blocking
            return {
                "phase": TDDPhase.AWAITING_RED.value,
                "test_file": None,
                "impl_file": str(path),
                "block_reason": f"No test file found. Create test first: tests/test_{path.stem.replace('_', '_')}.py",
            }

    # Load TDD state - NO CACHE, direct file read every time
    tdd_state = TDDState(test_file)
    state = tdd_state.load()

    return state


def should_block_edit(file_path: str, phase: str) -> tuple[bool, str | None]:
    """Determine if Edit/Write should be blocked based on TDD phase.

    Returns:
        tuple: (should_block, reason_message)
    """
    if phase == TDDPhase.AWAITING_RED.value:
        # Blocking: Implementation file edits during AWAITING_RED
        if not is_tdd_exempt(file_path):
            return (
                True,
                f"TDD phase AWAITING_RED: Write test first before editing {Path(file_path).name}",
            )

    elif phase == TDDPhase.RED_CONFIRMED.value:
        # Blocking: Implementation file edits during RED_CONFIRMED
        if not is_tdd_exempt(file_path):
            return (
                True,
                f"TDD phase RED_CONFIRMED: Test failing, cannot edit implementation {Path(file_path).name}",
            )

    elif phase == TDDPhase.GREEN_CONFIRMED.value:
        # Blocking: Test edits during GREEN_CONFIRMED (implementation phase)
        if is_tdd_exempt(file_path) or file_path.startswith("test_"):
            return (
                True,
                f"TDD phase GREEN_CONFIRMED: Implementation in progress, cannot edit test {Path(file_path).name}",
            )

    elif phase == TDDPhase.REFACTORING.value:
        # Allow both, but ideally check tests pass first
        pass

    return False, None


def process_hook(tool_input: dict, data: dict) -> tuple[bool, str | None]:
    """Main hook entry point.

    Args:
        tool_input: Tool input dict with 'name' and other tool-specific data
        data: Additional context data

    Returns:
        tuple: (should_continue, error_message)
        - should_continue: True to allow, False to block
        - error_message: Error message if blocking, None otherwise
    """
    tool_name = (
        tool_input.get("name")
        or tool_input.get("tool_name")
        or tool_input.get("tool")
        or ""
    )

    # Only process Edit/Write operations
    if tool_name not in ("Edit", "Write", "MultiEdit"):
        return True, None

    # Get file being edited
    edit_file = os.environ.get("CLAUDE_TOOL_EDIT_FILE", "")
    write_file = os.environ.get("CLAUDE_TOOL_WRITE_FILE", "")
    file_path = edit_file or write_file

    if not file_path:
        return True, None

    # Check if TDD gate is explicitly disabled (requires conscious decision)
    if os.environ.get("TDD_GATE_DISABLED", "").lower() in ("1", "true"):
        debug_log("TDD gate disabled via TDD_GATE_DISABLED")
        return True, None

    # Get TDD state for this file
    state = get_tdd_state_for_file(file_path)

    if not state:
        # No TDD state exists - default-deny for implementation files
        # Check if this is an implementation file that should require TDD
        path = Path(file_path)
        if not is_tdd_exempt(file_path):
            # Implementation file without active TDD cycle - block
            return False, (
                f"No active TDD cycle for {path.name}. "
                f"Start TDD first: create test file, then write failing test (RED phase)."
            )
        # Exempt file - allow
        return True, None

    phase = state.get("phase", "")
    test_file = state.get("test_file", "")

    # Check if this is a synthetic "no test file" block
    block_reason = state.get("block_reason")
    if block_reason:
        # Implementation file without test - block the edit
        return False, block_reason

    debug_log(f"TDD gate: file={file_path}, phase={phase}, test_file={test_file}")

    # Check if discovery is complete
    if phase == TDDPhase.DISCOVER.value:
        is_complete, reason = check_discovery_complete(state, test_file)
        if not is_complete:
            return True, None  # Let them work in discovery phase

    # Check if should block based on phase
    should_block, reason = should_block_edit(file_path, phase)

    if should_block:
        return False, reason

    return True, None


@hook_main
def main():
    """Entry point for hook execution."""

    # Read tool input from stdin
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        # No input data, allow
        print(json.dumps({"continue": True}))
        return

    # Read data file if provided
    data_file = os.environ.get("CLAUDE_DATA_FILE")
    data = {}
    if data_file and Path(data_file).exists():
        try:
            with open(data_file, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            pass

    should_continue, error_message = process_hook(input_data, data)

    if should_continue:
        print(json.dumps({"continue": True}))
    else:
        print(json.dumps({"continue": False, "error": {"message": error_message}}))
        sys.exit(1)  # Exit with error code to block


if __name__ == "__main__":
    main()
