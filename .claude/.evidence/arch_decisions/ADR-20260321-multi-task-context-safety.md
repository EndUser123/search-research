# ADR-20260321: Multi-Task Skill Execution + Context Safety

**Status:** Proposed
**Date:** 2026-03-21
**Context:** `/code` skill stopped prematurely during a 20+ task execution; context compaction interrupted mid-workflow; session resumed at "0% until auto-c…" causing user to ask "Why did you stop?" twice.

---

## Decision

Implement four coordinated changes to prevent premature skill termination and ensure graceful context compaction:

1. **PreToolUse Context Budget Warning** — warn at ~80% context usage before compaction fires
2. **Stop Hook Skill Contract Enforcement** — block stops when skill declares continuous execution
3. **Pre-Compaction Task State Checkpoint** — verify pending operations are persisted before compaction
4. **Graceful Post-Compaction Resume** — inject explicit resume context instead of silent "0% until auto-c…"

---

## Rationale

The chat history shows a 4-failure cascade:
1. LLM stopped after TASK-002 despite 20+ tasks remaining
2. Compaction fired mid-workflow with no warning
3. Session resumed without task context (user saw blank state)
4. User had to ask "Why did you stop?" twice to recover

Each failure compounds the next. Fixing only one part leaves the cascade intact.

---

## Changes

### Change A: PreToolUse Context Budget Warning

**File:** `P:\.claude\hooks\PreToolUse_observe_before_act_gate.py` (or new hook)

**Logic:**
- Estimate context percent from hook input (`data.get("context_percent", 0)`)
- At ≥80%, inject checkpoint reminder before each tool
- Message: "⚠️ CONTEXT AT ~{percent}% — Save task state to hooks/state/. Next: complete current task or request graceful compaction."

**Why PreToolUse:** Natural checkpoint moment before each tool execution.

---

### Change B: Stop Hook Skill Contract Enforcement

**File:** `P:\.claude\hooks\Stop_tilldone_gate.py`

**Add Layer 3** to existing tilldone gate:
- Read skill state marker (`continuous: true` field)
- If skill declares continuous execution but LLM used no implementation tools → block with "SKILL CONTRACT: {skill} is designed for continuous execution."

**Marker format:**
```json
{
  "skill": "code",
  "continuous": true,
  "tasks_remaining": 15
}
```

---

### Change C: Pre-Compaction Task State Checkpoint

**File:** `P:\.claude\hooks\PreCompact_handoff_capture.py`

**Add to `main()`:**
- Check for `hooks/state/task_checkpoint_{terminal_id}.json`
- If missing or stale (TTL > 2 hours) → warn "NO TASK CHECKPOINT FOUND — Active tasks may be lost"

**PostToolUse task tracker must write checkpoint** before each tool:
```python
# In posttooluse/task_tracker_hook.py
path.write_text(json.dumps({
    "pending_operations": operations,
    "timestamp": time.time()
}))
```

---

### Change D: Graceful Post-Compaction Resume

**File:** `P:\.claude\hooks\SessionStart_handoff_restore.py`

**Replace silent "0% until auto-c…" with explicit resume:**
```
📍 SESSION RESTORED FROM CHECKPOINT
Goal: {goal}
Pending: {n} operations
Next: {next_step}
Type 'continue' or 'resume' to proceed.
```

---

## Tradeoffs

| Quality | Improved | Degraded |
|---------|----------|----------|
| Reliability | Skill completes to end without premature stop | Slightly more blocking hooks |
| Maintainability | More hooks to maintain | Catch contract violations early |
| Performance Efficiency | Context warnings prevent wasted compaction | Adds ~10ms to PreToolUse |

---

## Multi-Terminal Safety

- Checkpoint files: `{terminal_id}`-scoped (terminal_id persists across compaction; session_id does not)
- Context warnings: Read-only, no state modification
- Skill markers: Written at task start, cleared at task end, terminal-scoped
- Resume messages: Generated fresh from handoff envelope, no cross-terminal state

---

## Implementation Order

| Priority | Change | Why |
|----------|--------|-----|
| 1 | D: Graceful Resume | Fixes user-visible "Why did you stop?" loop immediately |
| 2 | A: Context Budget Warning | Prevents compaction surprise — highest leverage |
| 3 | C: Task Checkpoint Verification | Ensures pending operations survive compaction |
| 4 | B: Skill Contract Enforcement | Deepest fix — prevents LLM from choosing to stop |

---

## Consequences

**Positive:**
- User never sees "Why did you stop?" after compaction
- Skills execute to completion without premature LLM self-termination
- Pending operations survive compaction with zero loss

**Negative:**
- 4 new hook behaviors to maintain
- Context warnings may feel唠叨 if threshold is too aggressive
- Checkpoint TTL adds complexity to state management
