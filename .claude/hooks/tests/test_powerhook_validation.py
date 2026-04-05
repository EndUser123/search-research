#!/usr/bin/env python3
"""
Unit tests for PowerShellArgumentValidator.

Tests cover:
1. Happy path (valid function with @Args)
2. Missing @Args detection
3. Alias exemption (p-glm)
4. Bypass flags (--no-arg-validation, --allow-alias)
5. Multi-terminal isolation
6. Stale data immunity (mtime-based cache invalidation)
7. Module export detection (skip internal functions)
8. Splatting pattern (@PSBoundParameters)
9. Begin/Process/End block detection
10. All-optional parameters (no forwarding needed)
11. ScriptBlock invocation pattern
12. Commented-out code (should be ignored)
"""

import os
import sys
import tempfile
import time
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from PostToolUse_powershell_validator import PowerShellArgumentValidator, ValidationResult


class TestPowerShellArgumentValidatorHappyPath:
    """Test 1: Happy path - valid function with @Args forwarding."""

    def test_valid_function_with_args_splatting(self):
        """Function with @Args splatting should pass."""
        ps_content = r"""
function cc-glm {
    param([Parameter(ValueFromRemainingArguments = $true)] [object[]] $Args)
    & 'P:\.claude\proxy\cc-glm.ps1' @Args
    claude @Args
}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ps1", delete=False) as f:
            f.write(ps_content)
            f.flush()
            file_path = Path(f.name)

        try:
            validator = PowerShellArgumentValidator()
            result = validator.validate_file(file_path)

            assert result.passed, f"Expected PASS but got FAIL: {result.findings}"
            # Should have at least one finding about the function having forwarding
            assert any(
                "forwards arguments correctly" in finding.lower() or "@Args" in finding
                for finding in result.findings
            ), f"Expected forwarding confirmation, got: {result.findings}"
        finally:
            os.unlink(file_path)

    def test_valid_function_with_dollar_args(self):
        """Function with $Args reference should pass."""
        ps_content = """
function invoke-script {
    param([string[]]$Arguments)
    foreach ($arg in $Args) {
        Write-Host $arg
    }
}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ps1", delete=False) as f:
            f.write(ps_content)
            f.flush()
            file_path = Path(f.name)

        try:
            validator = PowerShellArgumentValidator()
            result = validator.validate_file(file_path)

            assert result.passed, f"Expected PASS but got FAIL: {result.findings}"
        finally:
            os.unlink(file_path)


class TestPowerShellArgumentValidatorMissingForwarding:
    """Test 2: Missing @Args detection."""

    def test_function_without_args_forwarding(self):
        """Function with params but no @Args forwarding should fail."""
        ps_content = """
function broken-wrapper {
    param([string]$Path, [string]$Filter)
    & 'script.ps1' -Path $Path -Filter $Filter
}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ps1", delete=False) as f:
            f.write(ps_content)
            f.flush()
            file_path = Path(f.name)

        try:
            validator = PowerShellArgumentValidator()
            result = validator.validate_file(file_path)

            assert not result.passed, "Expected FAIL but got PASS"
            # Check for missing @Args forwarding pattern (actual output: "missing @Args forwarding (line N)")
            assert any(
                "missing @args forwarding" in finding.lower() for finding in result.findings
            ), f"Expected forwarding warning, got: {result.findings}"
        finally:
            os.unlink(file_path)


class TestPowerShellArgumentValidatorAliasExemption:
    """Test 3: Alias exemption (p-glm)."""

    def test_exempt_alias_p_glm(self):
        """p-glm alias should be exempt with info message."""
        ps_content = r"""
