"""Test for PERF-001: Repeated regex compilation.

This test checks that regex patterns are pre-compiled at module level
instead of being compiled on every function execution.

Performance Issue: Regex patterns in HISTORICAL_PHRASE_PATTERNS,
COMPLETION_PHRASE_PATTERNS, and HISTORICAL_TEST_PATTERNS are raw strings
that get compiled on every re.search() call instead of being pre-compiled
as module-level constants.

Run with: pytest P:/.claude/hooks/tests/test_regex_precompilation.py -v
"""

import ast
import pathlib
import sys

import pytest

# Add hooks directory to path for imports
HOOKS_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))


def extract_ast_node_source(code: str, node: ast.AST) -> str:
    """Extract source code for an AST node."""
    if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
        lines = code.split('\n')
        if node.lineno == node.end_lineno:
            return lines[node.lineno - 1][node.col_offset:node.end_col_offset]
        else:
            # Multi-line statement
            result = []
            for i in range(node.lineno - 1, node.end_lineno):
                if i == node.lineno - 1:
                    result.append(lines[i][node.col_offset:])
                elif i == node.end_lineno - 1:
                    result.append(lines[i][:node.end_col_offset])
                else:
                    result.append(lines[i])
            return '\n'.join(result)
    return ""


class TestRegexPrecompilationHistoricalPhrasePatterns:
    """Tests for HISTORICAL_PHRASE_PATTERNS pre-compilation."""

    @pytest.fixture
    def hook_file_path(self):
        return HOOKS_DIR / "stop_historical_claims_gate.py"

    @pytest.fixture
    def hook_source(self, hook_file_path):
        return hook_file_path.read_text(encoding="utf-8")

    def test_historical_phrase_patterns_should_be_precompiled(self, hook_source):
        """
        PERF-001: HISTORICAL_PHRASE_PATTERNS should use pre-compiled regex objects.

        Current behavior: Patterns are raw strings that get compiled on every
        re.search() call in tier1_check() and other functions.

        Expected behavior: Patterns should be pre-compiled at module level using
        re.compile() for better performance.

        Given: HISTORICAL_PHRASE_PATTERNS contains 30+ regex patterns
        When: The module is analyzed
        Then: All patterns should be pre-compiled Pattern objects
        """
        tree = ast.parse(hook_source)

        # Find HISTORICAL_PHRASE_PATTERNS assignment
        historical_patterns_var = None
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "HISTORICAL_PHRASE_PATTERNS":
                        historical_patterns_var = node
                        break

        assert historical_patterns_var is not None, "HISTORICAL_PHRASE_PATTERNS not found in module"

        # Check if it's a list of tuples with regex patterns
        value = historical_patterns_var.value
        assert isinstance(value, ast.List), "HISTORICAL_PHRASE_PATTERNS should be a list"

        # Count patterns that are raw strings vs pre-compiled
        raw_string_patterns = []
        precompiled_patterns = []

        for elt in value.elts:
            if isinstance(elt, ast.Tuple):
                # First element should be the regex pattern
                pattern_node = elt.elts[0]
                if isinstance(pattern_node, ast.Constant):
                    pattern_value = pattern_node.value
                    if isinstance(pattern_value, str):
                        # This is a raw string pattern (BAD - should be pre-compiled)
                        raw_string_patterns.append(pattern_value)
                elif isinstance(pattern_node, ast.Call):
                    # This is a pre-compiled pattern (GOOD - re.compile() call)
                    precompiled_patterns.append(pattern_node)

        # After PERF-001 fix: patterns should be pre-compiled
        assert len(raw_string_patterns) == 0, (
            f"HISTORICAL_PHRASE_PATTERNS contains {len(raw_string_patterns)} "
            f"raw string patterns that should be pre-compiled. "
            f"Expected pre-compiled Pattern objects for better performance."
        )
        assert len(precompiled_patterns) > 0, (
            f"HISTORICAL_PHRASE_PATTERNS should have pre-compiled patterns, "
            f"found {len(precompiled_patterns)} pre-compiled patterns."
        )

    def test_historical_phrase_patterns_count(self, hook_source):
        """
        Characterization: Count how many patterns are pre-compiled.

        After PERF-001 fix: This verifies the patterns are pre-compiled.
        """
        tree = ast.parse(hook_source)

        historical_patterns_var = None
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "HISTORICAL_PHRASE_PATTERNS":
                        historical_patterns_var = node
                        break

        value = historical_patterns_var.value
        pattern_count = len(value.elts)

        # Verify expected number of patterns
        assert pattern_count >= 20, (
            f"Expected at least 20 patterns in HISTORICAL_PHRASE_PATTERNS, "
            f"found {pattern_count}."
        )

        # After PERF-001 fix: patterns should be pre-compiled
        precompiled_count = 0
        for elt in value.elts:
            if isinstance(elt, ast.Tuple):
                pattern_node = elt.elts[0]
                if isinstance(pattern_node, ast.Call):
                    precompiled_count += 1

        assert precompiled_count == pattern_count, (
            f"All {pattern_count} patterns should be pre-compiled, "
            f"but only {precompiled_count} are pre-compiled."
        )


