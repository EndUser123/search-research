---
name: bgkill
description: Background task cleanup - manage and kill zombie processes in Claude Code
version: "1.0.0"
status: stable
category: utility
triggers:
  - /bgkill
  - "background tasks"
  - "zombie processes"
aliases:
  - /bgkill

suggest:
  - /health-monitor
  - /obs
  - /debug
---

# /bgkill - Background Task Cleanup

## Purpose

Manage and kill zombie processes in Claude Code.

## Project Context

### Constitution/Constraints
- User-initiated cleanup only
- No background services (matches constitutional constraints)
- Explicit confirmation required for killall

### Technical Context
- Uses TaskOutput tool for status retrieval
- Uses KillShell for task termination
- Task status: running, completed, failed, hung

### Architecture Alignment
- Part of utility skills family
- Integrates with /health-monitor and /obs
- Supports /debug workflow cleanup

## Your Workflow

1. **List Tasks** - Show all background tasks with status
2. **Identify Targets** - Find hung or failed tasks
3. **Kill Specific** - Terminate by task ID
4. **Kill All** - Clean slate with confirmation
5. **Verify Cleanup** - Confirm tasks terminated

## Validation Rules

### Prohibited Actions
- **NEVER killall without confirmation** - user must approve
- **NEVER claim kill without verification** - check TaskOutput after

### Required Output Format
- Show task ID, status, and description
- Group by status (running, completed, failed, hung)
- Action recommendations per task

Manage background tasks and zombie processes in Claude Code.

## Usage

```bash
/bgkill              # List all background tasks
/bgkill list         # Same as above
/bgkill kill <id>    # Kill specific task by ID
/bgkill killall      # Kill all background tasks (with confirmation)
/bgkill status        # Show task status summary
```

## Task Status

| Status | Meaning | Action |
|--------|---------|--------|
| running | Active task | Monitor or kill |
| completed | Finished, output ready | Retrieve output |
| failed | Exited with error | Check error |
| hung | No progress >30s | Kill it |

## Examples

```bash
# See what's running
/bgkill

# Kill hung task
/bgkill kill bash_3

# Clean slate - kill everything
/bgkill killall
```

## Implementation

Uses TaskOutput tool to retrieve status and KillShell to terminate tasks.
