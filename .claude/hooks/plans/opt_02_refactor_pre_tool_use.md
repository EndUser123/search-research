# Plan 02: Refactor PreToolUse Execution Firewall

## Problem Statement
`pre_tool_use.py` (2,600+ lines) acts as a "God script" for the Layer 2 Execution Firewall. It mixes pattern loading, validator logic, git safety checks, and TDD enforcement in one file.

## Objectives
- Reduce `pre_tool_use.py` to <500 lines.
- Modularize validators into `P:/.claude/hooks/pretooluse/`.
- Improve the clarity of safety rules and enforcement logic.

## Proposed Changes

### 1. Create New Package Structure
- Create `P:/.claude/hooks/pretooluse/__init__.py`.
- Create specialized validator modules:
    - `security_patterns.py`: Logic for dangerous command detection (moved from `dangerous_patterns` list).
    - `git_safety.py`: Logic for `_check_git_checkout_safety` and `_check_git_add_anti_bleed`.
    - `path_protector.py`: Logic for `protected_files` and `_check_file_permission_protection`.
    - `tdd_enforcer.py`: Integration with TDD evidence and validation.
    - `constitutional_gate.py`: Logic for PART C.1 compliance.

### 2. Refactor ExecutionFirewall Class
- Refactor `ExecutionFirewall` to be a lightweight coordinator.
- Use a registry of validators that are executed sequentially or based on tool type.
- Move large static lists (patterns, protected files) to JSON/YAML configuration files or dedicated data modules.

### 3. Shared Registry Pattern
- Adopt the same `Registry` pattern used in `PostToolUse_router.py` to ensure architectural consistency across all hook layers.

## Success Criteria
- `pre_tool_use.py` is under 500 lines.
- Security blocking remains deterministic and correct.
- Improved observability into which validator blocked or warned about an operation.
