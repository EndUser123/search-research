#!/usr/bin/env python3
from __future__ import annotations

"""
PostToolUse TDD State - Skill-based version with terminal isolation

Handles TDD phase transitions after tool execution.

Transitions:
- Test file written → Associate with cycle, transition to AWAITING_RED
- Test run with failure → AWAITING_RED → RED_CONFIRMED
- Test run with pass → RED_CONFIRMED → GREEN_CONFIRMED
- Impl file written during GREEN → Track in impl_files

This hook runs AFTER tool execution, so it has access to results.
Standalone version with complete main() function for skill-based execution.

Phase 3 Integration (ADR-20260324):
- Uses phase_transition_logger for evidence binding
- Uses enforcement_tiers for constitutional compliance
- Uses cold_code_review_dispatch for adversarial review
"""

import json
import os
import sys
from pathlib import Path

# Add hooks directory to path for imports
hooks_dir = Path("P:/.claude/hooks")
if str(hooks_dir) not in sys.path:
    sys.path.insert(0, str(hooks_dir))

# Add __lib directory explicitly for hook_base module
# Required when run as subprocess from skills/tdd/hooks/
lib_dir = hooks_dir / "__lib"
if str(lib_dir) not in sys.path:
    sys.path.insert(0, str(lib_dir))

# Add hooks/tdd directory for Phase 3 modules
tdd_hooks_dir = hooks_dir / "tdd"
if str(tdd_hooks_dir) not in sys.path:
    sys.path.insert(0, str(tdd_hooks_dir))

# Add skill-guard to path for breadcrumb tracking
from __lib.skill_guard_path import ensure_skill_guard_in_syspath
ensure_skill_guard_in_syspath()

# Import auto-logging decorator and TDD core
# Guard these imports — they fail when run as subprocess from skills/tdd/hooks/
# The standalone main() doesn't need hook_main decorator for skill-based execution
try:
    from __lib.hook_base import hook_main
    from performance_tracker import track_hook_performance
    from tdd_core import (
        TDDApproval,
        TDDConfig,
        TDDPhase,
        TDDState,
        TestResultParser,
        cleanup_expired_states,
        debug_log,
        extract_test_file_from_command,
        find_active_tdd_cycle,
        find_pytest_json_report,
        is_test_command,
        normalize_path,
        parse_pytest_json_report,
        run_regression_tests,
    )
except ImportError:
    # Fallback for skill-based subprocess execution — no-op decorators, minimal stubs
    hook_main = lambda f: f  # type: ignore
    track_hook_performance = lambda *a, **k: lambda f: f  # type: ignore
    TDDApproval = None  # type: ignore
    TDDConfig = None  # type: ignore
    TDDPhase = None  # type: ignore
    TDDState = None  # type: ignore
    TestResultParser = None  # type: ignore
    def debug_log(*a, **k): pass
    def cleanup_expired_states(): pass
    def extract_test_file_from_command(x): return None
    def find_active_tdd_cycle(): return None
    def find_pytest_json_report(): return None
    def is_test_command(x): return False
    def normalize_path(x): return x
    def parse_pytest_json_report(x): return None
    def run_regression_tests(**k): return {}

# Phase 3 modules (ADR-20260324 Clean-Room TDD Loop v2)
try:
    from enforcement_tiers import (
        EnforcementTier,
        EnforcementTierManager,
        get_enforcement_tier,
    )
    from phase_transition_logger import (
        compute_evidence_hash,
        log_phase_transition,
    )

    PHASE3_AVAILABLE = True
    debug_log("PostToolUse_tdd_state: Phase 3 modules loaded successfully")
except ImportError as e:
    debug_log(f"PostToolUse_tdd_state: Phase 3 modules not available: {e}")
    PHASE3_AVAILABLE = False
    log_phase_transition = None  # type: ignore
    compute_evidence_hash = None  # type: ignore
    EnforcementTier = None  # type: ignore
    EnforcementTierManager = None  # type: ignore
    get_enforcement_tier = None  # type: ignore

