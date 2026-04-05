#!/usr/bin/env python3
"""
Unit tests for PythonArgumentForwardingValidator.

Tests cover:
1. Happy path (valid function with *args/**kwargs)
2. Missing forwarding detection
3. Exempt decorator detection (@property, @staticmethod, @classmethod)
4. All-optional parameters exemption
5. Parameterless function exemption
6. No functions found handling
7. File not found handling
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "__lib"))

from argument_forwarding_validator import (
    PythonArgumentForwardingValidator,
    ValidationResult,
)


class TestPythonArgumentForwardingValidatorHappyPath:
    """Test 1: Happy path - valid function with *args/**kwargs forwarding."""

    def test_valid_function_with_args_splatting(self):
        """Function with *args/**kwargs should pass."""
        py_content = """
def wrapper(*args, **kwargs):
    target_function(*args, **kwargs)
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(py_content)
            f.flush()
            file_path = Path(f.name)

        try:
            validator = PythonArgumentForwardingValidator()
            result = validator.validate_file(file_path)

            assert result.passed, f"Expected PASS but got FAIL: {result.findings}"
            assert any(
                "forwards arguments correctly" in finding.lower() or "args" in finding.lower()
                for finding in result.findings
            ), f"Expected forwarding confirmation, got: {result.findings}"
        finally:
            os.unlink(file_path)

    def test_valid_function_with_kwargs_only(self):
        """Function with **kwargs should pass."""
        py_content = """
def wrapped_call(**kwargs):
    some_api.call(**kwargs)
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(py_content)
            f.flush()
            file_path = Path(f.name)

        try:
            validator = PythonArgumentForwardingValidator()
            result = validator.validate_file(file_path)

            assert result.passed, f"Expected PASS but got FAIL: {result.findings}"
        finally:
            os.unlink(file_path)

    def test_valid_function_with_explicit_forwarding(self):
        """Function that explicitly forwards each parameter should pass."""
        py_content = """
def explicit_forward(a, b, c):
    target(a=a, b=b, c=c)
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(py_content)
            f.flush()
            file_path = Path(f.name)

        try:
            validator = PythonArgumentForwardingValidator()
            result = validator.validate_file(file_path)

            assert result.passed, f"Expected PASS but got FAIL: {result.findings}"
        finally:
            os.unlink(file_path)


class TestPythonArgumentForwardingValidatorMissingForwarding:
    """Test 2: Missing *args/**kwargs detection."""

    def test_function_without_forwarding(self):
        """Function with explicit params but no forwarding should fail."""
        py_content = """
def broken_wrapper(path, filter):
    # Does NOT forward the parameters to any target function
    return path + "/" + filter
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(py_content)
            f.flush()
            file_path = Path(f.name)

        try:
            validator = PythonArgumentForwardingValidator()
            result = validator.validate_file(file_path)

            assert not result.passed, "Expected FAIL but got PASS"
            assert any(
                "missing" in finding.lower() and "args" in finding.lower()
                for finding in result.findings
            ), f"Expected forwarding warning, got: {result.findings}"
        finally:
            os.unlink(file_path)


class TestPythonArgumentForwardingValidatorExemptDecorators:
    """Test 3: Decorator exemption detection."""

    def test_property_decorator_exempt(self):
        """@property decorator should be exempt."""
        py_content = """
class MyClass:
    @property
    def my_property(self):
        return self._value
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(py_content)
            f.flush()
            file_path = Path(f.name)

        try:
            validator = PythonArgumentForwardingValidator()
            result = validator.validate_file(file_path)

            assert result.passed, f"Expected PASS (exempt), got FAIL: {result.findings}"
            assert any(
                "exempt" in finding.lower() and "decorator" in finding.lower()
                for finding in result.findings
            ), f"Expected decorator exemption, got: {result.findings}"
        finally:
            os.unlink(file_path)

    def test_staticmethod_decorator_exempt(self):
        """@staticmethod decorator should be exempt."""
        py_content = """
class MyClass:
    @staticmethod
    def static_method(x, y):
        return x + y
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(py_content)
            f.flush()
            file_path = Path(f.name)

        try:
            validator = PythonArgumentForwardingValidator()
            result = validator.validate_file(file_path)

            assert result.passed, f"Expected PASS (exempt), got FAIL: {result.findings}"
        finally:
            os.unlink(file_path)

    def test_classmethod_decorator_exempt(self):
        """@classmethod decorator should be exempt."""
        py_content = """
class MyClass:
    @classmethod
    def class_method(cls, x):
        return cls.value + x
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(py_content)
            f.flush()
            file_path = Path(f.name)

        try:
            validator = PythonArgumentForwardingValidator()
            result = validator.validate_file(file_path)

            assert result.passed, f"Expected PASS (exempt), got FAIL: {result.findings}"
        finally:
            os.unlink(file_path)


class TestPythonArgumentForwardingValidatorExemptions:
    """Test 4-5: Exemption conditions."""

    def test_all_optional_parameters_exempt(self):
        """Function with all default values should be exempt."""
        py_content = """
def with_defaults(a=1, b=2, c=3):
    target_function(a, b, c)
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(py_content)
            f.flush()
            file_path = Path(f.name)

        try:
            validator = PythonArgumentForwardingValidator()
            result = validator.validate_file(file_path)

            assert result.passed, f"Expected PASS (exempt), got FAIL: {result.findings}"
            assert any(
                "exempt" in finding.lower() or "no forwarding needed" in finding.lower()
                for finding in result.findings
            ), f"Expected exemption, got: {result.findings}"
        finally:
            os.unlink(file_path)

    def test_parameterless_function_exempt(self):
        """Function without parameters should be exempt."""
        py_content = """
def simple_function():
    return "hello"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(py_content)
            f.flush()
            file_path = Path(f.name)

        try:
            validator = PythonArgumentForwardingValidator()
            result = validator.validate_file(file_path)

            assert result.passed, f"Expected PASS (exempt), got FAIL: {result.findings}"
        finally:
            os.unlink(file_path)


class TestPythonArgumentForwardingValidatorEdgeCases:
    """Test 6-8: Edge cases and error handling."""

    def test_no_functions_found(self):
        """File with no function definitions should report info message."""
        py_content = """
# Just constants
MY_CONSTANT = 42
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(py_content)
            f.flush()
            file_path = Path(f.name)

        try:
            validator = PythonArgumentForwardingValidator()
            result = validator.validate_file(file_path)

            assert result.passed, f"Expected PASS, got FAIL: {result.findings}"
            assert any(
                "no functions found" in finding.lower() for finding in result.findings
            ), f"Expected 'no functions' message, got: {result.findings}"
        finally:
            os.unlink(file_path)

    def test_file_not_found(self):
        """Non-existent file should return ValidationResult with error."""
        validator = PythonArgumentForwardingValidator()
        result = validator.validate_file(Path("/nonexistent/path/file.py"))

        assert not result.passed, "Should FAIL for non-existent file"
        assert any(
            "not found" in finding.lower() or "file not found" in finding.lower()
            for finding in result.findings
        ), f"Expected file not found message, got: {result.findings}"

    def test_syntax_error(self):
        """File with syntax error should report error."""
        py_content = """
def broken_function(
    # Missing closing paren
    pass
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(py_content)
            f.flush()
            file_path = Path(f.name)

        try:
            validator = PythonArgumentForwardingValidator()
            result = validator.validate_file(file_path)

            assert not result.passed, "Should FAIL for syntax error"
            assert any(
                "syntax error" in finding.lower() for finding in result.findings
            ), f"Expected syntax error, got: {result.findings}"
        finally:
            os.unlink(file_path)

    def test_no_arg_validation_flag(self):
        """--no-arg-validation should skip argument forwarding checks."""
        py_content = """
def broken_wrapper(path, filter):
    # Does NOT forward the parameters to any target function
    return path + "/" + filter
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(py_content)
            f.flush()
            file_path = Path(f.name)

        try:
            validator = PythonArgumentForwardingValidator(no_arg_validation=True)
            result = validator.validate_file(file_path)

            # Should pass with skipped validation message
            assert result.passed, f"Expected PASS (skipped), got FAIL: {result.findings}"
            assert any(
                "skipped" in finding.lower() for finding in result.findings
            ), f"Expected skipped message, got: {result.findings}"
        finally:
            os.unlink(file_path)


class TestPythonArgumentForwardingValidatorValidationResult:
    """Test ValidationResult container class."""

    def test_validation_result_passed(self):
        """ValidationResult with passed=True should render correctly."""
        result = ValidationResult(True, ["Finding 1", "Finding 2"])
        assert result.passed
        assert len(result.findings) == 2
        assert "✅ PASS" in str(result) or "PASS" in str(result)

    def test_validation_result_failed(self):
        """ValidationResult with passed=False should render correctly."""
        result = ValidationResult(False, ["Error: missing *args"])
        assert not result.passed
        assert "❌ FAIL" in str(result) or "FAIL" in str(result)

    def test_validation_result_no_findings(self):
        """ValidationResult with empty findings should still render."""
        result = ValidationResult(True, [])
        assert result.passed
        assert len(result.findings) == 0


class TestPythonArgumentForwardingValidatorMultiTerminalIsolation:
    """Test 7: Multi-terminal isolation."""

    def test_terminal_id_detection_default(self):
        """Without CLAUDE_TERMINAL_ID env var, should use 'default'."""
        # Clear the env var if set
        original_val = os.environ.get("CLAUDE_TERMINAL_ID")
        if "CLAUDE_TERMINAL_ID" in os.environ:
            del os.environ["CLAUDE_TERMINAL_ID"]

        try:
            validator = PythonArgumentForwardingValidator()
            assert (
                validator.terminal_id == "default"
            ), f"Expected 'default', got {validator.terminal_id}"
            assert "default" in str(
                validator.cache_dir
            ), f"Cache dir should include 'default': {validator.cache_dir}"
        finally:
            # Restore original value
            if original_val:
                os.environ["CLAUDE_TERMINAL_ID"] = original_val

    def test_terminal_id_detection_custom(self):
        """With CLAUDE_TERMINAL_ID env var, should use custom value."""
        original_val = os.environ.get("CLAUDE_TERMINAL_ID")
        os.environ["CLAUDE_TERMINAL_ID"] = "test_terminal_123"

        try:
            validator = PythonArgumentForwardingValidator()
            assert (
                validator.terminal_id == "test_terminal_123"
            ), f"Expected 'test_terminal_123', got {validator.terminal_id}"
            assert "test_terminal_123" in str(
                validator.cache_dir
            ), f"Cache dir should include terminal ID: {validator.cache_dir}"
        finally:
            # Restore original value
            if original_val:
                os.environ["CLAUDE_TERMINAL_ID"] = original_val
            elif "CLAUDE_TERMINAL_ID" in os.environ:
                del os.environ["CLAUDE_TERMINAL_ID"]

    def test_cache_isolation_between_terminals(self):
        """Different terminals should have separate caches."""
        py_content = "def test(*args): pass"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(py_content)
            f.flush()
            file_path = Path(f.name)

        try:
            # Create validator for terminal 1
            os.environ["CLAUDE_TERMINAL_ID"] = "terminal_1"
            validator1 = PythonArgumentForwardingValidator()
            result1 = validator1.validate_file(file_path)

            # Create validator for terminal 2
            os.environ["CLAUDE_TERMINAL_ID"] = "terminal_2"
            validator2 = PythonArgumentForwardingValidator()
            result2 = validator2.validate_file(file_path)

            # Both should pass
            assert result1.passed
            assert result2.passed

            # Caches should be separate
            assert validator1.cache_dir != validator2.cache_dir
            assert "terminal_1" in str(validator1.cache_dir)
            assert "terminal_2" in str(validator2.cache_dir)
        finally:
            os.unlink(file_path)
            if "CLAUDE_TERMINAL_ID" in os.environ:
                del os.environ["CLAUDE_TERMINAL_ID"]


class TestPythonArgumentForwardingValidatorStaleDataImmunity:
    """Test 8: Stale data immunity (mtime-based cache invalidation)."""

    def test_cache_invalidates_on_file_change(self):
        """Cache should invalidate when file mtime changes."""
        py_content = "def test(*args): pass"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(py_content)
            f.flush()
            file_path = Path(f.name)

        try:
            validator = PythonArgumentForwardingValidator()

            # First validation - cache miss
            cache_key_before = validator._compute_cache_key(file_path)
            result1 = validator.validate_file(file_path)

            # Modify file to change mtime
            import time

            time.sleep(0.01)  # Ensure mtime changes
            with open(file_path, "a") as f:
                f.write("\n# Modified")

            # Cache key should change
            cache_key_after = validator._compute_cache_key(file_path)
            assert (
                cache_key_before != cache_key_after
            ), "Cache key should change after file modification"

            # Second validation - cache miss due to mtime change
            result2 = validator.validate_file(file_path)

            # Both should pass
            assert result1.passed
            assert result2.passed
        finally:
            os.unlink(file_path)

    def test_cache_key_includes_mtime(self):
        """Cache key should include file mtime."""
        py_content = "def test(*args): pass"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(py_content)
            f.flush()
            file_path = Path(f.name)

        try:
            validator = PythonArgumentForwardingValidator()
            cache_key = validator._compute_cache_key(file_path)

            # Cache key should be a tuple of (file_path, mtime)
            assert isinstance(cache_key, tuple), f"Cache key should be tuple, got {type(cache_key)}"
            assert len(cache_key) == 2, f"Cache key should have 2 elements, got {len(cache_key)}"
            assert isinstance(
                cache_key[0], str
            ), f"First element should be str (path), got {type(cache_key[0])}"
            assert isinstance(
                cache_key[1], float
            ), f"Second element should be float (mtime), got {type(cache_key[1])}"
            assert cache_key[0] == str(file_path), "First element should be file path"
            assert cache_key[1] > 0, f"mtime should be positive, got {cache_key[1]}"
        finally:
            os.unlink(file_path)


class TestPythonArgumentForwardingValidatorFileExtensions:
    """Test 9: File extension filtering."""

    def test_get_file_extensions(self):
        """get_file_extensions should return ['.py']."""
        validator = PythonArgumentForwardingValidator()
        extensions = validator.get_file_extensions()
        assert extensions == [".py"], f"Expected ['.py'], got {extensions}"


class TestPythonArgumentForwardingValidatorAstExtraction:
    """Test 10: AST function extraction and forwarding detection."""

    def test_detects_args_in_params(self):
        """Should detect *args in function parameters."""
        py_content = """
def has_args_in_params(*args):
    return args
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(py_content)
            f.flush()
            file_path = Path(f.name)

        try:
            validator = PythonArgumentForwardingValidator()
            result = validator.validate_file(file_path)

            assert result.passed, "Function with *args in params should pass"
        finally:
            os.unlink(file_path)

    def test_detects_kwargs_in_params(self):
        """Should detect **kwargs in function parameters."""
        py_content = """
def has_kwargs_in_params(**kwargs):
    return kwargs
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(py_content)
            f.flush()
            file_path = Path(f.name)

        try:
            validator = PythonArgumentForwardingValidator()
            result = validator.validate_file(file_path)

            assert result.passed, "Function with **kwargs in params should pass"
        finally:
            os.unlink(file_path)

    def test_detects_varargs_keyword(self):
        """Should detect *args and **kwargs via vararg/kwarg."""
        py_content = """
def uses_varargs(*args, **kwargs):
    return list(args), kwargs
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(py_content)
            f.flush()
            file_path = Path(f.name)

        try:
            validator = PythonArgumentForwardingValidator()
            result = validator.validate_file(file_path)

            assert result.passed, "Function with *args, **kwargs should pass"
        finally:
            os.unlink(file_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
