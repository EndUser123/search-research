# Investigation Ledger System

**Purpose:** Tracks what Claude Code actually investigates (files read, searches, executions) and blocks claims that aren't substantiated by investigation.

**Status:** Production - Integrated with Stop router

---

## Problem Solved

Claude Code sometimes fabricates claims about code behavior without actually reading the relevant files. This system:

1. **Tracks investigation activity** via PostToolUse hooks
2. **Validates claims** in responses reference investigated topics
3. **Enforces confidence ceilings** based on investigation depth
4. **Triggers self-assessment** when diagnostic questions answered without investigation

---

## Architecture

```
PostToolUse → InvestigationTracker → session_ledger_{terminal_or_session}.json
                                             ↓
Stop → StopHook_investigation_required → "Did you investigate?" (self-prompt)
Stop → Stop_investigation_validator → "Do claims match ledger?" (block)
```

### Two-Layer Defense

| Layer | Hook | Action | Severity |
|-------|------|--------|----------|
| 1 | `StopHook_investigation_required.py` | Self-prompt if diagnostic Q + no tools | WARN |
| 2 | `Stop_investigation_validator.py` | Block if claims exceed investigation | CRITICAL |

**Layer 1** catches the "meta-failure" where LLM responds without using ANY tools.
**Layer 2** catches claims that don't match what was actually investigated.

---

## Evidence Tier System

| Tier | Ceiling | Requirement |
|------|---------|-------------|
| 1 | 95% | 3+ files read + successful execution |
| 3 | 75% | 2+ files read OR (1 file + 2 searches) |
| 4 | 50% | 1 file read OR 1 search |
| None | 0% | No investigation |

**Rule:** Confidence cannot exceed tier ceiling.

---

## Components

| File | Purpose |
|------|---------|
| `ledger.py` | Core tracking - file reads, searches, executions |
| `validate_claims.py` | Detects claim patterns, validates against investigation |
| `validate_confidence.py` | Detects confidence levels, validates against ceiling |
| `Stop_investigation_validator.py` | Stop hook: blocks unsubstantiated claims |
| `test_investigation_ledger.py` | 24 tests (all passing) |
| `test_integration.py` | Integration tests for end-to-end validation |

### Related Components (outside this directory)

| File | Purpose |
|------|---------|
| `posttooluse/investigation_tracker.py` | In-process tracker for PostToolUse registry |
| `StopHook_investigation_required.py` | Self-prompt for diagnostic questions |

---

## Integration

### Current Integration (via routers)

The system is integrated via the hook routers:

**PostToolUse_router.py** - `posttooluse/investigation_tracker.py`:
- Runs in-process (~5ms overhead)
- Records Read, Search, Grep, Bash tool usage to ledger
- Pins `CLAUDE_SESSION_ID`/`CLAUDE_TERMINAL_ID` context when session metadata is available
- Writes `session_id` + `terminal_id` into tool-sequence entries for downstream evidence consumers

**Stop_router.py** - Two hooks in sequence:
```python
HOOK_SEQUENCE = [
    ...
    ("StopHook_investigation_required.py", "INVESTIGATION_REQUIRED_ENABLED", "true"),
    ("investigation-ledger/Stop_investigation_validator.py", "INVESTIGATION_LEDGER_ENABLED", "true"),
    ...
]
```

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `INVESTIGATION_LEDGER_ENABLED` | `true` | Enable/disable ledger tracking and validation |
| `INVESTIGATION_REQUIRED_ENABLED` | `true` | Enable/disable self-prompt for diagnostic questions |
| `CLAUDE_SESSION_ID` | runtime | Session-scoped ledger/tool-sequence isolation key |
| `CLAUDE_TERMINAL_ID` | runtime | Terminal-scoped isolation key (preserved if already set) |

---

## Behavior

### What Gets Tracked

- **File reads:** Read, View, Cat, GetFile tools
- **Searches:** Search, Grep, Find, Ripgrep, Glob tools
- **Executions:** Bash, Shell, Exec, Run, Terminal tools
- **Directory listings:** list_directory, ls, dir