# Import diagnostics for automatic problem detection
try:
    from tdd_diagnostics import run_diagnostics
except ImportError:
    debug_log("PostToolUse_tdd_state: tdd_diagnostics not available")
    run_diagnostics = lambda: {"timestamp": "diagnostics_unavailable"}

# Import breadcrumb tracking
try:
    from skill_guard.breadcrumb.tracker import set_breadcrumb

    BREADCRUMB_ENABLED = True
except ImportError:
    debug_log("PostToolUse_tdd_state: skill_guard not available")
    BREADCRUMB_ENABLED = False
    set_breadcrumb = lambda *args: None  # No-op fallback

# Import EvidenceManager from /code skill for evidence tracking
try:
    code_utils_path = Path("P:/.claude/skills/code_v1.0")
    if str(code_utils_path) not in sys.path:
        sys.path.insert(0, str(code_utils_path))
    from utils.evidence import EvidenceManager

    EVIDENCE_AVAILABLE = True
except ImportError:
    debug_log("PostToolUse_tdd_state: EvidenceManager not available")
    EVIDENCE_AVAILABLE = False
    EvidenceManager = None  # type: ignore


def handle_test_file_write(file_path: str, config: TDDConfig) -> dict | None:
    """Handle test file creation/modification."""
    debug_log(f"handle_test_file_write: checking {file_path}")

    if not config.is_test_file(file_path):
        debug_log(f"handle_test_file_write: {file_path} is not a test file")
        return None

    # Normalize path for consistent state keying
    normalized_path = normalize_path(file_path)
    debug_log(f"handle_test_file_write: normalized to {normalized_path}")

    # Find or create TDD state for this test file
    tdd = TDDState(normalized_path)
    state = tdd.load()
    phase = TDDPhase.from_string(state.get("phase", ""))

    debug_log(f"handle_test_file_write: current phase={phase.value}")

    # If IDLE or new, transition to AWAITING_RED
    if phase == TDDPhase.IDLE:
        state["phase"] = TDDPhase.AWAITING_RED.value
        state["test_file"] = normalized_path
        tdd.save(state)
        debug_log("handle_test_file_write: transitioned to AWAITING_RED")

        # Mark breadcrumb step complete
        set_breadcrumb("tdd", "write_failing_tests")

        return {
            "transition": "IDLE → AWAITING_RED",
            "message": f"TDD cycle started for {file_path}. Run the test to confirm RED.",
        }

    # Update test file reference if needed
    if state.get("test_file") != normalized_path:
        state["test_file"] = normalized_path
        tdd.save(state)
        debug_log("handle_test_file_write: updated test_file reference")

    return None


