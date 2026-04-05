---
name: ralph-loop
description: User-friendly wrapper for Ralph-style autonomous development loops with automatic plan resolution
aliases: [ralph-loop, ralph]
version: 0.1.0
author: loop-core contributors
---

# /ralph-loop — Ralph-Style Autonomous Development Loop (with Plan Resolution)

User-friendly wrapper for Ralph-style autonomous development loops that automatically resolves plan file paths and delegates to `/loop-code`.

## Purpose

Provides a simplified interface to the Ralph-style autonomous development loop by:
- Automatically resolving plan file paths using intelligent fallback
- Delegating to `/loop-code` for actual loop execution
- Supporting flexible plan organization strategies
- Enabling per-terminal plan isolation for multi-terminal workflows

## When to Use

Use `/ralph-loop` when you want to:
- Run an autonomous development loop without manually specifying plan paths
- Use the default `.claude/loop/plan.md` location
- Run per-terminal isolated loops with `plan.{terminal_id}.md`
- Use project-root `plan.md` as a fallback
- Explicitly specify a custom plan path

## How It Works

### Plan Resolution Strategy

`/ralph-loop` uses a 4-tier priority system to resolve plan paths:

1. **Explicit path** (highest priority): If you provide a plan path argument, use it
2. **Default location**: Check `.claude/loop/plan.md` (standard location)
3. **Per-terminal**: Check `plan.{terminal_id}.md` (multi-terminal isolation)
4. **Root fallback**: Check `plan.md` in project root (backward compatibility)

### Resolution Examples

```bash
# Explicit path (highest priority)
/ralph-loop path/to/custom.md

# Default .claude/loop/plan.md
/ralph-loop

# Per-terminal plan (e.g., plan.console_abc123.md)
/ralph-loop

# Root plan.md fallback
/ralph-loop
```

### Multi-Terminal Isolation

When running multiple loops in parallel terminals, each terminal can have its own plan:

```
project/
├── .claude/loop/plan.md          # Default plan (shared)
├── plan.console_abc123.md         # Terminal-specific plan A
├── plan.console_xyz789.md         # Terminal-specific plan B
└── plan.md                        # Root fallback (shared)
```

**Terminal A** (`console_abc123`): Uses `plan.console_abc123.md`
**Terminal B** (`console_xyz789`): Uses `plan.console_xyz789.md`
**Other terminals**: Use `.claude/loop/plan.md` or `plan.md`

## Usage

### Basic Usage

```bash
# Auto-resolve plan path (checks default, per-terminal, root)
/ralph-loop

# Explicit plan path
/ralph-loop path/to/custom.md

# With description
/ralph-loop "Implement user authentication with OAuth2"
```

### Example Plan File

```markdown
# Feature: User Authentication

## RALPH_STATUS

- EXIT_SIGNAL: false
- completion_indicators: 0
- current_task: TASK-001

## Tasks

- [ ] TASK-001 Design database schema for users table
- [ ] TASK-002 Implement password hashing utility
- [ ] TASK-003 Create login endpoint
- [ ] TASK-004 Write unit tests for auth module
- [ ] TASK-005 Verify all tests pass and document API
```

### Plan Resolution Workflow

1. **User invokes** `/ralph-loop` (with optional path/description)
2. **Resolve plan path** using 4-tier priority
3. **Validate plan exists** (error if not found)
4. **Detect terminal ID** for multi-terminal isolation
5. **Delegate to `/loop-code`** with resolved plan path
6. **Execute autonomous loop** until exit conditions met

## Plan Organization Patterns

### Pattern 1: Centralized Default (Recommended)

```
project/
└── .claude/loop/plan.md          # Single shared plan
```

**Best for**: Single-terminal workflows, standard development

### Pattern 2: Per-Terminal Isolation

```
project/
├── plan.console_abc123.md         # Terminal A plan
├── plan.console_xyz789.md         # Terminal B plan
```

**Best for**: Parallel feature development, testing isolation

### Pattern 3: Root Fallback

```
project/
└── plan.md                        # Root-level plan
```

**Best for**: Simple projects, backward compatibility

### Pattern 4: Hybrid (Most Flexible)

```
project/
├── .claude/loop/plan.md          # Shared baseline
├── plan.console_abc123.md         # Terminal A overrides
└── plan.console_xyz789.md         # Terminal B overrides
```

**Best for**: Multi-terminal with shared baseline

## Integration with /loop-code

`/ralph-loop` is a thin wrapper that:

1. **Resolves plan path** using `scripts.plan_resolution.resolve_plan_path()`
2. **Validates plan exists** before invoking `/loop-code`
3. **Delegates to `/loop-code`** with resolved plan path
4. **Provides user-friendly error messages** for resolution failures

### Architecture

```
┌─────────────────────────────────────────────────────┐
│ /ralph-loop Skill                                  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  1. Parse arguments (path, description)            │
│  2. Resolve plan path (4-tier priority)            │
│  3. Validate plan exists                           │
│  4. Delegate to /loop-code                         │
│                                                     │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ /loop-code Skill                                   │
├─────────────────────────────────────────────────────┤
│                                                     │
│  - Detect terminal_id                               │
│  - Parse plan tasks                                 │
│  - Execute /code for each task                      │
│  - Track completion state                           │
│  - Exit based on policy                             │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Error Handling

### Plan Not Found

If no plan file is found after resolution:

```
Error: No plan file found in project.