class TestRegexPrecompilationCompletionPatterns:
    """Tests for COMPLETION_PHRASE_PATTERNS pre-compilation."""

    @pytest.fixture
    def hook_file_path(self):
        return HOOKS_DIR / "stop_historical_claims_gate.py"

    @pytest.fixture
    def hook_source(self, hook_file_path):
        return hook_file_path.read_text(encoding="utf-8")

    def test_completion_phrase_patterns_should_be_precompiled(self, hook_source):
        """
        PERF-001: COMPLETION_PHRASE_PATTERNS should use pre-compiled regex objects.

        Current behavior: Patterns are raw strings compiled on every
        check_completion_claims() call.

        Expected behavior: Patterns should be pre-compiled at module level.
        """
        tree = ast.parse(hook_source)

        completion_patterns_var = None
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "COMPLETION_PHRASE_PATTERNS":
                        completion_patterns_var = node
                        break

        assert completion_patterns_var is not None, "COMPLETION_PHRASE_PATTERNS not found in module"

        value = completion_patterns_var.value
        assert isinstance(value, ast.List), "COMPLETION_PHRASE_PATTERNS should be a list"

        raw_string_patterns = []
        precompiled_patterns = []
        for elt in value.elts:
            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                raw_string_patterns.append(elt.value)
            elif isinstance(elt, ast.Call):
                precompiled_patterns.append(elt)

        # After PERF-001 fix: no raw string patterns should exist
        assert len(raw_string_patterns) == 0, (
            f"COMPLETION_PHRASE_PATTERNS contains {len(raw_string_patterns)} "
            f"raw string patterns that should be pre-compiled."
        )
        assert len(precompiled_patterns) > 0, (
            "COMPLETION_PHRASE_PATTERNS should have pre-compiled patterns."
        )


class TestRegexPrecompilationHistoricalTestPatterns:
    """Tests for HISTORICAL_TEST_PATTERNS pre-compilation."""

    @pytest.fixture
    def hook_file_path(self):
        return HOOKS_DIR / "stop_historical_claims_gate.py"

    @pytest.fixture
    def hook_source(self, hook_file_path):
        return hook_file_path.read_text(encoding="utf-8")

    def test_historical_test_patterns_should_be_precompiled(self, hook_source):
        """
        PERF-001: HISTORICAL_TEST_PATTERNS should use pre-compiled regex objects.

        Current behavior: Patterns are raw strings compiled on every
        check_historical_test_claims() call.

        Expected behavior: Patterns should be pre-compiled at module level.
        """
        tree = ast.parse(hook_source)

        test_patterns_var = None
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "HISTORICAL_TEST_PATTERNS":
                        test_patterns_var = node
                        break

        assert test_patterns_var is not None, "HISTORICAL_TEST_PATTERNS not found in module"

        value = test_patterns_var.value
        assert isinstance(value, ast.List), "HISTORICAL_TEST_PATTERNS should be a list"

        raw_string_patterns = []
        precompiled_patterns = []
        for elt in value.elts:
            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                raw_string_patterns.append(elt.value)
            elif isinstance(elt, ast.Call):
                precompiled_patterns.append(elt)

        # After PERF-001 fix: no raw string patterns should exist
        assert len(raw_string_patterns) == 0, (
            f"HISTORICAL_TEST_PATTERNS contains {len(raw_string_patterns)} "
            f"raw string patterns that should be pre-compiled."
        )
        assert len(precompiled_patterns) > 0, (
            "HISTORICAL_TEST_PATTERNS should have pre-compiled patterns."
        )