def handle_test_run(command: str, exit_code: int, stdout: str, stderr: str) -> dict | None:
    """Handle test command execution results."""
    debug_log(f"handle_test_run: command={command[:50]}..., exit_code={exit_code}")

    if not is_test_command(command):
        debug_log("handle_test_run: not a test command")
        return None

    # FIRST: Try to extract specific test file from command
    # This takes priority over finding any active cycle
    test_file = extract_test_file_from_command(command)

    if test_file:
        debug_log(f"handle_test_run: extracted test file {test_file}")
        tdd = TDDState(test_file)
        state = tdd.load()
        # If IDLE, transition to AWAITING_RED first
        if state.get("phase") == TDDPhase.IDLE.value:
            state["phase"] = TDDPhase.AWAITING_RED.value
            state["test_file"] = test_file
            tdd.save(state)
            debug_log(f"handle_test_run: created new cycle in AWAITING_RED for {test_file}")
    else:
        # Fallback: Find any active TDD cycle
        debug_log("handle_test_run: no test file in command, looking for active cycle")
        tdd = find_active_tdd_cycle()
        if not tdd:
            debug_log("handle_test_run: no active TDD cycle found")
            return None
        state = tdd.load()

    state = tdd.load()
    phase = TDDPhase.from_string(state.get("phase", ""))
    debug_log(f"handle_test_run: current phase={phase.value}")

    # Parse test results - try multiple sources
    result = None

    # Source 1: stdout/stderr (if available)
    if stdout or stderr:
        result = TestResultParser.parse(stdout, stderr, exit_code)
        debug_log(f"handle_test_run: parsed from stdout/stderr, verdict={result.get('verdict')}")

    # Source 2: pytest-json-report (fallback when stdout empty)
    if not result or result.get("verdict") == "unknown":
        json_report = find_pytest_json_report()
        if json_report:
            result = parse_pytest_json_report(json_report)
            debug_log(
                f"handle_test_run: parsed from pytest-json-report, verdict={result.get('verdict')}"
            )

    # Source 3: exit code only (last resort)
    if not result:
        result = {
            "exit_code": exit_code,
            "verdict": "failed" if exit_code != 0 else "unknown",
            "is_test_output": False,
            "passed": 0,
            "failed": 0,
            "errors": 0,
        }
        debug_log(
            f"handle_test_run: using exit code only fallback, verdict={result.get('verdict')}"
        )

    # Record test result
    state["last_test_result"] = result["verdict"]
    state["last_test_exit_code"] = exit_code
    state["last_test_time"] = __import__("datetime").datetime.now().isoformat()

    # Phase transitions based on result
    if phase == TDDPhase.AWAITING_RED:
        if result["verdict"] == "failed":
            state["phase"] = TDDPhase.RED_CONFIRMED.value
            TDDApproval.clear(state)  # Clear any approval on successful transition
            tdd.save(state)
            debug_log("handle_test_run: AWAITING_RED → RED_CONFIRMED")

            # Phase 3: Log phase transition (ADR-20260324)
            impl_path = (
                state.get("impl_files", [""])[0]
                if state.get("impl_files")
                else state.get("test_file", "")
            )
            log_tdd_phase_transition(
                from_phase="AWAITING_RED",
                to_phase="RED_CONFIRMED",
                impl_path=impl_path,
                test_output=stdout or stderr or "",
                metadata={"test_file": state.get("test_file", ""), "verdict": "failed"},
            )

            # Mark breadcrumb step complete
            set_breadcrumb("tdd", "confirm_tests_fail")

            # Record TDD evidence if enabled (TASK-001)
            task_id = state.get("task_id", "TDD-AUTO")
            evidence_result = record_tdd_evidence(task_id, state)
            if evidence_result and evidence_result.get("success"):
                debug_log(f"handle_test_run: Recorded RED evidence for {task_id}")

            return {
                "transition": "AWAITING_RED → RED_CONFIRMED",
                "message": "✓ RED confirmed. Now write implementation to make it pass.",
                "test_result": result,
            }
        elif result["verdict"] == "passed":
            # STRICT TDD: Test passed in AWAITING_RED means test isn't testing anything useful
            # Stay in AWAITING_RED and warn user
            tdd.save(state)
            debug_log(
                "handle_test_run: staying in AWAITING_RED (test passed - needs failing assertion)"
            )
            return {
                "transition": None,
                "message": "⚠ Test passed immediately in AWAITING_RED phase. Write a failing assertion first to verify your test catches the expected behavior.",
                "test_result": result,
            }
        else:
            tdd.save(state)
            return {
                "transition": None,
                "message": "? Could not determine test result. Check output manually.",
                "test_result": result,
            }

    elif phase == TDDPhase.RED_CONFIRMED:
        if result["verdict"] == "passed":
            state["phase"] = TDDPhase.GREEN_CONFIRMED.value
            TDDApproval.clear(state)
            tdd.save(state)
            debug_log("handle_test_run: RED_CONFIRMED → GREEN_CONFIRMED")

            # Phase 3: Log phase transition (ADR-20260324)
            impl_path = (
                state.get("impl_files", [""])[0]
                if state.get("impl_files")
                else state.get("test_file", "")
            )
            log_tdd_phase_transition(
                from_phase="RED_CONFIRMED",
                to_phase="GREEN_CONFIRMED",
                impl_path=impl_path,
                test_output=stdout or stderr or "",
                metadata={"test_file": state.get("test_file", ""), "verdict": "passed"},
            )

            # Mark breadcrumb step complete
            set_breadcrumb("tdd", "confirm_tests_pass")

            # Record TDD evidence if enabled (TASK-001)
            task_id = state.get("task_id", "TDD-AUTO")
            evidence_result = record_tdd_evidence(task_id, state)
            if evidence_result and evidence_result.get("success"):
                debug_log(f"handle_test_run: Recorded GREEN evidence for {task_id}")

            # Run regression tests after GREEN
            regression_result = run_regression_tests(
                impl_file=state.get("impl_files", [""])[0] if state.get("impl_files") else "",
                test_file=state.get("test_file", ""),
            )

            message = "✓ GREEN achieved! Ready to refactor or start new feature."
            if regression_result.get("related_count", 0) > 0 or regression_result.get(
                "integration_ran", False
            ):
                regression_msg = regression_result.get("output", "")
                if regression_msg:
                    message = f"{message}\n  [REGRESSION] {regression_msg}"

            # Warn if regression tests failed
            if not regression_result.get("passed", True):
                message += "\n  ⚠ Regression tests failed! Fix before committing."

            return {
                "transition": "RED_CONFIRMED → GREEN_CONFIRMED",
                "message": message,
                "test_result": result,
                "regression": regression_result,
            }
        else:
            tdd.save(state)
            return {
                "transition": None,
                "message": "Test still failing. Continue implementing.",
                "test_result": result,
            }

    elif phase == TDDPhase.GREEN_CONFIRMED:
        if result["verdict"] == "failed":
            # Regression! Back to RED
            state["phase"] = TDDPhase.RED_CONFIRMED.value
            tdd.save(state)

            # Phase 3: Log phase transition (ADR-20260324)
            impl_path = (
                state.get("impl_files", [""])[0]
                if state.get("impl_files")
                else state.get("test_file", "")
            )
            log_tdd_phase_transition(
                from_phase="GREEN_CONFIRMED",
                to_phase="RED_CONFIRMED",
                impl_path=impl_path,
                test_output=stdout or stderr or "",
                metadata={
                    "test_file": state.get("test_file", ""),
                    "verdict": "failed",
                    "regression": True,
                },
            )

            return {
                "transition": "GREEN_CONFIRMED → RED_CONFIRMED (regression)",
                "message": "⚠ Regression detected! Test now failing.",
                "test_result": result,
            }
        else:
            tdd.save(state)
            return {
                "transition": None,
                "message": "Tests still passing. Continue refactoring or start new cycle.",
                "test_result": result,
            }

    elif phase == TDDPhase.REFACTORING:
        if result["verdict"] == "failed":
            # Regression during refactor
            state["phase"] = TDDPhase.RED_CONFIRMED.value
            tdd.save(state)

            # Phase 3: Log phase transition (ADR-20260324)
            impl_path = (
                state.get("impl_files", [""])[0]
                if state.get("impl_files")
                else state.get("test_file", "")
            )
            log_tdd_phase_transition(
                from_phase="REFACTORING",
                to_phase="RED_CONFIRMED",
                impl_path=impl_path,
                test_output=stdout or stderr or "",
                metadata={
                    "test_file": state.get("test_file", ""),
                    "verdict": "failed",
                    "regression": True,
                    "during_refactor": True,
                },
            )

            return {
                "transition": "REFACTORING → RED_CONFIRMED (regression)",
                "message": "⚠ Refactoring broke tests! Fix before continuing.",
                "test_result": result,
            }
        else:
            # Record TDD evidence if enabled (TASK-001)
            task_id = state.get("task_id", "TDD-AUTO")
            evidence_result = record_tdd_evidence(task_id, state)
            if evidence_result and evidence_result.get("success"):
                debug_log(f"handle_test_run: Recorded REFACTOR evidence for {task_id}")

            tdd.save(state)
            return {
                "transition": None,
                "message": "Refactoring safe. Tests still pass.",
                "test_result": result,
            }

    tdd.save(state)
    return None


