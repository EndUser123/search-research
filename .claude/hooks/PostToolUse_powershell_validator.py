#!/usr/bin/env python3
"""
PostToolUse Hook: PowerShell Argument Forwarding Validator

Automatically validates PowerShell wrapper functions when .ps1 files are
created or modified to detect argument forwarding bugs before they cause issues.

This hook provides automatic validation feedback without requiring manual CLI
invocation of the PowerShell argument validator.

Run: PostToolUse (after Edit/Write tools)
Timeout: 5 seconds
Exit Codes:
  - 0: Allow (always - advisory mode only)

Author: Claude Code
Date: 2026-03-15
Related: plan-20260315-hook-validation-cli.md
"""

import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Add hooks lib to path for imports
hooks_lib = Path(__file__).resolve().parent / "__lib"
sys.path.insert(0, str(hooks_lib))


@dataclass
class ValidationResult:
    """Result of PowerShell argument forwarding validation."""

    passed: bool
    findings: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        """String representation with status icon."""
        status = "✅ PASS" if self.passed else "❌ FAIL"
        findings_str = "\n".join(self.findings) if self.findings else "No findings"
        return f"{status} ValidationResult(passed={self.passed}, findings=[{findings_str}])"


class PowerShellArgumentValidator:
    """Validates PowerShell wrapper functions for proper argument forwarding.

    Detects wrapper functions that accept parameters but don't forward them
    via @Args or @PSBoundParameters, which causes argument forwarding bugs.
    """

    # Pattern for PowerShell function definitions (supports hyphens in names)
    FUNCTION_PATTERN = re.compile(r"function\s+([\w-]+)\s*\{", re.IGNORECASE | re.MULTILINE)

    # Pattern for individual parameter definitions
    PARAM_PATTERN = re.compile(
        r"\[\s*parameter\s*\([^\)]*\)\s*\]?\s*\[?(\w+)\]?\s*\$(\w+)(?:\s*=\s*([^,\)]+))?",
        re.IGNORECASE,
    )

    # Pattern for @Args or @PSBoundParameters usage
    ARGS_FORWARDING_PATTERN = re.compile(r"@(?:Args|PSBoundParameters)\b", re.IGNORECASE)

    # Pattern for $Args reference (indicates usage)
    DOLLAR_ARGS_PATTERN = re.compile(r"\$Args\b", re.IGNORECASE)

    # Pattern for intentional separate parameter passing (not @Args forwarding)
    INTENTIONAL_SEPARATE_PATTERN = re.compile(r'&\s+[\'"][^\'"]+\.ps1[\'"]\s+', re.IGNORECASE)

    def __init__(self, no_arg_validation: bool = False, allow_alias: bool = False):
        """Initialize validator.

        Args:
            no_arg_validation: Skip argument forwarding checks (for --no-arg-validation flag)
            allow_alias: Suppress alias-related messages (for --allow-alias flag)
        """
        self.no_arg_validation = no_arg_validation
        self.allow_alias = allow_alias
        self.terminal_id = os.environ.get("CLAUDE_TERMINAL_ID", "default")
        self.cache_dir = Path(os.environ.get("TEMP", "/tmp")) / f"ps_validator_{self.terminal_id}"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache = {}

    def validate_file(self, file_path: Path) -> ValidationResult:
        """Validate a PowerShell file for argument forwarding issues.

        Args:
            file_path: Path to .ps1 file to validate

        Returns:
            ValidationResult with findings list
        """
        if not file_path.exists():
            return ValidationResult(passed=False, findings=[f"❌ File not found: {file_path}"])

        try:
            content = file_path.read_text(encoding="utf-8")
        except OSError as e:
            return ValidationResult(passed=False, findings=[f"❌ Error reading file: {e}"])

        findings = []
        all_passed = True

        # Check for Set-Alias statements (info level, not blocking)
        alias_matches = re.finditer(
            r"Set-Alias\s+-Name\s+([^\s]+)\s+-Value\s+[^\s]+", content, re.IGNORECASE
        )
        for match in alias_matches:
            alias_name = match.group(1)
            if alias_name == "p-glm":
                findings.append("ℹ️ Alias 'p-glm' is exempt from validation")
            elif not self.allow_alias:
                findings.append(f"ℹ️ Alias '{alias_name}' detected (use --allow-alias to suppress)")

        # Find all functions
        functions = self._find_functions(content)
        if not functions:
            findings.append("ℹ️ No functions found in file")
            return ValidationResult(passed=True, findings=findings)

        # Validate each function
        for func_name, func_body in functions.items():
            # Skip if this is a commented function
            if self._is_commented_out(func_body, content):
                continue

            func_result = self._validate_function(func_name, func_body, content)
            findings.extend(func_result.findings)
            if not func_result.passed:
                all_passed = False

        return ValidationResult(passed=all_passed, findings=findings)

    def _find_functions(self, content: str) -> dict:
        """Extract all function definitions and their bodies.

        Args:
            content: PowerShell file content

        Returns:
            Dict mapping function names to their function bodies
        """
        functions = {}
        lines = content.split("\n")
        current_function = None
        brace_count = 0
        function_start = -1
        found_param = False

        for i, line in enumerate(lines):
            # Check for function definition (supports hyphens in names)
            func_match = self.FUNCTION_PATTERN.match(line)
            if func_match:
                current_function = func_match.group(1)
                function_start = i
                brace_count = line.count("{") - line.count("}")
                found_param = "param(" in line.lower()
                continue

            # Track braces if we're in a function
            if current_function is not None:
                brace_count += line.count("{") - line.count("}")
                found_param = found_param or "param(" in line.lower()

                # Extract function body when we close the opening brace
                if brace_count == 0 and i > function_start:
                    # Only include if it has a param block (it's a wrapper function)
                    if found_param:
                        func_body = "\n".join(lines[function_start : i + 1])
                        functions[current_function] = func_body
                    current_function = None
                    function_start = -1
                    found_param = False

        return functions

    def _is_commented_out(self, func_body: str, full_content: str) -> bool:
        """Check if a function is commented out.

        Args:
            func_body: The function body text
            full_content: Full file content to check for leading comments

        Returns:
            True if function appears to be commented out
        """
        # Check if the function definition itself starts with #
        # A commented function would have "# function" not "function"
        lines = func_body.strip().split("\n")
        if lines and lines[0].strip().startswith("#"):
            return True
        return False

    def _validate_function(
        self, func_name: str, func_body: str, full_content: str
    ) -> ValidationResult:
        """Validate a single function for argument forwarding.

        Args:
            func_name: Name of the function
            func_body: Function body text
            full_content: Full file content

        Returns:
            ValidationResult for this function
        """
        findings = []

        # Skip validation if disabled
        if self.no_arg_validation:
            findings.append(f"✓ {func_name}: arg validation skipped (--no-arg-validation)")
            return ValidationResult(passed=True, findings=findings)

        # Check if function has a param block
        if "param(" not in func_body.lower():
            findings.append(f"✓ {func_name}: exempt (no param block)")
            return ValidationResult(passed=True, findings=findings)

        # Extract parameters
        params = self._extract_parameters(func_body)
        if not params:
            findings.append(f"✓ {func_name}: exempt (no parameters)")
            return ValidationResult(passed=True, findings=findings)

        # Check exemption: all optional parameters
        if self._all_params_optional(params):
            findings.append(f"✓ {func_name}: exempt (all params optional)")
            return ValidationResult(passed=True, findings=findings)

        # Check for @Args or @PSBoundParameters forwarding
        has_args_forwarding = bool(self.ARGS_FORWARDING_PATTERN.search(func_body))
        has_dollar_args = bool(self.DOLLAR_ARGS_PATTERN.search(func_body))

        # Check for intentional separate parameter passing
        # BUT: This should NOT exempt functions with mixed optional/required params
        has_intentional_separate = bool(self.INTENTIONAL_SEPARATE_PATTERN.search(func_body))

        if has_args_forwarding or has_dollar_args:
            findings.append(f"✓ {func_name}: forwards arguments correctly")
            return ValidationResult(passed=True, findings=findings)

        # Function has required params but no forwarding
        findings.append(
            f"✗ {func_name}: missing @Args forwarding (line {self._find_line_number(func_name, full_content)})"
        )
        return ValidationResult(passed=False, findings=findings)

    def _extract_parameters(self, func_body: str) -> list[dict]:
        """Extract parameter definitions from function body.

        Args:
            func_body: Function body text

        Returns:
            List of param dicts with 'name', 'type', 'default_value' keys
        """
        params = []
        # Find param block
        param_start = func_body.lower().find("param(")
        if param_start == -1:
            return params

        # Find matching closing paren for param(
        paren_depth = 0
        in_param = False
        param_end = -1

        for i in range(len(func_body)):
            char = func_body[i]
            if char == "(":
                if not in_param and i > 0 and func_body[i - 5 : i].lower() == "param":
                    in_param = True
                    paren_depth = 1
                elif in_param:
                    paren_depth += 1
            elif char == ")":
                if in_param:
                    paren_depth -= 1
                    if paren_depth == 0:
                        param_end = i
                        break

        if param_end == -1:
            return params

        param_block = func_body[param_start : param_end + 1]

        # Simple approach: extract all $VariableName patterns
        # This is more reliable than complex bracket/paren counting
        param_pattern = re.compile(r"\$(\w+)(?:\s*=\s*([^,\)]+))?", re.MULTILINE)

        # Also check for Parameter attributes to detect ValueFromRemainingArguments
        remaining_args_pattern = re.compile(
            r"ValueFromRemainingArguments\s*=\s*\$true", re.IGNORECASE
        )

        has_remaining_args = remaining_args_pattern.search(param_block) is not None

        # Extract all variable names
        param_names = param_pattern.findall(param_block)

        for name, default_value in param_names:
            # Check if this specific parameter has ValueFromRemainingArguments
            # by looking for the pattern: [Parameter(ValueFromRemainingArguments=$true)] $Name
            is_remaining_args = False
            param_name_pattern = re.compile(
                rf"\[Parameter\s*\([^)]*ValueFromRemainingArguments\s*=\s*\$true[^)]*\)\][^[]*\${re.escape(name)}",
                re.IGNORECASE,
            )
            if param_name_pattern.search(param_block):
                is_remaining_args = True
            # Also check if the parameter is named $Args (common convention for remaining args)
            elif name == "Args" and has_remaining_args:
                is_remaining_args = True

            param_info = {
                "name": name,
                "type": "object",
                "default_value": default_value.strip() if default_value else None,
                "is_remaining_args": is_remaining_args,
            }
            params.append(param_info)

        return params

    def _parse_parameter(self, param_str: str) -> dict:
        """Parse a single parameter definition.

        Args:
            param_str: Parameter definition string

        Returns:
            Dict with 'name', 'type', 'default_value' keys
        """
        param_str = param_str.strip()
        if not param_str:
            return None

        # Check for default value
        default_value = None
        if "=" in param_str:
            parts = param_str.split("=", 1)
            param_str = parts[0].strip()
            default_value = parts[1].strip()

        # Extract parameter name (last $word)
        name_match = re.search(r"\$(\w+)", param_str)
        if not name_match:
            return None

        name = name_match.group(1)

        # Extract type
        type_match = re.search(r"\[(\w+(?:\.\w+)*)\]", param_str)
        param_type = type_match.group(1) if type_match else "object"

        # Check for ValueFromRemainingArguments (these are $Args collectors, not regular params)
        if "ValueFromRemainingArguments" in param_str:
            # Treat as special case - not a regular parameter
            return {
                "name": name,
                "type": param_type,
                "default_value": default_value,
                "is_remaining_args": True,
            }

        return {
            "name": name,
            "type": param_type,
            "default_value": default_value,
            "is_remaining_args": False,
        }

    def _all_params_optional(self, params: list[dict]) -> bool:
        """Check if ALL parameters are optional (have default values).

        CRITICAL FIX: Must return False for mixed optional/required parameters.

        Args:
            params: List of parameter dicts from _extract_parameters

        Returns:
            True only if ALL parameters have default values (or no params)
            False if ANY parameter is required (no default value)
        """
        if not params:
            return False  # No params found, not "all optional"

        # Filter out ValueFromRemainingArguments parameters (they're $Args collectors)
        regular_params = [p for p in params if not p.get("is_remaining_args", False)]

        if not regular_params:
            return True  # Only $Args collector, exempt

        # ALL parameters must have default values to be exempt
        # MIXED optional + required = NOT exempt
        for param in regular_params:
            if param.get("default_value") is None:
                return False  # Found required parameter

        return True  # ALL parameters have defaults

    def _find_line_number(self, func_name: str, full_content: str) -> int:
        """Find the line number of a function definition.

        Args:
            func_name: Function name to search for
            full_content: Full file content

        Returns:
            Line number (1-indexed)
        """
        lines = full_content.split("\n")
        for i, line in enumerate(lines, 1):
            if re.search(rf"\bfunction\s+{re.escape(func_name)}\b", line, re.IGNORECASE):
                return i
        return 1

    def _compute_cache_key(self, file_path: Path) -> tuple:
        """Compute cache key including file mtime for staleness detection.

        Args:
            file_path: Path to file

        Returns:
            Tuple of (file_path, mtime) for cache key
        """
        try:
            mtime = file_path.stat().st_mtime
        except OSError:
            mtime = 0
        return (str(file_path), mtime)


