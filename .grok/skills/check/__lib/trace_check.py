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
import importlib
import json
import sys
from pathlib import Path
from typing import Any


def extract_class_methods(
    source: str,
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Map class name → method names, and class name → base class names.

    Returns (methods, bases) where:
    - methods[class_name] = [method_name, ...]
    - bases[class_name] = [base_class_name, ...]

    Handles inheritance for classes defined IN THE SAME FILE. Base classes
    from other modules can't be resolved here — pyright/pylint handle those.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {}, {}

    methods: dict[str, list[str]] = {}
    bases: dict[str, list[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            class_methods = []
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    class_methods.append(child.name)
            methods[node.name] = class_methods
            # Extract base class names (only Name nodes — string/attribute bases
            # are from other modules and can't be resolved here)
            base_names = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    base_names.append(base.id)
                elif isinstance(base, ast.Subscript):
                    # Generic: Base[T] → unwrap to Base
                    inner = base.value
                    if isinstance(inner, ast.Name):
                        base_names.append(inner.id)
                    elif isinstance(inner, ast.Attribute):
                        base_names.append(inner.attr)
            bases[node.name] = base_names
    return methods, bases


def _resolve_methods(
    cls: str,
    methods: dict[str, list[str]],
    bases: dict[str, list[str]],
    seen: set[str] | None = None,
) -> set[str]:
    """Get all methods available on a class, including
    inherited methods from same-file base classes."""
    if seen is None:
        seen = set()
    if cls in seen or cls not in methods:
        return set()
    seen.add(cls)
    result = set(methods[cls])
    for base in bases.get(cls, []):
        result |= _resolve_methods(base, methods, bases, seen)
    return result


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


def _has_external_base(
    cls: str,
    methods: dict[str, list[str]],
    bases: dict[str, list[str]],
    seen: set[str] | None = None,
) -> bool:
    """Check if a class (or any of its same-file ancestors) has
    a base class defined in another module that we can't resolve."""
    if seen is None:
        seen = set()
    if cls in seen:
        return False
    seen.add(cls)
    for base in bases.get(cls, []):
        if base not in methods:
            return True
        if _has_external_base(base, methods, bases, seen):
            return True
    return False


def _extract_imports(source: str) -> dict[str, str]:
    """Map imported class/function names to their module paths.

    Handles `from X import Y` → {"Y": "X"} and
    `import X.Y` → {"X": "X"}.
    Returns name → module_path mapping.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {}

    imports: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                name = alias.asname or alias.name
                imports[name] = module
        elif isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname or alias.name.split(".")[0]
                imports[name] = alias.name
    return imports


def _extract_external_bases(
    source: str,
    methods: dict[str, list[str]],
    bases: dict[str, list[str]],
) -> dict[str, list[str]]:
    """Find external base class names for each class.

    Returns class_name → [external_base_name, ...] for bases that
    come from imports or builtins (anything not defined in this file).
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {}

    imports = _extract_imports(source)
    external_bases: dict[str, list[str]] = {}

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        ext_names = []
        for base in node.bases:
            base_name = None
            if isinstance(base, ast.Name):
                base_name = base.id
            elif isinstance(base, ast.Attribute):
                # e.g., textual.app.App — take last segment
                base_name = base.attr
            elif isinstance(base, ast.Subscript):
                # Generic: ModalScreen[bool] → unwrap to ModalScreen
                inner = base.value
                if isinstance(inner, ast.Name):
                    base_name = inner.id
                elif isinstance(inner, ast.Attribute):
                    base_name = inner.attr
            if not base_name:
                continue
            # External if: imported via from/import, OR not defined in this file
            is_imported = base_name in imports
            is_not_in_file = base_name not in methods
            if is_imported or is_not_in_file:
                ext_names.append(base_name)
        if ext_names:
            external_bases[node.name] = ext_names

    return external_bases


def _try_resolve_external_method(
    class_name: str,
    method_name: str,
    external_bases: dict[str, list[str]],
    imports: dict[str, str],
) -> str:
    """Try to resolve whether a method exists on an external base class.

    Returns:
        "defined" — method confirmed to exist on the external base
        "undefined" — method confirmed to NOT exist
        "unresolved" — couldn't import or inspect the base
    """
    ext_base_names = external_bases.get(class_name, [])
    for base_name in ext_base_names:
        # Try import-map resolution first (for `from X import Y`)
        module_path = imports.get(base_name)

        # Handle builtins (dict, list, Exception, etc.) — no import needed
        base_obj = None
        if module_path:
            try:
                mod = importlib.import_module(module_path)
                base_obj = getattr(mod, base_name, None)
            except Exception:
                pass
        if base_obj is None:
            # Try builtins (dict, list, str, Exception, etc.)
            import builtins
            base_obj = getattr(builtins, base_name, None)

        if base_obj is None:
            continue

        if hasattr(base_obj, method_name):
            return "defined"
        # Check via MRO for inherited methods on class types
        if isinstance(base_obj, type):
            for klass in base_obj.__mro__:
                if method_name in klass.__dict__:
                    return "defined"
            # Found the class, checked MRO, method not there — confirmed undefined
            return "undefined"
    return "unresolved"


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

    class_methods, class_bases = extract_class_methods(source)
    self_calls = extract_self_calls(source)
    imports = _extract_imports(source)
    external_bases = _extract_external_bases(source, class_methods, class_bases)

    findings: list[dict[str, Any]] = []
    for call in self_calls:
        cls = call["class"]
        method = call["method"]
        # Skip dunders — they're framework-provided
        if method.startswith("__") and method.endswith("__"):
            continue
        # Check if method is defined in the class or inherited from same-file bases
        if cls in class_methods:
            available = _resolve_methods(cls, class_methods, class_bases)
            if method not in available:
                # Try to resolve via external base class import
                resolution = _try_resolve_external_method(
                    cls, method, external_bases, imports
                )
                if resolution == "defined":
                    # Confirmed defined on external base — suppress
                    continue
                elif resolution == "undefined":
                    # Confirmed undefined even on external base — real bug
                    confidence = "high"
                    policy = "deterministic_failures"
                    resolution_note = (
                        " (confirmed undefined on external base "
                        f"{external_bases.get(cls, [])} via import resolution)"
                    )
                else:
                    # Couldn't resolve — fall back to confidence scoring
                    has_external = bool(external_bases.get(cls))
                    confidence = "low" if has_external else "high"
                    policy = (
                        "advisory" if has_external
                        else "deterministic_failures"
                    )
                    resolution_note = (
                        " (class has external base classes — "
                        "may be inherited, import resolution failed)"
                        if has_external else ""
                    )
                findings.append({
                    "file": path,
                    "line": call["line"],
                    "method": method,
                    "class": cls,
                    "confidence": confidence,
                    "policy": policy,
                    "resolution": resolution,
                    "issue": (
                        f"self.{method}() called at line "
                        f"{call['line']} but not defined "
                        f"on class {cls}{resolution_note}"
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

    # Count by confidence for status output
    high_conf = sum(1 for f in all_findings if f.get("confidence") == "high")
    low_conf = sum(1 for f in all_findings if f.get("confidence") == "low")

    result = {
        "status": "ok",
        "findings": all_findings,
        "finding_count": len(all_findings),
        "high_confidence_count": high_conf,
        "low_confidence_count": low_conf,
        "files_checked": len(args.paths),
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
