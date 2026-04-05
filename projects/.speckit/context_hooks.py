#!/usr/bin/env python3
"""
Context validation hooks for integration with tool operations
Automatically validates project context before major operations
"""

from session_context_manager import SessionContextManager


class ContextValidator:
    """
    Provides validation hooks to prevent project context confusion
    """

    def __init__(self):
        self.manager = SessionContextManager()

    def should_validate_operation(self, operation_type: str, description: str = "") -> bool:
        """
        Determine if operation requires context validation
        Returns True if validation should be performed
        """
        # High-risk operations that always need validation
        high_risk_patterns = [
            'create', 'implement', 'build', 'develop', 'write',
            'modify', 'edit', 'refactor', 'delete', 'remove'
        ]

        # Project-specific operations
        project_patterns = [
            'gpu', 'platform', 'integration', 'testing',
            'workload', 'batch_downloader', 'acceleration'
        ]

        op_lower = operation_type.lower() + " " + description.lower()

        # Check for high-risk patterns
        if any(pattern in op_lower for pattern in high_risk_patterns):
            return True

        # Check for project-specific patterns
        if any(pattern in op_lower for pattern in project_patterns):
            return True

        return False

    def pre_operation_validation(self, operation_type: str, description: str = "", auto_correct: bool = True) -> bool:
        """
        Perform pre-operation validation with optional auto-correction
        Returns True if operation should proceed
        """
        if not self.should_validate_operation(operation_type, description):
            return True  # No validation needed

        # Check current context
        worktree_context = self.manager.get_worktree_context()

        # If we have a worktree context but no active context, set it automatically
        if worktree_context and not self.manager.current_context and auto_correct:
            try:
                self.manager.set_active_context(worktree_context, force=True)
                print(f"🎯 Auto-set context: {worktree_context}")
                return True
            except ValueError:
                pass  # Continue to manual validation

        # Validate the operation
        return self.manager.pre_operation_check(f"{operation_type}: {description}")

    def validate_file_operation(self, file_path: str, operation: str) -> bool:
        """
        Validate file operations in project context
        """
        # Extract context from file path
        path_lower = file_path.lower()

        if 'gpu' in path_lower or 'workload' in path_lower:
            return self.pre_operation_validation(operation, f"GPU-related file: {file_path}")
        elif 'platform' in path_lower or 'odysee' in path_lower or 'rumble' in path_lower:
            return self.pre_operation_validation(operation, f"Platform-related file: {file_path}")
        elif 'batch_downloader' in path_lower:
            return self.pre_operation_validation(operation, f"BatchDownloader file: {file_path}")

        return True  # Allow non-project-specific operations

    def get_context_warning(self) -> str | None:
        """
        Get context warning message for current situation
        """
        worktree_context = self.manager.get_worktree_context()
        active_context = self.manager.current_context

        if not active_context and worktree_context:
            return f"⚠️  No active context set. Worktree suggests: {worktree_context}"

        if active_context and worktree_context and active_context.tsk_id != worktree_context:
            return f"⚠️  Context mismatch! Active: {active_context.tsk_id}, Worktree: {worktree_context}"

        return None

# Global validator instance
_validator = None

def get_validator() -> ContextValidator:
    """Get or create global validator instance"""
    global _validator
    if _validator is None:
        _validator = ContextValidator()
    return _validator

def validate_before_operation(operation_type: str, description: str = "") -> bool:
    """
    Convenience function for operation validation
    Can be called from any tool operation
    """
    validator = get_validator()
    return validator.pre_operation_validation(operation_type, description)

def validate_file_operation(file_path: str, operation: str) -> bool:
    """
    Convenience function for file operation validation
    """
    validator = get_validator()
    return validator.validate_file_operation(file_path, operation)

def show_context_status():
    """
    Show current context status and any warnings
    """
    validator = get_validator()
    warning = validator.get_context_warning()

    if warning:
        print(warning)
        print("💡 Use: python .speckit/commands/context show")
        print("💡 Set context: python .speckit/commands/context set <TSK_ID>")
        return False

    if validator.manager.current_context:
        print(f"✅ Context: {validator.manager.current_context.tsk_id}")
        return True

    print("ℹ️  No active context set")
    return True

if __name__ == "__main__":
    # Test the validator
    show_context_status()
