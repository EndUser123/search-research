#!/usr/bin/env python3
"""
Deep Lens Framework - 6-lens code review system.

Provides systematic multi-dimensional code analysis across:
1. State/Edge-Case Lens - State management and edge cases
2. Identity/Invariants Lens - Identity preservation and invariants
3. I/O Validation Lens - Input/output and validation
4. Concurrency Lens - Race conditions and atomic operations
5. Errors/Logging Lens - Error paths and logging
6. Tests/Coverage Lens - Test coverage
"""

import ast
import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LensResult:
    """Result from a single lens verification.

    Attributes:
        status: Overall status ("pass", "fail", "skip")
        lens_name: Name of the lens that produced this result
        findings: List of detailed findings
        severity: Severity level ("info", "low", "medium", "high", "critical")
    """

    status: str
    lens_name: str
    findings: list[str] = field(default_factory=list)
    severity: str = "medium"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "status": self.status,
            "lens_name": self.lens_name,
            "findings": self.findings,
            "severity": self.severity,
        }


class StateEdgeCaseLens:
    """Verify state management and edge cases.

    Checks:
    - State initialization
    - Edge case handling (empty, None, boundary conditions)
    - Defensive programming for list/dict/string access
    """

    lens_name = "state_edge_case"

    def _find_parent(self, node: ast.AST, parent_map: dict[ast.AST, ast.AST]) -> ast.AST | None:
        """Find parent of node in parent_map."""
        current = node
        while current in parent_map:
            current = parent_map[current]
            if isinstance(current, ast.If):
                return current
        return None

    def _is_defensively_guarded(
        self, subscript: ast.Subscript, parent_map: dict[ast.AST, ast.AST]
    ) -> bool:
        """Check if a subscript access is guarded by a defensive check.

        Three patterns are recognized as defensive guards:
        1. Subscript inside if body with positive check (if 'key' in data: return data['key'])
        2. Subscript inside if orelse with negative check (if 'key' not in data: ... else: return data['key'])
        3. Early return: if statement before subscript has early return (if 'key' not in data: return; ... x = data['key'])
        """
        # First check: subscript inside if body/orelse
        current = subscript
        if_node = None
        in_orelse = False

        while current in parent_map:
            current = parent_map[current]
            if isinstance(current, ast.If):
                if_node = current
                if self._is_in_orelse(subscript, if_node, parent_map):
                    in_orelse = True
                break

        if if_node is not None:
            # Pattern 1 & 2: Subscript is inside an if branch
            test_str = ast.unparse(if_node.test)

            if isinstance(subscript.slice, ast.Constant):
                key = subscript.slice.value
                if isinstance(key, str):
                    container = ast.unparse(subscript.value)

                    if in_orelse:
                        # Pattern 2: Guarded by 'not in' check, subscript in orelse
                        if (
                            f"'{key}' not in {container}" in test_str
                            or f'"{key}" not in {container}' in test_str
                        ):
                            return True
                        # Also: Guarded by 'in' check, subscript in body (but we're in orelse, so this means key exists)
                        if (
                            f"'{key}' in {container}" in test_str
                            or f'"{key}" in {container}' in test_str
                        ):
                            return True
                    else:
                        # Pattern 1: Subscript in body branch - need positive 'in' check
                        if (
                            f"'{key}' in {container}" in test_str
                            or f'"{key}" in {container}' in test_str
                        ):
                            return True
            elif isinstance(subscript.slice, (ast.Index, ast.Constant)):
                container = ast.unparse(subscript.value)
                if f"{container} and" in test_str:
                    return True

        # Pattern 3: Check for early return guard (if statement before subscript with early return)
        if self._has_early_return_guard(subscript, parent_map):
            return True

        return False

    def _has_early_return_guard(
        self, subscript: ast.Subscript, parent_map: dict[ast.AST, ast.AST]
    ) -> bool:
        """Check if there's an if statement with early return before the subscript.

        Pattern: if 'key' not in data: return None; ... x = data['key']
        The if statement comes before the subscript and returns early if guard condition is true.
        """
        # Find the function containing the subscript
        func_node = None
        current = subscript
        while current in parent_map:
            if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_node = current
                break
            current = parent_map[current]

        if func_node is None:
            return False

        # Get subscript position in function body
        subscript_index = self._find_statement_index(subscript, func_node, parent_map)
        if subscript_index is None:
            return False

        # Check all if statements before the subscript
        for i in range(subscript_index):
            stmt = func_node.body[i]
            if isinstance(stmt, ast.If):
                # Check if this if has early return and guards the subscript
                if self._if_guard_matches_subscript(stmt, subscript):
                    return True

        return False

    def _find_statement_index(
        self,
        node: ast.AST,
        func_node: ast.FunctionDef | ast.AsyncFunctionDef,
        parent_map: dict[ast.AST, ast.AST],
    ) -> int | None:
        """Find the index of a statement in the function body.

        Walks up from node to find which statement in func_node.body contains it.
        """
        # Walk up from node until we hit a direct child of func_node
        current = node
        while current in parent_map:
            parent = parent_map[current]
            if parent is func_node:
                # current is a direct child of func_node
                for i, stmt in enumerate(func_node.body):
                    if stmt is current:
                        return i
            current = parent
        return None

    def _if_guard_matches_subscript(self, if_node: ast.If, subscript: ast.Subscript) -> bool:
        """Check if an if statement guards the subscript via early return pattern.

        Returns True if:
        1. If test contains 'key' not in container (negative guard)
        2. If body contains an early return
        3. Container and key match the subscript
        """
        # Check for early return in if body
        if not self._has_early_return(if_node.body):
            return False

        # Extract test condition
        test_str = ast.unparse(if_node.test)

        # Extract container and key from subscript
        if isinstance(subscript.slice, ast.Constant):
            key = subscript.slice.value
            if isinstance(key, str):
                container = ast.unparse(subscript.value)

                # Check if test is 'key' not in container
                if (
                    f"'{key}' not in {container}" in test_str
                    or f'"{key}" not in {container}' in test_str
                ):
                    return True

        return False

    def _has_early_return(self, stmt_list: list[ast.stmt]) -> bool:
        """Check if a statement list contains an early return.

        Early return means ast.Return appears before any other significant work.
        For guard purposes, any return in the body counts.
        """
        for stmt in stmt_list:
            if isinstance(stmt, ast.Return):
                return True
            # Don't recurse into nested if/for/while - only check top-level returns
        return False

    def _is_in_orelse(
        self, node: ast.AST, if_node: ast.If, parent_map: dict[ast.AST, ast.AST]
    ) -> bool:
        """Check if a node is in the orelse branch of an if statement."""
        current = node
        while current in parent_map and current is not if_node:
            current = parent_map[current]
            # Check if we're in any orelse node
            if isinstance(current, tuple) or hasattr(current, "__class__"):
                # Walk up the orelse chain
                temp = current
                while temp in parent_map and temp is not if_node:
                    temp = parent_map[temp]

        # More direct approach: check if node is descendant of any orelse node
        for orelse_node in if_node.orelse:
            if self._is_descendant(node, orelse_node, parent_map):
                return True
        return False

    def _is_descendant(
        self, potential_descendant: ast.AST, ancestor: ast.AST, parent_map: dict[ast.AST, ast.AST]
    ) -> bool:
        """Check if potential_descendant is a descendant of ancestor."""
        current = potential_descendant
        while current in parent_map:
            if current is ancestor:
                return True
            current = parent_map[current]
        return False

    def verify(self, code: str, context: dict[str, Any]) -> LensResult:
        """Verify code for state management and edge cases."""
        findings = []
        severity = "medium"

        # Parse AST
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return LensResult(
                status="skip",
                lens_name=self.lens_name,
                findings=["Syntax error - cannot analyze"],
                severity="critical",
            )

        # Build parent map to find enclosing if statements
        parent_map: dict[ast.AST, ast.AST] = {}
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                parent_map[child] = node

        # Check for subscript access patterns
        for node in ast.walk(tree):
            if isinstance(node, ast.Subscript):
                if isinstance(node.value, ast.Name):
                    access_expr = ast.unparse(node)
                    if not self._is_defensively_guarded(node, parent_map):
                        findings.append(f"Uninitialized state access: {access_expr}")

        # Check for potential boundary/empty issues
        # Look for range(len(x)) pattern without preceding if
        range_match = re.search(r"range\(len\([^)]+\)\)", code)
        if range_match:
            range_start = range_match.start()
            if "if" not in code[:range_start]:
                findings.append("Missing boundary or empty check")

        status = "fail" if findings else "pass"
        return LensResult(
            status=status, lens_name=self.lens_name, findings=findings, severity=severity
        )


