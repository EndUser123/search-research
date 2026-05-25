#!/usr/bin/env python3
from __future__ import annotations

"""
Post-Fix Validation Hook
========================

Validates code fixes immediately after Edit/Write operations.
Prevents common errors like:
- Non-existent method calls
- Broken imports
- Syntax errors
- Missing test verification

Extracted from PostToolUse_fix_validator.py for in-process execution.
"""

import ast
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

# Import base class
from posttooluse.base import PostToolUseHook


class FixValidator(PostToolUseHook):
    """Validates code fixes immediately after Edit operations."""

    env_var = "FIX_VALIDATOR_ENABLED"
    default_enabled = True

    # Code file extensions to validate
    CODE_EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs"}

    # Python built-ins and common methods
    BUILTINS = {
        "print", "len", "str", "int", "float", "list", "dict", "set", "tuple",
        "range", "enumerate", "zip", "map", "filter", "sorted", "sum", "min", "max",
        "abs", "any", "all", "bool", "type", "isinstance", "issubclass", "hasattr",
        "getattr", "setattr", "open", "input", "exec", "eval", "super",
        "append", "extend", "insert", "remove", "pop", "clear", "get", "keys",
        "values", "items", "update", "setdefault", "popitem", "add", "discard",
        "union", "intersection", "difference", "find", "index", "count", "split",
        "strip", "lower", "upper", "replace", "startswith", "endswith", "format",
        "join", "None", "True", "False",
    }

    # Standard library modules
    STDLIB_MODULES = {
        "os", "sys", "re", "json", "pathlib", "datetime", "collections",
        "itertools", "functools", "typing", "dataclasses", "enum", "asyncio",
        "threading", "multiprocessing", "subprocess", "math", "random",
        "statistics", "decimal", "fractions", "io", "string", "textwrap",
        "unicodedata", "codecs", "hashlib", "hmac", "secrets", "uuid",
        "base64", "http", "urllib", "socket", "ssl", "ftplib", "poplib",
        "email", "mimetypes", "html", "xml", "csv", "sqlite3", "dbm",
        "pickle", "shelve", "marshal",
    }

    def __init__(self):
        super().__init__()
        self.hooks_dir = Path(__file__).resolve().parent.parent
        self.validation_log = self.hooks_dir / "data" / "fix_validations.jsonl"
        self.catch_log = self.hooks_dir / "data" / "fix_validator_catches.jsonl"
        self.validation_log.parent.mkdir(parents=True, exist_ok=True)

    def process(self, tool_name: str, tool_input: dict[str, Any], tool_response: dict[str, Any]) -> dict[str, Any]:
        """
        Validate a code fix after Edit/Write operation.

        Returns dict with validation results.
        """
        result = {
            "passed": True,
            "status": "PASS",
            "issues": [],
            "injection": None,
        }

        # Only validate Edit/Write operations
        if tool_name not in ("Edit", "Write"):
            return result

        file_path = tool_input.get("file_path", "")
        if not file_path:
            return result

        # Skip validation for non-code files
        if not self._is_code_file(file_path):
            result["status"] = "SKIP"
            return result

        # Get content for validation
        # CRITICAL: Read from disk for BOTH Edit and Write operations (trust but verify)
        new_content = ""
        try:
            with open(file_path) as f:
                new_content = f.read()
        except FileNotFoundError:
            # File doesn't exist after Write/Edit - this is critical
            result["status"] = "FAIL"
            result["issues"].append({
                "type": "FILE_NOT_FOUND",
                "severity": "CRITICAL",
                "message": f"File not found after {tool_name} operation: {file_path}",
            })
            result["injection"] = self._format_injection(file_path, result["issues"])
            self._log_catch(file_path, result["status"], result["issues"])
            return result
        except Exception:
            return result  # Can't read file, skip validation

        # 1. Syntax Check
        syntax_ok, syntax_error = self._check_syntax(new_content, file_path)
        if not syntax_ok:
            result["status"] = "FAIL"
            result["issues"].append({
                "type": "SYNTAX_ERROR",
                "severity": "CRITICAL",
                "message": syntax_error,
            })
            result["injection"] = self._format_injection(file_path, result["issues"])
            self._log_catch(file_path, result["status"], result["issues"])
            return result

        # 2. Extract new method/function calls
        new_calls = self._extract_new_calls("", new_content)

        # 3. Validate each new call
        for call in new_calls:
            call_validation = self._validate_method_call(call, new_content, file_path)
            if not call_validation["exists"]:
                result["status"] = "WARN"
                result["issues"].append({
                    "type": "UNDEFINED_METHOD",
                    "severity": "HIGH",
                    "message": f"Called method `{call}` may not exist in the current scope",
                    "suggestion": f"Verify `{call}` is defined or imported",
                })

        # 4. Import validation
        import_issues = self._validate_imports(new_content, file_path)
        if import_issues:
            result["status"] = "WARN" if result["status"] == "PASS" else "FAIL"
            result["issues"].extend(import_issues)

        # Log catches and create injection if issues found
        if result["status"] in ("WARN", "FAIL") and result["issues"]:
            self._log_catch(file_path, result["status"], result["issues"])
            result["injection"] = self._format_injection(file_path, result["issues"])

        return result

    def _is_code_file(self, file_path: str) -> bool:
        """Check if file is a code file that needs validation."""
        return any(file_path.endswith(ext) for ext in self.CODE_EXTENSIONS)

    def _check_syntax(self, content: str, file_path: str) -> tuple[bool, str | None]:
        """Check syntax of the content."""
        if file_path.endswith(".py"):
            try:
                ast.parse(content)
                return True, None
            except SyntaxError as e:
                return False, f"Line {e.lineno}: {e.msg}"
        return True, None  # Skip syntax check for non-Python files

    def _extract_new_calls(self, old_content: str, new_content: str) -> list[str]:
        """Extract newly added method/function calls."""
        new_lines = [line for line in new_content.split("\n") if line not in old_content.split("\n")]
        new_calls = []

        call_patterns = [
            r"self\._?(\w+)\(",
            r"self\.(\w+)\(",
            r"(\w+)\.\s*(\w+)\(",
            r"(\w+)\(",
        ]

        for line in new_lines:
            for pattern in call_patterns:
                matches = re.finditer(pattern, line)
                for match in matches:
                    if match.groups():
                        method_name = match.groups()[-1]
                        if not self._is_builtin(method_name):
                            new_calls.append(method_name)

        return list(set(new_calls))

    def _is_builtin(self, name: str) -> bool:
        """Check if name is a Python builtin or common method."""
        return name in self.BUILTINS

    def _validate_method_call(self, method_name: str, content: str, file_path: str) -> dict[str, Any]:
        """Validate if a method call is likely to exist."""
        is_defined = False

        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if node.name == method_name:
                        is_defined = True
                        break
                elif isinstance(node, ast.AsyncFunctionDef):
                    if node.name == method_name:
                        is_defined = True
                        break
        except SyntaxError:
            pass

        import_patterns = [rf"from .* import .*{method_name}", rf"import .*{method_name}"]
        is_imported = any(re.search(pattern, content) for pattern in import_patterns)

        return {
            "method": method_name,
            "exists": is_defined or is_imported,
            "defined_locally": is_defined,
            "likely_imported": is_imported,
        }

    def _validate_imports(self, content: str, file_path: str) -> list[dict[str, Any]]:
        """Validate imports in the content."""
        issues = []

        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if not self._check_import_available(alias.name):
                            issues.append({
                                "type": "IMPORT_ERROR",
                                "severity": "MEDIUM",
                                "message": f"Import `{alias.name}` may not be available",
                                "suggestion": f"Verify `{alias.name}` is installed",
                            })
                elif isinstance(node, ast.ImportFrom):
                    if node.module and not self._check_import_available(node.module):
                        issues.append({
                            "type": "IMPORT_ERROR",
                            "severity": "MEDIUM",
                            "message": f"Import from `{node.module}` may not be available",
                            "suggestion": f"Verify `{node.module}` is installed",
                        })
        except SyntaxError:
            pass

        return issues

    def _check_import_available(self, module_name: str) -> bool:
        """Check if an import is likely available."""
        if module_name.split(".")[0] in self.STDLIB_MODULES:
            return True

        # Common third-party libraries
        common_third_party = {
            "requests", "numpy", "pandas", "pytest", "click", "typer",
            "pydantic", "fastapi", "sqlalchemy", "alembic", "flask",
            "django", "aiohttp", "httpx", "rich", "tqdm",
        }
        if module_name.split(".")[0] in common_third_party:
            return True

        # Project-specific imports
        if module_name.startswith("src.") or module_name.startswith("__csf"):
            return True

        return False

    def _format_injection(self, file_path: str, issues: list[dict]) -> str:
        """Format issues as injection message."""
        lines = [
            "",
            "⚠️ FIX VALIDATION WARNING",
            f"File: {Path(file_path).name}",
            ""
        ]

        for issue in issues:
            lines.append(f"  [{issue['severity']}] {issue['type']}")
            if "message" in issue:
                lines.append(f"    {issue['message']}")
            if "suggestion" in issue:
                lines.append(f"    Suggestion: {issue['suggestion']}")

        lines.append("")
        return "\n".join(lines)

    def _log_catch(self, file_path: str, status: str, issues: list[dict]) -> None:
        """Log when we actually catch something (for value assessment)."""
        try:
            with open(self.catch_log, "a") as f:
                f.write(json.dumps({
                    "timestamp": datetime.now().isoformat(),
                    "file": file_path,
                    "status": status,
                    "issues": issues
                }) + "\n")
        except Exception:
            pass  # Don't fail if logging fails
