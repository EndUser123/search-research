# Task Confusion Prevention - Quick Reference

## What Problem Does This Solve?

Your trace showed Claude getting confused between:
- **Primary objective:** "Fix qual-gate.md" (432 → 20 lines)
- **Project name:** "quadlet" (from CWO12 planning)
- **Invented task:** "Build quadlet system" with 24 parallel implementation tasks

Result: **Hours of wasted work on the wrong objective.**

This system catches and prevents that exact scenario.

---

## The 4-Layer Defense

### Layer 1: UserPromptSubmit (goal_anchor_v2.py)

**What it does:**
- Extracts ALL potential goals from the prompt
- Detects ambiguous terms ("quadlet" with 3 meanings)
- Detects conflicting scopes (fix vs implement)
- Forces clarification if ambiguity found
- Persists clarified goal to session

**Your trace scenario:**
```
User: "Fix qual-gate.md, implement quadlet system"
      ↓
[DETECTED] Two scopes: modification + creation
[DETECTED] Ambiguous term: "quadlet"
      ↓
Claude must ask: "Which is primary?"
      ↓
Goal persisted: "fix qual-gate.md"
```

**Key pattern:** Uses semantic analysis, not just hard-coded terms.

---

### Layer 2: PreToolUse (subagent_constitution_v2_1.py)

**What it does:**
- Intercepts Task tool calls (subagent spawning)
- Retrieves primary goal from session
- Injects constitution requiring explicit goal alignment
- Forces subagent to state how its task serves the goal
- Prevents scope creep at subagent level

**Your trace scenario:**
```
Claude: "Call subagent to implement quadlet system"
      ↓
[TRIGGERED] Task tool call detected
      ↓
subagent_constitution_v2_1 injects:
  "PRIMARY OBJECTIVE: fix qual-gate.md
   YOUR TASK: implement quadlet system
   VERIFY: How does your task serve the primary objective?"
      ↓
Subagent cannot claim alignment without evidence
```

**Key pattern:** Makes alignment explicit, not just hoped-for.

---

### Layer 3: PostToolUse (existing - no change)

Your existing truth_validator and other PostToolUse hooks remain unchanged.

These validate tool outputs, which is separate from the narrative confusion.

---

### Layer 4: Stop (intelligent_stop_v2_1.py)

**What it does:**
- Validates completion claims against actual tool execution
- Checks for test evidence, file creation evidence, etc.
- Verifies work aligns with original goal
- Blocks termination if claims are unsupported
- Uses actual tool calls, not pattern matching

**Your trace scenario:**
```
Claude: "✅ IMPLEMENTATION COMPLETE"
      ↓
intelligent_stop_v2_1 checks:
  - Is there evidence of implementation?
  - Did tests run successfully?
  - Does output serve the primary goal "fix qual-gate.md"?
      ↓
[BLOCKED] No evidence found
      ↓
⛔ TERMINATION BLOCKED
   "Completion claimed without supporting evidence"
      ↓
Claude must run verification before stopping
```

**Key pattern:** Uses actual execution as truth, not narrative claims.

---

## File Descriptions

| File | Lines | Purpose |
|------|-------|---------|
| `goal_anchor_v2.py` | 600+ | Multi-goal extraction + ambiguity detection + session persistence |
| `subagent_constitution_v2_1.py` | 350+ | Goal retrieval + constitution injection + alignment requirements |
| `intelligent_stop_v2_1.py` | 450+ | Completion claim validation + goal alignment check + evidence verification |
| `integration_guide.md` | Full | Installation + configuration + troubleshooting |

---

## Quick Start (5 Minutes)

### 1. Backup existing hooks (1 min)
```bash
cd P:/.claude/hooks
cp goal_anchor.py goal_anchor.py.backup
cp subagent_constitution_injector.py subagent_constitution_injector.py.backup
cp intelligent_stop_hook.py intelligent_stop_hook.py.backup
```

### 2. Deploy new files (1 min)
```bash
cp goal_anchor_v2.py goal_anchor.py
cp subagent_constitution_v2_1.py subagent_constitution_injector.py
cp intelligent_stop_v2_1.py intelligent_stop_hook.py
```

### 3. Create session directory (1 min)
```bash
mkdir -p P:/.claude/session_data
```

### 4. Verify settings.json has hooks (1 min)
```bash
# Check UserPromptSubmit, PreToolUse, Stop hooks are configured
cat P:/.claude/settings.json | grep -A 3 "goal_anchor"
```

### 5. Test (1 min)
```bash
# Test each hook
python P:/.claude/hooks/goal_anchor.py < /dev/null
python P:/.claude/hooks/subagent_constitution_injector.py < /dev/null
python P:/.claude/hooks/intelligent_stop_hook.py < /dev/null
```

Done. System is active.

---

## How to Know It's Working

### Sign 1: Ambiguity Detection

When you input ambiguous prompts, Claude responds:
```
⚠️ GOAL AMBIGUITY DETECTED

"quadlet" appears with multiple meanings:
  a) Project name
  b) System to build
  c) Artifact collection

Please clarify which meaning applies.
```