class IdentityInvariantsLens:
    """Verify identity preservation and invariants.

    Checks:
    - Mutable default arguments
    - Invariant assertions
    - Object identity comparisons
    """

    lens_name = "identity_invariants"

    def verify(self, code: str, context: dict[str, Any]) -> LensResult:
        """Verify code for identity and invariant issues."""
        findings = []

        # Check for mutable default arguments
        mutable_defaults = re.findall(r"def\s+\w+\([^)]*=\s*\[[^\]]*\]", code)
        if mutable_defaults:
            findings.append(f"Mutable default argument detected: {mutable_defaults}")

        # Check for missing assertions in classes with __init__
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    has_init = any(
                        isinstance(n, ast.FunctionDef) and n.name == "__init__" for n in node.body
                    )
                    has_asserts = False
                    for child in ast.walk(node):
                        if isinstance(child, ast.Assert):
                            has_asserts = True
                            break

                    if has_init and not has_asserts:
                        findings.append(
                            f"Class {node.name} has __init__ but no invariant assertions"
                        )
        except SyntaxError:
            pass

        # Check for is vs == usage (heuristic)
        if " is " in code and " is not " not in code:
            findings.append("Using 'is' for comparison (should use == for value equality)")

        status = "fail" if findings else "pass"
        return LensResult(status=status, lens_name=self.lens_name, findings=findings)


