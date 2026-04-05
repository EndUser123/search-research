# SessionContextManager Tool Integration Guide

## Overview

This guide shows how to integrate SessionContextManager into existing tools to prevent project context confusion. The integration is **optional, non-breaking, and adds minimal overhead**.

## Quick Start

### 1. Add Context Validation to Any Tool

```python
# Import at the top of your tool implementation
from .claude.hooks.context_aware_hooks import validate_read_operation

# Add at the start of your tool function
def Read(file_path: str, offset: int = 0, limit: int = None):
    # SessionContextManager integration (optional)
    if not validate_read_operation(file_path):
        print("❌ Read operation blocked by context validation")
        return  # Stop the operation

    # Your existing Read implementation continues...
```

### 2. Available Validation Functions

| Tool | Validation Function | Integration Point |
|------|-------------------|------------------|
| Read | `validate_read_operation(file_path)` | Before file access |
| Edit | `validate_edit_operation(file_path, old, new)` | Before file modification |
| Write | `validate_write_operation(file_path, content)` | Before file creation |
| Task | `validate_task_operation(description, subagent_type)` | Before task execution |
| Bash | `validate_bash_operation(command)` | Before command execution |
| Glob | `validate_glob_operation(pattern)` | Before file search |

## Integration Examples

### Read Tool Integration

```python
from .claude.hooks.context_aware_hooks import validate_read_operation

def Read(file_path: str, offset: int = 0, limit: int = None):
    """Enhanced Read tool with context validation."""

    # Optional: Skip validation for system files
    if not file_path.startswith(("P:/__csf.nip/", "P:/projects/", "P:/yt-fts-alt-platforms/")):
        return read_file_directly(file_path, offset, limit)

    # SessionContextManager validation
    if not validate_read_operation(file_path):
        print("❌ Read operation blocked - project context mismatch")
        print("💡 Use: python .speckit/commands/context show")
        return

    # Existing Read implementation
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # ... rest of existing implementation
            pass
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        raise
```

### Edit Tool Integration

```python
from .claude.hooks.context_aware_hooks import validate_edit_operation

def Edit(file_path: str, old_string: str, new_string: str, replace_all: bool = False):
    """Enhanced Edit tool with context validation."""

    # SessionContextManager validation
    if not validate_edit_operation(file_path, old_string, new_string):
        print("❌ Edit operation blocked - project context mismatch")
        print("💡 Use: python .speckit/commands/context set <TSK_ID>")
        return

    # Existing Edit implementation
    try:
        with open(file_path, 'r') as f:
            # ... rest of existing implementation
            pass
    except Exception as e:
        print(f"❌ Error editing file: {e}")
        raise
```

### Task Tool Integration

```python
from .claude.hooks.context_aware_hooks import validate_task_operation

def Task(description: str, prompt: str, subagent_type: str, **kwargs):
    """Enhanced Task tool with context validation."""

    # SessionContextManager validation
    if not validate_task_operation(description, subagent_type):
        print("❌ Task operation blocked - project context mismatch")
        print("💡 Use: python .speckit/commands/context detect")
        return

    # Existing Task implementation
    try:
        # ... rest of existing implementation
        pass
    except Exception as e:
        print(f"❌ Error executing task: {e}")
        raise
```

### Write Tool Integration

```python
from .claude.hooks.context_aware_hooks import validate_write_operation

def Write(file_path: str, content: str):
    """Enhanced Write tool with context validation."""

    # SessionContextManager validation
    if not validate_write_operation(file_path, content):
        print("❌ Write operation blocked - project context mismatch")
        print("💡 Use: python .speckit/commands/context validate --operation 'create file'")
        return

    # Existing Write implementation
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        print(f"❌ Error writing file: {e}")
        raise
```

## Enhanced Path Validation

### Integration with Existing Path Validator

```python
from .claude.hooks.enhanced_path_validator import EnhancedPathValidator

def validate_file_operation_enhanced(file_path: str, operation: str = "modify"):
    """Enhanced file validation with context awareness."""

    validator = EnhancedPathValidator()
    result = validator.validate_file_operation_with_context(file_path, operation)

    if not result["is_safe"]:
        if result.get("context_block_reason"):
            print(f"❌ Context validation failed: {result['context_block_reason']}")
        else:
            print(f"❌ Path validation failed: {result['violation_type']}")
        return False

    return True
```

## Context Management Commands

### User-Facing Commands

```bash
# Show current context
python .speckit/commands/context show

# Set active context
python .speckit/commands/context set TSK-ALT-PLATFORM-DOWNLOADING

# Detect available projects
python .speckit/commands/context detect

# Validate operation
python .speckit/commands/context validate --operation "Implement GPU integration"

# Clear context
python .speckit/commands/context clear
```

