# Plan: User Directive Obligation Tracker

**Created**: 2026-03-18
**Objective**: Implement a two-component hook system that detects when the user issues an explicit directive to "search/read/find [resource]" and blocks the Stop hook if no matching tool event occurred in that turn.

---

## Status Summary

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1: UserPromptSubmit Detector | ⏳ PENDING | Detect directives, write state file |
| Phase 2: Stop Hook Verifier | ⏳ PENDING | Check tool events, block on omission |
| Phase 3: Registration & Cleanup | ⏳ PENDING | Wire into router + remove dead env var |
| Phase 4: Tests | ⏳ PENDING | Unit tests for both components |

---

## Problem Statement

The LLM silently ignored an explicit user directive: "search the chat history." No hook blocked the response because the existing system only catches:
- **Fabrication** (`StopHook_cross_validator`): LLM *claims* it did something → no tool evidence
- **LLM-declared omissions** (`declaration_reminder` + `arch_first_enforcer`): LLM *says* "I'll do X" → blocks until done
- **Skill bypass** (`StopHook_skill_execution_gate`): `/command` invoked → LLM responds with prose

The missing case: **User issues directive → LLM completes turn → directive was never executed**. Silent omission with no claim.

---

## Context Analysis

### Existing Patterns (Confirmed by code inspection)

**`declaration_reminder.py`** (UserPromptSubmit module, `core_hook_modules` list):
- Detects "I'll update X" patterns in LLM output (N/A — triggers on user prompt text instead)
- Wait: This actually runs on the *user's* prompt, detecting when the USER declared something in prior turn? No — it detects declaration patterns in the user prompt and writes state for the arch_first_enforcer to read.

Actually re-reading: `declaration_reminder.py` runs at UserPromptSubmit and detects patterns *in the incoming user prompt* like "I'll update the template" — but that doesn't make sense because the user wouldn't say that. Re-reading the docstring: "Prevents 'I'll update the template' declarations without execution" — this tracks when Claude declares intent and the state persists to next turn.

Actually the flow is: UserPromptSubmit fires BEFORE Claude responds. So it reads the user's prompt (not Claude's response). The declaration_reminder detects when the user's prompt contains "I'll update" (i.e., the AI previously said that and user is now replying). This is part of the pushback protocol.

Actually looking at it more carefully — the hook runs on the USER prompt, but it detects if Claude had previously declared intent. The state file is created when a declaration is detected, and the PreToolUse `arch_first_enforcer` reads it. The flow is:
1. Claude says "I'll update the template" (detected via Stop hook or separate mechanism)
2. Next user turn fires UserPromptSubmit
3. `declaration_reminder` checks if the previous turn had a declaration and injects reminder

**Wait** - the `declaration_reminder.py` searches for patterns in the current user prompt, not Claude's output. This is the *user pushing back* ("why didn't you update it?") pattern, or Claude may have included declarative text in its previous response that gets injected into the next prompt somehow.

For our purpose: The closest analog is `declaration_reminder` as a UserPromptSubmit module that writes state + the Stop hook that reads it.

**`Stop_router.py`** HOOK_SEQUENCE (lines 98-127): Stop hooks are registered here and in `ACTIVE_RUNTIME_HOOKS`.

**`stop/Stop_gto_checklist_gate.py`**: Example of a Stop hook in the `stop/` subdirectory.

**Evidence store**: `load_tool_events(session_id, limit)` returns dicts with `name` key = tool name (Read, Grep, Glob, Bash, etc.).

### Turn Tracking

The `turn_marker.py` module increments a turn counter. The state file can record the turn number at obligation creation; the Stop hook checks if current_turn - creation_turn >= TIMEOUT_TURNS.

The evidence store tracks tool events per session. Tool names that satisfy a "search/read" obligation: `Read`, `Grep`, `Glob`, `Bash` (when containing grep/search/cat/type commands), `WebFetch`, `WebSearch`.

---

## Existing Implementation Discovery

Files confirmed to exist:
- `P:/.claude/hooks/UserPromptSubmit_modules/declaration_reminder.py` — analog for Component 1
- `P:/.claude/hooks/UserPromptSubmit_modules/registry.py` — `core_hook_modules` list at line 601
- `P:/.claude/hooks/Stop_router.py` — HOOK_SEQUENCE + ACTIVE_RUNTIME_HOOKS
- `P:/.claude/hooks/stop/Stop_gto_checklist_gate.py` — Stop hook in stop/ subdirectory
- `P:/.claude/hooks/UserPromptSubmit_modules/base.py` — HookResult, HookContext

State file convention: `P:/.claude/hooks/state/arch_declaration_{terminal_id}.json`
Our convention: `P:/.claude/hooks/state/pending_obligation_{terminal_id}.json`

Dead env var: `INVESTIGATE_BEFORE_EXPLAIN_ENABLED=true` in settings.json — hook is archived, env var should be removed.

---

## Test Discovery

Test files location: `P:/.claude/hooks/UserPromptSubmit_modules/tests/`