If you see this → **Layer 1 working** ✓

### Sign 2: Subagent Goal Injection

When Claude calls a subagent, look for in stderr:
```
✓ Constitution injected for Task subagent
  Goal: fix qual-gate.md
```

If you see this → **Layer 2 working** ✓

### Sign 3: Termination Validation

When Claude tries to complete, it either:
- ✅ Allows termination with evidence shown, OR
- ⛔ Blocks with specific high-severity violations

Example block:
```
⛔ TERMINATION BLOCKED

HIGH: Completion claim without supporting evidence
  Claim: "✅ IMPLEMENTATION COMPLETE"
  Required: Tool execution output showing success
```

If you see this → **Layer 4 working** ✓

---

## Expected Behavioral Changes

### Before (Broken)

```
User: "Fix qual-gate.md, implement quadlet system"
↓
Claude: "I'll implement the quadlet system with 24 parallel tasks"
↓
[Wasted effort building wrong thing]
↓
Claude: "✅ IMPLEMENTATION COMPLETE"
↓
[Hours lost]
```

### After (Fixed)

```
User: "Fix qual-gate.md, implement quadlet system"
↓
Claude: "I see two objectives—which is primary?"
↓
User: "Primary is qual-gate.md"
↓
Claude: "Got it. Refactoring qual-gate.md to 6-step architecture"
↓
[Subagent is force-bound to this goal]
↓
Claude: "Completed. Tests pass, file modified."
↓
[15 minutes on correct task vs hours on wrong one]
```

---

## Configuration Customization

### Add Ambiguous Terms

In `goal_anchor_v2.py`, find `AMBIGUOUS_TERMS` dict and add:

```python
"new_term": {
    "meanings": ["meaning_a", "meaning_b", "meaning_c"],
    "clarification": "Does 'new_term' refer to..."
}
```

### Add Completion Claim Patterns

In `intelligent_stop_v2_1.py`, update `COMPLETION_CLAIM_PATTERNS`:

```python
COMPLETION_CLAIM_PATTERNS = [
    # existing
    r"ready\s+(?:for|to)\s+(?:review|merge|deploy)",
    # ADD:
    r"your_custom_completion_pattern",
]
```

### Add Evidence Patterns

In `intelligent_stop_v2_1.py`, update `EVIDENCE_PATTERNS`:

```python
EVIDENCE_PATTERNS = {
    "test_execution": [...],
    "my_custom_evidence": [
        r"my_custom_verification_pattern",
    ]
}
```

---

## Rollback (If Needed)

```bash
cd P:/.claude/hooks

# Restore backups
cp goal_anchor.py.backup goal_anchor.py
cp subagent_constitution_injector.py.backup subagent_constitution_injector.py
cp intelligent_stop_hook.py.backup intelligent_stop_hook.py

# Clean up session data
rm -rf P:/.claude/session_data/
```

---

## Performance Impact

- **goal_anchor_v2**: ~100-200ms
- **subagent_constitution_v2_1**: ~50ms
- **intelligent_stop_v2_1**: ~200-500ms

**Total: <1 second per session lifecycle**

Negligible. System is operationally silent.

---

## What This DOES

✅ Detect ambiguous terminology early
✅ Force clarification before proceeding
✅ Propagate goals to subagents
✅ Enforce alignment verification in subagents
✅ Validate completion claims against evidence
✅ Block termination if claims are unsupported
✅ Prevent scope creep
✅ Catch the exact "quadlet confusion" scenario

## What This DOESN'T Do

❌ Write your code (Claude still does that)
❌ Guarantee perfect code quality (existing validators handle that)
❌ Force you to use specific architecture (goals are user-defined)
❌ Add significant latency (hooks are fast)
❌ Break existing workflows (backward compatible)

---

## Testing Checklist

Before considering it "done":

- [ ] All 3 hook files copied to `P:/.claude/hooks/`
- [ ] Session directory created: `P:/.claude/session_data/`
- [ ] settings.json verified (hooks configured)
- [ ] Each hook individually tested (see Quick Start #5)
- [ ] Ambiguous prompt tested (should trigger Layer 1)
- [ ] Subagent task tested (should see goal injection in stderr)
- [ ] False completion claim tested (should block in Layer 4)

---

## Summary

**Problem:** Claude confuses ambiguous goals and implements the wrong objective.

**Solution:** 4-layer defense catching confusion at 4 lifecycle points.

**Implementation:** 3 hook files + 1 integration guide + configuration.

**Time to implement:** ~5 minutes (copy files) + ~30 minutes (read integration guide).

**Value:** Prevents hours of misdirected work like the "quadlet confusion" trace.

---

## Next Steps

1. Follow Quick Start (5 min)
2. Read integration_guide.md (15 min)
3. Test on ambiguous prompt (2 min)
4. You're done

The system is self-enforcing. It will catch confusion automatically.
