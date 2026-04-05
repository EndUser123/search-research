# Grounded Artifact Validation (GAV) - Implementation Plan

## Overview

Building a mechanical grounding system that prevents LLM from writing explanations about the **wrong artifact**. Pattern: Ground (deterministic) → Echo (LLM, constrained) → Validate (deterministic) → Narrate (LLM, free).

**Problem being solved**: When hooks block tool calls, the LLM sometimes pattern-matches on prior context and writes RCAs about completely different commands/hooks than what actually blocked.

**Solution**: Extract exact artifact data deterministically, force LLM to echo it, validate the echo matches, then allow free narration.

## Scope

**Phase 1** (this implementation):
- Artifact Grounder module (`__lib/artifact_grounder.py`)
- PreToolUse integration (write artifact on block)
- PostToolUse Artifact Validator (inject + cleanup only)
- Settings.json wiring
- SessionEnd cleanup
- Unit tests

**Phase 2** (future work, not in this plan):
- Drift detection in PostToolUse validator
- Test failure grounding schema

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      PreToolUse.py Router                       │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Hook returns block decision                               │ │
│  └────────────────────┬───────────────────────────────────────┘ │
│                       │                                          │
│                       ▼                                          │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Artifact Grounder: Extract structured data                 │ │
│  │ - tool_name, tool_input, blocking_hook, raw_reason        │ │
│  │ - Extract command tokens for drift detection              │ │
│  └────────────────────┬───────────────────────────────────────┘ │
│                       │                                          │
│                       ▼                                          │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Write: hooks/state/grounded_artifact_{session}.json      │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│              PostToolUse_artifact_validator.py                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 3A: Inject artifact context when exists                    │ │
│  │ - Read grounded_artifact_{session}.json                    │ │
│  │ - Format as: "GROUNDED ARTIFACT (mechanical): ..."        │ │
│  │ - Inject via additionalContext                             │ │
│  └────────────────────┬───────────────────────────────────────┘ │
│                       │                                          │
│                       ▼                                          │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 3B: Cleanup on successful tool call                       │ │
│  │ - Delete artifact file when tool succeeds                 │ │
│  └────────────────────┬───────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   SessionEnd_cleanup.py                         │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Cleanup: Delete all grounded_artifact_*.json files        │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

1. **Block occurs**: PreToolUse hook returns `{"decision": "block", "reason": "..."}`
2. **Ground artifact**: Extract `tool_input["command"]`, `blocking_hook`, `reason` into structured JSON
3. **Write artifact**: Save to `hooks/state/grounded_artifact_{safe_session}.json`
4. **Next PostToolUse**: Read artifact, inject context to LLM
5. **Success cleanup**: Delete artifact file when next tool call succeeds
6. **Session cleanup**: Delete all artifacts on session end

## Error Handling

**Best-effort philosophy** — GAV failures never block the block:
- If artifact grounder fails → block still happens, just without artifact
- If context injection fails → LLM continues without grounded context
- If cleanup fails → worst case is orphaned file (cleaned on session end)
- All GAV code wrapped in try/except with `pass`

**Never write to stderr** — Claude Code treats stderr as hook errors

## Test Strategy

### Unit Tests (`test_artifact_validation_hooks.py`)

**Test artifact_grounder.py:**
- `test_ground_blocked_command_basic` — Verify schema structure
- `test_ground_blocked_command_preserves_exact_command` — EXACT match required
- `test_extract_command_tokens` — Token extraction gets meaningful words
- `test_ground_git_safety_block` — Git blocks include subcommand

**Test lifecycle:**
- `test_write_and_read_artifact` — Can write and read back
- `test_cleanup_removes_artifact` — Success deletes artifact

**Test drift detection** (Phase 2, not implementing now):
- `test_no_drift_when_command_mentioned` — No warning when RCA quotes actual command
- `test_drift_when_wrong_command` — Warning when RCA talks about different command

### Integration Test (Manual)

1. Trigger a PreToolUse block (e.g., run command blocked by authorization)
2. Verify `grounded_artifact_*.json` created in `hooks/state/`
3. Verify next LLM response includes injected artifact context
4. Run successful tool call, verify artifact file deleted

## Standards Compliance

**Python standards** (`/code-python`):
- Type hints on all functions
- Docstrings on all public functions
- `pathlib.Path` for all file operations
- `re` for regex, `shlex` for shell parsing
- Error handling: `try/except` with specific exceptions

**Universal standards** (`/code-standards`):
- DRY: Session ID resolution pattern reused from PreToolUse.py
- Single responsibility: Separate modules for grounding, validation, cleanup
- Clear naming: `ground_blocked_command()`, `inject_artifact_context()`

## Ramifications

**Impact on existing code:**
- **PreToolUse.py**: Add ~15 lines (artifact grounding on block)
- **PostToolUse_router.py**: Add one new hook registration
- **SessionEnd_cleanup.py**: Add ~5 lines (cleanup artifact files)
- **settings.json**: Add one new PostToolUse hook entry