def handle_impl_file_write(file_path: str, config: TDDConfig) -> dict | None:
    """Handle implementation file write - track association."""
    if config.is_test_file(file_path):
        return None

    # Check if this is a source file
    path = Path(file_path)
    src_extensions = {".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs"}
    if path.suffix not in src_extensions:
        return None

    # Find active TDD cycle
    tdd = find_active_tdd_cycle()
    if not tdd:
        return None

    state = tdd.load()
    phase = TDDPhase.from_string(state.get("phase", ""))
    test_file = state.get("test_file", "")

    # Only track impl files in the same project as the test file
    # Compare project roots to avoid cross-project contamination
    from tdd_core import find_project_root

    impl_project = find_project_root(file_path)
    test_project = find_project_root(test_file) if test_file else None

    if impl_project and test_project and impl_project != test_project:
        debug_log(
            f"handle_impl_file_write: skipping {file_path} - different project (impl={impl_project}, test={test_project})"
        )
        return None

    # Track impl file during appropriate phases
    if phase in (
        TDDPhase.RED_CONFIRMED,
        TDDPhase.GREEN_CONFIRMED,
        TDDPhase.REFACTORING,
    ):
        normalized_path = normalize_path(file_path)
        impl_files = state.get("impl_files", [])
        if normalized_path not in impl_files:
            impl_files.append(normalized_path)
            state["impl_files"] = impl_files
            tdd.save(state)

            # Mark breadcrumb step complete (implementation during RED or refactor)
            if phase == TDDPhase.RED_CONFIRMED:
                set_breadcrumb("tdd", "implement_minimal_code")
            elif phase == TDDPhase.REFACTORING:
                set_breadcrumb("tdd", "refactor_code")

            return {
                "action": "impl_file_tracked",
                "message": f"Tracking {file_path} as implementation for {state.get('test_file')}",
            }

    # Transition to refactoring if GREEN and editing
    if phase == TDDPhase.GREEN_CONFIRMED:
        state["phase"] = TDDPhase.REFACTORING.value
        tdd.save(state)

        # Phase 3: Log phase transition (ADR-20260324)
        impl_path = normalize_path(file_path)
        log_tdd_phase_transition(
            from_phase="GREEN_CONFIRMED",
            to_phase="REFACTORING",
            impl_path=impl_path,
            test_output="",  # No test output at this transition
            metadata={
                "test_file": state.get("test_file", ""),
                "trigger": "impl_file_write",
            },
        )

        return {
            "transition": "GREEN_CONFIRMED → REFACTORING",
            "message": "Entering refactoring phase. Tests should stay green.",
        }

    return None


