#!/usr/bin/env python3
"""
Tests for Verification Theater Prevention (v2.4.0)
==================================================

Tests the trivial command filtering and verification theater detection
added in assumption_audit_v2.py v2.4.0.

Run with: pytest tests/test_verification_theater.py -v
"""

import sys
from pathlib import Path

# Add hooks directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from assumption_audit_v2 import (
    evaluate_response,
    get_bash_command_name,
    has_success_claims,
    is_diagnostic_bash_command,
    is_trivial_bash_command,
    is_weak_evidence_command,
)


class TestBashCommandExtraction:
    """Tests for get_bash_command_name()"""

    def test_simple_command(self):
        assert get_bash_command_name("echo test") == "echo"
        assert get_bash_command_name("pytest tests/") == "pytest"
        assert get_bash_command_name("cat file.txt") == "cat"

    def test_pipeline_returns_last_command(self):
        # Pipeline should return the LAST command (final output producer)
        assert get_bash_command_name("echo test | python script.py") == "python"
        assert get_bash_command_name("cat file | grep pattern") == "grep"
        assert get_bash_command_name("ls | head -5") == "head"

    def test_path_prefix_stripped(self):
        assert get_bash_command_name("/usr/bin/python test.py") == "python"
        assert get_bash_command_name("C:\\Python\\python.exe test.py") == "python"

    def test_extension_stripped(self):
        assert get_bash_command_name("python.exe test.py") == "python"
        assert get_bash_command_name("script.sh arg") == "script"

    def test_empty_input(self):
        assert get_bash_command_name("") == ""
        assert get_bash_command_name("   ") == ""


class TestTrivialCommandDetection:
    """Tests for is_trivial_bash_command()"""

    def test_echo_is_trivial(self):
        assert is_trivial_bash_command("echo done")
        assert is_trivial_bash_command("echo 'test passed'")
        assert is_trivial_bash_command("printf 'success'")

    def test_file_manipulation_is_trivial(self):
        assert is_trivial_bash_command("mkdir temp")
        assert is_trivial_bash_command("touch file.txt")
        assert is_trivial_bash_command("rm -rf temp")
        assert is_trivial_bash_command("cp a.txt b.txt")
        assert is_trivial_bash_command("mv old.txt new.txt")

    def test_environment_commands_trivial(self):
        assert is_trivial_bash_command("cd /home")
        assert is_trivial_bash_command("export VAR=value")
        assert is_trivial_bash_command("clear")

    def test_diagnostic_commands_not_trivial(self):
        assert not is_trivial_bash_command("pytest tests/")
        assert not is_trivial_bash_command("cat config.yaml")
        assert not is_trivial_bash_command("grep error log.txt")
        assert not is_trivial_bash_command("python script.py")
        assert not is_trivial_bash_command("git status")

    def test_pipeline_with_diagnostic_not_trivial(self):
        # Even though echo is trivial, pipeline ending in python is not
        assert not is_trivial_bash_command("echo test | python script.py")
        assert not is_trivial_bash_command("echo | grep pattern")


class TestWeakEvidenceDetection:
    """Tests for is_weak_evidence_command()"""

    def test_ls_is_weak(self):
        assert is_weak_evidence_command("ls")
        assert is_weak_evidence_command("ls -la")
        assert is_weak_evidence_command("dir")
        assert is_weak_evidence_command("tree")

    def test_diagnostic_not_weak(self):
        assert not is_weak_evidence_command("pytest")
        assert not is_weak_evidence_command("cat file")
        assert not is_weak_evidence_command("grep pattern")


class TestDiagnosticCommandDetection:
    """Tests for is_diagnostic_bash_command()"""

    def test_test_runners_diagnostic(self):
        assert is_diagnostic_bash_command("pytest tests/")
        assert is_diagnostic_bash_command("npm test")
        assert is_diagnostic_bash_command("cargo test")

    def test_file_inspection_diagnostic(self):
        assert is_diagnostic_bash_command("cat file.txt")
        assert is_diagnostic_bash_command("grep pattern file")
        assert is_diagnostic_bash_command("head -10 file")
        assert is_diagnostic_bash_command("tail -f log")

    def test_execution_diagnostic(self):
        assert is_diagnostic_bash_command("python script.py")
        assert is_diagnostic_bash_command("node app.js")
        assert is_diagnostic_bash_command("go run main.go")

    def test_trivial_not_diagnostic(self):
        assert not is_diagnostic_bash_command("echo done")
        assert not is_diagnostic_bash_command("mkdir temp")

    def test_weak_not_diagnostic(self):
        # Weak evidence is explicitly not "diagnostic" for success claims
        assert not is_diagnostic_bash_command("ls")
        assert not is_diagnostic_bash_command("dir")