Set-Alias -Name p-glm -Value 'P:\.claude\proxy\cc-glm.ps1'
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ps1", delete=False) as f:
            f.write(ps_content)
            f.flush()
            file_path = Path(f.name)

        try:
            validator = PowerShellArgumentValidator()
            result = validator.validate_file(file_path)

            # Should pass but with info message about exemption
            assert result.passed, f"Expected PASS (exempt), got FAIL: {result.findings}"
            assert any(
                "exempt" in finding.lower() and "p-glm" in finding.lower()
                for finding in result.findings
            ), f"Expected exemption message, got: {result.findings}"
        finally:
            os.unlink(file_path)

    def test_non_exempt_alias_warning(self):
        """Non-exempt alias should generate info message."""
        ps_content = """
Set-Alias -Name my-alias -Value 'script.ps1'
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ps1", delete=False) as f:
            f.write(ps_content)
            f.flush()
            file_path = Path(f.name)

        try:
            validator = PowerShellArgumentValidator()
            result = validator.validate_file(file_path)

            # Should pass but with info message about alias
            assert result.passed, f"Expected PASS (alias), got FAIL: {result.findings}"
            assert any(
                "alias" in finding.lower() for finding in result.findings
            ), f"Expected alias message, got: {result.findings}"
        finally:
            os.unlink(file_path)


class TestPowerShellArgumentValidatorBypassFlags:
    """Test 4: Bypass flags (--no-arg-validation, --allow-alias)."""

    def test_no_arg_validation_flag(self):
        """--no-arg-validation should skip argument forwarding checks."""
        ps_content = """
function broken-wrapper {
    param([string]$Path, [string]$Filter)
    & 'script.ps1' -Path $Path -Filter $Filter
}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ps1", delete=False) as f:
            f.write(ps_content)
            f.flush()
            file_path = Path(f.name)

        try:
            validator = PowerShellArgumentValidator(no_arg_validation=True)
            result = validator.validate_file(file_path)

            # Should pass with skipped validation message
            assert result.passed, f"Expected PASS (skipped), got FAIL: {result.findings}"
            assert any(
                "skipped" in finding.lower() or "arg validation skipped" in finding.lower()
                for finding in result.findings
            ), f"Expected skipped message, got: {result.findings}"
        finally:
            os.unlink(file_path)

    def test_allow_alias_flag(self):
        """--allow-alias should suppress all alias messages."""
        ps_content = """
Set-Alias -Name my-alias -Value 'script.ps1'
Set-Alias -Name another-alias -Value 'other.ps1'
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ps1", delete=False) as f:
            f.write(ps_content)
            f.flush()
            file_path = Path(f.name)

        try:
            validator = PowerShellArgumentValidator(allow_alias=True)
            result = validator.validate_file(file_path)

            # Should pass with no alias messages (they're suppressed)
            assert result.passed, f"Expected PASS, got FAIL: {result.findings}"
            # With allow_alias, alias messages should be suppressed
            # The only messages should be about "no functions found" or similar
            for finding in result.findings:
                assert "alias" not in finding.lower(), f"Alias message not suppressed: {finding}"
        finally:
            os.unlink(file_path)


class TestPowerShellArgumentValidatorMultiTerminalIsolation:
    """Test 5: Multi-terminal isolation."""

    def test_terminal_id_detection_default(self):
        """Without CLAUDE_TERMINAL_ID env var, should use 'default'."""
        # Clear the env var if set
        original_val = os.environ.get("CLAUDE_TERMINAL_ID")
        if "CLAUDE_TERMINAL_ID" in os.environ:
            del os.environ["CLAUDE_TERMINAL_ID"]

        try:
            validator = PowerShellArgumentValidator()
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
            validator = PowerShellArgumentValidator()
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
        ps_content = "function test { @Args }"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ps1", delete=False) as f:
            f.write(ps_content)
            f.flush()
            file_path = Path(f.name)

        try:
            # Create validator for terminal 1
            os.environ["CLAUDE_TERMINAL_ID"] = "terminal_1"
            validator1 = PowerShellArgumentValidator()
            result1 = validator1.validate_file(file_path)

            # Create validator for terminal 2
            os.environ["CLAUDE_TERMINAL_ID"] = "terminal_2"
            validator2 = PowerShellArgumentValidator()
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


class TestPowerShellArgumentValidatorStaleDataImmunity:
    """Test 6: Stale data immunity (mtime-based cache invalidation)."""

    def test_cache_invalidates_on_file_change(self):
        """Cache should invalidate when file mtime changes."""
        ps_content = "function test { @Args }"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ps1", delete=False) as f:
            f.write(ps_content)
            f.flush()
            file_path = Path(f.name)

        try:
            validator = PowerShellArgumentValidator()

            # First validation - cache miss
            cache_key_before = validator._compute_cache_key(file_path)
            result1 = validator.validate_file(file_path)

            # Modify file to change mtime
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
        ps_content = "function test { @Args }"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ps1", delete=False) as f:
            f.write(ps_content)
            f.flush()
            file_path = Path(f.name)

        try:
            validator = PowerShellArgumentValidator()
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


class TestPowerShellArgumentValidatorSplattingPattern:
    """Test 8: Splatting pattern (@PSBoundParameters)."""

    def test_psboundparameters_splatting(self):
        """Function with @PSBoundParameters should pass."""
        ps_content = """
