#!/usr/bin/env python3
"""
Tests for Reflexion Verifier Hook

Tests the zero-friction self-healing verification system:
- Truncation detection
- Syntax validation
- Auto-retry mechanism
- Evidence recording for Stop hooks
"""

# Import the module to test
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from posttooluse.reflexion_verifier import ReflexionVerifier


class TestReflexionVerifier:
    """Test Reflexion verifier behavior."""

    def test_reads_from_disk_not_input(self):
        """
        Verify that Reflexion verifier reads ACTUAL file from disk,
        not the input content (trust but verify).

        This is the core fix for the truncation issue.
        """
        hook = ReflexionVerifier()

        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            test_file = f.name
            # Write correct content
            f.write("def hello():\n    print('world')\n")

        try:
            # Simulate Write operation with CORRECT input
            tool_input = {
                "file_path": test_file,
                "content": "def hello():\n    print('world')\n"  # 32 bytes
            }
            tool_response = {}  # Success

            # But the file on disk is TRUNCATED (simulate truncation)
            # Must be SYNTACTICALLY VALID Python (has pass statement)
            Path(test_file).write_text("def hello():\n    pass\n")  # Valid but wrong content!

            result = hook.process("Write", tool_input, tool_response)

            # Should detect size mismatch because it reads from DISK
            assert result["status"] == "WARN"
            # Check for size mismatch message in the injection (content differs)
            assert "size mismatch" in result["injection"].lower() or "truncation" in result["injection"].lower()

        finally:
            Path(test_file).unlink()

    def test_missing_file_after_write(self):
        """
        When Write reports success but file doesn't exist on disk,
        this is CRITICAL and should block immediately.
        """
        hook = ReflexionVerifier()

        test_file = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
        test_file.close()
        Path(test_file.name).unlink()  # Delete immediately

        try:
            tool_input = {
                "file_path": test_file.name,
                "content": "def hello():\n    print('world')\n"
            }
            tool_response = {}  # Reports success

            result = hook.process("Write", tool_input, tool_response)

            # Should fail - file doesn't exist after Write
            assert result["status"] == "FAIL"
            assert "not found" in result["injection"]

        finally:
            if Path(test_file.name).exists():
                Path(test_file.name).unlink()

    def test_syntax_error_blocks(self):
        """
        Syntax errors should BLOCK (critical severity)
        because they prevent execution.
        """
        hook = ReflexionVerifier()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            test_file = f.name
            # Write Python with syntax error
            f.write("def hello(:\n    print('world')\n")

        try:
            # Simulate Write operation
            tool_input = {
                "file_path": test_file,
                "content": "def hello(:\n    print('world')\n"  # Has syntax error
            }
            tool_response = {}

            result = hook.process("Write", tool_input, tool_response)

            # Should block due to syntax error
            assert result["status"] == "FAIL"
            assert "SYNTAX_ERROR" in result["injection"]

        finally:
            Path(test_file).unlink()

    def test_auto_retry_with_self_healing(self):
        """
        When fixable issues are detected, should inject self-healing prompt
        and increment retry counter instead of blocking.
        """
        hook = ReflexionVerifier()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            test_file = f.name

        try:
            # Simulate Write with truncated content (fixable issue)
            tool_input = {
                "file_path": test_file,
                "content": "def hello():\n    print('world')\n" * 100  # Large content
            }
            tool_response = {}

            # Truncate file on disk (use syntactically valid Python)
            Path(test_file).write_text("def hello():\n    pass\n")

            result = hook.process("Write", tool_input, tool_response)

            # Should WARN and inject self-healing prompt
            assert result["status"] == "WARN"
            assert "Self-Healing Action Required" in result["injection"]
            assert "Retry 1/3" in result["injection"]

            # Check retry count incremented
            retry_count = hook._get_retry_count(test_file)
            assert retry_count == 1

        finally:
            Path(test_file).unlink()
            if hook.retry_file.exists():
                hook.retry_file.unlink()

    def test_evidence_recording_for_stop_hooks(self):
        """
        Should always record evidence (post_edit_readbacks) for Stop hooks
        to verify edit-result claims.
        """
        hook = ReflexionVerifier()
        # Clear evidence log from previous tests for isolation
        if hook.evidence_log.exists():
            hook.evidence_log.unlink()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            test_file = f.name
            content = "def hello():\n    print('world')\n"
            f.write(content)

        try:
            tool_input = {"file_path": test_file, "content": content}
            tool_response = {}

            result = hook.process("Write", tool_input, tool_response)

            # Should record evidence even on PASS
            assert result["status"] == "PASS"

            # Check evidence log was created
            assert hook.evidence_log.exists()
            evidence_entries = hook.evidence_log.read_text(encoding="utf-8")
            # Escape backslashes for JSON comparison
            escaped_path = test_file.replace("\\", "\\\\")
            assert escaped_path in evidence_entries
            assert '"operation"' in evidence_entries

        finally:
            Path(test_file).unlink()
            if hook.evidence_log.exists():
                hook.evidence_log.unlink()

    def test_max_retries_surfaces_to_user(self):
        """
        After MAX_RETRIES (3), should surface issues to user with
        clear guidance instead of continuing to retry.
        """
        hook = ReflexionVerifier()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            test_file = f.name

        try:
            # Set retry count to MAX
            hook._increment_retry(test_file)
            hook._increment_retry(test_file)
            hook._increment_retry(test_file)

            tool_input = {
                "file_path": test_file,
                "content": "x" * 1000  # Large content
            }
            tool_response = {}

            # Truncate file on disk
            Path(test_file).write_text("x")

            result = hook.process("Write", tool_input, tool_response)

            # Should WARN with max retries message
            assert result["status"] == "WARN"
            assert "Healing attempts exhausted" in result["injection"]
            assert "3 retries" in result["injection"]

            # Retry counter should be cleared
            retry_count = hook._get_retry_count(test_file)
            assert retry_count == 0

        finally:
            Path(test_file).unlink()
            if hook.retry_file.exists():
                hook.retry_file.unlink()

    def test_pass_with_no_issues(self):
        """
        When file is correctly written, should PASS silently
        with no injection (zero friction).
        """
        hook = ReflexionVerifier()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            test_file = f.name
            content = "def hello():\n    print('world')\n"
            f.write(content)

        try:
            tool_input = {"file_path": test_file, "content": content}
            tool_response = {}

            result = hook.process("Write", tool_input, tool_response)

            # Should pass with no injection
            assert result["status"] == "PASS"
            assert result["injection"] is None

        finally:
            Path(test_file).unlink()



    def test_verifies_non_code_files_for_truncation(self):
        """
        Non-code files (markdown, config, etc.) should now be verified
        for truncation and file existence, not skipped.
        """
        hook = ReflexionVerifier()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            test_file = f.name
            # Write markdown content
            f.write("# Heading\n\nSome content here.\n")

        try:
            # Simulate Write operation with large expected content
            tool_input = {
                "file_path": test_file,
                "content": "# Heading\n\n" + "x" * 1000  # 1000+ bytes expected
            }
            tool_response = {}

            # File on disk is much smaller (truncated)
            Path(test_file).write_text("# Heading\n\nSmall content\n")

            result = hook.process("Write", tool_input, tool_response)

            # Should WARN about size mismatch - non-code files are now verified
            assert result["status"] == "WARN"
            assert "size" in result["injection"].lower() or "truncat" in result["injection"].lower()

        finally:
            Path(test_file).unlink()

    def test_non_code_file_missing_detected(self):
        """
        Missing non-code files should still be detected as critical failures.
        """
        hook = ReflexionVerifier()

        test_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        test_file.close()
        Path(test_file.name).unlink()  # Delete immediately

        try:
            tool_input = {
                "file_path": test_file.name,
                "content": "key: value\n"
            }
            tool_response = {}  # Reports success

            result = hook.process("Write", tool_input, tool_response)

            # Should FAIL - file doesn't exist (even though it's .yaml)
            assert result["status"] == "FAIL"
            assert "not found" in result["injection"]

        finally:
            if Path(test_file.name).exists():
                Path(test_file.name).unlink()

    def test_tighter_truncation_threshold(self):
        """
        Truncation threshold is now 0.5 (50%) instead of 0.1 (10%).
        Files smaller than 50% of expected size should trigger warning.
        """
        hook = ReflexionVerifier()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            test_file = f.name

        try:
            # Expected: 1000 bytes
            # Actual: 400 bytes (40% of expected - below new 50% threshold)
            tool_input = {
                "file_path": test_file,
                "content": "x" * 1000
            }
            tool_response = {}

            # Write file that's 40% of expected size
            Path(test_file).write_text("x" * 400)

            result = hook.process("Write", tool_input, tool_response)

            # Should WARN - 40% < 50% threshold
            assert result["status"] == "WARN"
            assert "truncat" in result["injection"].lower()

        finally:
            Path(test_file).unlink()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
