# TDD System Documentation

## Overview

The TDD (Test-Driven Development) enforcement system consists of three layers:

1. **Skills** - Documentation and guidance
2. **Hooks** - Actual enforcement (blocking/allowing operations)
3. **Commands** - User-facing control interface

---

## How the Hook Knows What Phase We're In

### State Storage

**Location:** `P:/.claude/hooks/.state/tdd-state/`

**Format:** JSON files named `tdd.{hash}.json` where `{hash}` is the MD5 hash (first 12 chars) of the **test file path**.

**Example state file:**
```json
{
  "phase": "red_confirmed",
  "test_file": "p:/projects/yt-fts/tests/test_download.py",
  "impl_files": ["p:/projects/yt-fts/src/yt_fts/download/handler.py"],
  "last_test_result": "failed",
  "last_test_exit_code": 1,
  "last_test_time": "2025-01-07T14:30:00",
  "approval": null,
  "created_at": "2025-01-07T14:00:00",
  "updated_at": "2025-01-07T14:30:00"
}
```

### State Key Design

- **Keyed by TEST file** (not implementation file)
- This prevents cross-file contamination
- Each test file has its own TDD cycle
- Multiple TDD cycles can exist simultaneously

### How Hooks Read State

```python
# In PreToolUse_tdd_gate.py
tdd = TDDState(test_file)           # Finds state file by hash
state = tdd.load()                  # Reads JSON from disk
phase = TDDPhase.from_string(state.get("phase", ""))  # Parses phase

if phase == TDDPhase.AWAITING_RED:
    # Block implementation writes
```

### Phase Transitions

```
┌──────────┐    Write test    ┌──────────────┐    pytest fails    ┌──────────────┐
│   IDLE   │ ───────────────> │ AWAITING_RED │ ──────────────────> │ RED_CONFIRMED │
└──────────┘                   └──────────────┘                      └──────────────┘
                                                                  │
                                                                  │ pytest passes
                                                                  ▼
                                                            ┌──────────────┐
                                                            │GREEN_CONFIRMED│
                                                            └──────────────┘
                                                                  │
                                                                  │ Edit impl
                                                                  ▼
                                                            ┌──────────────┐
                                                            │  REFACTORING  │
                                                            └──────────────┘
```

---

## Component Interactions

### 1. UserPromptSubmit_tdd_eval.py

**Event:** User submits a prompt

**Triggers:** Creation patterns (commands, not questions)
- `implement`, `build`, `create`, `add`, `develop`, `write`
- `new feature`, `new function`, `new class`
- `write test`, `add test`, `test that`

**Excludes:** Questions about implementation
- "How would you implement X?" → No trigger (question)
- "What's the best way to add Y?" → No trigger (question)
- "Implement X" → Triggers (command)
- "Add feature Y" → Triggers (command)

**Action:** Injects TDD skill instruction into context

**Does NOT block** - only adds guidance

### 2. PreToolUse_tdd_gate.py

**Event:** Before tool executes (Write, Edit, Bash, Task)

**Reads:** State file to get current phase

**Blocks:**
- Implementation writes during `AWAITING_RED`
- Bash file-writes during `AWAITING_RED`
- Task subagent dispatch during `AWAITING_RED`
- Test edits during `RED_CONFIRMED` (no moving goalposts)

**Allows:**
- Test file writes (always)
- Files with `# NOTDD:` comment
- Files in `scripts/`, `prototypes/`, `examples/`
- When `/tdd approve` was used (5-minute window)

### 3. PostToolUse_tdd_state.py

**Event:** After tool executes

**Transitions phases:**
- Test file written → `IDLE` → `AWAITING_RED`
- pytest fails → `AWAITING_RED` → `RED_CONFIRMED`
- pytest passes → `RED_CONFIRMED` → `GREEN_CONFIRMED`
- Regression → `GREEN_CONFIRMED` → `RED_CONFIRMED`
- Impl edit during GREEN → `GREEN_CONFIRMED` → `REFACTORING`

**Detects test results from:**
1. stdout/stderr (pytest patterns: "X failed", "X passed")
2. pytest-json-report (`.report.json`)
3. Exit code (fallback)