class IOLens:
    """Verify input/output and validation.

    Checks:
    - Input validation
    - Output sanitization
    - Schema compliance
    - Path validation
    """

    lens_name = "io"

    def verify(self, code: str, context: dict[str, Any]) -> LensResult:
        """Verify code for I/O validation issues."""
        findings = []

        # Check for file operations without validation
        if re.search(r"open\([^)]+\)", code):
            has_validation = bool(
                re.search(r"if\s+.*?(?:filename|path)", code, re.DOTALL)
                or re.search(r"raise\s+ValueError", code)
                or re.search(r"isinstance", code)
            )
            if not has_validation:
                findings.append("File open without validation")

        # Check for HTML output without escaping
        # Look for HTML tags in code
        has_html_tags = bool(re.search(r"<[^>]+>", code))
        # Check for f-strings with braces (potential interpolation)
        has_interpolation = bool(re.search(r'f["\'].*?\{.*?\}.*?["\']', code))
        # Check for escape/sanitize functions
        has_escape = bool(
            re.search(r"(html\.escape|escape|sanitize|cgi\.escape)", code, re.IGNORECASE)
        )

        if has_html_tags and has_interpolation and not has_escape:
            findings.append("HTML output without escape")

        # Check for SQL injection patterns
        sql_patterns = [
            (r'f["\']SELECT.*?\{.*?\}.*?FROM', "f-string SQL query"),
            (r'["\']SELECT.*?%s.*?FROM', "%-format SQL query"),
        ]
        for pattern, desc in sql_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                findings.append(f"Potential SQL injection - {desc}")

        status = "fail" if findings else "pass"
        return LensResult(status=status, lens_name=self.lens_name, findings=findings)


class ConcurrencyLens:
    """Verify concurrency and TOCTOU safety.

    Checks:
    - Race conditions
    - Atomic operations
    - Locking
    """

    lens_name = "concurrency"

    def verify(self, code: str, context: dict[str, Any]) -> LensResult:
        """Verify code for concurrency issues."""
        findings = []

        # Check for global variable access without locks
        # Be specific about what constitutes a lock (threading.Lock, with lock, etc.)
        has_global = "global " in code
        # Look for actual lock usage patterns, not just the word "lock"
        has_actual_lock = bool(
            re.search(r"threading\.Lock\(\)|mutex\s*=\s*Lock\(\)|with\s+lock:", code)
            or re.search(r"lock\s*=\s*threading\.(Lock|RLock|Semaphore)", code)
        )

        if has_global and not has_actual_lock:
            findings.append("Global variable access without locking")

        # Check for TOCTOU patterns
        toctou_patterns = [
            (
                r"os\.path\.exists.*?(?:open|read|write)",
                "TOCTOU race: exists() then file operation",
            ),
            (
                r"os\.path\.isfile.*?(?:open|read|write)",
                "TOCTOU race: isfile() then file operation",
            ),
        ]

        for pattern, desc in toctou_patterns:
            if re.search(pattern, code, re.DOTALL):
                findings.append(desc)

        # Check for threading without locks
        if re.search(r"(threading\.Thread|Thread\()", code) and not has_actual_lock:
            findings.append("Threading code without locks")

        status = "fail" if findings else "pass"
        return LensResult(status=status, lens_name=self.lens_name, findings=findings)