**No breaking changes:**
- Existing hooks continue working unchanged
- GAV is pure add-on (best-effort, never blocks)
- Backwards compatible: if GAV fails, hooks still work

**Multi-terminal safety:**
- All artifact files keyed by session ID
- No cross-terminal bleed
- Each terminal has its own artifact

## Pre-Mortem (6 Months Later: Why Did This Fail?)

### Failure Mode 1: Artifact file orphan accumulation
**Root cause**: Cleanup on success doesn't run, SessionEnd cleanup incomplete
**Preventive action**:
- Test: Verify artifact deleted after successful tool call
- Test: Verify SessionEnd deletes all artifacts
- Monitoring: Check `hooks/state/` for old `grounded_artifact_*.json` files

### Failure Mode 2: Wrong session ID causes cross-terminal artifact pollution
**Root cause**: Session ID resolution doesn't match PreToolUse.py pattern
**Preventive action**:
- Test: Create artifact from terminal A, verify terminal B doesn't see it
- Code: Copy `_resolve_session_id()` and `_safe_id()` from PreToolUse.py exactly

### Failure Mode 3: Context injection interferes with other PostToolUse hooks
**Root cause**: Multiple hooks trying to inject context, only one wins
**Preventive action**:
- Test: Run with FixValidator + Artifact Validator together
- Code: Ensure our injection appends to existing injections

### Failure Mode 4: Performance degradation on every tool call
**Root cause**: Reading artifact file on every PostToolUse is slow
**Preventive action**:
- Test: Measure artifact validator runtime (target < 10ms)
- Code: Only read artifact if file exists (fast path check)

### Failure Mode 5: Special characters in command cause JSON serialization errors
**Root cause**: Command with quotes, backslashes, Unicode breaks JSON
**Preventive action**:
- Test: Create artifact with command containing `\"P:\path\", 'quotes', Unicode`
- Code: Use `json.dumps(ensure_ascii=False)` for proper encoding

## Observability Plan

**What shows if GAV is working:**
- Artifact files created in `hooks/state/` when blocks occur
- LLM responses quote exact blocked commands after blocks
- No orphaned artifact files accumulate

**What would detect failure:**
- Alert: "Orphaned artifact files older than 1 hour" → cleanup broken
- Alert: "Cross-terminal artifact bleed" → session ID bug
- Metric: "Blocks without artifacts" → grounder failing silently

**Where to look during diagnosis:**
- `hooks/state/grounded_artifact_*.json` — current artifact state
- Hook logs (if enabled) — grounder/validator lifecycle events
- LLM responses after blocks — check for exact command quoting

## Tasks

### Task 1: Create artifact_grounder.py module
**File**: `P:/.claude/hooks/__lib/artifact_grounder.py`

**Functions to implement:**
- `ground_blocked_command(data, blocking_hook, reason) -> dict`
- `ground_git_safety_block(data, blocking_hook, reason) -> dict`
- `extract_command_tokens(command, max_tokens=10) -> list[str]`
- `_resolve_session_id(data) -> str` (copy from PreToolUse.py)
- `_safe_id(value) -> str` (copy from PreToolUse.py)

**Schema output:**
```python
{
    "schema": "blocked_command",
    "version": 1,
    "timestamp": 1709000000.0,
    "session_id": "abc-123",
    "tool_name": "Bash",
    "tool_input": {"command": "exact command here"},
    "blocking_hook": "PreToolUse_authorization_gate.py",
    "raw_reason": "Blocked: requires authorization",
    "command_tokens": ["python", "import", "sys"]  # top 5-10 tokens
}
```

**Acceptance criteria:**
- Schema includes all required fields
- `tool_input["command"]` is EXACT (no truncation, no sanitization)
- Command tokens extracted meaningfully (stopwords removed)
- Session ID resolution matches PreToolUse.py pattern

### Task 2: Integrate artifact grounding into PreToolUse.py
**File**: `P:/.claude/hooks/PreToolUse.py` (modify)

**Changes:**
1. Import artifact grounder (lines ~350)
2. Add `_write_grounded_artifact(data, artifact)` function
3. Call grounding at line 492 (after block decision)

**Code to add at line 492:**
```python
# After: if res.get("decision") == "block":
# Ground the artifact (best-effort, never block the block)
try:
    from __lib.artifact_grounder import ground_blocked_command, ground_git_safety_block

    _msg = res.get("message") or res.get("reason")
    _blocking_hook = res.get("blocking_hook", hook)

    # Choose schema based on blocking hook
    if "git_safety" in _blocking_hook.lower():
        artifact = ground_git_safety_block(data, _blocking_hook, _msg)
    else:
        artifact = ground_blocked_command(data, _blocking_hook, _msg)

    # Write to state (session-scoped)
    _write_grounded_artifact(data, artifact)
except Exception:
    pass  # Grounding is best-effort, never block the block
```

