#!/usr/bin/env python3
"""
Argument Forwarding Validators

Base class and language-specific validators for detecting wrapper functions
that define explicit parameters but don't forward them.

Multi-terminal isolation: Uses CLAUDE_TERMINAL_ID env var for cache isolation.
Stale data immunity: Uses file mtime in cache key for auto-invalidation.
"""

import ast
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ValidationResult:
    """Result of file validation."""

    passed: bool
    findings: list[str]

    def __str__(self) -> str:
        if self.passed:
            return "✅ PASS"
        else:
            return "❌ FAIL"


class ArgumentForwardingValidator(ABC):
    """Base class for argument forwarding validators.

    Provides common infrastructure for caching, multi-terminal isolation,
    and stale data immunity. Language-specific detection is implemented
    in subclasses.
    """

    def __init__(
        self,
        no_arg_validation: bool = False,
    ):
        """Initialize the validator.

        Args:
            no_arg_validation: Skip argument forwarding checks (scan file structure only)
        """
        self.no_arg_validation = no_arg_validation
        self.terminal_id = os.environ.get("CLAUDE_TERMINAL_ID", "default")
        self.cache_dir = Path("P:/.claude/state/validation_cache") / self.terminal_id
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[tuple, ValidationResult] = {}

    def validate_file(self, file_path: Path) -> ValidationResult:
        """Validate a file for argument forwarding.

        Args:
            file_path: Path to the file to validate

        Returns:
            ValidationResult with passed status and list of findings
        """
        # Check if file exists
        if not file_path.exists():
            return ValidationResult(False, [f"File not found: {file_path}"])

        # Check cache
        cache_key = self._compute_cache_key(file_path)
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            return ValidationResult(False, [f"Error reading file: {e}"])

        # Delegate to language-specific validation
        result = self._validate_content(file_path, content)

        # Cache result
        self._cache[cache_key] = result
        return result

    def _compute_cache_key(self, file_path: Path) -> tuple:
        """Compute cache key including file mtime for stale data immunity."""
        try:
            mtime = file_path.stat().st_mtime
            return (str(file_path), mtime)
        except Exception:
            return (str(file_path), 0.0)

    @abstractmethod
    def _validate_content(self, file_path: Path, content: str) -> ValidationResult:
        """Validate file content for argument forwarding.

        Args:
            file_path: Path to the file being validated
            content: File content as string

        Returns:
            ValidationResult for this file
        """
        pass

    @abstractmethod
    def get_file_extensions(self) -> list[str]:
        """Return list of file extensions this validator handles.

        Examples:
            [".ps1"] for PowerShell
            [".py"] for Python
            [".ps1", ".py"] for multi-language validator
        """
        pass


