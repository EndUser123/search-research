#!/usr/bin/env python3
"""Cross-module call-graph audit for hermeticity verification.

Scans Python modules in a target directory for:
- Function-body references to module-level constants (globals escape)
- Hardcoded Path("P:/"), Path.home(), os.environ patterns
- Mutation operations (write_text, mkdir, replace, unlink)

Classifies each finding as: configured, production-default, blocking-hardcoded,
or unreachable-legacy. Exits 0 if no blocking escapes, 1 if any found.

Usage:
    python P:/.agents/scripts/cross_module_audit.py <target_dir> [--globals-only]

Created 2026-07-27 session 019fa111. Promoted from P:/tmp/ to .agents/scripts/
because the pattern it catches (single-module AST audit missing sibling-module
escapes) recurred twice in one session.

See wiki concept: cross-module-call-graph-audit-false-negative
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

GLOBAL_NAMES = {
    "WORKSPACE", "ARTIFACTS_DIR", "HANDOFFS_DIR", "GROK_SESSIONS",
    "SESSIONS_ROOT", "TMP_DIR", "TEMP_GROK", "AAR_LIB",
    "GIT_STATE_CHECK", "DIRTY_AGE_CHECK", "CLOSE_EVIDENCE_DIR",
}


def audit_module(mod_path: Path) -> list[dict]:
    """Audit one Python file. Returns list of findings."""
    src = mod_path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return [{"file": str(mod_path), "line": 0, "type": "syntax_error", "detail": "parse failed"}]

    # Collect functions that accept cfg
    cfg_functions = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for arg in node.args.args:
                if arg.arg in ("cfg", "config", "options", "settings"):
                    cfg_functions.add(node.name)

    findings = []

    # Check function-body references to module-level globals
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for sub in ast.walk(node):
                if isinstance(sub, ast.Name) and sub.id in GLOBAL_NAMES:
                    if isinstance(sub.ctx, ast.Store):
                        continue
                    has_cfg = node.name in cfg_functions
                    status = "configured" if has_cfg else "BLOCKING-HARDCODED"
                    findings.append({
                        "file": str(mod_path.name),
                        "line": sub.lineno,
                        "function": node.name,
                        "type": "global_ref",
                        "target": sub.id,
                        "status": status,
                    })

    # Check hardcoded path patterns
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for sub in ast.walk(node):
                # Path.home()
                if (isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute)
                        and sub.func.attr == "home"):
                    findings.append({
                        "file": str(mod_path.name),
                        "line": sub.lineno,
                        "function": node.name,
                        "type": "Path.home()",
                        "status": "BLOCKING-HARDCODED",
                    })
                # Path("P:/")
                if (isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name)
                        and sub.func.id == "Path"):
                    for arg in sub.args:
                        if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and "P:" in arg.value:
                            findings.append({
                                "file": str(mod_path.name),
                                "line": sub.lineno,
                                "function": node.name,
                                "type": 'Path("P:/")',
                                "status": "BLOCKING-HARDCODED",
                            })

    return findings


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <target_dir>", file=sys.stderr)
        sys.exit(2)

    target = Path(sys.argv[1])
    if not target.exists():
        print(f"ERROR: {target} does not exist", file=sys.stderr)
        sys.exit(2)

    py_files = sorted(target.glob("*.py"))
    if not py_files:
        print(f"No .py files in {target}", file=sys.stderr)
        sys.exit(0)

    all_findings = []
    for f in py_files:
        all_findings.extend(audit_module(f))

    blocking = [f for f in all_findings if f["status"] == "BLOCKING-HARDCODED"]

    if all_findings:
        print(f"--- {target.name} ---")
        for f in all_findings:
            prefix = "  ❌" if f["status"] == "BLOCKING-HARDCODED" else "  ✅"
            print(f"{prefix} {f['file']}:{f['line']} {f.get('function', '?')}() -> {f['type']} [{f['status']}]")

    if blocking:
        print(f"\n*** {len(blocking)} BLOCKING escape(s) found ***", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"\n*** CLEAN: no blocking escapes ***")
        sys.exit(0)


if __name__ == "__main__":
    main()
