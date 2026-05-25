#!/usr/bin/env python3
from __future__ import annotations

# --- plugin bootstrap ---
import sys as _s; from pathlib import Path as _P
_l = _P(__file__).resolve().parent.parent.parent / "__lib"
if str(_l) not in _s.path: _s.path.insert(0, str(_l))
from _bootstrap import bootstrap; _hooks_dir = bootstrap(__file__)
# --- end bootstrap ---


"""
Enhanced Path Validator with SessionContextManager Integration
===========================================================
Extends the existing path_validator.py with project context validation.

This integrates the SessionContextManager to prevent project context confusion
while maintaining all existing path validation functionality.

Usage:
    # Enhanced validation (same interface as path_validator)
    from enhanced_path_validator import EnhancedPathValidator
    validator = EnhancedPathValidator()
    result = validator.validate_file_operation_with_context(file_path, operation)

    # Backward compatibility
    result = validator.validate_file_operation(file_path)  # Works like original
"""

import re
import sys
from pathlib import Path
from typing import Any

from __lib import pre_tool_use_logic

# Import original path validator
from __lib.path_validator import PathValidator

# Import context management
context_manager_path = Path(__file__).resolve().parent.parent / "speckit" / "context_hooks.py"
if context_manager_path.exists():
    sys.path.insert(0, str(context_manager_path.parent))
    try:
        from context_hooks import show_context_status, validate_before_operation
        from context_hooks import (
            validate_file_operation as validate_context_file_operation,
        )
        CONTEXT_MANAGER_AVAILABLE = True
    except ImportError:
        CONTEXT_MANAGER_AVAILABLE = False
else:
    CONTEXT_MANAGER_AVAILABLE = False


class EnhancedPathValidator(PathValidator):
    """
    Enhanced path validator with SessionContextManager integration.
    Maintains full backward compatibility with PathValidator.
    """

    def __init__(self, config_path: Path | None = None, enable_context_validation: bool = True):
        """
        Initialize enhanced path validator.

        Args:
            config_path: Optional path to policy config (passed to parent)
            enable_context_validation: Whether to enable context validation
        """
        super().__init__(config_path)
        self.enable_context_validation = enable_context_validation and CONTEXT_MANAGER_AVAILABLE

        if self.enable_context_validation:
            print("🎯 SessionContextManager integration enabled")
        else:
            print("ℹ️  SessionContextManager not available - using path validation only")

    def validate_file_operation_with_context(self, file_path: str, operation: str = "modify", project_dir: str | None = None) -> dict[str, Any]:
        """
        Enhanced validation that includes both path safety and project context validation.

        Args:
            file_path: The file path to validate
            operation: Type of operation (create, modify, delete, etc.)
            project_dir: Optional project directory for bounds checking

        Returns:
            Dictionary with enhanced validation results
        """
        # First, do the original path validation
        path_result = self.validate_file_operation(file_path, project_dir)

        # Then, add context validation if enabled
        context_result = {
            "context_validated": True,
            "context_block_reason": None,
            "context_warning": None
        }

        if self.enable_context_validation:
            # Validate file operation against current context
            context_allowed = validate_context_file_operation(file_path, operation)

            if not context_allowed:
                path_result["is_safe"] = False
                path_result["violation_type"] = "CONTEXT_MISMATCH"
                context_result["context_validated"] = False
                context_result["context_block_reason"] = "File operation conflicts with current project context"

        # Merge results
        path_result.update(context_result)
        return path_result

    def validate_operation_with_context(self, operation_type: str, description: str = "") -> dict[str, Any]:
        """
        Validate a general operation against current project context.

        Args:
            operation_type: Type of operation (implement, create, modify, etc.)
            description: Optional description of the operation

        Returns:
            Dictionary with validation results
        """
        result = {
            "operation_type": operation_type,
            "description": description,
            "context_validated": True,
            "context_block_reason": None,
            "should_proceed": True
        }

        if self.enable_context_validation:
            # Show current context status
            context_ok = show_context_status()

            # Validate the operation
            should_proceed = validate_before_operation(operation_type, description)
            result["should_proceed"] = should_proceed
            result["context_validated"] = should_proceed

            if not should_proceed:
                result["context_block_reason"] = "Operation conflicts with current project context"

        return result

    def show_context_status(self) -> None:
        """Display current context status and warnings."""
        if self.enable_context_validation:
            show_context_status()
        else:
            print("ℹ️  SessionContextManager not available")

    def is_context_available(self) -> bool:
        """Check if SessionContextManager is available and enabled."""
        return self.enable_context_validation


# Convenience functions for backward compatibility and easy integration

def validate_file_with_context(file_path: str, operation: str = "modify", config_path: Path | None = None) -> dict[str, Any]:
    """
    Convenience function for file validation with context.

    Args:
        file_path: File path to validate
        operation: Operation type (create, modify, delete, etc.)
        config_path: Optional path validator config

    Returns:
        Enhanced validation result dictionary
    """
    validator = EnhancedPathValidator(config_path)
    return validator.validate_file_operation_with_context(file_path, operation)