def run(data: dict) -> dict | None:
    """Validate .ps1 files after Write/Edit operations.

    Args:
        data: Hook data dictionary from PostToolUse event

    Returns:
        dict with validation findings if .ps1 file was modified
        None otherwise
    """
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    # Only validate on Write or Edit operations
    if tool_name not in ("Write", "Edit"):
        return None

    file_path = tool_input.get("file_path", "")
    if not file_path:
        return None

    # Only validate .ps1 files
    if not file_path.endswith(".ps1"):
        return None

    # Check if file exists (may not for failed Write operations)
    path = Path(file_path)
    if not path.exists():
        return None

    # Run validation
    validator = PowerShellArgumentValidator()
    result = validator.validate_file(path)

    # Only report findings if there are any (pass or fail)
    if result.findings:
        # Build summary
        if result.passed:
            status_icon = "✅"
            status_text = "PASS"
        else:
            status_icon = "❌"
            status_text = "FAIL"

        # Format findings as JSON output
        findings_data = {
            "decision": "allow",  # Always allow - advisory only
            "validation": "PowerShell argument forwarding",
            "file": str(file_path),
            "status": status_text,
            "findings": result.findings,
        }

        # Print to stdout (not stderr - that would trigger hook error)
        print(
            f"\n{status_icon} PowerShell Validation: {path.name} - {status_text}", file=sys.stdout
        )
        for finding in result.findings:
            print(f"  {finding}", file=sys.stdout)
        print(file=sys.stdout)

        # Return data for potential downstream processing
        return findings_data

    return None


if __name__ == "__main__":
    # Read hook data from stdin
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        # Invalid JSON - allow operation
        sys.exit(0)

    # Run the validation
    run(input_data)

    # Always exit with success (advisory mode)
    sys.exit(0)