**Add helper function:**
```python
def _write_grounded_artifact(data: dict, artifact: dict) -> None:
    """Write grounded artifact to session-scoped state file."""
    session_id = _resolve_session_id(data)
    safe_session = _safe_id(session_id or "unknown")

    state_dir = HOOKS_DIR / "state"
    state_dir.mkdir(parents=True, exist_ok=True)

    artifact_path = state_dir / f"grounded_artifact_{safe_session}.json"
    artifact_path.write_text(json.dumps(artifact, ensure_ascii=False), encoding="utf-8")
```

**Acceptance criteria:**
- Artifact file created when hook blocks
- File path includes session ID (multi-terminal safe)
- Exception in grounder doesn't prevent block

### Task 3: Create PostToolUse_artifact_validator.py
**File**: `P:/.claude/hooks/PostToolUse_artifact_validator.py` (create)

**Functions to implement:**
- `check_and_inject_artifact(data) -> dict | None` — Inject context when artifact exists
- `cleanup_stale_artifact(data) -> None` — Delete on successful tool call
- `_read_grounded_artifact(data) -> dict | None` — Read artifact file
- `_artifact_path(data) -> Path | None` — Get artifact file path
- `_resolve_session_id(data) -> str` — Copy from PreToolUse.py
- `_safe_id(value) -> str` — Copy from PreToolUse.py

**Main function:**
```python
def main():
    # Read hook data from stdin
    try:
        raw_data = sys.stdin.read()
        if not raw_data:
            sys.exit(0)
        data = json.loads(raw_data)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    # Try to inject artifact context
    injection_result = check_and_inject_artifact(data)
    if injection_result:
        print(json.dumps(injection_result))
        sys.exit(0)

    # Cleanup on successful tool call
    cleanup_stale_artifact(data)

    sys.exit(0)
```

**Acceptance criteria:**
- Injects context when artifact file exists
- Context includes exact command, blocking hook, reason
- Deletes artifact when tool call succeeds
- Exception in validator doesn't break PostToolUse

### Task 4: Wire PostToolUse_artifact_validator in settings.json
**File**: `P:/.claude/settings.json` (modify)

**Add to PostToolUse hooks:**
```json
{
  "PostToolUse": [
    {
      "matcher": ".*",
      "hooks": [
        {
          "type": "command",
          "command": "python P:/.claude/hooks/__lib/hook_runner.py P:/.claude/hooks/PostToolUse_artifact_validator.py",
          "timeout": 5
        }
      ]
    }
  ]
}
```

**IMPORTANT**: This ADDS to existing PostToolUse hooks, doesn't replace them.

**Acceptance criteria:**
- New matcher added for all tool types (`.*`)
- Runs in addition to existing Edit|Write and Bash hooks
- Timeout set to 5 seconds

### Task 5: Add SessionEnd cleanup
**File**: `P:/.claude/hooks/SessionEnd_cleanup.py` (modify)

**Add to cleanup logic:**
```python
# In existing cleanup function
import glob

state_dir = HOOKS_DIR / "state"
for artifact_file in state_dir.glob("grounded_artifact_*.json"):
    try:
        artifact_file.unlink(missing_ok=True)
    except Exception:
        pass
```

**Acceptance criteria:**
- All `grounded_artifact_*.json` files deleted on session end
- Exception doesn't break SessionEnd cleanup

### Task 6: Create unit tests
**File**: `P:/.claude/hooks/tests/test_artifact_validation_hooks.py` (extend or create)

**Test classes:**
- `TestArtifactGrounder` — Test grounding functions
- `TestArtifactLifecycle` — Test write/read/cleanup
- `TestDriftDetection` — Drift detection (Phase 2, create empty test class)

**Acceptance criteria:**
- All tests pass
- Tests cover all grounding functions
- Tests verify exact command preservation

## Implementation Order

1. **Task 1** (artifact_grounder.py) — Foundation, no dependencies
2. **Task 6** (unit tests for grounder) — Test foundation
3. **Task 2** (PreToolUse integration) — Write artifacts
4. **Task 3** (PostToolUse validator) — Inject/cleanup
5. **Task 5** (SessionEnd cleanup) — Cleanup orphans
6. **Task 4** (settings.json) — Wire it all together
7. **Manual integration test** — Verify end-to-end flow

## Rollout Plan

**Phase 1** (this implementation):
- Artifact grounding + injection only
- No drift detection yet (that's Phase 2)
- Best-effort philosophy (failures don't break hooks)

**Phase 2** (future work):
- Add drift detection to PostToolUse validator
- Start in warning mode (inject advisory, don't block)
- Tune token extraction and drift thresholds

## Success Criteria

- ✅ Artifact file created when PreToolUse blocks
- ✅ LLM receives grounded artifact context after block
- ✅ Artifact deleted on successful tool call
- ✅ No orphaned artifacts accumulate
- ✅ Multi-terminal safe (session-keyed files)
- ✅ All unit tests pass
- ✅ Integration test passes manually