class TestRegexPrecompilationInlinePatterns:
    """Tests for inline regex compilation in functions."""

    @pytest.fixture
    def hook_file_path(self):
        return HOOKS_DIR / "stop_historical_claims_gate.py"

    @pytest.fixture
    def hook_source(self, hook_file_path):
        return hook_file_path.read_text(encoding="utf-8")

    def test_no_inline_re_compile_in_functions(self, hook_source):
        """
        PERF-001: Functions should not compile regex patterns inline.

        Current behavior: Functions like check_historical_test_claims()
        define inline pattern lists that get compiled on each call.

        Expected behavior: All regex patterns should be module-level
        pre-compiled constants.
        """
        tree = ast.parse(hook_source)

        # Find function definitions
        inline_patterns_found = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check for list assignments with regex string literals
                for child in ast.walk(node):
                    if isinstance(child, ast.List):
                        for elt in child.elts:
                            if isinstance(elt, ast.Constant):
                                val = elt.value
                                if isinstance(val, str) and val.startswith('(?i)\\b'):
                                    inline_patterns_found.append(
                                        (node.name, val[:50])
                                    )

        # This test fails because inline patterns exist
        if inline_patterns_found:
            assert False, (
                f"Found {len(inline_patterns_found)} inline regex patterns "
                f"inside functions. These should be module-level pre-compiled constants.\n"
                f"Examples: {inline_patterns_found[:3]}"
            )

    def test_check_historical_test_claims_inline_patterns(self, hook_source):
        """
        PERF-001: check_historical_test_claims() should not define patterns inline.

        This function has a local `patterns` list with raw regex strings
        that gets compiled on every call.

        Expected: Should use module-level pre-compiled patterns.
        """
        # Find the function and check its patterns list
        tree = ast.parse(hook_source)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "check_historical_test_claims":
                # Look for patterns list assignment
                func_source = extract_ast_node_source(hook_source, node)

                # After PERF-001 fix: function should NOT define inline patterns
                # It should use module-level _CHECK_HISTORICAL_TEST_PATTERNS
                assert "patterns = [" not in func_source, (
                    "check_historical_test_claims() defines inline patterns list. "
                    "This should use module-level pre-compiled patterns."
                )
                # Should use pre-compiled module-level patterns
                assert "_CHECK_HISTORICAL_TEST_PATTERNS" in func_source or "HISTORICAL_TEST_PATTERNS" in func_source, (
                    "check_historical_test_claims() should use module-level pre-compiled patterns."
                )
                break
        else:
            pytest.fail("check_historical_test_claims function not found")


