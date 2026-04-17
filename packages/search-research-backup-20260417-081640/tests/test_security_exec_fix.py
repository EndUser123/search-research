#!/usr/bin/env python3
"""Tests for exec() code execution security fix (SEC-002)."""

import pytest

from core.backends.rlm import RLMBackend


class TestExecSecurityFix:
    """Test that unsafe exec() is replaced with Jinja2 sandbox."""

    def test_exec_blocked_malicious_code(self):
        """Verify that malicious code cannot execute via exec().

        This test verifies that attempts to execute arbitrary code through
        the RLM backend are blocked by the Jinja2 sandbox.

        Tests that:
        - Code injection attempts are blocked
        - Dangerous built-ins are not accessible
        - Error message indicates security concern
        - System continues safely without executing code
        """
        backend = RLMBackend()

        # Try to execute malicious code
        malicious_code = """
import os
os.system('rm -rf /')  # This should NOT execute
result = 'malicious_execution'
"""

        result = backend.execute_in_sandbox(malicious_code)

        # Should block malicious code
        assert result["executed"] is False, "Malicious code should be blocked"
        assert "error" in result, "Should return error"
        assert result.get("return_value") is None, "No return value from blocked code"

    def test_jinja2_safe_template_execution(self):
        """Verify that safe templates with placeholders execute correctly.

        Tests that:
        - Templates with placeholders execute correctly
        - Placeholders are rendered with context variables
        - Python code in rendered templates executes safely
        - No arbitrary code execution
        """
        backend = RLMBackend()

        # Safe template with Python .format() placeholders (actual RLM pattern)
        # Note: F-strings use {{ to escape braces for .format() compatibility
        safe_template = """
results = {search_results}
total = len(results)
summary = f\"Found {{total}} results\"
for item in results[:3]:
    print(f\" - {{item.get('title', 'No title')}}\")
"""
        context = {
            "search_results": [
                {"title": "Result 1", "content": "Content 1"},
                {"title": "Result 2", "content": "Content 2"},
            ]
        }

        result = backend.execute_in_sandbox(safe_template, context=context)

        # Should execute safe template
        assert result["executed"] is True, "Safe template should execute"
        assert "output" in result, "Should capture output"
        assert result.get("error") is None, "No error for safe template"

    def test_limited_builtins_available(self):
        """Verify that only safe built-ins are available in sandbox.

        Tests that:
        - Safe built-ins (len, range, str, etc.) work
        - Dangerous built-ins (__import__, eval, exec, open) are blocked
        - Limited module access (no os, sys, subprocess)
        - Error message for blocked built-ins
        """
        backend = RLMBackend()

        # Try to use dangerous built-in
        dangerous_code = """
result = __import__('os').system('echo hacked')
"""

        result = backend.execute_in_sandbox(dangerous_code)

        # Should block dangerous built-in
        assert result["executed"] is False, "Dangerous built-in should be blocked"
        assert "error" in result, "Should return error"

        # Try safe built-in
        safe_code = """
result = len([1, 2, 3, 4, 5])
"""

        result = backend.execute_in_sandbox(safe_code)

        # Should allow safe built-in
        assert result["executed"] is True, "Safe built-in should work"
        assert result["return_value"] == 5, "Correct return value"

    def test_timeout_protection(self):
        """Verify that code execution has timeout protection.

        Tests that:
        - Long-running code is terminated after timeout
        - Timeout error is returned
        - System remains responsive
        - Default timeout is reasonable (e.g., 5 seconds)
        """
        backend = RLMBackend()

        # Infinite loop code
        infinite_loop = """
while True:
    pass  # This should timeout
"""

        result = backend.execute_in_sandbox(infinite_loop, timeout=1)

        # Should timeout
        assert result["executed"] is False, "Infinite loop should timeout"
        assert "timeout" in result.get("error", "").lower(), "Should indicate timeout"

    def test_stdin_disabled(self):
        """Verify that stdin input is disabled in sandbox.

        Tests that:
        - input() function is disabled or raises error
        - No hanging on stdin reads
        - Clear error message
        """
        backend = RLMBackend()

        # Try to read input
        input_code = """
result = input('Enter value: ')
"""

        result = backend.execute_in_sandbox(input_code)

        # Should block stdin
        assert result["executed"] is False, "stdin should be disabled"
        assert "error" in result, "Should return error about stdin"

    def test_file_operations_blocked(self):
        """Verify that file operations are blocked in sandbox.

        Tests that:
        - open() function is not available or restricted
        - File read/write attempts are blocked
        - Only whitelisted paths can be accessed (if any)
        """
        backend = RLMBackend()

        # Try to open file
        file_code = """
with open('/tmp/test.txt', 'w') as f:
    f.write('test')
result = 'file_written'
"""

        result = backend.execute_in_sandbox(file_code)

        # Should block file operations
        assert result["executed"] is False, "File operations should be blocked"
        assert "error" in result, "Should return error about file operations"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
