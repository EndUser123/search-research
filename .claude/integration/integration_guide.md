# Task Confusion Prevention System - Integration Guide

Complete installation and configuration guide for the 4-file system that prevents the "quadlet confusion" problem.

---

## Overview

The system consists of 4 enhanced hooks working across 4 lifecycle stages:

| Stage | Hook | File | Purpose |
|-------|------|------|---------|
| **UserPromptSubmit** | goal_anchor v2.0 | `goal_anchor_v2.py` | Detect ambiguity, extract goal, persist to session |
| **PreToolUse** | subagent_constitution v2.1 | `subagent_constitution_v2_1.py` | Retrieve goal, inject alignment requirements |
| **PostToolUse** | (no change) | (existing) | Validates tool output (existing logic) |
| **Stop** | intelligent_stop v2.1 | `intelligent_stop_v2_1.py` | Validate completion claims against actual execution |

---

## Installation Steps

### Step 1: Backup Existing Hooks

```bash
cd P:/.claude/hooks

# Backup existing files (in case rollback needed)
cp goal_anchor.py goal_anchor.py.backup
cp subagent_constitution_injector.py subagent_constitution_injector.py.backup
cp intelligent_stop_hook.py intelligent_stop_hook.py.backup
```

### Step 2: Deploy New Hook Files

Place the three new files in `P:/.claude/hooks/`:

```bash
# Copy files to hooks directory
cp goal_anchor_v2.py P:/.claude/hooks/goal_anchor.py
cp subagent_constitution_v2_1.py P:/.claude/hooks/subagent_constitution_injector.py
cp intelligent_stop_v2_1.py P:/.claude/hooks/intelligent_stop_hook.py

# Verify
ls -la P:/.claude/hooks/goal_anchor.py
ls -la P:/.claude/hooks/subagent_constitution_injector.py
ls -la P:/.claude/hooks/intelligent_stop_hook.py
```

### Step 3: Update settings.json Hook Configuration

Your existing `settings.json` should have the hooks. Verify the layer ordering is correct:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "^all$",
        "hooks": [
          {
            "type": "command",
            "command": "python P:/.claude/hooks/goal_anchor.py",
            "timeout": 5,
            "layer": "1_goal_anchor",
            "critical": true
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "^Task$",
        "hooks": [
          {
            "type": "command",
            "command": "python P:/.claude/hooks/subagent_constitution_injector.py",
            "timeout": 5,
            "layer": "2_subagent_constitution",
            "critical": true
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "^all$",
        "hooks": [
          {
            "type": "command",
            "command": "python P:/.claude/hooks/intelligent_stop_hook.py",
            "timeout": 10,
            "layer": "4_intelligent_stop",
            "critical": true
          }
        ]
      }
    ]
  }
}
```

**Important**: These should already be in your settings.json. If not, add them.

### Step 4: Create Session Data Directory

The hooks use session persistence. Create the directory:

```bash
mkdir -p P:/.claude/session_data
# Verify
ls -la P:/.claude/session_data/
```

### Step 5: Test Installation

Create a test script to verify the hooks load:

```bash
# Test goal_anchor
python P:/.claude/hooks/goal_anchor.py < /dev/null
# Expected: JSON output with extracted_goal

# Test subagent_constitution
python P:/.claude/hooks/subagent_constitution_injector.py < /dev/null
# Expected: JSON output with action

# Test intelligent_stop
python P:/.claude/hooks/intelligent_stop_hook.py < /dev/null
# Expected: JSON output with allow_stop
```

---

## Configuration

### Terminal Ambiguous Terms (in goal_anchor.py)

The system includes hard-coded ambiguous terms for your domain. If you want to add more:

In `goal_anchor_v2.py`, find the `AMBIGUOUS_TERMS` dict and add:

```python
AMBIGUOUS_TERMS = {
    "quadlet": {...},  # existing
    "implement": {...},  # existing
    # ADD NEW TERMS HERE:
    "system": {
        "meanings": ["software_architecture", "framework", "infrastructure"],
        "clarification": "Does 'system' refer to...",
    },
}
```

### Customizing Completion Claim Patterns (in intelligent_stop.py)

If your prompts use specific completion language, update `COMPLETION_CLAIM_PATTERNS`:

```python
COMPLETION_CLAIM_PATTERNS = [
    # existing patterns
    r"ready\s+(?:for|to)\s+(?:review|merge|deploy)",
    # ADD YOUR OWN:
    r"all\s+requirements\s+met",
]
```

### Customizing Evidence Patterns (in intelligent_stop.py)

Similarly, `EVIDENCE_PATTERNS` can be extended:

```python
EVIDENCE_PATTERNS = {
    "test_execution": [...],
    # ADD YOUR OWN CATEGORY:
    "custom_verification": [
        r"verified\s+with\s+custom\s+script",
    ],
}
```

---

## Operation & Monitoring

### How It Works in Practice

**Scenario 1: Ambiguous Input (prevented)**

```
User: "Fix qual-gate.md, implement quadlet system"
        ↓