# ============================================================================
# EVIDENCE TRACKING INTEGRATION (TASK-001)
# ============================================================================


def log_tdd_phase_transition(
    from_phase: str,
    to_phase: str,
    impl_path: str,
    test_output: str = "",
    metadata: dict | None = None,
) -> None:
    """Log TDD phase transition using Phase 3 logger.

    This is a thin wrapper around phase_transition_logger.log_phase_transition()
    that handles module availability and provides session/terminal context.

    Args:
        from_phase: Source phase name
        to_phase: Target phase name
        impl_path: Path to implementation file
        test_output: Test output for evidence binding
        metadata: Additional metadata dict
    """
    if not PHASE3_AVAILABLE or log_phase_transition is None:
        debug_log(
            f"log_tdd_phase_transition: Phase 3 not available, skipping log for {from_phase} → {to_phase}"
        )
        return

    try:
        session_id = os.environ.get("CLAUDE_SESSION_ID", "")
        terminal_id = get_terminal_id()

        # Get evidence directory (phase_transition_logger adds tdd95 subdirectory)
        evidence_dir = hooks_dir / "evidence"

        transition = log_phase_transition(
            from_phase=from_phase,
            to_phase=to_phase,
            impl_path=impl_path,
            session_id=session_id,
            terminal_id=terminal_id,
            test_output=test_output,
            evidence_dir=evidence_dir,
            metadata=metadata or {},
        )

        debug_log(
            f"log_tdd_phase_transition: Logged {from_phase} → {to_phase} "
            f"(hash={transition.evidence_hash[:8]}, impl={impl_path})"
        )

    except Exception as e:
        debug_log(f"log_tdd_phase_transition: Error logging transition: {e}")