---

## TDD Skill vs TDD Hooks

| Aspect | TDD Skill | TDD Hooks |
|--------|-----------|-----------|
| **Location** | `P:/.claude/skills/tdd/SKILL.md` | `P:/.claude/hooks/*.py` |
| **Type** | Documentation | Enforcement |
| **Role** | Explains WHAT to do | Controls what CAN be done |
| **Activation** | Keywords: implement, refactor, CC XX | Every tool execution |
| **Can block?** | No | Yes (PreToolUse_tdd_gate) |
| **State** | None | Reads/writes JSON files |

**Key insight:** The skill is just guidance. The hooks are what actually enforce TDD.

---

## Commands

### /tdd

State management command:

| Subcommand | Action |
|------------|--------|
| `/tdd status` | Show current phase, test file, approval |
| `/tdd approve <file>` | Grant 5-minute bypass window |
| `/tdd reset` | Clear all TDD state |
| `/tdd reset <file>` | Clear state for specific test |
| `/tdd on` | Enable TDD enforcement |
| `/tdd off` | Disable TDD enforcement |

### /refactor

Invokes the `tdd` skill with refactoring context:

```
/refactor function_name
```

- Reads TDD skill documentation
- Hooks still enforce actual cycle
- Characterization tests for refactoring

### /exec

Context-aware execution:

- Analyzes recent conversation, git status, errors
- "Implementation with TDD" is mentioned
- Doesn't directly invoke TDD skill
- Relies on `UserPromptSubmit_tdd_eval.py` for detection

---

## Exemptions

Files are exempt from TDD enforcement if:

1. **Test files** - They ARE the TDD
2. **Directory-based:** `scripts/`, `prototypes/`, `examples/`
3. **Content-based:** File contains `# NOTDD:` comment
4. **Cross-project:** Impl and test are in different project roots
5. **Global disabled:** `/tdd off` was used

---

## State File Lifecycle

```
┌────────────────────────────────────────────────────────────────────┐
│ 1. User writes test file                                           │
│    → PostToolUse creates: tdd.{hash}.json                          │
│    → phase = "awaiting_red"                                        │
├────────────────────────────────────────────────────────────────────┤
│ 2. User tries to write impl (blocked)                              │
│    → PreToolUse reads phase = "awaiting_red"                       │
│    → BLOCKS with guidance message                                  │
├────────────────────────────────────────────────────────────────────┤
│ 3. User runs pytest (fails)                                        │
│    → PostToolUse parses stderr: "1 failed"                         │
│    → Updates: phase = "red_confirmed"                              │
├────────────────────────────────────────────────────────────────────┤
│ 4. User writes impl (allowed)                                      │
│    → PreToolUse reads phase = "red_confirmed"                      │
│    → ALLOWS, tracks impl file                                      │
├────────────────────────────────────────────────────────────────────┤
│ 5. User runs pytest (passes)                                       │
│    → PostToolUse parses: "1 passed"                                │
│    → Updates: phase = "green_confirmed"                            │
├────────────────────────────────────────────────────────────────────┤
│ 6. State expires after 24 hours                                    │
│    → cleanup_expired_states() removes old files                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## Critical Files

| File | Purpose |
|------|---------|
| `P:/.claude/hooks/tdd_core.py` | State management, TDDState class, phase parsing |
| `P:/.claude/hooks/PreToolUse_tdd_gate.py` | Blocks violations before tool execution |
| `P:/.claude/hooks/PostToolUse_tdd_state.py` | Transitions phases after tool execution |
| `P:/.claude/hooks/UserPromptSubmit_tdd_eval.py` | Injects TDD guidance on creation patterns |
| `P:/.claude/skills/tdd/SKILL.md` | TDD workflow documentation |
| `P:/.claude/skills/tdd/SKILL.md` | `/tdd` command interface |
| `P:/.claude/skills/refactor/SKILL.md` | `/refactor` command (invokes tdd skill) |
| `P:/.claude/hooks/.state/tdd-state/` | State JSON files |
| `P:/.claude/hooks/.state/tdd-enabled` | Guard file for on/off |