goal_anchor.py detects:
  - Two conflicting scopes (modification vs creation)
  - Ambiguous term "quadlet"
        ↓
Claude receives:
  ⚠️ GOAL AMBIGUITY DETECTED
  Please clarify which is primary...
        ↓
Claude asks user to clarify
        ↓
Goal persisted to session
```

**Scenario 2: Subagent Receives Clear Goal**

```
Claude (lead): "Fix qual-gate.md"
        ↓
Goal persisted: "fix qual-gate.md" → SoloSessionBridge
        ↓
Claude calls: Task(agent=python-core, task="Implement quadlet system")
        ↓
subagent_constitution_injector.py:
  - Retrieves goal: "fix qual-gate.md"
  - Injects constitution requiring:
    1. State primary objective
    2. Show how task serves objective
    3. Define scope boundaries
        ↓
Subagent cannot claim alignment without evidence
```

**Scenario 3: False Completion Claims Caught**

```
Claude: "✅ IMPLEMENTATION COMPLETE"
        ↓
Session ends, intelligent_stop_hook fires
        ↓
intelligent_stop.py:
  - Finds completion claim
  - Looks for supporting tool execution
  - No test runs found, no file operations found
        ↓
⛔ TERMINATION BLOCKED
   "Completion claimed without supporting evidence"
        ↓
Claude must run verification before stopping
```

### Monitoring Logs

Check stderr for hook diagnostics:

```bash
# In your Claude Code terminal output, look for:
✓ Constitution injected for Task subagent
  Goal: fix qual-gate.md

⚠️  GOAL AMBIGUITY DETECTED
Multiple objectives found...

⛔ TERMINATION BLOCKED
Completion claim without supporting evidence
```

### Session State Inspection

View persisted goal state:

```bash
cat P:/.claude/session_data/goal_state.json

# Output:
# {
#   "primary_goal": "fix qual-gate.md",
#   "goal_scope": "modification",
#   "goal_confidence": 0.95,
#   "timestamp": "2025-12-15T18:50:00.000000"
# }
```

---

## Behavior Comparison: Before vs. After

### Before (Your "Quadlet Confusion" Trace)

```
User: "Fix qual-gate.md, implement quadlet system"
↓
goal_anchor (v1): Extracts one goal, misses ambiguity
↓
Claude proceeds with confusion
↓
Calls subagents to build non-existent "quadlet system"
↓
Subagents claim success without evidence
↓
"✅ IMPLEMENTATION COMPLETE"
↓
Stop hook doesn't validate claims
↓
Wasted hours on wrong direction
```

**Result: Hours of misdirected work**

### After (With This System)

```
User: "Fix qual-gate.md, implement quadlet system"
↓
goal_anchor_v2 detects:
  - Two conflicting scopes
  - Ambiguous term "quadlet"
↓
Claude MUST ask for clarification
↓
User: "Primary is qual-gate.md. Quadlet is just the project name."
↓
Goal persisted: "fix qual-gate.md" (modification scope)
↓
Claude calls subagent to refactor qual-gate.md
↓
subagent_constitution_v2_1 injects:
  "How does your task serve: fix qual-gate.md?"
↓
Subagent must explicitly verify alignment
↓
Subagent: "Primary goal is fix qual-gate.md.
           My task is refactor to 6-step architecture.
           Alignment: YES—direct refactor of that file."
↓
Subagent proceeds with clear scope
↓
Subagent completes and reports evidence
↓
intelligent_stop_v2_1 validates:
  - Completion claim: "Refactoring complete"
  - Evidence: ✓ qual-gate.md modified, ✓ tests pass, ✓ architecture verified
  ✅ Allow termination
↓
Clear, correct work delivered
```

**Result: 15 minutes on the right task instead of hours on the wrong one**

---

## Troubleshooting

### Problem: Hooks Not Firing

**Check 1: Hook file exists**
```bash
ls -la P:/.claude/hooks/goal_anchor.py
ls -la P:/.claude/hooks/subagent_constitution_injector.py
ls -la P:/.claude/hooks/intelligent_stop_hook.py
```

**Check 2: Syntax errors**
```bash
python -m py_compile P:/.claude/hooks/goal_anchor.py
python -m py_compile P:/.claude/hooks/subagent_constitution_injector.py
python -m py_compile P:/.claude/hooks/intelligent_stop_hook.py
```

**Check 3: settings.json is correct**
```bash
# Verify JSON is valid
python -c "import json; json.load(open('P:/.claude/settings.json'))"

# Check hook config
cat P:/.claude/settings.json | grep -A 5 "goal_anchor"
```

### Problem: "SoloSessionBridge not available" Warning

This is expected if your CSF NIP isn't in the Python path. The hooks fall back to environment variables and session files. Safe to ignore unless goal persistence isn't working.

**Fix:**
```bash
# Verify CSF NIP path
ls -la P:/__csf/src/solo/session_bridge.py

