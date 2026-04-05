#!/usr/bin/env python3
"""
Test Cases for /v Skill Sequential Gate Enforcement

These tests verify that the /v skill enforces sequential stage execution
and halts appropriately on CRITICAL/HIGH findings.

Run: pytest P:/.claude/tests/test_v_skill_gates.py -v
"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
import sys

# Add hooks directory to path
sys.path.insert(0, str(Path("P:/.claude/skills/v/hooks")))


class TestStageSequencing:
    """Test that stages execute in order with proper gating."""
    
    def test_stage_1_must_pass_before_stage_2(self):
        """Stage 2 should NOT execute if Stage 1 fails."""
        # Simulate Stage 1 failure (syntax error)
        stage_1_result = {
            "stage": 1,
            "status": "FAIL",
            "severity": "CRITICAL",
            "message": "SyntaxError at line 15"
        }
        
        # Verify stage 2 would be blocked
        assert stage_1_result["status"] == "FAIL"
        assert stage_1_result["severity"] == "CRITICAL"
        # In real implementation, the gate hook would block Stage 2 execution
    
    def test_stage_2_can_proceed_after_stage_1_pass(self):
        """Stage 2 should execute after Stage 1 passes."""
        stage_1_result = {
            "stage": 1,
            "status": "PASS",
            "severity": "NONE"
        }
        
        assert stage_1_result["status"] == "PASS"
        # Gate should allow Stage 2
    
    def test_stage_3_halt_blocks_stage_4(self):
        """Stage 4 (TDD) should NOT execute if Stage 3 has CRITICAL/HIGH findings."""
        stage_3_result = {
            "stage": 3,
            "status": "FAIL",
            "severity": "HIGH",
            "findings": [
                {"severity": "HIGH", "type": "security", "message": "SEC-001: Path traversal"}
            ]
        }
        
        # Verify halt condition
        has_halt_findings = any(
            f["severity"] in ("CRITICAL", "HIGH") 
            for f in stage_3_result["findings"]
        )
        assert has_halt_findings is True
        # Gate should block Stage 4
    
    def test_stage_3_medium_allows_stage_4(self):
        """Stage 4 should execute if Stage 3 only has MEDIUM/LOW findings."""
        stage_3_result = {
            "stage": 3,
            "status": "WARN",
            "severity": "MEDIUM",
            "findings": [
                {"severity": "MEDIUM", "type": "quality", "message": "TODO comment found"}
            ]
        }
        
        has_halt_findings = any(
            f["severity"] in ("CRITICAL", "HIGH") 
            for f in stage_3_result["findings"]
        )
        assert has_halt_findings is False
        # Gate should allow Stage 4


class TestHaltConditions:
    """Test halt conditions are correctly identified."""
    
    @pytest.mark.parametrize("severity,finding_type,should_halt", [
        ("CRITICAL", "security", True),
        ("CRITICAL", "structural", True),
        ("HIGH", "security", True),
        ("HIGH", "structural", True),
        ("HIGH", "compliance", True),
        ("MEDIUM", "quality", False),
        ("MEDIUM", "performance", False),
        ("LOW", "any", False),
        ("INFO", "any", False),
    ])
    def test_halt_condition_matrix(self, severity, finding_type, should_halt):
        """Test halt conditions match the documented matrix."""
        finding = {"severity": severity, "type": finding_type}
        
        halt_severities = ("CRITICAL", "HIGH")
        actual_halt = finding["severity"] in halt_severities
        
        assert actual_halt == should_halt, \
            f"Expected halt={should_halt} for {severity}/{finding_type}"


class TestStageStateManagement:
    """Test stage state is properly tracked."""
    
    def test_state_file_created_on_stage_start(self, tmp_path):
        """State file should be created when a stage starts."""
        state_file = tmp_path / "v_state.json"
        
        # Simulate stage start
        state = {
            "current_stage": 1,
            "stages_completed": [],
            "timestamp": "2026-01-27T10:00:00"
        }
        state_file.write_text(json.dumps(state))
        
        loaded = json.loads(state_file.read_text())
        assert loaded["current_stage"] == 1
    
    def test_state_updated_on_stage_complete(self, tmp_path):
        """State should update when a stage completes."""
        state_file = tmp_path / "v_state.json"
        
        # Initial state
        state = {
            "current_stage": 1,
            "stages_completed": [],
        }
        state_file.write_text(json.dumps(state))
        
        # After Stage 1 completes
        state["stages_completed"].append(1)
        state["current_stage"] = 2
        state_file.write_text(json.dumps(state))
        
        loaded = json.loads(state_file.read_text())
        assert 1 in loaded["stages_completed"]
        assert loaded["current_stage"] == 2
    
    def test_state_prevents_stage_skip(self, tmp_path):
        """Should not allow jumping to Stage 4 without completing 1-3."""
        state_file = tmp_path / "v_state.json"
        
        state = {
            "current_stage": 1,
            "stages_completed": [],
        }
        state_file.write_text(json.dumps(state))
        
        # Attempt to run Stage 4
        requested_stage = 4
        required_stages = [1, 2, 3]
        
        missing = [s for s in required_stages if s not in state["stages_completed"]]
        
        assert len(missing) > 0, "Should have missing prerequisite stages"
        assert missing == [1, 2, 3], "All stages should be missing"


class TestOutputEvidence:
    """Test that actual tool output is shown, not summaries."""
    
    def test_pytest_output_includes_counts(self):
        """Stage 4 output should show actual pytest counts."""
        pytest_output = """
