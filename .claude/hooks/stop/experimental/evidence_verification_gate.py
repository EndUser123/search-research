#!/usr/bin/env python3
"""
Evidence Verification Gate - Final gate before response completion.

CLASSIFICATION: Archive without integration

REASON: Wrong coupling direction. This gate imports EvidenceManager from the
/code skill's utils/evidence.py. Stop.py should NOT import from skills — the
direction should be skills importing from the framework. Additionally, this gate
has a non-standard process() signature (expects conversation + final_response)
rather than the standard run(data) -> dict|None protocol used by Stop.py gates.

PREVENTS: Implementation claims without file existence verification.
Integrates with EvidenceManager.mark_done() for file validation.

BLOCKING: Fails when implementation files missing from disk.

ADVISORY: Logs pytest failures but doesn't block on them.

ORIGIN: Stop_router.py — standalone parallel pipeline, never registered

INTEGRATION PATH: If EvidenceManager integration is needed, it should be
re-architected so that the /code skill writes evidence markers that Stop.py
reads, rather than Stop.py importing from the /code skill.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

# Add skills/code to path for EvidenceManager import
skills_code_path = Path(__file__).resolve().parent.parent.parent / "skills" / "code"
sys.path.insert(0, str(skills_code_path.resolve()))

from utils.evidence import EvidenceManager


class EvidenceVerificationGate:
    """Final verification gate for implementation file existence."""

    env_var = "EVIDENCE_VERIFICATION_GATE_ENABLED"
    default_enabled = True

    def _extract_task_id(self, conversation: dict) -> str | None:
        """Extract task_id from conversation context.

        Sources (in priority order):
        1. Environment variable: EVIDENCE_TASK_ID (set by /code skill)
        2. Conversation metadata: conversation.get("task_id")
        3. Scan ledger for single in-progress task (expensive fallback)

        Returns None if no task_id can be determined (gate passes).
        """
        # Priority 1: Environment variable (integration contract with /code skill)
        task_id = os.getenv("EVIDENCE_TASK_ID")
        if task_id:
            return task_id

        # Priority 2: Conversation metadata
        if conversation:
            task_id = conversation.get("task_id")
            if task_id:
                return task_id

        # Priority 3: Scan ledger for single in-progress task (fallback)
        # This is expensive but ensures gate works even without explicit task_id
        # Deferred: Can be implemented when needed
        return None

    def _run_python_tests(self, working_dir: str) -> tuple[bool, str]:
        """Run Python tests if pytest is available.

        Returns:
            (success, error_message)
        """
        # Check for pytest configuration
        if (
            not (Path(working_dir) / "pyproject.toml").exists()
            and not (Path(working_dir) / "pytest.ini").exists()
            and not (Path(working_dir) / "setup.cfg").exists()
        ):
            return True, ""  # No pytest configured, skip

        try:
            # Run pytest with capture_output
            result = subprocess.run(
                ["pytest", "-q"],
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=60,  # 1 minute timeout
            )

            if result.returncode != 0:
                error_msg = result.stdout or result.stderr
                return False, f"pytest failed: {error_msg[:200]}"

            return True, ""

        except subprocess.TimeoutExpired:
            return False, "pytest timed out after 60 seconds"
        except FileNotFoundError:
            # pytest not installed, skip gracefully
            return True, ""
        except Exception as e:
            # Other errors, log but don't block
            return True, f"pytest error (non-blocking): {str(e)[:100]}"

    def process(self, conversation: dict, final_response: str) -> dict:
        """Process verification gate.

        Args:
            conversation: Conversation metadata dict
            final_response: The final response about to be sent

        Returns:
            dict with 'passed' (bool) and optionally 'reason' (str) if failed
        """
        # Extract task_id
        task_id = self._extract_task_id(conversation)
        if not task_id:
            # No task_id to verify, pass through
            return {"passed": True}

        errors = []

        # 1. Run Python tests (advisory, logs failures but doesn't block)
        working_dir = os.getcwd()
        tests_passed, test_error = self._run_python_tests(working_dir)
        if not tests_passed:
            errors.append(test_error)

        # 2. Verify implementation vs evidence (BLOCKING)
        try:
            # Get terminal_id from environment or use default
            terminal_id = os.getenv("CLAUDE_TERMINAL_ID", "verification_gate")

            # Create EvidenceManager instance
            mgr = EvidenceManager(terminal_id)

            # Try to mark done - this validates file existence
            # Note: This will raise ValueError if:
            #   - Evidence incomplete (missing RED/GREEN/REFACTOR/VERIFY)
            #   - Implementation files missing from disk
            try:
                mgr.mark_done(task_id)
                # If we get here, all validations passed
            except ValueError as e:
                # Extract specific error type
                error_msg = str(e)
                if "Implementation files missing" in error_msg:
                    errors.append(f"File verification failed: {error_msg}")
                elif "missing evidence" in error_msg.lower():
                    errors.append(f"Evidence verification failed: {error_msg}")
                else:
                    errors.append(f"Verification failed: {error_msg}")

        except Exception as e:
            # EvidenceManager initialization or other errors
            errors.append(f"Verification system error: {str(e)}")

        # Determine result
        if errors:
            # Separate blocking from advisory errors
            blocking_errors = [
                e
                for e in errors
                if "File verification failed" in e
                or "Evidence verification failed" in e
                or "not found in ledger" in e
            ]
            advisory_errors = [e for e in errors if e not in blocking_errors]

            if blocking_errors:
                return {
                    "passed": False,
                    "reason": "VERIFICATION FAILED (blocking): " + "; ".join(blocking_errors),
                }

            if advisory_errors:
                # Log advisory errors but don't block
                print(
                    f"[EvidenceVerificationGate] Advisory: {'; '.join(advisory_errors)}",
                    file=sys.stderr,
                )
                return {"passed": True}

        return {"passed": True}


# Hook entry point
def process(conversation: dict, final_response: str) -> dict:
    """Entry point for stop hook."""
    gate = EvidenceVerificationGate()
    return gate.process(conversation, final_response)


if __name__ == "__main__":
    # Simple test

    # Mock conversation
    conv = {"task_id": "TASK-001"}

    # Test with no task_id
    result = process({}, "test response")
    print(f"No task_id test: {result}")

    # Test with task_id (will fail without ledger setup)
    result = process(conv, "test response")
    print(f"With task_id test: {result}")