function advanced-wrapper {
    param([string]$Path, [string]$Filter)
    & 'script.ps1' @PSBoundParameters
}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ps1", delete=False) as f:
            f.write(ps_content)
            f.flush()
            file_path = Path(f.name)

        try:
            validator = PowerShellArgumentValidator()
            result = validator.validate_file(file_path)

            assert result.passed, f"Expected PASS (splatting), got FAIL: {result.findings}"
        finally:
            os.unlink(file_path)


class TestPowerShellArgumentValidatorBeginProcessEnd:
    """Test 9: Begin/Process/End block detection."""

    def test_begin_process_end_blocks(self):
        """Advanced function with Begin/Process/End blocks should scan all blocks."""
        ps_content = """
function advanced-function {
    param([string[]]$Args)

    Begin {
        Write-Host "Starting"
    }

    Process {
        # Forwarding in Process block should be detected
        & 'script.ps1' @Args
    }

    End {
        Write-Host "Done"
    }
}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ps1", delete=False) as f:
            f.write(ps_content)
            f.flush()
            file_path = Path(f.name)

        try:
            validator = PowerShellArgumentValidator()
            result = validator.validate_file(file_path)

            assert result.passed, f"Expected PASS, got FAIL: {result.findings}"
        finally:
            os.unlink(file_path)


class TestPowerShellArgumentValidatorAllOptionalParameters:
    """Test 10: All-optional parameters (no forwarding needed)."""

    def test_parameterless_function_exemption(self):
        """Function without param block should be exempt."""
        ps_content = """
function simple-function {
    Write-Host "No parameters here"
    & 'script.ps1'
}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ps1", delete=False) as f:
            f.write(ps_content)
            f.flush()
            file_path = Path(f.name)

        try:
            validator = PowerShellArgumentValidator()
            result = validator.validate_file(file_path)

            # Should pass with exemption message
            assert result.passed, f"Expected PASS (exempt), got FAIL: {result.findings}"
        finally:
            os.unlink(file_path)

    def test_all_optional_parameters_exemption(self):
        """Function with all optional parameters should be exempt."""
        ps_content = """
function optional-params {
    param(
        [string]$Name = "default",
        [int]$Count = 1
    )
    & 'script.ps1' -Name $Name -Count $Count
}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ps1", delete=False) as f:
            f.write(ps_content)
            f.flush()
            file_path = Path(f.name)

        try:
            validator = PowerShellArgumentValidator()
            result = validator.validate_file(file_path)

            # Should pass with exemption message (all params are optional)
            assert result.passed, f"Expected PASS (all optional), got FAIL: {result.findings}"
        finally:
            os.unlink(file_path)

    def test_mixed_parameters_not_exempt(self):
        """Function with mixed optional and required parameters should require forwarding."""
        ps_content = """
function mixed-params {
    param(
        [string]$Name = "default",
        [string]$Path
    )
    & 'script.ps1' -Name $Name -Path $Path
}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ps1", delete=False) as f:
            f.write(ps_content)
            f.flush()
            file_path = Path(f.name)

        try:
            validator = PowerShellArgumentValidator()
            result = validator.validate_file(file_path)

            # Should FAIL - has required params but no @Args forwarding
            assert not result.passed, f"Expected FAIL (mixed params), got PASS: {result.findings}"
            assert any(
                "missing @args forwarding" in finding.lower() for finding in result.findings
            ), f"Expected forwarding warning, got: {result.findings}"
        finally:
            os.unlink(file_path)

    def test_single_param_with_optional_not_exempt(self):
        """Function with ValueFromRemainingArguments should NOT be exempt even if optional-looking."""
        ps_content = """
function remaining-args {
    param(
        [Parameter(ValueFromRemainingArguments)]
        [object[]]$Args
    )
    & 'script.ps1' @Args
}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ps1", delete=False) as f:
            f.write(ps_content)
            f.flush()
            file_path = Path(f.name)

        try:
            validator = PowerShellArgumentValidator()
            result = validator.validate_file(file_path)

            # Should pass because it has @Args forwarding
            assert result.passed, f"Expected PASS (@Args forwarding), got FAIL: {result.findings}"
        finally:
            os.unlink(file_path)


class TestPowerShellArgumentValidatorScriptBlock:
    """Test 11: ScriptBlock invocation pattern."""

    def test_scriptblock_invocation(self):
        """ScriptBlock invocation with @Args should pass."""
        ps_content = """