def get_phase_enforcement_tier(phase: str) -> str:
    """Get enforcement tier for a TDD phase.

    Args:
        phase: Phase name (lowercase)

    Returns:
        Tier string: "enforce", "warn", or "none"
    """
    if not PHASE3_AVAILABLE or get_enforcement_tier is None:
        return "none"  # Default to no enforcement if Phase 3 unavailable

    try:
        tier = get_enforcement_tier(phase)
        return tier.value if tier else "none"
    except Exception:
        return "none"


def is_evidence_tracking_enabled() -> bool:
    """Check if TDD evidence tracking is enabled via feature flag."""
    if not EVIDENCE_AVAILABLE:
        return False

    # Check environment variable
    return os.environ.get("TDD_EVIDENCE_TRACKING_ENABLED", "false").lower() == "true"


def get_terminal_id() -> str:
    """Get terminal ID for evidence tracking."""
    # Try environment variable first
    terminal_id = os.environ.get("CLAUDE_TERMINAL_ID")
    if terminal_id:
        return terminal_id

    # Fallback to hostname-based ID
    import socket

    hostname = socket.gethostname()
    pid = os.getpid()
    return f"{hostname}_{pid}"


def record_tdd_evidence(task_id: str, tdd_state: dict, terminal_id: str | None = None) -> dict:
    """Record TDD state snapshot as evidence.

    This function records TDD phase completion evidence without rerunning tests.
    It captures the current state of the TDD cycle as a snapshot.

    Args:
        task_id: TDD task identifier (e.g., "TDD-001")
        tdd_state: Current TDD state dictionary
        terminal_id: Terminal ID for isolation

    Returns:
        Result dict with success status and message
    """
    if not EVIDENCE_AVAILABLE or not is_evidence_tracking_enabled():
        return {"success": False, "reason": "Evidence tracking disabled"}

    if EvidenceManager is None:
        return {"success": False, "reason": "EvidenceManager not available"}

    try:
        terminal_id = terminal_id or get_terminal_id()
        phase = tdd_state.get("phase", "")
        test_file = tdd_state.get("test_file", "")
        impl_files = tdd_state.get("impl_files", [])
        last_test_result = tdd_state.get("last_test_result", "")
        last_test_exit_code = tdd_state.get("last_test_exit_code", -1)

        # Map TDD phases to EvidenceManager stages
        phase_to_stage = {
            "RED_CONFIRMED": "RED",
            "GREEN_CONFIRMED": "GREEN",
            "REFACTORING": "REFACTOR",
        }

        stage = phase_to_stage.get(phase)
        if not stage:
            return {"success": False, "reason": f"Phase {phase} not mapped to evidence stage"}

        # Create evidence manager for this terminal
        mgr = EvidenceManager(terminal_id)

        # Record evidence based on stage
        if stage == "RED":
            mgr.record_red(
                task_id,
                test_files=[test_file] if test_file else [],
                test_command=f"pytest {test_file}" if test_file else "pytest",
                failing_tests=1 if last_test_result == "failed" else 0,
            )

        elif stage == "GREEN":
            mgr.record_green(
                task_id,
                impl_files=impl_files,
                test_command=f"pytest {test_file}" if test_file else "pytest",
                passing_tests=1 if last_test_result == "passed" else 0,
            )

        elif stage == "REFACTOR":
            # REFACTOR evidence requires changes list
            mgr.record_refactor(
                task_id,
                changes=[f"Refactored during {stage} phase"],
                test_command=f"pytest {test_file}" if test_file else "pytest",
                passing_tests=1 if last_test_result == "passed" else 0,
            )

        return {"success": True, "stage": stage, "task_id": task_id, "phase": phase}

    except Exception as e:
        debug_log(f"record_tdd_evidence: Error recording evidence: {e}")
        return {"success": False, "reason": str(e)}