class PythonArgumentForwardingValidator(ArgumentForwardingValidator):
    """Validates Python wrapper functions for argument forwarding bugs.

    Detects functions that declare explicit parameters but don't forward them
    using *args, **kwargs, or forward-compatible patterns.

    Python argument forwarding patterns:
    - *args, **kwargs - Forward all positional/keyword arguments
    - Forward references - Explicit parameter forwarding to wrapped function
    - All parameters with defaults - No forwarding needed (all optional)

    Exemptions:
    - Functions without param block (no explicit parameters)
    - All parameters have default values
    - Known decorators (@property, @staticmethod, @classmethod)
    """

    DECORATOR_PATTERN = re.compile(r"^\s*@\s*(\w+)")
    EXEMPT_DECORATORS = {"property", "staticmethod", "classmethod", "setter", "deleter"}

    def _validate_content(self, file_path: Path, content: str) -> ValidationResult:
        """Validate Python file content for argument forwarding."""
        findings = []
        all_passed = True

        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            return ValidationResult(False, [f"Syntax error: {e}"])

        # Find all function definitions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_name = node.name
                func_start_line = node.lineno

                # Skip if decorated with exempt decorators
                if self._has_exempt_decorators(content, func_start_line):
                    findings.append(f"✓ {func_name}: exempt (decorator)")
                    continue

                # Check for forwarding patterns
                forwards_args = self._check_forwarding(node, content)

                if forwards_args:
                    findings.append(f"✓ {func_name}: forwards arguments correctly")
                    continue

                # Check for exemption conditions
                is_exempt = self._is_exempt_function(node)

                if is_exempt:
                    findings.append(f"✓ {func_name}: exempt (no forwarding needed)")
                    continue

                if self.no_arg_validation:
                    findings.append(f"ℹ️  {func_name}: arg validation skipped")
                    continue

                # Has params but no forwarding
                findings.append(
                    f"❌ {func_name}: missing *args/**kwargs forwarding (line {func_start_line})"
                )
                all_passed = False

        if not findings:
            findings.append("ℹ️  No functions found in file")

        return ValidationResult(all_passed, findings)

    def _has_exempt_decorators(self, content: str, func_line: int) -> bool:
        """Check if function has exempt decorators."""
        lines = content.split("\n")
        # Check lines before function definition (up to 5 lines back)
        start = max(0, func_line - 6)
        for line in lines[start:func_line]:
            match = self.DECORATOR_PATTERN.match(line)
            if match:
                decorator_name = match.group(1)
                if decorator_name in self.EXEMPT_DECORATORS:
                    return True
        return False

    def _check_forwarding(self, node: ast.FunctionDef, content: str) -> bool:
        """Check if function forwards arguments correctly."""
        # Check for *args, **kwargs in parameters
        has_varargs = node.args.vararg and node.args.vararg.arg == "args"
        has_varkw = node.args.kwarg and node.args.kwarg.arg == "kwargs"

        if has_varargs or has_varkw:
            return True

        # Get parameter names
        param_names = {arg.arg for arg in node.args.args}
        if node.args.vararg:
            param_names.add(node.args.vararg.arg)
        if node.args.kwarg:
            param_names.add(node.args.kwarg.arg)

        # Check for forwarding in function body
        # Look for calls with *args, **kwargs, or explicit forwarding
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                # Check for *args or **kwargs in the call
                for keyword in child.keywords:
                    if keyword.arg is None and isinstance(keyword.value, ast.Name):
                        # **kwargs-like splat
                        if keyword.value.id == "kwargs":
                            return True
                # Check for Starred nodes in args (Python 3.9+ compatible)
                for arg in child.args:
                    if isinstance(arg, ast.Starred):
                        if isinstance(arg.value, ast.Name) and arg.value.id == "args":
                            return True

                # Check for explicit forwarding (e.g., target(a=a, b=b, c=c))
                # Collect all forwarded keyword argument names
                forwarded_kwargs = set()
                for keyword in child.keywords:
                    if keyword.arg and isinstance(keyword.value, ast.Name):
                        if keyword.value.id in param_names:
                            forwarded_kwargs.add(keyword.arg)

                # Check if all parameters are forwarded
                if param_names and param_names == forwarded_kwargs:
                    return True

        return False

    def _is_exempt_function(self, node: ast.FunctionDef) -> bool:
        """Check if function is exempt from forwarding requirement."""
        # No param block (no explicit parameters)
        if not node.args.args and not node.args.kwonlyargs:
            return True

        # All parameters have defaults
        # In Python AST, defaults are stored in node.args.defaults list
        # The list is right-aligned: len(defaults) may be < len(args)
        num_args = len(node.args.args)
        num_defaults = len(node.args.defaults)

        # Check if all positional args have defaults
        all_have_defaults = num_args == num_defaults
        if all_have_defaults and not node.args.kwonlyargs:
            return True

        return False

    def get_file_extensions(self) -> list[str]:
        return [".py"]


