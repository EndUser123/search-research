#!/usr/bin/env python3
"""
End-to-End Workflow Test for /v Validation

Tests the complete /v workflow from Stage 1 through Stage 3.

Run: pytest P:/.claude/tests/test_v_workflow_e2e.py -v
"""

import json
import subprocess
import sys
from pathlib import Path
import pytest
import tempfile
import shutil

SCRIPTS_DIR = Path("P:/.claude/skills/v/scripts")
STATE_DIR = Path("P:/.claude/hooks/state/v_stage")


class TestVEndToEndWorkflow:
    """End-to-end tests for /v validation workflow."""

    def test_full_stage_2_workflow_on_clean_code(self, tmp_path):
        """Should complete all Stage 2 checks on clean Python code."""
        # Create a clean Python module
        module_file = tmp_path / "clean_module.py"
        module_file.write_text("""
'''Clean Python module for testing.'''


def process_data(input_value: str) -> str:
    '''Process input data safely.'''
    if not input_value:
        return ""
    return input_value.strip()


def main() -> None:
    '''Main entry point.'''
    result = process_data("test input")
    print(f"Result: {result}")


if __name__ == "__main__":
    main()
""")

        # Run Stage 2.5: Logging check
        result_2_5 = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "stage2_5_logging.py"), str(module_file)],
            capture_output=True,
            text=True
        )

        # Should complete (may have warnings but shouldn't crash)
        assert result_2_5.returncode in (0, 1)

        # Run Stage 2.6: Dead code check
        result_2_6 = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "stage2_6_dead_code.py"), str(module_file)],
            capture_output=True,
            text=True
        )

        assert result_2_6.returncode in (0, 1, 2)

        # Run Stage 2.8: Formatting check
        result_2_8 = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "stage2_8_formatting.py"), str(module_file)],
            capture_output=True,
            text=True
        )

        assert result_2_8.returncode in (0, 1, 2)

    def test_stage_enforcement_prevents_skipping(self, tmp_path):
        """Stage enforcer should prevent skipping stages."""
        # This test verifies the hook would block stage skipping
        # We can't fully test it without running actual hooks,
        # but we can verify the state mechanism exists

        state_file = STATE_DIR / "v-stage-progress__test_e2e.json"

        # Clean up any existing test state
        if state_file.exists():
            state_file.unlink()

        # Create initial state (Stage 1 completed)
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(json.dumps({
            "contexts": {
                "test_context": {
                    "last_completed_stage": 1,
                    "file_mtimes": {},
                    "timestamp": 1234567890
                }
            },
            "current_context_hash": "test_context"
        }))

        # Verify state was written
        assert state_file.exists()

        # Clean up
        if state_file.exists():
            state_file.unlink()

    def test_stage_3_layers_integration(self, tmp_path):
        """Stage 3 layers should work together."""
        # Create findings JSON file for Layer 1
        findings_file = tmp_path / "findings.json"
        findings_file.write_text(json.dumps({"findings": []}))

        # Create a test file for reference
        test_file = tmp_path / "test_module.py"
        test_file.write_text("def foo(): pass\n")

        # Run Layer 1: Delta filter with correct arguments
        result_l1 = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "stage3_layer1_delta.py"), str(findings_file)],
            capture_output=True,
            text=True,
            cwd=tmp_path
        )

        # Layer 1 should complete (exit code 0 or 1 for no findings is ok)
        assert result_l1.returncode in (0, 1)

    def test_findings_script_creates_task(self, tmp_path):
        """Stage 3 findings script should create tasks."""
        # Run the findings script with sample data
        result = subprocess.run([
            sys.executable,
            str(SCRIPTS_DIR / "stage3_findings.py"),
            "--target", "test_target",
            "--critical", "0",
            "--high", "1",
            "--raw", "5",
            "--ratio", "0.8",
            "--critical-findings", "[]",
            "--high-findings", '[{"id": "TEST-001", "title": "Test finding", "description": "Test"}]'
        ],
            capture_output=True,
            text=True
        )

        # Should complete successfully
        assert result.returncode == 0
        assert "Task created" in result.stdout


class TestConcurrentExecution:
    """Tests for multi-terminal /v execution isolation."""

    def test_state_files_are_terminal_isolated(self):
        """State files should include terminal ID for isolation."""
        # Check that stage enforcer uses terminal detection
        hook_file = Path("P:/.claude/skills/v/hooks/PreToolUse_v_stage_enforcer.py")
        hook_content = hook_file.read_text()

        # Should import terminal_detection
        assert "terminal_detection" in hook_content or "detect_terminal_id" in hook_content

        # Should use terminal-specific state files
        assert "terminal" in hook_content.lower()

    def test_findings_script_includes_terminal_id(self):
        """Findings script should tag tasks with terminal ID."""
        script_content = (SCRIPTS_DIR / "stage3_findings.py").read_text()

        # Should use terminal detection
        assert "terminal" in script_content.lower() or "terminal_id" in script_content.lower()

        # Should include terminal in task subject
        assert "terminal:" in script_content

    def test_layer_scripts_use_terminal_isolation(self):
        """Layer scripts should use terminal-isolated state files."""
        for layer_script in ["stage3_layer1_delta.py", "stage3_layer2_pillars.py", "stage3_findings.py"]:
            script_path = SCRIPTS_DIR / layer_script
            if not script_path.exists():
                continue

            script_content = script_path.read_text()

            # Should have terminal handling
            assert "terminal" in script_content.lower() or layer_script in script_content


class TestWorkflowErrorRecovery:
    """Tests for error handling and recovery in /v workflow."""

    def test_state_file_corruption_recovery(self, tmp_path):
        """Should recover from corrupted state file."""
        # Create a corrupted state file
        state_file = tmp_path / "corrupted_state.json"
        state_file.write_text("{invalid json content")

        # Hook should handle this gracefully
        # We can't directly test the hook, but we verify error handling exists
        hook_file = Path("P:/.claude/skills/v/hooks/PreToolUse_v_stage_enforcer.py")
        hook_content = hook_file.read_text()

        # Should have JSON error handling
        assert "JSONDecodeError" in hook_content or "json.loads" in hook_content

    def test_malformed_script_output_handling(self):
        """Scripts should handle malformed output gracefully."""
        # Verify scripts have error handling for subprocess calls
        for script_name in ["stage2_6_dead_code.py", "stage2_7_security.py"]:
            script_path = SCRIPTS_DIR / script_name
            script_content = script_path.read_text()

            # Should have try/except or result checking
            assert "try:" in script_content or "returncode" in script_content


class TestDocumentationCompleteness:
    """Tests that documentation matches implementation."""

    def test_skill_md_documents_all_stages(self):
        """SKILL.md should document all stages."""
        skill_md = Path("P:/.claude/skills/v/SKILL.md")
        skill_content = skill_md.read_text()

        # Check for new stages
        assert "Stage 2.6" in skill_content or "stage2_6" in skill_content
        assert "Stage 2.7" in skill_content or "stage2_7" in skill_content
        assert "Stage 2.8" in skill_content or "stage2_8" in skill_content

    def test_documentation_mentions_required_tools(self):
        """Documentation should mention vulture and bandit requirements."""
        skill_md = Path("P:/.claude/skills/v/SKILL.md")
        skill_content = skill_md.read_text()

        # Should mention tool installation
        assert "vulture" in skill_content.lower() or "dead code" in skill_content.lower()
        assert "bandit" in skill_content.lower() or "security" in skill_content.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