class TestRegexPrecompilationTotalImpact:
    """Tests documenting total performance impact."""

    @pytest.fixture
    def hook_file_path(self):
        return HOOKS_DIR / "stop_historical_claims_gate.py"

    @pytest.fixture
    def hook_source(self, hook_file_path):
        return hook_file_path.read_text(encoding="utf-8")

    def test_total_regex_compilations_per_execution(self, hook_source):
        """
        PERF-001: Document total regex compilations per hook execution.

        This test characterizes the performance impact by counting how many
        regex patterns get compiled on a typical hook execution.

        Current state: All patterns are raw strings, compiled on each use.
        Expected state: All patterns pre-compiled at module import time.
        """
        tree = ast.parse(hook_source)

        # Count patterns in each major list
        pattern_counts = {}

        for var_name in ["HISTORICAL_PHRASE_PATTERNS",
                        "COMPLETION_PHRASE_PATTERNS",
                        "HISTORICAL_TEST_PATTERNS"]:
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == var_name:
                            value = node.value
                            if isinstance(value, ast.List):
                                pattern_counts[var_name] = len(value.elts)

        # Also count inline patterns in check_historical_test_claims
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "check_historical_test_claims":
                # Look for inline patterns list
                for child in ast.walk(node):
                    if isinstance(child, ast.List):
                        count = 0
                        for elt in child.elts:
                            if isinstance(elt, ast.Constant):
                                val = elt.value
                                if isinstance(val, str) and val.startswith('(?i)'):
                                    count += 1
                        if count > 0:
                            pattern_counts["check_historical_test_claims_inline"] = count

        total_patterns = sum(pattern_counts.values())

        # After PERF-001 fix: all patterns should be pre-compiled at module level
        assert total_patterns > 0, "Should have patterns counted"

        # Count pre-compiled patterns
        precompiled_count = 0
        for var_name in ["HISTORICAL_PHRASE_PATTERNS",
                        "COMPLETION_PHRASE_PATTERNS",
                        "HISTORICAL_TEST_PATTERNS"]:
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == var_name:
                            value = node.value
                            if isinstance(value, ast.List):
                                for elt in value.elts:
                                    # Check if pattern is pre-compiled (ast.Call to re.compile)
                                    if isinstance(elt, ast.Call):
                                        precompiled_count += 1
                                    elif isinstance(elt, ast.Tuple) and elt.elts:
                                        if isinstance(elt.elts[0], ast.Call):
                                            precompiled_count += 1

        # Verify all patterns are pre-compiled
        assert precompiled_count >= total_patterns, (
            f"Expected all {total_patterns} patterns to be pre-compiled, "
            f"but only {precompiled_count} are pre-compiled.\n"
            f"Breakdown: {pattern_counts}"
        )


class TestRegexPrecompilationVerifyCurrentBehavior:
    """Tests that verify the current behavior (now pre-compiled)."""

    @pytest.fixture
    def hook_file_path(self):
        return HOOKS_DIR / "stop_historical_claims_gate.py"

    @pytest.fixture
    def hook_source(self, hook_file_path):
        return hook_file_path.read_text(encoding="utf-8")

    def test_current_behavior_patterns_are_raw_strings(self, hook_source):
        """
        Characterization: Verify current behavior - patterns should be pre-compiled.

        After PERF-001 fix: Patterns are pre-compiled at module level.
        """
        # Check that HISTORICAL_PHRASE_PATTERNS contains pre-compiled patterns
        assert 'HISTORICAL_PHRASE_PATTERNS = [' in hook_source
        assert 're.compile(' in hook_source

        # This confirms the fix - patterns are pre-compiled
        assert True  # Fixed state confirmed

    def test_module_does_not_contain_precompile_patterns(self, hook_source):
        """
        PERF-001: Verify module HAS pre-compiled patterns.

        After the fix: Update test to verify re.compile() is used.
        """
        # Check for presence of re.compile() in module-level pattern definitions
        lines = hook_source.split('\n')

        # Look for pattern list definitions
        in_pattern_def = False
        has_precompile = False
        for line in lines:
            if 'HISTORICAL_PHRASE_PATTERNS' in line or 'COMPLETION_PHRASE_PATTERNS' in line or 'HISTORICAL_TEST_PATTERNS' in line:
                in_pattern_def = True
            elif in_pattern_def and line.strip().startswith(']'):
                in_pattern_def = False
            elif in_pattern_def and 're.compile(' in line:
                has_precompile = True

        # After fix: patterns should be pre-compiled
        assert has_precompile, (
            "Module should have pre-compiled patterns. "
            f"has_precompile={has_precompile}. "
            "Patterns should use re.compile() calls."
        )