class TestSuccessClaimDetection:
    """Tests for has_success_claims()"""

    def test_fixed_claims(self):
        assert has_success_claims("The bug is fixed.")
        assert has_success_claims("I have fixed the issue.")
        assert has_success_claims("The problem has been resolved.")

    def test_working_claims(self):
        assert has_success_claims("It works now.")
        assert has_success_claims("The code is working correctly.")
        assert has_success_claims("This should work properly now.")

    def test_test_pass_claims(self):
        assert has_success_claims("All tests pass.")
        assert has_success_claims("The tests are passing.")
        assert has_success_claims("pytest shows 5 passed")

    def test_verification_claims(self):
        assert has_success_claims("I verified that it works.")
        assert has_success_claims("Confirmed the fix.")

    def test_neutral_statements_not_success(self):
        assert not has_success_claims("Let me check the file.")
        assert not has_success_claims("I'll investigate the issue.")
        assert not has_success_claims("Looking at the code...")

    def test_empty_input(self):
        assert not has_success_claims("")
        assert not has_success_claims(None)


class TestVerificationTheaterBlocking:
    """Integration tests for evaluate_response() theater detection"""

    def test_trivial_echo_blocks_success_claim(self):
        """echo "done" should NOT count as verification for "fixed" claims"""
        tool_sequence = [
            {"name": "Bash", "command": "echo 'test complete'"}
        ]

        result = evaluate_response(
            "The bug is fixed and working now.",
            tools_used=["Bash"],
            tool_sequence=tool_sequence
        )

        # Should block due to verification theater
        assert result["decision"] == "block"
        assert result["reason"] in ("NO_EVIDENCE", "VERIFICATION_THEATER")

    def test_pytest_allows_success_claim(self):
        """pytest should count as valid verification for success claims"""
        tool_sequence = [
            {"name": "Bash", "command": "pytest tests/test_fix.py -v"}
        ]

        result = evaluate_response(
            "The bug is fixed. Tests pass.",
            tools_used=["Bash"],
            tool_sequence=tool_sequence
        )

        # Should allow - pytest is diagnostic
        assert result["decision"] == "allow"

    def test_cat_allows_inspection_claim(self):
        """cat should count as valid evidence for file content claims"""
        tool_sequence = [
            {"name": "Bash", "command": "cat config.yaml | grep setting"}
        ]

        result = evaluate_response(
            "The config file contains the new setting.",
            tools_used=["Bash"],
            tool_sequence=tool_sequence
        )

        # Should allow - cat+grep is diagnostic
        assert result["decision"] == "allow"

    def test_read_tool_allows_claim(self):
        """Read tool should count as valid evidence"""
        tool_sequence = [
            {"name": "Read", "command": "config.yaml"}
        ]

        result = evaluate_response(
            "The config file is correct.",
            tools_used=["Read"],
            tool_sequence=tool_sequence
        )

        # Read is always strong evidence
        assert result["decision"] == "allow"

    def test_ls_alone_blocks_success_claim(self):
        """ls alone is weak evidence for success claims"""
        tool_sequence = [
            {"name": "Bash", "command": "ls -la tests/"}
        ]

        result = evaluate_response(
            "The fix is complete and working.",
            tools_used=["Bash"],
            tool_sequence=tool_sequence
        )

        # ls is weak evidence for success claims
        assert result["decision"] == "block"
        assert result["reason"] == "VERIFICATION_THEATER"

    def test_no_claims_always_allows(self):
        """No claims = no verification needed"""
        tool_sequence = [
            {"name": "Bash", "command": "echo hello"}
        ]

        result = evaluate_response(
            "Let me check something.",
            tools_used=["Bash"],
            tool_sequence=tool_sequence
        )

        # No success claims = no theater check
        assert result["decision"] == "allow"
        assert result["reason"] == "NO_CLAIMS"


class TestPipelineHandling:
    """Tests for pipeline command classification"""

    def test_echo_to_python_not_trivial(self):
        """echo | python should be classified by final command (python)"""
        assert not is_trivial_bash_command("echo 'data' | python process.py")

    def test_cat_to_grep_not_trivial(self):
        """cat | grep is diagnostic (grep is final)"""
        assert not is_trivial_bash_command("cat file.log | grep ERROR")

    def test_echo_to_tee_still_trivial(self):
        """echo | tee is still essentially trivial output"""
        # tee is not in TRIVIAL but it's just echoing to file
        # This test documents current behavior
        cmd = "echo test | tee output.txt"
        # Final command is tee, which is not in trivial set
        assert not is_trivial_bash_command(cmd)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
