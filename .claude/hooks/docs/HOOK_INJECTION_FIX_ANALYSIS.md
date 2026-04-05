# Hook Injection Failure Analysis & Fix Plan

**Date:** 2026-01-06
**Severity:** CRITICAL - All context injection is non-functional
**Confidence:** 95% (Tier 1: Evidence from logs, code inspection, official docs)

---

## Executive Summary

UserPromptSubmit hooks are executing but **zero content is being injected into Claude Code's context**. This means:
- Command directives are not being delivered to the LLM
- Goal anchors are not reaching the LLM
- All pre-generation constitutional enforcement is bypassed
- Stop hooks have no state to validate against

---

## Evidence

### 1. Diagnostic Logs (Tier 1)
```json
// P:/.claude/hooks/logs/diagnostics/cc_context.jsonl
{"injected_content": [], "injected_total_tokens": 0, ...}
```
**Every single prompt** shows zero injection. The hooks execute but nothing reaches Claude.

### 2. Code Inspection (Tier 3)
Both `command_directive_injector.py` and `goal_anchor.py` use incorrect output pattern:

```python
# WRONG - This pattern does nothing
print("RELAY_TO_USER:", flush=True)       # Invented pattern, not in CC spec
print(f"COMMAND DIRECTIVE: Read {FILE}")  # Text that should be context
print("END_RELAY", flush=True)            # Invented pattern

# Then at the end:
print(json.dumps(input_data))  # WRONG - echoes input, has no additionalContext
```

### 3. Official Claude Code Documentation (Tier 2)
From https://code.claude.com/docs/en/hooks:

```
UserPromptSubmit hooks can control whether a user prompt is processed and add context.

Adding context (exit code 0):
1. Plain text stdout (simpler): Any non-JSON text written to stdout is added as context
2. JSON with additionalContext (structured): Use the JSON format below

{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "My additional context here"
  }
}
```

### 4. GitHub Issues Confirm Bugs (Tier 2)

| Issue | Date | Description |
|-------|------|-------------|
| #13912 | 3 weeks ago | UserPromptSubmit stdout causes error despite docs |
| #8810 | Oct 2025 | UserPromptSubmit not working from subdirectories (Windows) |
| #10373 | Oct 2025 | SessionStart hook context not being injected |
| #13650 | Dec 2025 | SessionStart stdout silently dropped |

---

## Root Causes

### RC1: Mixed Output Format (CRITICAL)
Hooks print both plain text AND JSON. When JSON is detected, Claude Code parses it as the structured output and ignores any plain text. The JSON we output lacks `additionalContext` field.

### RC2: Invented "RELAY" Pattern (CRITICAL)
The "RELAY_TO_USER:" pattern has no meaning to Claude Code. This was an assumption that proved false.

### RC3: Echoing Input Data (CRITICAL)
`print(json.dumps(data))` at the end of hooks echoes the input back as JSON output. This is wrong - hooks should NOT echo input.

### RC4: Known Claude Code Bugs (MODERATE)
Multiple GitHub issues show UserPromptSubmit injection is flaky, especially on Windows.

---

## Fix Plan

### Phase 1: Create Test Hook (Verify Basic Functionality)

Create minimal test to verify injection works at all:

```python
#!/usr/bin/env python3
# P:/.claude/hooks/test_injection.py
"""Minimal test hook - does injection work at all?"""
import sys

# Method 1: Plain text (should work per docs)
print("TEST INJECTION: If Claude sees this, injection works!")
sys.exit(0)
```

Test with:
```
Ask Claude: "What's 2+2? (Do you see any TEST INJECTION text?)"
```

### Phase 2: Fix Hook Output Format

**BEFORE (Wrong):**
```python
print("RELAY_TO_USER:", flush=True)
print(f"COMMAND DIRECTIVE: ...", flush=True)
print("END_RELAY", flush=True)
print(json.dumps(input_data))  # Kills the text injection!
```

**AFTER (Correct - Plain Text):**
```python
# Just print the context you want to inject
print("""<command_directive>
Execute: python script.py
DO NOT: Describe this command
</command_directive>""")
# NO JSON output - let Claude Code handle exit code 0
sys.exit(0)
```

**AFTER (Correct - JSON):**
```python
import json
output = {
    "hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": """<command_directive>
Execute: python script.py
DO NOT: Describe this command
</command_directive>"""
    }
}
print(json.dumps(output))
sys.exit(0)
```

### Phase 3: Update All Injection Hooks

Files to fix:
1. `P:/.claude/hooks/UserPromptSubmit_command_directive_injector.py`
2. `P:/.claude/hooks/goal_anchor.py`
3. `P:/.claude/hooks/UserPromptSubmit_falsification_injector.py`
4. Any other hook using RELAY pattern

### Phase 4: Add Diagnostic Verification

Update `cc_context_diagnostic.py` to:
1. Log what the hook outputs
2. Verify injection in next prompt's context
3. Alert if injection fails

---