function dynamic-wrapper {
    param([scriptblock]$ScriptBlock, [object[]]$Args)
    & $ScriptBlock @Args
}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ps1", delete=False) as f:
            f.write(ps_content)
            f.flush()
            file_path = Path(f.name)

        try:
            validator = PowerShellArgumentValidator()
            result = validator.validate_file(file_path)

            assert result.passed, f"Expected PASS, got FAIL: {result.findings}"
        finally:
            os.unlink(file_path)


class TestPowerShellArgumentValidatorCommentedCode:
    """Test 12: Commented-out code should be ignored."""

    def test_commented_out_function(self):
        """Commented-out function should not trigger failures."""
        ps_content = """
# This is a commented function - should be ignored
# function broken-wrapper {
#     param([string]$Path)
#     & 'script.ps1' -Path $Path
# }

# Real function below
function real-wrapper {
    param([object[]]$Args)
    & 'script.ps1' @Args
}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ps1", delete=False) as f:
            f.write(ps_content)
            f.flush()
            file_path = Path(f.name)

        try:
            validator = PowerShellArgumentValidator()
            result = validator.validate_file(file_path)

            # Should pass because commented function is ignored
            assert (
                result.passed
            ), f"Expected PASS (commented code ignored), got FAIL: {result.findings}"
            # The real-wrapper should have forwarding
            assert any(
                "real-wrapper" in finding or "forwarding" in finding.lower()
                for finding in result.findings
            ), f"Expected real-wrapper validation, got: {result.findings}"
        finally:
            os.unlink(file_path)


class TestPowerShellArgumentValidatorValidationResult:
    """Test ValidationResult container class."""

    def test_validation_result_passed(self):
        """ValidationResult with passed=True should render correctly."""
        result = ValidationResult(True, ["Finding 1", "Finding 2"])
        assert result.passed
        assert len(result.findings) == 2
        assert "✅ PASS" in str(result) or "PASS" in str(result)

    def test_validation_result_failed(self):
        """ValidationResult with passed=False should render correctly."""
        result = ValidationResult(False, ["Error: missing @Args"])
        assert not result.passed
        assert "❌ FAIL" in str(result) or "FAIL" in str(result)

    def test_validation_result_no_findings(self):
        """ValidationResult with empty findings should still render."""
        result = ValidationResult(True, [])
        assert result.passed
        assert len(result.findings) == 0


class TestPowerShellArgumentValidatorFileNotFound:
    """Test file not found handling."""

    def test_file_not_found(self):
        """Non-existent file should return ValidationResult with error."""
        validator = PowerShellArgumentValidator()
        result = validator.validate_file(Path("/nonexistent/path/file.ps1"))

        assert not result.passed, "Should FAIL for non-existent file"
        assert any(
            "not found" in finding.lower() or "file not found" in finding.lower()
            for finding in result.findings
        ), f"Expected file not found message, got: {result.findings}"


class TestPowerShellArgumentValidatorFileReadError:
    """Test file read error handling."""

    def test_file_read_error(self, tmp_path):
        """File read error should be handled gracefully."""
        # Create a directory with .ps1 extension (will fail to read as file)
        invalid_file = tmp_path / "test.ps1"
        invalid_file.mkdir()

        try:
            validator = PowerShellArgumentValidator()
            result = validator.validate_file(invalid_file)

            assert not result.passed, "Should FAIL for read error"
            assert any(
                "error" in finding.lower() for finding in result.findings
            ), f"Expected error message, got: {result.findings}"
        finally:
            invalid_file.rmdir()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