# If it exists, the import should work
# If not, session files will be used instead (fallback works fine)
```

### Problem: Hooks Timing Out

If hooks are timing out (>5-10 seconds), it's likely:

1. **SoloSessionBridge is slow** — OK to increase timeout in settings.json
2. **File I/O is slow** — Check if P:/ drive is responsive
3. **Goal extraction is computationally expensive** — Normal for first prompt

**Fix:**
In `settings.json`, increase timeouts:

```json
{
  "timeout": 10,  // Change from 5 to 10
  "layer": "1_goal_anchor"
}
```

### Problem: Goal Not Persisting to Subagent

If a subagent doesn't receive the goal in its constitution:

**Check 1: Goal was extracted and persisted**
```bash
cat P:/.claude/session_data/goal_state.json
# Should show primary_goal
```

**Check 2: Subagent hook is running**
Look for in Claude Code output:
```
✓ Constitution injected for Task subagent
  Goal: [should show the goal]
```

**Check 3: Manual test**
```bash
echo '{"tool":"Task","input":{"task":"Test"}}' | python P:/.claude/hooks/subagent_constitution_injector.py
# Should show goal injection in output
```

---

## Rollback Instructions

If something goes wrong, revert to the previous version:

```bash
cd P:/.claude/hooks

# Restore backups
cp goal_anchor.py.backup goal_anchor.py
cp subagent_constitution_injector.py.backup subagent_constitution_injector.py
cp intelligent_stop_hook.py.backup intelligent_stop_hook.py

# Clean up session data (optional)
rm -rf P:/.claude/session_data/

# Verify restoration
ls -la goal_anchor.py
```

---

## Testing the System

### Test Case 1: Ambiguity Detection

```text
Input prompt:
"Fix qual-gate.md, implement quadlet system using parallel execution"

Expected:
⚠️ GOAL AMBIGUITY DETECTED
Multiple objectives found:
- [95%] fix qual-gate.md (modification)
- [85%] implement quadlet system (creation)

Please clarify which is primary.
```

### Test Case 2: Clear Single Goal

```text
Input prompt:
"Refactor qual-gate.md to use 6-step architecture"

Expected:
🎯 GOAL ANCHOR
Scope: MODIFICATION
Confidence: 95%
Primary Objective: refactor qual-gate.md to use 6-step architecture
```

### Test Case 3: Subagent Goal Propagation

```text
Lead prompt: "Fix qual-gate.md"
Lead calls: Task(task="Implement quadlet system")

Expected in subagent constitution:
PRIMARY OBJECTIVE (from lead agent):
fix qual-gate.md

YOUR ASSIGNED TASK:
Implement quadlet system

VERIFICATION: How does your task directly serve the primary objective?
[Forces subagent to recognize misalignment]
```

### Test Case 4: Completion Claim Validation

```text
Claude says: "✅ IMPLEMENTATION COMPLETE"
No tool execution before this claim

Expected:
⛔ TERMINATION BLOCKED
HIGH: Completion claimed without supporting evidence
Required: Tool execution output (test results, file operations)
```

---

## Performance Impact

The system adds minimal overhead:

- **goal_anchor_v2**: ~100-200ms (regex parsing of prompt)
- **subagent_constitution_v2_1**: ~50ms (goal retrieval + string injection)
- **intelligent_stop_v2_1**: ~200-500ms (conversation parsing + validation)

**Total: <1 second added per session lifecycle**

---

## Future Enhancements

Possible improvements (not in this version):

1. **ML-based ambiguity detection** — Rather than regex, use embeddings to find semantic ambiguity
2. **Automatic goal correction** — If subagent detects misalignment, auto-suggest clarification
3. **Audit trail** — Log all goal transitions for post-hoc analysis
4. **Goal metrics dashboard** — Track how often ambiguity is caught, scope creep prevented, etc.

---

## Support & Questions

If the system doesn't work as expected:

1. Check the troubleshooting section above
2. Verify all 3 hook files are in `P:/.claude/hooks/`
3. Check `settings.json` hook configuration
4. Look for error messages in stderr output
5. Test hooks individually (see Troubleshooting)

---

## Summary

This system prevents confusion by:

1. ✅ **Detecting ambiguity early** (goal_anchor_v2)
2. ✅ **Propagating goals to subagents** (subagent_constitution_v2_1)
3. ✅ **Forcing alignment verification** (subagent constitution requirements)
4. ✅ **Validating completion claims** (intelligent_stop_v2_1)

**Total implementation time: ~4.5 hours**
**Prevention value: Hours of misdirected work avoided**

The three hook files above contain all the code needed. Installation is a matter of copying files and verifying settings.json configuration.