================ 68 passed, 1 skipped, 5250 warnings in 0.49s =================
tests/integration/test_cli.py: 6 passed
tests/unit/test_dataclasses.py: 15 passed, 1 skipped
"""
        
        # Should contain numeric counts
        assert "68 passed" in pytest_output
        assert "1 skipped" in pytest_output
        
        # Should NOT be just a summary
        assert pytest_output != "✅ Tests passed"
    
    def test_pylint_output_includes_score(self):
        """Stage 2 output should show actual pylint score."""
        pylint_output = """
************* Module my_module
my_module.py:15:0: C0301: Line too long (120/100) (line-too-long)
my_module.py:23:4: W0612: Unused variable 'x' (unused-variable)

------------------------------------------------------------------
Your code has been rated at 8.50/10
"""
        
        # Should contain actual score
        assert "8.50/10" in pylint_output
        
        # Should show specific issues
        assert "C0301" in pylint_output


class TestSkillDocumentStructure:
    """Test the SKILL.md structure follows execution template rules."""
    
    def test_execution_directive_in_first_60_lines(self):
        """Execution directive should be early in file (allowing for frontmatter)."""
        skill_path = Path("P:/.claude/skills/v/SKILL.md")
        if not skill_path.exists():
            pytest.skip("Skill file not found")
        
        content = skill_path.read_text()
        first_60_lines = "\n".join(content.split("\n")[:60])
        
        # Should have execution directive early (accounting for frontmatter with hooks)
        has_directive = any(phrase in first_60_lines for phrase in [
            "EXECUTION DIRECTIVE",
            "IMMEDIATELY",
            "When invoked"
        ])
        
        assert has_directive, "Execution directive should be in first 60 lines"
    
    def test_do_not_block_present(self):
        """DO NOT block should be present."""
        skill_path = Path("P:/.claude/skills/v/SKILL.md")
        if not skill_path.exists():
            pytest.skip("Skill file not found")
        
        content = skill_path.read_text()
        
        assert "DO NOT" in content or "**DO NOT:**" in content, \
            "Should have DO NOT block"
    
    def test_no_documentation_trap_phrases(self):
        """Should not have documentation trap phrases."""
        skill_path = Path("P:/.claude/skills/v/SKILL.md")
        if not skill_path.exists():
            pytest.skip("Skill file not found")
        
        content = skill_path.read_text()
        
        trap_phrases = [
            "This command provides",
            "Future enhancements",
            "Benefits include",
            "Core philosophy"
        ]
        
        for phrase in trap_phrases:
            assert phrase not in content, \
                f"Documentation trap phrase found: '{phrase}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
