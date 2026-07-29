#!/usr/bin/env python3
"""Definition completeness check — automatic trace for called-but-undefined methods.

Ported from Claude /trace skill methodology (session 019fa94d, 2026-07-29).
Runs as a deterministic layer in /check Step 0.9. For each self.* method call
in changed .py files, verifies the method definition exists on the class.

Catches the _mark_row class of bug: called-but-undefined methods caused by
batch edits accidentally removing definitions.

Usage:
    python trace_check.py --paths path1.py path2.py [--output out.json]
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Any


def extract_class_methods(source: str) -> dict[str, list[str]]:
    """Map class name → list of method names defined in that class.

    Handles inheritance minimally: if a method is defined in a base class,
    it's available on subclasses. This script checks direct definitions only —
    pyright/pylint handle MRO resolution.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {}

    classes: dict[str, list[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            methods = []
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append(child.name)
            classes[node.name] = methods
    return classes


def extract_self_calls(source: str) -> list[dict[str, Any]]:
    """Find all self.method_name() calls with line numbers.

    Returns list of {line, method, class_context} entries.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    calls: list[dict[str, Any]] = []

    class ClassVisitor(ast.NodeVisitor):
        def __init__(self):
            self.calls = calls
            self.class_stack: list[str] = []

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            self.class_stack.append(node.name)
            self.generic_visit(node)
            self.class_stack.pop()

        def visit_Call(self, node: ast.Call) -> None:
            # Check for self.method() or self._method() pattern
            if (isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "self"):
                self.calls.append({
                    "line": node.lineno,
                    "method": node.func.attr,
                    "class": self.class_stack[-1] if self.class_stack else "<module>",
                })
            self.generic_visit(node)

    visitor = ClassVisitor()
    visitor.visit(tree)
    return calls


def check_file(path: str) -> list[dict[str, Any]]:
    """Check a single Python file for called-but-undefined self.* methods.

    Returns list of findings (empty if clean).
    """
    try:
        source = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    # Parse errors are findings — a file that can't parse is definitely broken
    try:
        ast.parse(source)
    except SyntaxError as e:
        return [{
            "file": path,
            "line": e.lineno or 0,
            "method": "<syntax-error>",
            "class": "<parse>",
            "issue": (
                f"SyntaxError at line {e.lineno or 0}: {e.msg}"
                " — AST parse failed, trace_check cannot analyze"
            ),
        }]

    class_methods = extract_class_methods(source)
    self_calls = extract_self_calls(source)

    findings: list[dict[str, Any]] = []
    for call in self_calls:
        cls = call["class"]
        method = call["method"]
        # Skip dunders — they're framework-provided
        if method.startswith("__") and method.endswith("__"):
            continue
        # Check if method is defined in the class
        if cls in class_methods:
            if method not in class_methods[cls]:
                findings.append({
                    "file": path,
                    "line": call["line"],
                    "method": method,
                    "class": cls,
                    "issue": (
                        f"self.{method}() called at line "
                        f"{call['line']} but not defined on class {cls}"
                    ),
                })
        elif cls == "<module>":
            # self.* at module scope is always a NameError at runtime
            findings.append({
                "file": path,
                "line": call["line"],
                "method": method,
                "class": "<module>",
                "issue": (
                    f"self.{method}() called at module scope "
                    f"(line {call['line']}) — NameError guaranteed"
                ),
            })

    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Definition completeness check — "
        "catch called-but-undefined self.* methods"
    )
    parser.add_argument(
        "--paths", nargs="+", required=True, help="Python files to check"
    )
    parser.add_argument(
        "--output", "-o", default=None,
        help="Write JSON result to this path"
    )
    args = parser.parse_args(argv)

    all_findings: list[dict[str, Any]] = []
    for path in args.paths:
        if Path(path).suffix == ".py" and Path(path).exists():
            findings = check_file(path)
            all_findings.extend(findings)

    result = {
        "status": "ok",
        "findings": all_findings,
        "finding_count": len(all_findings),
        "files_checked": len(args.paths),
        "policy": "deterministic_failures",
    }

    text = json.dumps(result, indent=2)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(text + "\n", encoding="utf-8")

    if all_findings:
        print(f"TRACE_CHECK: {len(all_findings)} called-but-undefined method(s) found:")
        for f in all_findings[:20]:
            print(f"  {f["file"]}:{f["line"]}: self.{f["method"]}() — {f["issue"]}")
        if len(all_findings) > 20:
            print(f"  ... +{len(all_findings) - 20} more")
    else:
        print(f"TRACE_CHECK: clean ({len(args.paths)} files checked)")

    return 0  # advisory — doesn't block CHECK alone


if __name__ == "__main__":
    sys.exit(main())