class ErrorsLens:
    """Verify error handling and logging.

    Checks:
    - Error paths
    - Logging
    - Graceful degradation
    """

    lens_name = "errors"

    def verify(self, code: str, context: dict[str, Any]) -> LensResult:
        """Verify code for error handling issues."""
        findings = []

        # Check for bare except clauses
        if re.search(r"except\s*:", code):
            findings.append("Bare except clause - catches all exceptions")

        # Check for except with pass (swallowed exceptions)
        # Look for "except:" or "except X:" followed by pass
        if re.search(r"except\s*(?:\w+)?\s*:\s*pass", code):
            findings.append("Exception caught but only pass (swallowed error)")

        # Check for file operations without try/except
        has_file_ops = bool(re.search(r"(open|\.read|\.write)\(", code))
        has_try_except = bool(re.search(r"try\s*:", code))

        if has_file_ops and not has_try_except:
            findings.append("File operations without error handling")

        # Check for risky operations without logging
        risky_keywords = ["database", "network", "api", "http"]
        code_lower = code.lower()
        for keyword in risky_keywords:
            if keyword in code_lower and "logging" not in code_lower:
                findings.append(f"Risky operation ({keyword}) without logging")
                break

        status = "fail" if findings else "pass"
        return LensResult(status=status, lens_name=self.lens_name, findings=findings)


class TestsLens:
    """Verify test coverage.

    Checks:
    - Coverage percentage
    - Missing scenarios
    - Test quality
    """

    lens_name = "tests"

    def verify(self, code: str, context: dict[str, Any]) -> LensResult:
        """Verify code for test coverage issues."""
        findings = []
        coverage_info = context.get("coverage", {})
        tests = context.get("tests", "")

        # Check coverage percentage
        percent_covered = coverage_info.get("percent_covered", 0)
        if percent_covered < 80.0:
            findings.append(f"Low test coverage: {percent_covered:.1f}% (threshold: 80%)")

        # Check for missing edge case tests
        if "def " in code:
            functions = re.findall(r"def\s+(\w+)\([^)]*\):", code)
            for func in functions:
                # Determine which edge cases are relevant based on function parameters
                edge_cases = []
                code_lower = code.lower()

                # Collection/sequence parameters need 'empty' and 'none' tests
                if any(p in code_lower for p in ["items", "data", "list", "collection", "array"]):
                    edge_cases.extend(["empty", "none"])

                # Numeric parameters need 'zero' and 'negative' tests
                if any(
                    p in code_lower for p in ["count", "num", "value", "amount", "size", "index"]
                ):
                    edge_cases.extend(["zero", "negative"])

                # String parameters need 'empty' tests
                if any(p in code_lower for p in ["name", "text", "str", "string"]):
                    edge_cases.append("empty")

                # Only check for tests if we identified relevant edge cases
                if edge_cases:
                    tests_lower = tests.lower()
                    missing_cases = [case for case in edge_cases if case not in tests_lower]

                    if missing_cases:
                        findings.append(
                            f"Function {func}: missing edge case tests ({', '.join(missing_cases)})"
                        )

        # Check for assert statements in tests
        if "def test_" in tests and "assert" not in tests:
            findings.append("Test functions exist but no assertions found")

        # Check for test complexity (single assert vs multiple scenarios)
        test_funcs = re.findall(r"def\s+(test_\w+)\([^)]*\):", tests)
        if test_funcs and len(test_funcs) == 1:
            findings.append("Only 1 test function - consider testing multiple scenarios")

        status = "fail" if findings else "pass"
        return LensResult(status=status, lens_name=self.lens_name, findings=findings)


class DeepLensVerifier:
    """Coordinator for all 6 lenses.

    Runs all lenses and aggregates results.
    """

    def __init__(self, coverage_threshold: float = 80.0):
        """
        Initialize verifier with configuration.

        Args:
            coverage_threshold: Minimum acceptable coverage percentage
        """
        self.coverage_threshold = coverage_threshold
        self.lenses = [
            StateEdgeCaseLens(),
            IdentityInvariantsLens(),
            IOLens(),
            ConcurrencyLens(),
            ErrorsLens(),
            TestsLens(),
        ]

    def verify(self, code: str, context: dict[str, Any]) -> dict[str, Any]:
        """
        Run all 6 lenses on the code.

        Args:
            code: Python code to analyze
            context: Additional context (file, coverage, tests, etc.)

        Returns:
            Dictionary with results from each lens plus overall_status.
            Each lens result is a LensResult object (not a dict).
        """
        results = {}

        # Add coverage threshold to context for TestsLens
        context_with_threshold = {**context, "coverage_threshold": self.coverage_threshold}

        for lens in self.lenses:
            lens_result = lens.verify(code, context_with_threshold)
            results[lens.lens_name] = lens_result

        # Determine overall status (all lenses must pass)
        all_pass = all(r.status == "pass" for r in results.values())

        results["overall_status"] = "pass" if all_pass else "fail"

        return results
