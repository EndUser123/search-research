"""Tests for specific exception handling (RCA-001-002 fix).

Verifies that all exception handlers use specific exception types
instead of bare except clauses.
"""

import ast
import re
import sys
from pathlib import Path


def check_file_for_bare_except(file_path: str | Path) -> list[dict]:
    """Check a Python file for bare except clauses.

    Returns:
        List of dicts with line number and context for each bare except found.
    """
    bare_excepts = []

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        content = ''.join(lines)

    # Parse AST to find bare except clauses
    try:
        tree = ast.parse(content, filename=str(file_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    # This is a bare except clause
                    bare_excepts.append({
                        'line': node.lineno,
                        'file': str(file_path),
                        'context': _get_context(lines, node.lineno)
                    })
    except SyntaxError:
        # Fall back to regex if AST parsing fails
        for i, line in enumerate(lines, 1):
            # Match bare except: except: or except : (with optional comments)
            if re.search(r'except\s*:\s*(?:#.*)?$', line):
                bare_excepts.append({
                    'line': i,
                    'file': str(file_path),
                    'context': _get_context(lines, i)
                })

    return bare_excepts


def _get_context(lines: list[str], line_num: int, context_lines: int = 2) -> str:
    """Get context around a line number."""
    start = max(0, line_num - context_lines - 1)
    end = min(len(lines), line_num + context_lines)
    context_lines_list = lines[start:end]
    return ''.join(context_lines_list).strip()


def test_no_bare_except_in_metrics_tracker():
    """Verify metrics_tracker.py has no bare except clauses."""
    from rca import metrics_tracker
    file_path = Path(metrics_tracker.__file__)
    bare_excepts = check_file_for_bare_except(file_path)
    assert not bare_excepts, f"Found bare except clauses in {file_path}: {bare_excepts}"


def test_no_bare_except_in_pattern_registry():
    """Verify pattern_registry.py has no bare except clauses."""
    from rca import pattern_registry
    file_path = Path(pattern_registry.__file__)
    bare_excepts = check_file_for_bare_except(file_path)
    assert not bare_excepts, f"Found bare except clauses in {file_path}: {bare_excepts}"


def test_no_bare_except_in_outcome_recorder():
    """Verify outcome_recorder.py has no bare except clauses."""
    from rca import outcome_recorder
    file_path = Path(outcome_recorder.__file__)
    bare_excepts = check_file_for_bare_except(file_path)
    assert not bare_excepts, f"Found bare except clauses in {file_path}: {bare_excepts}"


def test_no_bare_except_in_fix_registry():
    """Verify fix_registry.py has no bare except clauses."""
    from rca import fix_registry
    file_path = Path(fix_registry.__file__)
    bare_excepts = check_file_for_bare_except(file_path)
    assert not bare_excepts, f"Found bare except clauses in {file_path}: {bare_excepts}"


def test_no_bare_except_in_session_preflight():
    """Verify session_preflight.py has no bare except clauses."""
    from rca import session
    file_path = Path(session.__file__)
    bare_excepts = check_file_for_bare_except(file_path)
    assert not bare_excepts, f"Found bare except clauses in {file_path}: {bare_excepts}"


def test_no_bare_except_in_debugpy_client():
    """Verify debugpy_client.py has no bare except clauses."""
    from rca import debugpy_client
    file_path = Path(debugpy_client.__file__)
    bare_excepts = check_file_for_bare_except(file_path)
    assert not bare_excepts, f"Found bare except clauses in {file_path}: {bare_excepts}"


def test_no_bare_except_in_phase_state_manager():
    """Verify phase_state_manager.py has no bare except clauses."""
    from rca import phase_state_manager
    file_path = Path(phase_state_manager.__file__)
    bare_excepts = check_file_for_bare_except(file_path)
    assert not bare_excepts, f"Found bare except clauses in {file_path}: {bare_excepts}"


def test_no_bare_except_in_temporal_check():
    """Verify temporal_check.py has no bare except clauses."""
    from rca import temporal_check
    file_path = Path(temporal_check.__file__)
    bare_excepts = check_file_for_bare_except(file_path)
    assert not bare_excepts, f"Found bare except clauses in {file_path}: {bare_excepts}"


def test_no_bare_except_in_evidence_saturation():
    """Verify evidence_saturation.py has no bare except clauses."""
    from rca import evidence_saturation
    file_path = Path(evidence_saturation.__file__)
    bare_excepts = check_file_for_bare_except(file_path)
    assert not bare_excepts, f"Found bare except clauses in {file_path}: {bare_excepts}"


def test_no_bare_except_in_cks_pattern_integration():
    """Verify cks_pattern_integration.py has no bare except clauses."""
    from rca.integration import cks_pattern_integration
    file_path = Path(cks_pattern_integration.__file__)
    bare_excepts = check_file_for_bare_except(file_path)
    assert not bare_excepts, f"Found bare except clauses in {file_path}: {bare_excepts}"


def test_hook_files_no_bare_except():
    """Verify hook scripts have no bare except clauses."""
    hook_dir = Path(__file__).parent.parent / "skill" / "hooks"
    hook_files = [
        "SessionEnd_rca_cleanup.py",
        "PostToolUse_rca_init.py",
        "PostToolUse_rca_phase_tracker.py",
    ]

    issues = []
    for hook_file in hook_files:
        file_path = hook_dir / hook_file
        if file_path.exists():
            bare_excepts = check_file_for_bare_except(file_path)
            if bare_excepts:
                issues.extend(bare_excepts)

    assert not issues, f"Found bare except clauses in hooks: {issues}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