## Implementation: Fixed command_directive_injector.py

```python
#!/usr/bin/env python3
"""
Command Directive Injector v3.0 - FIXED OUTPUT FORMAT
=====================================================
Uses correct Claude Code hook output schema.
"""

import json
import sys
from pathlib import Path

# ... (keep existing extraction logic) ...

def output_injection(content: str):
    """Output injection using CORRECT Claude Code format."""
    # Option A: Plain text (simpler, works if CC parses it)
    # print(content)
    # sys.exit(0)
    
    # Option B: JSON with additionalContext (more reliable)
    output = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": content
        }
    }
    print(json.dumps(output))
    sys.exit(0)

def main():
    # ... (keep existing detection logic) ...
    
    if injection_content:
        output_injection(injection_content)
    else:
        # No injection needed - just exit cleanly
        sys.exit(0)
    
    # DO NOT: print(json.dumps(input_data)) - this kills injection!
```

---

## Verification Plan

1. **Create test hook** - Verify basic injection works
2. **Fix one hook** - command_directive_injector.py
3. **Test with /refactor** - Should see directive in context
4. **Check logs** - `injected_content` should have data
5. **Roll out to other hooks** - goal_anchor.py, etc.

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Fix doesn't work due to CC bugs | 40% | HIGH | Test both plain text and JSON formats |
| Breaking other hooks | 20% | MED | Test in isolation first |
| Path issues on Windows | 30% | MED | Use absolute paths |

**Reversibility:** 1.25 (Easy - can revert hook changes)

---

## Success Criteria

1. `cc_context.jsonl` shows `injected_content: [...]` with data
2. `/refactor` command executes instead of being described
3. Goal anchor appears in Claude's context window
4. Stop hooks have state to validate against

---

## Verification Results (2026-01-06)

### Fixed Hooks - VERIFIED WORKING

1. **command_directive_injector.py** v3.0
   ```bash
   echo '{"prompt": "/refactor test.py"}' | python hook.py
   # Output: {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": "..."}}
   ```
   ✅ Outputs correct JSON format

2. **goal_anchor.py** v4.0
   ```bash
   echo '{"prompt": "fix the bug in parser"}' | python hook.py
   # Output: {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": "<solo_dev_context>..."}}
   ```
   ✅ Outputs correct JSON format

3. **falsification_injector.py** v2.0
   ```bash
   echo '{"prompt": "put the file in src"}' | python hook.py
   # Output: {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": "..."}}
   ```
   ✅ Outputs correct JSON format

### Remaining Hooks (Low Priority)

These hooks also use wrong output format but are non-critical:
- UserPromptSubmit_debug_guidance.py
- UserPromptSubmit_buc_trigger.py  
- UserPromptSubmit_periodic_reminder.py
- user_prompt_submit_cks.py
- anti_sycophancy/advocate_injection.py

## Next Steps

1. [x] Create test_injection.py
2. [x] Fix command_directive_injector.py
3. [x] Fix goal_anchor.py  
4. [x] Fix falsification_injector.py
5. [x] Verify all three output correct JSON format
6. [x] Test in live Claude Code session - **CONFIRMED WORKING**
7. [x] cc_context.jsonl doesn't detect (monitoring limitation, not functional issue)
8. [ ] Fix remaining low-priority hooks (optional)

## FINAL STATUS: ✅ INJECTION WORKING

User verified in Claude Code:
```
<solo_dev_context>
CONTEXT: Solo developer workflow. No enterprise infrastructure.
TERMINOLOGY:
- deployment → implementation
- production → development environment
- staging → (omit)
- rollout → immediate availability
- pipeline → workflow
</solo_dev_context>

📌 GOAL ANCHOR
Scope: ANALYSIS
Confidence: 75%
Primary Objective: ...
```

**Root cause was confirmed:** RELAY pattern was invented and doesn't exist in Claude Code.
**Fix confirmed:** JSON with `hookSpecificOutput.additionalContext` works.

---

## CONSOLIDATION: Unified Prompt Injector v1.0

**Problem discovered:** Multiple hooks outputting `additionalContext` JSON may conflict.
When `command_directive_injector` and `goal_anchor` were in the same settings block,
only `goal_anchor` output appeared - the second hook overwrote the first.

**Solution:** Consolidated all injection hooks into single `unified_prompt_injector.py`.

**Benefits:**
- Single output, no conflict
- Token budget control (configurable MAX_TOKENS)
- Single debug point
- Matches "Constitution-Primary, Hook-Minimal" philosophy

**Components combined:**
1. Solo dev context (~80 tokens, always)
2. Command directive (when slash command detected)
3. Goal anchor (always)
4. Falsification reminder (when assumption risk detected)

**Deprecated files (kept for reference):**
- `UserPromptSubmit_command_directive_injector.py`
- `goal_anchor.py`
- `UserPromptSubmit_falsification_injector.py`

**Active file:**
- `unified_prompt_injector.py` (settings.json updated)
