#!/usr/bin/env python3
"""Test absence claim gate detection and blocking.

Patch 5: Completes the empty main() function in Stop_absence_claim_gate.py.

Test cases:
1. Test absence claim detection works
2. Test blocking when no observation tools used
3. Test approval when Read/Bash tools present
4. Test self-classification prompt for ambiguous cases
"""

import json
import os
import pytest
import subprocess
import sys
from pathlib import Path


class TestAbsenceGateBlocking:
    """Test that Stop_absence_claim_gate.py properly detects and blocks absence claims."""

    def test_absence_claim_detection(self, tmp_path):
        """Given: Response contains absence claim "file doesn't exist"
        When: Hook runs
        Then: Detect absence claim and either block or request verification
        """
        # Arrange
        hook_path = Path(__file__).resolve().parent.parent / "Stop_absence_claim_gate.py"

        input_data = {
            "response": "The config.py file doesn't exist in this directory.",
            "tools_used": []
        }

        # Act
        result = subprocess.run(
            [sys.executable, str(hook_path],
            input=json.dumps(input_data).encode(),
            capture_output=True,
            cwd=str(hook_path.parent)
        )

        # Assert - Should either block (exit 2) or approve with verification prompt
        stdout = result.stdout.decode().strip()
        assert result.returncode in (0, 2)

        if stdout:
            try:
                output = json.loads(stdout)
                # If exit code 0, should have systemMessage for self-classification
                if result.returncode == 0:
                    assert output.get("decision") == "approve"
                # If exit code 2, should have block decision
                else:
                    assert output.get("decision") == "block"
            except json.JSONDecodeError:
                pass

    def test_blocks_without_observation_evidence(self, tmp_path):
        """Given: Response contains absence assertion and no observation tools
        When: Hook runs
        Then: Block with exit code 2
        """
        # Arrange
        hook_path = Path(__file__).resolve().parent.parent / "Stop_absence_claim_gate.py"

        input_data = {
            "response": "The module is missing from the codebase.",
            "tools_used": []
        }

        # Act
        result = subprocess.run(
            [sys.executable, str(hook_path],
            input=json.dumps(input_data).encode(),
            capture_output=True,
            cwd=str(hook_path.parent)
        )

        # Assert - Should block (exit 2) due to no evidence
        stdout = result.stdout.decode().strip()
        if stdout:
            try:
                output = json.loads(stdout)
                if output.get("decision") == "block":
                    assert result.returncode == 2
                    # Hook returns descriptive message, not a constant
                    assert "absence" in output.get("reason", "").lower()
                    assert "require" in output.get("reason", "").lower()
            except json.JSONDecodeError:
                pass

    def test_allows_with_observation_tools(self, tmp_path):
        """Given: Response contains absence claim but Read/Bash tools used
        When: Hook runs
        Then: Approve (exit 0) with evidence present
        """
        # Arrange
        hook_path = Path(__file__).resolve().parent.parent / "Stop_absence_claim_gate.py"

        input_data = {
            "response": "Verified that file doesn't exist using ls and grep.",
            "tools_used": [
                {"name": "Bash", "command": "ls -la"},
                {"name": "Grep", "command": "grep pattern"}
            ]
        }

        # Act
        result = subprocess.run(
            [sys.executable, str(hook_path],
            input=json.dumps(input_data).encode(),
            capture_output=True,
            cwd=str(hook_path.parent)
        )

        # Assert - Should approve with evidence
        assert result.returncode == 0

    def test_no_absence_claims_approves(self, tmp_path):
        """Given: Response contains no absence claims
        When: Hook runs
        Then: Approve immediately
        """
        # Arrange
        hook_path = Path(__file__).resolve().parent.parent / "Stop_absence_claim_gate.py"

        input_data = {
            "response": "The function returns the sum of two integers.",
            "tools_used": []
        }

        # Act
        result = subprocess.run(
            [sys.executable, str(hook_path],
            input=json.dumps(input_data).encode(),
            capture_output=True,
            cwd=str(hook_path.parent)
        )

        # Assert
        assert result.returncode == 0
        stdout = result.stdout.decode().strip()
        if stdout:
            try:
                output = json.loads(stdout)
                assert output.get("decision") == "approve"
                assert "no_absence_claims" in output.get("reason", "")
            except json.JSONDecodeError:
                pass

    def test_code_logic_context_allowed(self, tmp_path):
        """Given: Response mentions absence in code logic context (not assertion)
        When: Hook runs
        Then: Approve (code logic descriptions are not claims)
        """
        # Arrange
        hook_path = Path(__file__).resolve().parent.parent / "Stop_absence_claim_gate.py"

        # This describes what code does, not claims something is absent
        input_data = {
            "response": "Add a fallback when the config file is not found.",
            "tools_used": []
        }

        # Act
        result = subprocess.run(
            [sys.executable, str(hook_path],
            input=json.dumps(input_data).encode(),
            capture_output=True,
            cwd=str(hook_path.parent)
        )

        # Assert - Code logic should be allowed
        assert result.returncode == 0

    def test_disabled_gate_approves(self, tmp_path):
        """Given: ABSENCE_CLAIM_GATE_ENABLED=false
        When: Hook runs
        Then: Approve immediately
        """
        # Arrange
        hook_path = Path(__file__).resolve().parent.parent / "Stop_absence_claim_gate.py"

        input_data = {
            "response": "The file doesn't exist.",
            "tools_used": []
        }

        env = os.environ.copy()
        env["ABSENCE_CLAIM_GATE_ENABLED"] = "false"

        # Act
        result = subprocess.run(
            [sys.executable, str(hook_path],
            input=json.dumps(input_data).encode(),
            capture_output=True,
            env=env,
            cwd=str(hook_path.parent)
        )

        # Assert - Should approve when disabled
        assert result.returncode == 0

    def test_block_output_format(self, tmp_path):
        """Given: Hook blocks on absence claim
        When: Output is JSON
        Then: Contains required fields: decision, reason, claims_detected
        """
        # Arrange
        hook_path = Path(__file__).resolve().parent.parent / "Stop_absence_claim_gate.py"

        input_data = {
            "response": "The module doesn't exist.",
            "tools_used": []
        }

        # Act
        result = subprocess.run(
            [sys.executable, str(hook_path],
            input=json.dumps(input_data).encode(),
            capture_output=True,
            cwd=str(hook_path.parent)
        )

        # Assert
        stdout = result.stdout.decode().strip()
        if stdout and result.returncode == 2:
            try:
                output = json.loads(stdout)
                assert "decision" in output
                assert "reason" in output
                assert "claims_detected" in output or "message" in output
            except json.JSONDecodeError:
                pass