Searched locations (in priority order):
1. .claude/loop/plan.md
2. plan.{terminal_id}.md
3. plan.md

Solution: Create a plan file or use explicit path:
  /ralph-loop path/to/plan.md
```

### Invalid Plan Path

If explicit path doesn't exist:

```
Error: Plan file not found: path/to/plan.md

Solution: Check the path or create the file:
  touch path/to/plan.md
```

### Plan Parse Error

If plan file has invalid format:

```
Error: Failed to parse plan file: plan.md

This usually means:
- No tasks found (need "- [ ] TASK-XXX" format)
- Invalid markdown structure

Solution: Check plan format matches examples.
```

## Exit Conditions

`/ralph-loop` inherits exit conditions from `/loop-code`:

- **completion_indicators >= min_completion_indicators** (always required)
- **EXIT_SIGNAL: true** in RALPH_STATUS (if `require_exit_signal` enabled)
- **All tasks complete** (if `require_all_tasks_complete` enabled)
- **Verification passed** (if `require_verification_pass` enabled)

See `/loop-code` documentation for exit policy configuration.

## State Management

`/ralph-loop` uses the same state management as `/loop-code`:

```
~/.claude/state/terminals/<terminal_id>/
├── loop_state.json          # Current loop state
├── loop_metrics.json        # Performance metrics
└── logs/
    └── decision.log         # Decision log
```

Each terminal has isolated state, enabling parallel loops.

## Examples

### Example 1: Single-Terminal Workflow

```bash
# Create plan
mkdir -p .claude/loop
cat > .claude/loop/plan.md << 'EOF'
# Feature: Add User Registration

## RALPH_STATUS
- EXIT_SIGNAL: false
- completion_indicators: 0

## Tasks
- [ ] TASK-001 Design registration form
- [ ] TASK-002 Implement form validation
- [ ] TASK-003 Add database storage
- [ ] TASK-004 Write tests
EOF

# Run loop
/ralph-loop
```

### Example 2: Multi-Terminal Isolation

```bash
# Terminal 1: Feature development
cat > plan.console_abc123.md << 'EOF'
# Feature: Authentication
## Tasks
- [ ] TASK-001 Implement login
EOF

/ralph-loop  # Uses plan.console_abc123.md

# Terminal 2: Bug fixes (simultaneous)
cat > plan.console_xyz789.md << 'EOF'
# Feature: Bug Fixes
## Tasks
- [ ] TASK-001 Fix navigation bug
EOF

/ralph-loop  # Uses plan.console_xyz789.md
```

### Example 3: Explicit Plan Path

```bash
# Run with custom plan location
/ralph-loop docs/my_feature_plan.md

# Run with description
/ralph-loop "Implement OAuth2 authentication"
```

### Example 4: Root Plan Fallback

```bash
# Simple project with root-level plan
cat > plan.md << 'EOF'
# Project Tasks
## Tasks
- [ ] TASK-001 Setup project
- [ ] TASK-002 Implement feature
EOF

/ralph-loop  # Automatically finds plan.md
```

## Comparison: /ralph-loop vs /loop-code

| Feature | /ralph-loop | /loop-code |
|---------|-------------|------------|
| **Plan resolution** | Automatic (4-tier) | Manual (explicit path) |
| **Use case** | User-friendly, flexible | Precise control |
| **Per-terminal plans** | Supported (auto-detected) | Manual specification |
| **Error messages** | User-friendly diagnostics | Technical errors |
| **Arguments** | Optional path/description | Required plan path |

**When to use `/ralph-loop`**:
- Standard development workflows
- Multi-terminal parallel development
- Flexible plan organization
- User-friendly interface

**When to use `/loop-code`**:
- Precise control over plan path
- Scripted automation
- Non-standard plan locations
- Integration with other tools

## Related Commands

- **/loop-code** — Core Ralph-style autonomous loop (used by `/ralph-loop`)
- **/code** — Feature development workflow (executed by loop for each task)
- **/verify** — Verification orchestrator (optional exit condition)

## Files

- **Skill**: `P:/packages/loop-core/skills/ralph-loop/SKILL.md`
- **Plan resolution**: `P:/packages/loop-core/scripts/plan_resolution.py`
- **Core loop**: `P:/packages/loop-core/skills/loop-code/SKILL.md`
- **Tests**: `P:/packages/loop-core/tests/test_ralph_loop_plan_resolution.py`

## Implementation Notes

The `/ralph-loop` skill delegates to `/loop-code` for actual loop execution. The key differences are:

1. **Plan Resolution**: Uses `resolve_plan_path()` to auto-detect plans
2. **Validation**: Checks plan existence before invoking `/loop-code`
3. **Error Messages**: Provides user-friendly diagnostics
4. **Flexibility**: Supports optional path argument and description

The core loop logic, state management, and exit conditions are identical to `/loop-code`.

## Tags

ralph-loop, autonomous-development, plan-resolution, multi-terminal, wrapper, convenience
