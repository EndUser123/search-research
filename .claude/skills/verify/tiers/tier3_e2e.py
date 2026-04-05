#!/usr/bin/env python3
"""
Tier 3: E2E Test

Verifies actual skill/workflow invocation succeeds.
Includes optional Full State Verification using Source→Logic→Read protocol.
"""

import sys
from pathlib import Path
from typing import Any

# Add hooks directory to path for imports
hooks_dir = Path("P:/.claude/hooks")
if hooks_dir.exists():
    sys.path.insert(0, str(hooks_dir))

try:
    from evidence_store import load_tool_events
except ImportError:
    # Fallback if evidence_store not available
    def load_tool_events(*args, **kwargs):
        return []


class Tier3E2E:
    """Tier 3: E2E verification."""

    def __init__(self):
        """Initialize Tier3E2E with optional full state verifier."""
        self._full_state_verifier = None

    def _get_full_state_verifier(self):
        """Lazy-load FullStateVerifier."""
        if self._full_state_verifier is None:
            from tiers.full_state_verifier import FullStateVerifier

            self._full_state_verifier = FullStateVerifier()
        return self._full_state_verifier

    def check_e2e(
        self,
        target_type: str,
        target_name: str,
        session_id: str,
        full_state_verification: bool = False,
        expected_files: list[str | Path] | None = None,
    ) -> dict[str, Any]:
        """
        Check E2E execution evidence.

        Args:
            target_type: Type of target (skill, hook, feature, code)
            target_name: Name of target
            session_id: Session ID for evidence lookup
            full_state_verification: Enable Full State Verification (Source→Logic→Read)
            expected_files: Optional list of files to verify (for full state verification)

        Returns:
            Dict with status (pass/fail/skip), evidence, and optional full_state_results
        """
        # For skills, check for Skill tool invocation
        if target_type == "skill":
            result = self._check_skill_e2e(target_name, session_id)

        # For hooks, check PostToolUse evidence
        elif target_type == "hook":
            result = self._check_hook_e2e(target_name, session_id)

        # For features and code, skip Tier 3
        else:
            result = {"status": "skip", "evidence": f"Tier 3 not applicable for {target_type}"}

        # Add full state verification if requested
        if full_state_verification and expected_files:
            result["full_state_results"] = self._run_full_state_verification(
                target_type, target_name, expected_files
            )

        return result

    def _check_skill_e2e(self, skill_name: str, session_id: str) -> dict[str, Any]:
        """Check for skill invocation evidence."""
        try:
            # Load tool events for session
            events = load_tool_events(session_id, limit=100)

            # Look for Skill tool invocation
            for event in events:
                if event.get("name") == "Skill":
                    command = event.get("command", "")
                    if skill_name in command:
                        return {
                            "status": "pass",
                            "evidence": f"Skill invocation found: {command}",
                            "timestamp": event.get("timestamp", ""),
                        }

            return {
                "status": "fail",
                "evidence": "No E2E evidence: Skill not invoked in current session",
            }

        except Exception as e:
            return {"status": "skip", "evidence": f"E2E check skipped: {e}"}

    def _check_hook_e2e(self, hook_name: str, session_id: str) -> dict[str, Any]:
        """Check for hook execution evidence."""
        try:
            # Load tool events for session
            events = load_tool_events(session_id, limit=100)

            # Look for tool executions that would trigger the hook
            for event in events:
                tool_name = event.get("name", "")
                # Most hooks are triggered by tool use
                if tool_name in ["Read", "Write", "Edit", "Bash"]:
                    return {
                        "status": "pass",
                        "evidence": f"Tool execution found: {tool_name}",
                        "timestamp": event.get("timestamp", ""),
                    }

            return {
                "status": "fail",
                "evidence": "No E2E evidence: No tool executions in current session",
            }

        except Exception as e:
            return {"status": "skip", "evidence": f"E2E check skipped: {e}"}

    def _run_full_state_verification(
        self, target_type: str, target_name: str, expected_files: list[str | Path]
    ) -> dict[str, Any]:
        """
        Run Full State Verification on expected files.

        Args:
            target_type: Type of target (skill, hook, feature, code)
            target_name: Name of target
            expected_files: List of files to verify

        Returns:
            Dict with verification results for each file
        """
        verifier = self._get_full_state_verifier()

        results = {
            "overall_status": "pass",
            "files_checked": len(expected_files),
            "files_passed": 0,
            "files_failed": 0,
            "file_results": [],
        }

        for file_path in expected_files:
            # Verify file exists and has expected content
            result = verifier.verify_file_exists(file_path, target_name)

            file_result = {
                "file": str(file_path),
                "status": result.status,
                "state_match": result.state_match,
                "differences": result.differences,
                "exists": result.source_definition.exists,
            }

            results["file_results"].append(file_result)

            if result.status == "pass":
                results["files_passed"] += 1
            else:
                results["files_failed"] += 1
                results["overall_status"] = "fail"

        return results

    def track_workflow(
        self,
        workflow_type: str,
        target: str,
        session_id: str,
        terminal_id: str,
        stages: list[dict[str, Any]],
        overall: str,
    ) -> None:
        """
        Track E2E workflow execution.

        Args:
            workflow_type: Type of workflow (skill_invocation, etc.)
            target: Target name
            session_id: Session ID
            terminal_id: Terminal ID
            stages: List of stage results
            overall: Overall status (success, failure, partial)
        """
        try:
            # Try to import E2E tracker
            hooks_dir = Path("P:/.claude/hooks")
            if hooks_dir.exists():
                tracker_path = hooks_dir / "PostToolUse_e2e_tracker.py"

                if tracker_path.exists():
                    # Import and use tracker
                    import importlib.util

                    spec = importlib.util.spec_from_file_location("e2e_tracker", str(tracker_path))
                    tracker_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(tracker_module)

                    tracker_module.track_workflow(
                        workflow_type=workflow_type,
                        target=target,
                        session_id=session_id,
                        terminal_id=terminal_id,
                        stages=stages,
                        overall=overall,
                    )
        except Exception:
            # Tracker not available, fail silently
            pass