Existing test patterns:
- `test_declaration_pattern_detection` — positive/negative matching
- `test_state_file_creation` — state file written correctly
- `test_terminal_id_extraction` — terminal scoping

We need parallel tests for our two components.

---

## Proposed Solution

### Component 1: `user_directive_obligation.py` (UserPromptSubmit module)

Detects explicit resource-fetch directives in user prompts. A directive must have:
1. A **fetch verb**: search, find, read, look, check, look up, locate
2. A **concrete resource**: file path, "the transcript", "chat history", "the logs", specific filenames

Writes `pending_obligation_{terminal_id}.json`:
```json
{
  "directive": "search the chat history",
  "resource_type": "transcript",
  "resource_hint": "chat history",
  "turn_number": 42,
  "timestamp": 1742300000.0,
  "session_id": "abc123",
  "terminal_id": "console_xyz"
}
```

**Directive detection patterns** (require both verb AND concrete noun):
```python
FETCH_VERBS = r"(?:search|find|look\s+(?:in|through|at|for|up)|read|check|scan|grep|locate)"
CONCRETE_NOUNS = [
    r"(?:the\s+)?(?:chat\s+)?(?:history|transcript|log(?:s|file)?)",  # chat history, transcript
    r"(?:the\s+)?(?:previous|prior|earlier|last)\s+(?:conversation|session|message|turn)",
    r"(?:the\s+)?(?:jsonl?|\.jsonl?)\s+file",  # transcript file
    r"(?:the\s+)?(?:file|files?)\s+(?:at|in|under)\s+[^\s]+",  # "file at path"
    r"[A-Za-z0-9_/\\.-]+\.(jsonl?|log|txt|md|py|json)",  # explicit file paths
    r"(?:the\s+)?(?:hook|skill|memory)\s+(?:log|file|state)",  # hook logs
]
```

Injects context reminder when obligation is stored:
```
⚠️ USER DIRECTIVE DETECTED: You were asked to [search/read] [resource].

This obligation is tracked. You MUST execute a Read/Grep/Glob/Bash tool call
targeting [resource] before completing your response.

Failure to execute the directive will block turn completion.
```

**Non-detection cases** (to avoid false positives):
- Vague: "search for a solution", "find a way to" — no concrete resource
- Past tense declarative: "I searched the history" — already claimed done (handled by cross-validator)
- Questions: "Can you find...?" — not an imperative directive (use imperative mood detection)

### Component 2: `stop/StopHook_directive_obligation.py` (Stop hook)

At Stop time:
1. Load `pending_obligation_{terminal_id}.json` — if none, allow.
2. Check turn expiry: if `current_turn - creation_turn >= OBLIGATION_TIMEOUT_TURNS` (default 3), log and clear, allow.
3. Load tool events from evidence store for this turn.
4. Check if any tool event matches the obligation's resource type:
   - `Read` tool called → satisfied
   - `Grep` tool called → satisfied
   - `Glob` tool called → satisfied
   - `Bash` with relevant command (grep, cat, type, findstr, etc.) → satisfied
   - `WebFetch`/`WebSearch` for transcript-type obligations → satisfied
5. If no matching tool event → **block** with message showing what was required.
6. Write to obligation audit log: `.claude/hooks/logs/obligation_audit.jsonl`.

**Block message**:
```
⛔ USER DIRECTIVE NOT EXECUTED

The user asked you to: [directive]

You were required to read/search [resource_hint] but no Read/Grep/Glob/Bash
tool event was found in this turn.

Required action:
  Read the resource: [resource_hint]
  OR use Grep/Bash to search it

Do NOT summarize from memory. Execute the actual tool call.

To bypass: Add --skip-obligation to your message.
```

**Turn-based expiry** (from Perplexity analysis):
- `OBLIGATION_TIMEOUT_TURNS=3` (env var)
- More semantically correct than time TTL: a directive about "chat history" is stale after 3 turns of topic change, regardless of elapsed time.

**Bypass**: `--skip-obligation` flag in user message clears obligation state.

---

## Implementation Plan

### Phase 1: UserPromptSubmit Detector

**TASK-001**: Create `user_directive_obligation.py`
- File: `P:/.claude/hooks/UserPromptSubmit_modules/user_directive_obligation.py`
- Action: Implement directive detection + state write + context injection
- Points: 5
- Acceptance:
  - Detects "search the chat history" → writes obligation state file
  - Does NOT detect "find a solution" (no concrete resource)
  - Does NOT detect "can you search the transcript?" (question form — too ambiguous, defer)
  - Injects reminder context when obligation stored
  - State file is terminal-scoped
- Prerequisites: None

**TASK-002**: Register in `registry.py`
- File: `P:/.claude/hooks/UserPromptSubmit_modules/registry.py`
- Action: Add `"user_directive_obligation"` to `core_hook_modules` list after `declaration_reminder`
- Points: 1
- Acceptance: Module imports without error when registry loads
- Prerequisites: TASK-001

### Phase 2: Stop Hook Verifier