def validate_operation_with_context(operation_type: str, description: str = "", config_path: Path | None = None) -> dict[str, Any]:
    """
    Convenience function for general operation validation.

    Args:
        operation_type: Type of operation
        description: Optional operation description
        config_path: Optional path validator config

    Returns:
        Validation result dictionary
    """
    validator = EnhancedPathValidator(config_path)
    return validator.validate_operation_with_context(operation_type, description)


def show_context_status_simple():
    """Show current context status (simple interface)."""
    if CONTEXT_MANAGER_AVAILABLE:
        show_context_status()
    else:
        print("ℹ️  SessionContextManager not available")


# Integration helper for existing tools

class ToolOperationValidator:
    """
    Helper class for integrating context validation into existing tools.
    Provides simple methods that can be called at the start of tool operations.
    """

    @staticmethod
    def validate_file_operation(file_path: str, operation: str = "modify") -> bool:
        """
        Validate file operation for tool integration.
        Returns True if operation should proceed.

        Args:
            file_path: File path being operated on
            operation: Type of operation

        Returns:
            True if operation is allowed, False otherwise
        """
        if not CONTEXT_MANAGER_AVAILABLE:
            return True  # No context validation available

        return validate_context_file_operation(file_path, operation)

    @staticmethod
    def validate_major_operation(operation_type: str, description: str = "") -> bool:
        """
        Validate major operation for tool integration.
        Returns True if operation should proceed.

        Args:
            operation_type: Type of operation
            description: Optional description

        Returns:
            True if operation is allowed, False otherwise
        """
        if not CONTEXT_MANAGER_AVAILABLE:
            return True  # No context validation available

        return validate_before_operation(operation_type, description)

    @staticmethod
    def show_context_warning():
        """Show context status warning if needed."""
        if CONTEXT_MANAGER_AVAILABLE:
            show_context_status()


def run(data: dict) -> dict | None:
    """In-process execution entry point."""
    # Only mutation tools can violate path policy — reads are always safe
    _WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
    if data.get("tool_name") not in _WRITE_TOOLS:
        return None

    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if not file_path:
        return None

    validator = EnhancedPathValidator()
    result = validator.validate_file_operation(file_path)

    if not result["is_safe"]:
        violation = result.get("violation_type")

        # Check edit consent for ALL violations, not just CLAUDE_SENSITIVE_EDIT
        has_consent, consent_reason, canonical_path = pre_tool_use_logic.check_claude_edit_consent(data, file_path)
        if has_consent:
            return None

        # If no consent and it's a sensitive edit, show consent request
        if violation == "CLAUDE_SENSITIVE_EDIT":
            # Case-insensitive prefix removal for Windows (P:/ vs p:/)
            relative_hint = re.sub(r'^[pP]:/\.claude/', '', canonical_path)
            return {
                "decision": "block",
                "message": (
                    f"⚠️ SENSITIVE FILE: {canonical_path}\n"
                    "This file is protected by a safety hook.\n\n"
                    "AGENT INSTRUCTION: Present this consent request to the user"
                    " — do not skip or work around it:\n"
                    f"  Type exactly: approve edit {relative_hint}\n\n"
                    "Once the user types that phrase, retry the edit."
                ),
                "blocking_hook": "PreToolUse_path_validator.py",
            }

        # For other violations without consent, show the violation message
        # Enhanced message for SYMLINK_ESCAPE to show target and guidance
        if violation == "SYMLINK_ESCAPE":
            try:
                from pathlib import Path
                link_target = Path(file_path).resolve(strict=False)
                return {
                    "decision": "block",
                    "message": (
                        f"⛔ SYMLINK BLOCKED: {file_path}\n"
                        f"→ This file is symlinked to: {link_target}\n\n"
                        f"✓ Edit the target file directly — changes auto-sync via symlink.\n"
                        f"✗ No manual copy needed — the symlink handles synchronization.\n\n"
                        f"Edit this file instead:\n  {link_target}"
                    ),
                    "blocking_hook": "PreToolUse_path_validator.py",
                }
            except Exception:
                # Fallback to generic message if resolution fails
                pass

        if violation == "ROOT_LEVEL_WRITE":
            return {
                "decision": "block",
                "message": (
                    f"⛔ ROOT_LEVEL_WRITE: Cannot write to project root.\n"
                    f"Path: {file_path}\n\n"
                    "AGENT INSTRUCTION: Choose a subdirectory and retry:\n"
                    "  P:/.claude/tmp/<filename>   (temp/draft files)\n"
                    "  P:/.tmp/<filename>           (scratch work)\n"
                    "Retry the write with a corrected path."
                ),
                "blocking_hook": "PreToolUse_path_validator.py",
            }
        return {
            "decision": "block",
            "message": f"Path Security Violation: {violation}\nPath: {file_path}",
            "blocking_hook": "PreToolUse_path_validator.py",
        }
    return None

if __name__ == "__main__":
    # Original CLI / Subprocess behavior
    import json
    try:
        data = json.load(sys.stdin)
        res = run(data)
        if res and res.get("decision") == "block":
            print(json.dumps(res))
            sys.exit(2)
        sys.exit(0)
    except Exception:
        sys.exit(0)
