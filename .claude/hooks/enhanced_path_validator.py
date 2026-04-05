#!/usr/bin/env python3
from __future__ import annotations

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

import sys
from pathlib import Path
from typing import Any

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


if __name__ == "__main__":
    # Demo functionality
    import argparse

    parser = argparse.ArgumentParser(description="Enhanced path validator with context management")
    parser.add_argument("--check-path", metavar="PATH", help="Check file path with context validation")
    parser.add_argument("--check-operation", metavar="OPERATION", help="Check operation with context validation")
    parser.add_argument("--description", metavar="DESC", help="Operation description")
    parser.add_argument("--show-context", action="store_true", help="Show current context status")
    parser.add_argument("--config", metavar="FILE", help="Custom path validator config")

    args = parser.parse_args()

    if args.show_context:
        show_context_status_simple()

    elif args.check_path:
        result = validate_file_with_context(args.check_path, "check", args.config)
        status = "✅ ALLOWED" if result["is_safe"] else "❌ BLOCKED"
        print(f"{status}: {args.check_path}")
        print(f"  Path validation: {result['violation_type']}")
        if result.get("context_block_reason"):
            print(f"  Context validation: {result['context_block_reason']}")

    elif args.check_operation:
        result = validate_operation_with_context(args.check_operation, args.description or "", args.config)
        status = "✅ ALLOWED" if result["should_proceed"] else "❌ BLOCKED"
        print(f"{status}: {args.check_operation}")
        if result.get("context_block_reason"):
            print(f"  Reason: {result['context_block_reason']}")

    else:
        parser.print_help()