## Performance Impact

### Benchmarks

| Operation | Without Context | With Context | Overhead |
|-----------|----------------|-------------|----------|
| Read validation | 0.00ms | 0.10ms | +0.10ms |
| Edit validation | 0.00ms | 0.30ms | +0.30ms |
| Task validation | 0.00ms | 0.80ms | +0.80ms |
| Path validation | 0.16ms | 0.20ms | +0.04ms |

**Overall Impact**: Minimal (<1ms for most operations)

### Optimization Tips

1. **Cache validation results** for repeated operations
2. **Skip validation** for system files (`.git`, cache directories)
3. **Use `force=True`** for emergency operations
4. **Batch validations** for multiple file operations

## Error Handling

### Context Validation Failures

```python
from .claude.hooks.context_aware_hooks import validate_task_operation

def safe_task_execution(description: str, subagent_type: str):
    """Task execution with proper error handling."""

    try:
        if not validate_task_operation(description, subagent_type):
            # Context validation failed
            print("❌ Context validation failed")
            print("🔧 Solutions:")
            print("   1. Set correct context: python .speckit/commands/context set <TSK_ID>")
            print("   2. Force operation: add force=True to validation call")
            print("   3. Check available projects: python .speckit/commands/context detect")
            return False

        # Execute task
        return execute_task(description, subagent_type)

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
```

## Configuration

### Custom Context Validation

```python
from .claude.hooks.context_aware_hooks import ContextAwareHooks

class CustomContextValidator(ContextAwareHooks):
    """Custom context validator for specific needs."""

    def validate_custom_operation(self, custom_data: dict) -> bool:
        """Custom validation logic."""

        # Check if operation affects project context
        if self._is_project_affecting(custom_data):
            return self.validate_task_operation(
                custom_data.get('description', ''),
                custom_data.get('subagent_type')
            )

        return True

    def _is_project_affecting(self, data: dict) -> bool:
        """Custom logic to determine if operation affects project context."""
        indicators = ['gpu', 'platform', 'integration', 'workload']
        description = data.get('description', '').lower()
        return any(indicator in description for indicator in indicators)
```

## Testing

### Unit Tests for Integration

```python
import unittest
from .claude.hooks.context_aware_hooks import validate_task_operation

class TestContextIntegration(unittest.TestCase):

    def test_gpu_task_validation(self):
        """Test GPU task validation in different contexts."""

        # Mock platform context
        with mock_context("TSK-ALT-PLATFORM-DOWNLOADING"):
            result = validate_task_operation("Implement GPU integration")
            self.assertFalse(result)  # Should be blocked

        # Mock GPU context
        with mock_context("TSK-GPU-ACCELERATION"):
            result = validate_task_operation("Implement GPU integration")
            self.assertTrue(result)   # Should be allowed

    def test_force_override(self):
        """Test force override functionality."""

        result = validate_task_operation(
            "Implement GPU integration",
            force=True  # Should override validation
        )
        self.assertTrue(result)
```

## Migration Path

### Phase 1: Non-Breaking Integration
1. Add context validation functions as optional imports
2. Add validation calls at the start of tool functions
3. Maintain full backward compatibility

### Phase 2: Enhanced Features
1. Add context-aware error messages
2. Integrate with existing path validation
3. Add user-friendly commands

### Phase 3: Full Integration
1. Make context validation default for major operations
2. Add configuration options for validation strictness
3. Integrate with IDE and editor plugins

## Troubleshooting

### Common Issues

**Issue**: Import errors for context hooks
```bash
# Solution: Check if .speckit directory exists
ls -la .speckit/
python -c "from .claude.hooks.context_aware_hooks import validate_task_operation; print('OK')"
```

**Issue**: Context validation always blocking
```bash
# Solution: Check current context
python .speckit/commands/context show
python .speckit/commands/context detect
```

**Issue**: Performance impact
```bash
# Solution: Profile validation performance
python .speckit/integration_demo.py
# Look for operations with >10ms overhead
```

## Support

### Context Management Commands

```bash
# Get help
python .speckit/commands/context --help

# Show system status
python .speckit/integration_demo.py

# Test validation
python .claude/hooks/enhanced_path_validator.py --check-path "test_file.py"
```

### Debug Information

```python
from .claude.hooks.context_aware_hooks import get_hooks

hooks = get_hooks()
print(f"Context available: {hooks.context_available}")
print("Current context status:")
hooks.show_context_status()
```

---

This integration provides robust project context validation while maintaining full backward compatibility and minimal performance impact. The system is designed to prevent the exact type of project confusion that led to its creation.