class PowerShellArgumentForwardingValidator(ArgumentForwardingValidator):
    """Validates PowerShell wrapper functions for argument forwarding bugs.

    Detects functions that declare parameters but don't forward them using
    @Args, @PSBoundParameters, or $Args patterns.

    PowerShell argument forwarding patterns:
    - @Args - Splat all arguments
    - @PSBoundParameters - Splat bound parameters
    - $Args - Reference remaining arguments

    Exemptions:
    - No param block
    - All parameters have defaults (all optional)
    - Intentional separate parameter passing patterns
    - Known exempt aliases (p-glm)
    """

    # Pattern for intentional separate parameter passing (false positive exemption)
    INTENTIONAL_SEPARATE_PATTERN = re.compile(
        r"""
        [&]\s*                    # Call operator
        [\'"][^\'"]+[\'"]\s+     # Quoted script path
        \$(?!Args\b)\w+          # Variable that's NOT $Args (intentional separate param)
    """,
        re.VERBOSE,
    )

    def _validate_content(self, file_path: Path, content: str) -> ValidationResult:
        """Validate PowerShell file content for argument forwarding."""
        findings = []
        all_passed = True

        # Parse functions from PowerShell content
        functions = self._extract_functions(content)

        # Validate each function
        if functions:
            for func_name, func_body in functions.items():
                result = self._validate_function(func_name, func_body)
                findings.extend(result.findings)
                if not result.passed:
                    all_passed = False

        # Check for aliases
        alias_findings = self._check_aliases(content)
        findings.extend(alias_findings)

        # If no functions and no aliases found, add info message
        if not functions and not alias_findings:
            findings.append("ℹ️  No functions found in file")

        return ValidationResult(all_passed, findings)

    def _extract_functions(self, content: str) -> dict[str, str]:
        """Extract function definitions from PowerShell content.

        Skips commented functions (lines starting with #).
        Uses brace counting to properly find function end boundaries.

        Returns:
            Dict mapping function names to function bodies
        """
        functions = {}

        # Find all function declarations: function name {
        func_pattern = r"function\s+([\w-]+)\s*\{"
        for match in re.finditer(func_pattern, content):
            func_name = match.group(1)
            func_start = match.end()

            # Get the line containing the function declaration
            line_start = content.rfind("\n", 0, match.start()) + 1
            line = content[line_start : match.end()]

            # Skip commented functions (line starts with # after stripping whitespace)
            if line.lstrip().startswith("#"):
                continue

            # Count braces to find the matching closing brace
            brace_count = 1
            i = func_start
            while i < len(content) and brace_count > 0:
                if content[i] == "{":
                    brace_count += 1
                elif content[i] == "}":
                    brace_count -= 1
                i += 1

            if brace_count == 0:
                func_body = content[func_start : i - 1].strip()
                functions[func_name] = func_body

        return functions

    def _validate_function(self, func_name: str, func_body: str) -> ValidationResult:
        """Validate a single function for argument forwarding.

        Args:
            func_name: Name of the function
            func_body: Function body content

        Returns:
            ValidationResult for this function
        """
        findings = []

        # Check for param block
        has_param_block = bool(re.search(r"param\s*\(", func_body))

        # Check for forwarded arguments
        has_at_args = "@Args" in func_body
        has_dollar_args = "$Args" in func_body
        has_psbound = "@PSBoundParameters" in func_body

        # Check if function forwards arguments correctly
        forwards_args = has_at_args or has_dollar_args or has_psbound

        # Check for forwarding BEFORE exemption patterns
        # Valid @Args/@PSBoundParameters forwarding takes precedence
        if forwards_args:
            findings.append(f"✓ {func_name}: forwards arguments correctly")
            return ValidationResult(True, findings)

        # Exemption patterns (only checked if no forwarding found)
        is_exempt = self._is_exempt_function(func_name, func_body, has_param_block)

        if is_exempt:
            findings.append(f"✓ {func_name}: exempt (no forwarding needed)")
            return ValidationResult(True, findings)

        if not has_param_block:
            findings.append(f"✓ {func_name}: no param block (exempt)")
            return ValidationResult(True, findings)

        if self.no_arg_validation:
            findings.append(f"ℹ️  {func_name}: arg validation skipped")
            return ValidationResult(True, findings)

        # If we get here, has param block but no forwarding
        findings.append(
            f"❌ {func_name}: missing @Args forwarding (line {self._find_line_number(func_body, 'param')})"
        )
        return ValidationResult(False, findings)

    def _is_exempt_function(self, func_name: str, func_body: str, has_param_block: bool) -> bool:
        """Check if function is exempt from argument forwarding requirement.

        Exemptions:
        - No param block
        - All parameters have defaults (all optional)
        - Intentional separate parameter passing (false positive exemption)
        - Known exempt aliases (p-glm is a simple wrapper)
        """
        if not has_param_block:
            return True

        # Check for all-optional parameters
        if self._all_params_optional(func_body):
            return True

        # Check for intentional separate parameter passing (false positive exemption)
        # This catches patterns like: & 'script.ps1' $modeArg where modeArg is
        # intentionally extracted from $Args and passed separately
        if self.INTENTIONAL_SEPARATE_PATTERN.search(func_body):
            return True

        # Known exempt aliases (p-glm is a simple wrapper)
        if func_name == "p-glm":
            return True

        return False

    def _all_params_optional(self, func_body: str) -> bool:
        """Check if all parameters have default values.

        Note: Parameters with ValueFromRemainingArguments are NOT considered
        optional for exemption purposes - they still require argument forwarding.
        """
        # Find param block
        param_match = re.search(r"param\s*\((.*?)\)", func_body, re.DOTALL)
        if not param_match:
            return False

        param_block = param_match.group(1)

        # Check for ValueFromRemainingArguments - if present, params are NOT all optional
        # This attribute means the function accepts remaining args, not that they're optional
        if "ValueFromRemainingArguments" in param_block:
            return False

        # Check if any parameter lacks a default value
        # Pattern: [type]$param (no default) vs [type]$param = 'value' (has default)
        required_params = re.findall(r"\$(\w+)\s*[,\)]", param_block)
        params_with_defaults = re.findall(r"\$(\w+)\s*=", param_block)

        # If all params have defaults, or no params found (simple param block)
        return len(required_params) == 0 or len(required_params) == len(params_with_defaults)

    def _find_line_number(self, func_body: str, pattern: str) -> int:
        """Find the approximate line number of a pattern in function body."""
        # Count newlines before the pattern to get line number
        pos = func_body.find(pattern)
        if pos == -1:
            return 1  # Default to line 1 if pattern not found
        return func_body[:pos].count("\n") + 1

    def _check_aliases(self, content: str) -> list[str]:
        """Check for Set-Alias statements.

        Returns:
            List of findings about aliases
        """
        findings = []

        # Find Set-Alias statements
        alias_pattern = r"Set-Alias\s+-Name\s+(\S+)\s*-Value\s+(\S+)"
        aliases = re.findall(alias_pattern, content)

        for alias_name, target in aliases:
            if alias_name == "p-glm":
                findings.append("ℹ️  Alias 'p-glm' exempt (known simple wrapper)")
            else:
                findings.append(f"ℹ️  Alias '{alias_name}' points to '{target}'")

        return findings

    def get_file_extensions(self) -> list[str]:
        return [".ps1"]


# For backward compatibility - expose the old class name
PowerShellArgumentValidator = PowerShellArgumentForwardingValidator
