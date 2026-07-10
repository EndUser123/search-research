#!/usr/bin/env python3
"""
Completion Validator Hook
=========================

PostToolUse hook that detects false completion claims for unregistered modules.

Problem: AI claims "Implementation Complete: Gate is live and ready for production"
after writing code + tests, but module isn't in core_hook_modules registry
so it never runs.

Solution: When a module file is written, immediately verify it's registered
in core_hook_modules. Warns if module won't execute because it's not in the registry.

Architecture:
1. Triggers on Write/Edit operations for Python files in UserPromptSubmit_modules/
2. Extracts module name from file path
3. Parses registry.py to check if module is in core_hook_modules list
4. Returns warning via additionalContext for unregistered modules

This prevents the abstraction_clarity_gate failure case where code + tests
are written, but the module is never registered so it never runs.

Based on proactive-honesty.md memory:
- Never claim "done" beyond verified reality
- Always state what remains unverified
- Prefer honest uncertainty over confident guessing
"""

import ast
import re
from pathlib import Path
from typing import Any

# Import base class
from posttooluse.base import PostToolUseHook


class CompletionValidator(PostToolUseHook):
    """
    Validates completion claims against integration reality.

    Prevents false "live/ready" claims by checking:
    - Module exists in UserPromptSubmit_modules/ directory
    - Module is registered in core_hook_modules list in registry.py
    - Module can be imported (has valid Python syntax)
    """

    env_var = "COMPLETION_VALIDATOR_ENABLED"
    default_enabled = True
    tool_matcher = {"Write", "Edit"}

    def __init__(self):
        super().__init__()
        # Cache for core_hook_modules list
        self._registry_cache: list[str] | None = None
        # Path to registry.py
        self.registry_file = (
            Path(__file__).resolve().parent.parent / "UserPromptSubmit_modules" / "registry.py"
        )

    def process(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_response: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Validate completion claims against integration status.

        Args:
            tool_name: Name of the tool that was executed
            tool_input: Input parameters passed to the tool
            tool_response: Response/output from the tool

        Returns:
            Dict with validation results. May include injection for unregistered modules.
        """
        result = {
            "passed": True,
            "injection": None,
            "module_name": None,
            "is_registered": False,
            "claims_detected": [],
        }

        # Extract file path
        file_path = self._extract_file_path(tool_input, tool_response)
        if not file_path:
            return result

        # Skip non-UserPromptSubmit_modules files
        if "UserPromptSubmit_modules" not in file_path:
            return result

        # Extract module name from file path
        module_name = self._extract_module_name(file_path)
        if not module_name:
            return result

        result["module_name"] = module_name

        # Verify module is in core_hook_modules registry at file-write time
        # This catches registration issues immediately, preventing the
        # abstraction_clarity_gate failure case
        is_registered = self._verify_module_registered(module_name)
        result["is_registered"] = is_registered

        # If module not registered, inject warning
        # This prevents claiming "done" when module won't actually execute
        if not is_registered:
            result["passed"] = False
            result["injection"] = self._generate_registration_warning(
                module_name=module_name
            )

        return result

    def _extract_file_path(
        self,
        tool_input: dict[str, Any],
        tool_response: dict[str, Any]
    ) -> str | None:
        """Extract file path from tool input/response."""
        if isinstance(tool_input, dict):
            path = (
                tool_input.get("file_path") or
                tool_input.get("path") or
                tool_input.get("filePath") or
                tool_input.get("target")
            )
            if path:
                return path

        # Try other fields
        if isinstance(tool_response, dict):
            return tool_response.get("file_path") or tool_response.get("path")

        return None

    def _extract_module_name(self, file_path: str) -> str | None:
        """
        Extract module name from file path.

        Example: "P:/.claude/hooks/UserPromptSubmit_modules/truthfulness_gate.py"
        Returns: "truthfulness_gate"
        """
        path = Path(file_path)
        if path.parent.name == "UserPromptSubmit_modules":
            # Direct child of UserPromptSubmit_modules/
            return path.stem  # filename without .py extension
        return None

    def _verify_module_registered(self, module_name: str) -> bool:
        """
        Verify module is in core_hook_modules registry list.

        Args:
            module_name: Name of the module to check

        Returns:
            True if module is in core_hook_modules list
        """
        # Use cached registry if available
        if self._registry_cache is not None:
            return module_name in self._registry_cache

        # Parse registry.py via AST to extract core_hook_modules entries.
        # A non-greedy regex was used here before and truncated at the first
        # ']' inside the list — a comment containing "[PLAN]/[RATIONALE]"
        # (registry.py:776) hid every module registered after it, producing
        # false NOT-REGISTERED warnings for correctly registered modules.
        # AST parsing ignores comments, so bracket-bearing comments are inert.
        try:
            tree = ast.parse(self.registry_file.read_text(encoding="utf-8"))
            module_names: list[str] = []
            for node in ast.walk(tree):
                if not isinstance(node, ast.Assign):
                    continue
                for target in node.targets:
                    if (
                        getattr(target, "id", None) == "core_hook_modules"
                        and isinstance(node.value, (ast.List, ast.Tuple))
                    ):
                        module_names.extend(
                            elt.value
                            for elt in node.value.elts
                            if isinstance(elt, ast.Constant)
                            and isinstance(elt.value, str)
                        )

            # Cache for future use
            self._registry_cache = module_names

            return module_name in module_names

        except Exception:
            # Fail open - don't block on registry parse errors
            return False

    def _generate_registration_warning(
        self,
        module_name: str
    ) -> str:
        """
        Generate warning injection for unregistered module.

        Args:
            module_name: Name of the module that was written but not registered

        Returns:
            Warning message string
        """
        warning = f"""⚠️ **MODULE NOT REGISTERED - WILL NOT EXECUTE**

**Module**: {module_name}.py
**Location**: UserPromptSubmit_modules/{module_name}.py

**Issue**: This module file was created/modified, but it's not registered in the `core_hook_modules` list in `registry.py`.

**Impact**: Without registration, this module will never be loaded or executed:
- UserPromptSubmit hooks will not call this module
- The `@register_hook` decorator never runs
- Any code in this module is dead code

**To fix this:**
1. Open `UserPromptSubmit_modules/registry.py`
2. Find the `core_hook_modules` list (search for `core_hook_modules = [`)
3. Add `"{module_name}",` to the list
4. Save the file

**Example:**
```python
core_hook_modules = [
    "abstraction_clarity_gate",
    "{module_name}",  # ← Add this line
    # ... other modules
]
```

**Verification:**
After adding to registry, the module will load on next UserPromptSubmit event.

**Related**: See proactive-honesty.md - "Integration verified" principle
"""
        return warning
