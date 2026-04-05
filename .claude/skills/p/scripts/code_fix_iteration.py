#!/usr/bin/env python3
"""
Code Fix Iteration Orchestrator

Implements the core iteration loop algorithm for the autonomous code fixing process.
This script orchestrates the iterative fixing workflow until convergence is achieved
or maximum iterations are exceeded.

Key features:
- Multi-terminal safe: Uses terminal-scoped state files
- Content-addressed state: Uses SHA256 hashes for validation
- Fresh data: Always re-computes findings, never caches
- Concurrent modification detection: Halts if findings change externally
- External modification detection: Halts if git state changes during iteration
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add lib directory to path for imports
script_dir = Path(__file__).parent
lib_dir = script_dir.parent / "lib"
sys.path.insert(0, str(lib_dir))

from file_utils import atomic_write, get_file_mtime_snapshot, sha256sum_file
from git import get_git_commit_sha


class ConcurrentModificationError(RuntimeError):
    """Raised when the findings file is modified externally during iteration."""

    pass


def iso8601_now() -> str:
    """
    Get current timestamp in ISO8601 format.

    Returns:
        ISO8601 formatted timestamp string with microseconds
    """
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def parse_duration(start_iso: str, end_iso: str) -> float:
    """
    Calculate duration in seconds between two ISO8601 timestamps.

    Args:
        start_iso: Start timestamp in ISO8601 format
        end_iso: End timestamp in ISO8601 format

    Returns:
        Duration in seconds as a float

    Raises:
        ValueError: If timestamps cannot be parsed
    """
    try:
        start = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
        end = datetime.fromisoformat(end_iso.replace("Z", "+00:00"))
        return (end - start).total_seconds()
    except ValueError as e:
        raise ValueError(f"Invalid ISO8601 timestamp format: {e}")


def load_findings(findings_file: str) -> list[dict[str, Any]]:
    """
    Load findings from a JSON file.

    Args:
        findings_file: Path to the findings JSON file

    Returns:
        List of finding dictionaries

    Raises:
        FileNotFoundError: If findings file doesn't exist
        json.JSONDecodeError: If findings file is not valid JSON
        ValueError: If findings are not in expected format
    """
    with open(findings_file, encoding='utf-8') as f:
        findings = json.load(f)

    # Validate it's a list
    if not isinstance(findings, list):
        raise ValueError(f"Findings file must contain a list, got {type(findings).__name__}")

    return findings


def count_medium_plus(findings: list[dict[str, Any]]) -> int:
    """
    Count findings with MEDIUM, HIGH, or CRITICAL severity.

    Args:
        findings: List of finding dictionaries

    Returns:
        Count of findings with medium or higher severity
    """
    count = 0
    for finding in findings:
        severity = finding.get("severity", "").upper()
        if severity in ["MEDIUM", "HIGH", "CRITICAL"]:
            count += 1
    return count


def count_total_fixes(generations: list[dict[str, Any]]) -> int:
    """
    Count total fixes applied across all generations.

    Args:
        generations: List of generation dictionaries from state

    Returns:
        Total number of fixes applied
    """
    total = 0
    for generation in generations:
        fixes = generation.get("fixes_applied", [])
        if isinstance(fixes, list):
            total += len(fixes)
    return total


def run_code_fix_workflow(findings: list[dict[str, Any]]) -> list[str]:
    """
    Run the /code Fix workflow on the given findings.

    QUAL-004: This function is NOT YET IMPLEMENTED.
    The code fix iteration orchestrator is currently experimental/prototype code.

    Args:
        findings: List of finding dictionaries to fix

    Returns:
        List of fix descriptions that were applied

    Raises:
        NotImplementedError: This function is not yet implemented
    """
    raise NotImplementedError(
        "run_code_fix_workflow() is not yet implemented. "
        "The code fix iteration orchestrator is experimental code. "
        "Use manual /code Fix workflow instead."
    )


def run_p2_review() -> str:
    """
    Run the P2 adversarial review to generate new findings.

    QUAL-004: This function is NOT YET IMPLEMENTED.
    The code fix iteration orchestrator is currently experimental/prototype code.

    Returns:
        Path to the new findings JSON file

    Raises:
        NotImplementedError: This function is not yet implemented
    """
    raise NotImplementedError(
        "run_p2_review() is not yet implemented. "
        "The code fix iteration orchestrator is experimental code. "
        "Use manual /p --phase=2 workflow instead."
    )


def code_fix_iteration_loop(
    initial_findings_file: str,
    terminal_id: str,
    project_root: str,
    max_iterations: int = 5
) -> dict[str, Any]:
    """
    Iteratively fix findings until no MEDIUM+ issues remain.

    Multi-terminal safe: Uses terminal-scoped state file.
    No TTL: Uses content-addressed state (SHA256 hashes).
    Fresh data: Always re-computes findings, never caches.

    Args:
        initial_findings_file: Path to initial findings JSON file
        terminal_id: Unique identifier for the terminal session
        project_root: Absolute path to project root directory
        max_iterations: Maximum number of iterations (default: 5)

    Returns:
        Complete state dictionary with all generations and final result

    Raises:
        ConcurrentModificationError: If findings file is modified externally
        FileNotFoundError: If findings file doesn't exist
        ValueError: If findings are invalid
    """
    # Ensure project root is absolute path
    project_root = str(Path(project_root).resolve())

    # State file path (terminal-scoped)
    state_file = Path(project_root) / ".claude" / "state" / f"code-fix-{terminal_id}.json"

    # Ensure state directory exists
    state_file.parent.mkdir(parents=True, exist_ok=True)

    # Initialize state
    print(f"[Initialization] Loading findings from {initial_findings_file}")
    initial_findings = load_findings(initial_findings_file)
    initial_hash = sha256sum_file(initial_findings_file)

    state = {
        "version": "1.0.0",
        "terminal_id": terminal_id,
        "project_root": project_root,
        "status": "in_progress",
        "initial_findings": {
            "file": str(Path(initial_findings_file).resolve()),
            "sha256": initial_hash,
            "total_count": len(initial_findings),
            "medium_plus_count": count_medium_plus(initial_findings),
            "collected_at": iso8601_now()
        },
        "generations": []
    }

    # Save initial state
    atomic_write(str(state_file), json.dumps(state, indent=2))

    print(f"[Initialization] Initial findings: {len(initial_findings)} total, "
          f"{state['initial_findings']['medium_plus_count']} medium+")

    # Main iteration loop
    iteration = 0
    while iteration < max_iterations:
        iteration += 1
        print(f"\n[Iteration {iteration}] Starting...")

        # SAFETY CHECK: Verify we're still working on same findings
        # Use cached hash from initial state to avoid re-reading file (PERF-001 fix)
        current_findings_hash = state["initial_findings"]["sha256"]
        if current_findings_hash != initial_hash:
            raise ConcurrentModificationError(
                f"Findings file modified externally! "
                f"Expected {initial_hash[:8]}..., got {current_findings_hash[:8]}..."
            )

        # Get current findings (from previous iteration or initial)
        if iteration == 1:
            current_findings_file = state["initial_findings"]["file"]
        else:
            current_findings_file = state["generations"][-1]["findings_file"]

        current_findings = load_findings(current_findings_file)
        medium_plus_count = count_medium_plus(current_findings)

        print(f"[Iteration {iteration}] Current findings: {medium_plus_count} medium+ issues")

        # EXIT CONDITION: No MEDIUM+ issues
        if medium_plus_count == 0:
            state["status"] = "completed"
            state["final_result"] = {
                "status": "success",
                "total_iterations": iteration - 1,
                "total_fixes_applied": count_total_fixes(state["generations"]),
                "convergence_achieved": True,
                "completed_at": iso8601_now()
            }
            atomic_write(str(state_file), json.dumps(state, indent=2))
            print(f"\n✅ Convergence achieved after {iteration - 1} iteration(s)")
            break

        # SNAPSHOT: Record code state before fixes
        print(f"[Iteration {iteration}] Recording code snapshot...")
        code_snapshot = {
            "git_commit": get_git_commit_sha(cwd=project_root),
            "file_mtime": get_file_mtime_snapshot(root_dir=project_root)
        }

        generation = {
            "iteration": iteration,
            "findings_sha256": sha256sum_file(current_findings_file),
            "findings_file": str(Path(current_findings_file).resolve()),
            "medium_plus_count": medium_plus_count,
            "code_snapshot": code_snapshot,
            "started_at": iso8601_now(),
            "fixes_applied": []
        }

        # FIX: Run /code Fix workflow
        print(f"[Iteration {iteration}] Running /code Fix workflow...")
        try:
            fixes_applied = run_code_fix_workflow(current_findings)
            generation["fixes_applied"] = fixes_applied
        except Exception as e:
            print(f"[Iteration {iteration}] ⚠️  Fix workflow failed: {e}")
            state["status"] = "halted"
            state["final_result"] = {
                "status": "failed",
                "total_iterations": iteration - 1,
                "total_fixes_applied": count_total_fixes(state["generations"]),
                "convergence_achieved": False,
                "completed_at": iso8601_now(),
                "error": str(e)
            }
            atomic_write(str(state_file), json.dumps(state, indent=2))
            break

        # REVIEW: Re-run P2 adversarial review
        print(f"[Iteration {iteration}] Re-running P2 review...")
        try:
            new_findings_file = run_p2_review()
        except Exception as e:
            print(f"[Iteration {iteration}] ⚠️  P2 review failed: {e}")
            state["status"] = "halted"
            state["final_result"] = {
                "status": "failed",
                "total_iterations": iteration - 1,
                "total_fixes_applied": count_total_fixes(state["generations"]),
                "convergence_achieved": False,
                "completed_at": iso8601_now(),
                "error": str(e)
            }
            atomic_write(str(state_file), json.dumps(state, indent=2))
            break

        # VALIDATE: Check for external modifications (PERF-002: Only check git commit SHA, skip expensive glob)
        print(f"[Iteration {iteration}] Validating code state...")
        new_git_commit = get_git_commit_sha(cwd=project_root)

        if new_git_commit != code_snapshot["git_commit"]:
            print("⚠️  WARNING: Git commit changed during iteration")
            print("External modifications detected, halting for safety")
            state["status"] = "halted"
            state["final_result"] = {
                "status": "user_halted",
                "total_iterations": iteration,
                "total_fixes_applied": count_total_fixes(state["generations"]) + len(fixes_applied),
                "convergence_achieved": False,
                "completed_at": iso8601_now(),
                "reason": "external_modification"
            }
            atomic_write(str(state_file), json.dumps(state, indent=2))
            break

        generation["completed_at"] = iso8601_now()
        generation["duration_seconds"] = parse_duration(
            generation["started_at"],
            generation["completed_at"]
        )
        generation["findings_file"] = str(Path(new_findings_file).resolve())
        # Preserve initial file_mtime snapshot but update git commit SHA (PERF-002: skip redundant glob)
        generation["code_snapshot"] = {
            "git_commit": new_git_commit,
            "file_mtime": code_snapshot["file_mtime"]
        }

        state["generations"].append(generation)
        atomic_write(str(state_file), json.dumps(state, indent=2))

        print(f"[Iteration {iteration}] Complete: {len(fixes_applied)} fixes applied, "
              f"duration: {generation['duration_seconds']:.2f}s")

    # MAX ITERATIONS EXCEEDED
    if iteration >= max_iterations and state["status"] == "in_progress":
        print(f"\n⚠️  Halted: Max iterations ({max_iterations}) exceeded")
        state["status"] = "halted"
        state["final_result"] = {
            "status": "max_iterations_reached",
            "total_iterations": max_iterations,
            "total_fixes_applied": count_total_fixes(state["generations"]),
            "convergence_achieved": False,
            "completed_at": iso8601_now()
        }
        atomic_write(str(state_file), json.dumps(state, indent=2))

    return state


def main():
    """CLI interface for the iteration orchestrator."""
    parser = argparse.ArgumentParser(
        description="Code Fix Iteration Orchestrator - "
                    "Iteratively fix findings until convergence",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python code_fix_iteration.py --findings findings.json --terminal term-001
  python code_fix_iteration.py --findings findings.json --terminal term-001 --max-iterations 3
  python code_fix_iteration.py --findings findings.json --terminal term-001 --project-root /path/to/project
        """
    )

    parser.add_argument(
        "--findings",
        required=True,
        help="Path to initial findings JSON file"
    )

    parser.add_argument(
        "--terminal",
        required=True,
        help="Terminal ID for state file scoping"
    )

    parser.add_argument(
        "--max-iterations",
        type=int,
        default=5,
        help="Maximum number of iterations (default: 5)"
    )

    parser.add_argument(
        "--project-root",
        default=os.getcwd(),
        help="Project root path (default: current directory)"
    )

    args = parser.parse_args()

    # Validate arguments
    if not os.path.exists(args.findings):
        print(f"Error: Findings file not found: {args.findings}", file=sys.stderr)
        sys.exit(1)

    if args.max_iterations < 1 or args.max_iterations > 5:
        print("Error: max-iterations must be between 1 and 5", file=sys.stderr)
        sys.exit(1)

    if not os.path.isdir(args.project_root):
        print(f"Error: Project root not found: {args.project_root}", file=sys.stderr)
        sys.exit(1)

    try:
        # Run the iteration loop
        print("=" * 70)
        print("Code Fix Iteration Orchestrator")
        print("=" * 70)
        print(f"Findings: {args.findings}")
        print(f"Terminal: {args.terminal}")
        print(f"Project Root: {args.project_root}")
        print(f"Max Iterations: {args.max_iterations}")
        print("=" * 70)

        state = code_fix_iteration_loop(
            initial_findings_file=args.findings,
            terminal_id=args.terminal,
            project_root=args.project_root,
            max_iterations=args.max_iterations
        )

        # Print summary
        print("\n" + "=" * 70)
        print("Iteration Summary")
        print("=" * 70)
        print(f"Status: {state['status']}")
        if "final_result" in state:
            result = state["final_result"]
            print(f"Total Iterations: {result['total_iterations']}")
            print(f"Total Fixes Applied: {result['total_fixes_applied']}")
            print(f"Convergence Achieved: {result['convergence_achieved']}")
        print(f"Generations: {len(state['generations'])}")
        print("=" * 70)

    except ConcurrentModificationError as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