**TASK-003**: Create `stop/StopHook_directive_obligation.py`
- File: `P:/.claude/hooks/stop/StopHook_directive_obligation.py`
- Action: Implement obligation check + tool event matching + block logic
- Points: 5
- Acceptance:
  - Loads pending obligation, checks turn expiry
  - Finds matching tool events → allows
  - No matching tool events → blocks with clear message
  - Clears obligation after block or satisfaction
  - Writes to obligation audit log
- Prerequisites: TASK-001

**TASK-004**: Register in `Stop_router.py`
- File: `P:/.claude/hooks/Stop_router.py`
- Action: Add to HOOK_SEQUENCE + ACTIVE_RUNTIME_HOOKS
  ```python
  # In HOOK_SEQUENCE, after StopHook_cross_validator:
  ("stop/StopHook_directive_obligation.py", "DIRECTIVE_OBLIGATION_ENABLED", True, "inprocess"),
  ```
- Points: 2
- Acceptance: Hook appears in router dispatch table; env var can disable it
- Prerequisites: TASK-003

### Phase 3: Registration & Cleanup

**TASK-005**: Add env var to settings.json
- File: `P:/.claude/settings.json`
- Action: Add `"DIRECTIVE_OBLIGATION_ENABLED": "true"` and `"OBLIGATION_TIMEOUT_TURNS": "3"` to env section; also REMOVE the dead `"INVESTIGATE_BEFORE_EXPLAIN_ENABLED": "true"` entry
- Points: 1
- Acceptance: Settings file has new env vars; dead env var is gone
- Prerequisites: TASK-004

### Phase 4: Tests

**TASK-006**: Unit tests for `user_directive_obligation.py`
- File: `P:/.claude/hooks/UserPromptSubmit_modules/tests/test_user_directive_obligation.py`
- Action: Write tests covering detection patterns + false positives + state file creation
- Points: 3
- Test scenarios:
  1. `"search the chat history"` → obligation detected, state written
  2. `"find the transcript at C:\\Users\\..."` → obligation detected
  3. `"find a solution to this problem"` → NOT detected (no concrete resource)
  4. `"search for patterns"` → NOT detected (no concrete resource)
  5. State file is terminal-scoped (different terminals get different files)
  6. Context injection contains required phrases
  7. Disabled by `DIRECTIVE_OBLIGATION_ENABLED=false`
- Prerequisites: TASK-001

**TASK-007**: Unit tests for `StopHook_directive_obligation.py`
- File: `P:/.claude/hooks/stop/tests/test_stopHook_directive_obligation.py`
- Action: Write tests covering obligation loading + tool matching + blocking + expiry
- Points: 3
- Test scenarios:
  1. No pending obligation → allow
  2. Obligation present + Read tool event → allow + clear state
  3. Obligation present + Grep tool event → allow + clear state
  4. Obligation present + no tool events → block with message
  5. Obligation present + turn expired (> TIMEOUT_TURNS) → allow + clear state
  6. Bypass flag `--skip-obligation` in stop data → allow + clear state
  7. Multi-terminal isolation (terminal A obligation not visible to terminal B)
- Prerequisites: TASK-003

---

## Risks

- **False positive rate on detection patterns**: Narrow verb+noun requirement reduces this, but "find the issue" could still match "issue" as a resource. Mitigate: require the noun to be a file/path/transcript/log type (not generic nouns).
- **Turn counter availability**: The Stop hook needs current turn number. Evidence store may not expose this directly. Fallback: use timestamp TTL (5 minutes) if turn count unavailable.
- **Tool event scope**: `load_tool_events()` returns session-scoped events, not turn-scoped. The Stop hook must filter to only events *after* the obligation was created (use `timestamp` field comparison).

---

## Success Criteria

1. `search the chat history` directive creates obligation state → Stop hook blocks if no Read/Grep occurs
2. `read the file at C:\path\file.jsonl` directive → Read of that file satisfies it
3. `find a solution` → NO obligation created (false positive prevented)
4. After 3 turns without satisfaction → obligation automatically expires (no block)
5. `--skip-obligation` bypass works
6. Dead `INVESTIGATE_BEFORE_EXPLAIN_ENABLED` env var removed from settings.json
7. All 14+ tests pass

---

## Dependencies

- Phase 1 complete before Phase 2 (Stop hook needs state file format)
- Phase 2 complete before Phase 3 (registration needs the file to exist)
- All phases complete before Phase 4 (tests validate final wired behavior)

---

## Rollback Strategy

File-based: deleting/reverting the three new files and removing the registry entries + Stop_router entries reverts to prior state. No database migrations. Settings.json changes are trivially reversible via git.

```bash
# Rollback commands:
git checkout P:/.claude/hooks/UserPromptSubmit_modules/registry.py
git checkout P:/.claude/hooks/Stop_router.py
git checkout P:/.claude/settings.json
rm P:/.claude/hooks/UserPromptSubmit_modules/user_directive_obligation.py
rm P:/.claude/hooks/stop/StopHook_directive_obligation.py
```