### Layer 1: Investigation Required (Self-Prompt)

Triggers when:
1. User asks diagnostic question ("How does X work?", "Why is Y failing?")
2. No investigation tools used this turn
3. Response is substantial (>150 chars, not a question)

Action: Injects self-assessment prompt asking LLM to verify it investigated.

### Layer 2: Investigation Validator (Block)

Blocks when:
1. Response contains claim patterns about system behavior
2. Claims reference topics not in investigation ledger
3. Confidence exceeds investigation-based ceiling

### What Passes

- Short responses (<100 chars for claims, <50 chars for confidence)
- Questions
- Responses that reference investigated files
- Hedged claims ("might", "could", "possibly")
- Confidence within ceiling limits
- Responses admitting uncertainty ("I don't know", "Let me check")

---

## Session Management

- **Timeout:** Ledger resets after 4 hours
- **Location:** `.claude/data/session_ledger_{id}.json` (terminal/session scoped)
- **Locking:** File locks prevent race conditions on parallel tool calls
- **Identity precedence:** `CLAUDE_TERMINAL_ID` → `CLAUDE_SESSION_ID` → terminal detection fallback

### Assumption Audit Evidence Alignment (2026-02)

To prevent `VERIFICATION_THEATER` false positives from cross-session tool bleed:

- `PostToolUse_router.py` now records `session_id` in tool-sequence entries.
- `assumption_audit_v2.py` now loads sequence via `load_tool_sequence_filtered(session_id, terminal_id)`.
- `tool_sequence_manager.py` now supports session/terminal-filtered reads.

---

## Testing

```bash
# Run ledger tests
python -m pytest P:/.claude/hooks/investigation-ledger/test_investigation_ledger.py -v

# Run integration tests
python P:/.claude/hooks/investigation-ledger/test_integration.py

# Test specific category
python -m pytest P:/.claude/hooks/investigation-ledger/test_investigation_ledger.py -v -k "Claim"
```

---

## Debugging

### Check current ledger state

```python
import sys
sys.path.insert(0, "P:/.claude/hooks/investigation-ledger")
from ledger import get_investigation_stats, calculate_confidence_ceiling
print(get_investigation_stats())
print(calculate_confidence_ceiling())
```

### Reset ledger manually

```python
from ledger import reset_ledger
reset_ledger()
```

### Test claim validation

```python
from validate_claims import validate_claims
result = validate_claims("Your response text here")
print(result)
```

### Check investigation_required behavior

```python
# Test diagnostic question detection
import sys
sys.path.insert(0, "P:/.claude/hooks")
from StopHook_investigation_required import is_diagnostic_question, investigation_occurred

print(is_diagnostic_question("How does the hook system work?"))  # True
print(is_diagnostic_question("Hello"))  # False
```

---

## Design Principles

1. **Structural over pattern-based:** Tool usage is binary (reliable), regex is fragile
2. **LLM self-assessment:** The LLM knows if it investigated - direct questions work
3. **Two-layer defense:** Self-prompt catches early, validator catches claims
4. **Graceful degradation:** Errors in ledger don't block responses
5. **Observation-only for PostToolUse:** Never blocks tool execution, only records

---

## Hardening from Critique

| Concern | Fix Applied |
|---------|-------------|
| JSON corruption | Atomic writes + error recovery |
| Race conditions | File locking with timeout |
| Windows `fcntl` | Platform-specific imports (msvcrt) |
| Pattern bypass | Structural check (tool usage) + LLM self-prompt |
| False evidence | Rejects speculation markers |
| Meta-failure | StopHook_investigation_required catches no-tool responses |

---

## Removal / Disable

```bash
# Disable via environment
export INVESTIGATION_LEDGER_ENABLED=false
export INVESTIGATION_REQUIRED_ENABLED=false
```

Or remove from Stop_router.py HOOK_SEQUENCE.
