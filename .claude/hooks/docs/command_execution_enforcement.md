# Command Execution Enforcement System v1.0

> **⚠️ SUPERSEDED:** This documentation describes the legacy system.
> See `skill_enforcement.md` for the current architecture (v2.1).

## Purpose

Ensures slash commands are **executed**, not **described**.

## Problem Solved

Prior system (`slash_command_reminder.py`) injected advisory text:
```
⚠️ SLASH COMMAND DETECTED
Read the FULL command file...
```

This was **easily ignored** by the LLM, leading to:
- Commands being summarized instead of executed
- Goal displacement where LLM creates meta-work instead of actual work
- No post-generation validation to catch violations

## Solution Architecture

### Pre-Generation: `command_directive_injector.py`

**Layer:** `0_command_directive` (UserPromptSubmit)

**What it does:**
1. Detects slash command in user prompt
2. Reads command file from `P:/.claude/skills/{name}/SKILL.md`
3. Extracts:
   - `⚡ EXECUTION DIRECTIVE` section
   - `**DO NOT:**` rules
   - `**DEFAULT:**` behavior
4. Injects as **structured critical context**
5. Saves command state for post-generation validator

### Post-Generation: `command_execution_validator.py`

**Layer:** `4_command_execution` (Stop)

**What it does:**
1. Loads command state saved by injector
2. Validates response against:
   - **Description patterns** (highest priority)
   - **DO NOT rule violations**
   - **Command-specific rules**
   - **Execution evidence** (mitigating factor)
3. **Blocks** if response describes instead of executes

## Configuration

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `COMMAND_DIRECTIVE_INJECTOR_ENABLED` | `true` | Enable/disable pre-generation injection |
| `COMMAND_EXECUTION_VALIDATOR_ENABLED` | `true` | Enable/disable post-generation validation |

## Files

| File | Purpose |
|------|---------|
| `command_directive_injector.py` | Pre-generation directive injection |
| `command_execution_validator.py` | Post-generation compliance validation |
| `session_data/active_command.json` | State sharing between hooks |
| `_archive_v1/slash_command_reminder.py` | Archived advisory-only hook |

## Testing

```bash
python P:/.claude/hooks/command_execution_validator.py --test
```

## Principle

> **Structural enforcement > instruction injection**
