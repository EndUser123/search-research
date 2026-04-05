"""
Tests for SEC-003: Bash Allowlist Bypass Prevention via Full Command Parsing.

These tests validate that the bash syntax validator properly parses the full
command string using shlex.split() and rejects dangerous command chaining patterns.

Run with: pytest .claude/hooks/tests/test_bash_allowlist.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# The enhanced validation logic doesn't exist yet - use skipif pattern
try:
    from __lib.bash_allowlist_validator import (
        _DANGEROUS_PATTERNS,
        is_command_allowed,
        validate_command_segments,
    )
except (ImportError, ModuleNotFoundError):
    validate_command_segments = None
    is_command_allowed = None
    _DANGEROUS_PATTERNS = {}


# -------------------------------------------------------------------
# Test: SEC-003-001 — Chained python -c is rejected
# -------------------------------------------------------------------
@pytest.mark.skipif(
    validate_command_segments is None,
    reason="bash_allowlist_validator not implemented yet",
)
def test_rejects_chained_python():
    """
    'ls; python -c \"import os; os.system('rm -rf /')\"' must be rejected.

    The validator must parse ALL segments via shlex.split() and detect
    the dangerous python -c invocation even when preceded by a safe command.
    """
    command = "ls; python -c \"import os; os.system('rm -rf /')\""
    result = validate_command_segments(command)
    assert result is not None, "Command should be rejected"
    assert result.get("decision") == "block", "Should block dangerous command"


# -------------------------------------------------------------------
# Test: SEC-003-002 — Simple cat passes
# -------------------------------------------------------------------
@pytest.mark.skipif(
    validate_command_segments is None,
    reason="bash_allowlist_validator not implemented yet",
)
def test_passes_simple_cat():
    """
    'cat file.txt' passes validation.

    Simple read-only commands with no dangerous patterns should be allowed.
    """
    command = "cat file.txt"
    result = validate_command_segments(command)
    assert result is None, "Simple cat should be allowed"


# -------------------------------------------------------------------
# Test: SEC-003-003 — Simple python script passes
# -------------------------------------------------------------------
@pytest.mark.skipif(
    validate_command_segments is None,
    reason="bash_allowlist_validator not implemented yet",
)
def test_passes_simple_python():
    """
    'python script.py' passes (only if .py extension and no flags).

    Simple python script execution without flags or code injection is allowed.
    """
    command = "python script.py"
    result = validate_command_segments(command)
    assert result is None, "Simple python script should be allowed"


# -------------------------------------------------------------------
# Test: SEC-003-004 — python with flags is rejected
# -------------------------------------------------------------------
@pytest.mark.skipif(
    validate_command_segments is None,
    reason="bash_allowlist_validator not implemented yet",
)
def test_rejects_python_with_flags():
    """
    'python -m pip install requests' must be rejected.

    Any python invocation with flags (-c, -m, -f, -x) is dangerous.
    """
    command = "python -m pip install requests"
    result = validate_command_segments(command)
    assert result is not None, "python with flags should be rejected"
    assert result.get("decision") == "block"


# -------------------------------------------------------------------
# Test: SEC-003-005 — shlex handles escaping correctly
# -------------------------------------------------------------------
@pytest.mark.skipif(
    validate_command_segments is None,
    reason="bash_allowlist_validator not implemented yet",
)
def test_shlex_handles_escaping():
    """
    shlex.split() properly handles quoted strings and escaping.

    Commands like 'echo "hello; world"' should NOT be split on the
    semicolon inside quotes. The semicolon is part of the string data,
    not a command separator.
    """
    command = 'echo "hello; world"'
    result = validate_command_segments(command)
    # Should be allowed - semicolon is inside quotes
    assert result is None, "Semicolons inside quotes should not trigger rejection"


# -------------------------------------------------------------------
# Test: SEC-003-006 — && chaining is rejected
# -------------------------------------------------------------------
@pytest.mark.skipif(
    validate_command_segments is None,
    reason="bash_allowlist_validator not implemented yet",
)
def test_rejects_double_ampersand_chaining():
    """
    'ls && python -c \"import os\"' must be rejected.

    && is a command chaining operator that can bypass argv[0] checks.
    """
    command = 'ls && python -c "import os"'
    result = validate_command_segments(command)
    assert result is not None, "&& chaining should be rejected"
    assert result.get("decision") == "block"


# -------------------------------------------------------------------
# Test: SEC-003-007 — || chaining is rejected
# -------------------------------------------------------------------
@pytest.mark.skipif(
    validate_command_segments is None,
    reason="bash_allowlist_validator not implemented yet",
)
def test_rejects_double_pipe_chaining():
    """
    'ls || python -c \"import os\"' must be rejected.

    || is a command chaining operator that can bypass argv[0] checks.
    """
    command = 'ls || python -c "import os"'
    result = validate_command_segments(command)
    assert result is not None, "|| chaining should be rejected"
    assert result.get("decision") == "block"


# -------------------------------------------------------------------
# Test: SEC-003-008 — eval is always rejected
# -------------------------------------------------------------------
@pytest.mark.skipif(
    validate_command_segments is None,
    reason="bash_allowlist_validator not implemented yet",
)
def test_rejects_eval():
    """
    'eval $VAR' must be rejected.

    eval is inherently dangerous as it executes shell code from variables.
    """
    command = "eval $VAR"
    result = validate_command_segments(command)
    assert result is not None, "eval should be rejected"
    assert result.get("decision") == "block"


# -------------------------------------------------------------------
# Test: SEC-003-009 — exec is always rejected
# -------------------------------------------------------------------
@pytest.mark.skipif(
    validate_command_segments is None,
    reason="bash_allowlist_validator not implemented yet",
)
def test_rejects_exec():
    """
    'exec bash' must be rejected.

    exec replaces the current shell process, which is dangerous.
    """
    command = "exec bash"
    result = validate_command_segments(command)
    assert result is not None, "exec should be rejected"
    assert result.get("decision") == "block"


# -------------------------------------------------------------------
# Test: SEC-003-010 — subprocess patterns rejected
# -------------------------------------------------------------------
@pytest.mark.skipif(
    validate_command_segments is None,
    reason="bash_allowlist_validator not implemented yet",
)
def test_rejects_subprocess_patterns():
    """
    'subprocess.run([\"python\", \"-c\", \"...\"])' in any form rejected.

    subprocess calls in shell commands are dangerous.
    """
    command = "python -c 'import subprocess; subprocess.run([\"ls\"])'"
    result = validate_command_segments(command)
    assert result is not None, "subprocess patterns should be rejected"
    assert result.get("decision") == "block"


# -------------------------------------------------------------------
# Test: SEC-003-011 — os.system rejected
# -------------------------------------------------------------------
@pytest.mark.skipif(
    validate_command_segments is None,
    reason="bash_allowlist_validator not implemented yet",
)
def test_rejects_os_system():
    """
    'os.system(\"ls\")' style invocations rejected.

    os.system is a code injection vector.
    """
    command = "python -c 'import os; os.system(\"ls\")'"
    result = validate_command_segments(command)
    assert result is not None, "os.system should be rejected"
    assert result.get("decision") == "block"


# -------------------------------------------------------------------
# Test: SEC-003-012 — safe read-only commands with flags pass
# -------------------------------------------------------------------
@pytest.mark.skipif(
    validate_command_segments is None,
    reason="bash_allowlist_validator not implemented yet",
)
def test_passes_safe_commands_with_flags():
    """
    'head -n 10 file.txt' passes.

    Read-only commands (head, tail, grep, etc.) are allowed even with flags.
    """
    command = "head -n 10 file.txt"
    result = validate_command_segments(command)
    assert result is None, "Safe commands with flags should be allowed"


# -------------------------------------------------------------------
# Test: SEC-003-013 — bash -c rejected
# -------------------------------------------------------------------
@pytest.mark.skipif(
    validate_command_segments is None,
    reason="bash_allowlist_validator not implemented yet",
)
def test_rejects_bash_c():
    """
    'bash -c \"ls\"' must be rejected.

    bash -c allows arbitrary shell execution.
    """
    command = 'bash -c "ls"'
    result = validate_command_segments(command)
    assert result is not None, "bash -c should be rejected"
    assert result.get("decision") == "block"


# -------------------------------------------------------------------
# Test: SEC-003-014 — perl -e rejected
# -------------------------------------------------------------------
@pytest.mark.skipif(
    validate_command_segments is None,
    reason="bash_allowlist_validator not implemented yet",
)
def test_rejects_perl_e():
    """
    'perl -e \"print \\\"hello\\\"\"' must be rejected.

    perl -e allows arbitrary code execution.
    """
    command = 'perl -e "print \\"hello\\""'
    result = validate_command_segments(command)
    assert result is not None, "perl -e should be rejected"
    assert result.get("decision") == "block"


# -------------------------------------------------------------------
# Test: SEC-003-015 — ruby -e rejected
# -------------------------------------------------------------------
@pytest.mark.skipif(
    validate_command_segments is None,
    reason="bash_allowlist_validator not implemented yet",
)
def test_rejects_ruby_e():
    """
    'ruby -e \"puts \\\"hello\\\"\"' must be rejected.

    ruby -e allows arbitrary code execution.
    """
    command = 'ruby -e "puts \\"hello\\""'
    result = validate_command_segments(command)
    assert result is not None, "ruby -e should be rejected"
    assert result.get("decision") == "block"


# -------------------------------------------------------------------
# Characterization test: Import module
# -------------------------------------------------------------------
def test_module_import():
    """
    Characterization test: Verify bash_allowlist_validator module can be imported.

    This test will FAIL in the RED phase because the module doesn't exist yet.
    Once the module is implemented, this test should pass.
    """
    from __lib.bash_allowlist_validator import (
        _DANGEROUS_PATTERNS,
        is_command_allowed,
        validate_command_segments,
    )

    # If we get here, the import succeeded
    assert validate_command_segments is not None
    assert is_command_allowed is not None
    assert isinstance(_DANGEROUS_PATTERNS, (set, list, tuple))