def generate_evidence_artifact(
    task_id: str, phase: str, evidence: dict, terminal_id: str | None = None
) -> Path | None:
    """Generate markdown evidence artifact in .evidence/ directory.

    Args:
        task_id: TDD task identifier
        phase: TDD phase (RED, GREEN, REFACTOR, VERIFY)
        evidence: Evidence dictionary with timestamp and details
        terminal_id: Terminal ID for isolation

    Returns:
        Path to generated artifact file, or None if disabled
    """
    if not EVIDENCE_AVAILABLE or not is_evidence_tracking_enabled():
        return None

    try:
        # Create .evidence directory
        skill_dir = Path(__file__).parent.parent
        evidence_dir = skill_dir / ".evidence"
        evidence_dir.mkdir(parents=True, exist_ok=True)

        # Generate artifact filename
        timestamp = evidence.get("timestamp", "")
        date_str = timestamp.split("T")[0] if timestamp else "unknown"
        artifact_name = f"{task_id}_{phase}_{date_str}.md"
        artifact_path = evidence_dir / artifact_name

        # Generate markdown content
        content = f"""# {phase} Evidence - {task_id}

**Timestamp**: {timestamp}
**Phase**: {phase}

## Evidence Details

```json
{json.dumps(evidence, indent=2)}
```

---

This artifact was automatically generated by the TDD evidence tracking system.
Task ID: {task_id}
Phase: {phase}
"""

        # Write artifact
        artifact_path.write_text(content)

        return artifact_path

    except Exception as e:
        debug_log(f"generate_evidence_artifact: Error generating artifact: {e}")
        return None


def cleanup_old_evidence(evidence_dir: Path, max_days: int = 7) -> int:
    """Clean up evidence artifacts older than max_days.

    Args:
        evidence_dir: Path to .evidence directory
        max_days: Maximum age in days (default: 7)

    Returns:
        Number of artifacts cleaned up
    """
    if not evidence_dir.exists():
        return 0

    try:
        import time

        cutoff_time = time.time() - (max_days * 24 * 60 * 60)
        cleaned_count = 0

        for artifact_path in evidence_dir.glob("*.md"):
            if artifact_path.stat().st_mtime < cutoff_time:
                artifact_path.unlink()
                cleaned_count += 1
                debug_log(f"cleanup_old_evidence: Removed old artifact {artifact_path.name}")

        return cleaned_count

    except Exception as e:
        debug_log(f"cleanup_old_evidence: Error during cleanup: {e}")
        return 0


# ============================================================================
# MAIN HOOK ENTRY POINT
# ============================================================================


@track_hook_performance("PostToolUse")
@hook_main
def main():
    """PostToolUse hook entry point - complete standalone version."""
    # Periodic cleanup
    cleanup_expired_states()

    # Read hook input from stdin
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        # No input data, exit gracefully
        print(json.dumps({}))
        return

    tool_name = input_data.get("name", "")
    tool_input = input_data.get("tool_input", {})
    tool_response = input_data.get("response", {})

    # Initialize config
    config = TDDConfig()

    result = None

    # Handle different tool types
    if tool_name in ("Edit", "Write", "MultiEdit"):
        # Get file that was written
        file_path = (
            tool_input.get("path", "")
            or tool_response.get("path", "")
            or os.environ.get("CLAUDE_TOOL_EDIT_FILE", "")
            or os.environ.get("CLAUDE_TOOL_WRITE_FILE", "")
        )
        if file_path:
            result = handle_test_file_write(file_path, config)
            if not result:
                result = handle_impl_file_write(file_path, config)

    elif tool_name == "Bash":
        # Check if this was a test command
        command = tool_input.get("command", "") or ""
        exit_code = tool_response.get("error_code", 0)  # 0 = success
        stdout = tool_response.get("stdout", "")
        stderr = tool_response.get("stderr", "")

        if command:
            result = handle_test_run(command, exit_code, stdout, stderr)

    # Output result
    if result:
        print(json.dumps(result))
    else:
        print(json.dumps({}))


if __name__ == "__main__":
    main()
