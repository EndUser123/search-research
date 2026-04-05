#!/usr/bin/env python3
"""
Enforce that LEDGER_AVAILABLE is never defined inline in hook files.

The canonical definition lives in __lib/runtime_env.py.
Any hook file that defines LEDGER_AVAILABLE = ... is a regression.
"""
import ast
from pathlib import Path

HOOKS_DIR = Path("P:/.claude/hooks")
EXEMPT = {
    HOOKS_DIR / "__lib" / "runtime_env.py",  # the canonical definition
}


def _hook_py_files():
    for p in HOOKS_DIR.rglob("*.py"):
        if "__pycache__" in p.parts:
            continue
        if p in EXEMPT:
            continue
        yield p


def test_no_inline_ledger_available():
    violations = []
    for path in _hook_py_files():
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            # Try UTF-16 for files with UTF-16 BOM
            try:
                source = path.read_text(encoding="utf-16")
            except (OSError, UnicodeDecodeError):
                continue
        if "LEDGER_AVAILABLE" not in source:
            continue
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "LEDGER_AVAILABLE":
                        # Allow the canonical pattern: LEDGER_AVAILABLE = _ledger_available()
                        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name):
                            if node.value.func.id == "_ledger_available":
                                continue
                        violations.append(f"{path}:{node.lineno}")
    assert not violations, (
        "LEDGER_AVAILABLE defined inline (use __lib.runtime_env.ledger_available instead):\n"
        + "\n".join(violations)
    )


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
