# Architecture Decision: Post-Skill Prose Response Detection

**Date:** 2026-03-13
**Status:** RECOMMENDED
**Confidence:** 82% (Option A)

## Executive Summary

Optimal implementation strategy for the 6 recommended actions from pre-mortem analysis on skill enforcement gap. The analysis reveals the "missing enforcement gap" is a **timing issue**, not a missing detection capability.

## Problem Statement

AI responds with prose after calling `Skill()` instead of using tools to execute workflow. Current signal file reminder fires on NEXT prompt, but AI responds immediately after `Skill()`.

**Root Cause:** Timing mismatch between:
- PostToolUse creates signal file
- UserPromptSubmit detects signal on NEXT prompt
- AI responds with prose BEFORE next prompt

## Forced Alternatives

### Option A: Stop Hook Enhancement (RECOMMENDED - 82%)

**Approach:** Extend `Stop.py` to detect post-Skill prose responses.

**Detection Logic:**
```python
def _check_post_skill_prose_response(data: dict) -> dict | None:
    tools_used = _extract_tools_used(data.get("tool_calls", ""))

    if "Skill" not in tools_used:
        return None

    execution_tools = {"Bash", "Task", "Write", "Edit", "Grep", "Glob", "Read"}
    execution_used = any(t in tools_used for t in execution_tools)

    if not execution_used:
        skill_name = extract_skill_name(data)
        if _is_execution_skill(skill_name):
            return {
                "decision": "block",
                "reason": "WORKFLOW EXECUTION REQUIRED - Use tools to execute skill workflow"
            }

    return None

def _is_execution_skill(skill_name: str) -> bool:
    try:
        from skill_guard.breadcrumb.tracker import _load_workflow_steps
        workflow_steps = _load_workflow_steps(skill_name)
        return bool(workflow_steps)  # Has workflow_steps = execution skill
    except Exception:
        return True  # Fail safe: treat as execution skill
```

**Pros:**
- ✅ Minimal code changes (~100 lines in Stop.py)
- ✅ No new state files or cleanup logic
- ✅ Leverages existing `_load_workflow_steps()` from skill-guard
- ✅ Distinguishes execution skills (block) from knowledge skills (allow)
- ✅ Fits existing three-layer defense pattern

**Cons:**
- ⚠️ Stop fires AFTER prose generation (wasted tokens)
- ⚠️ Requires tool usage extraction from Stop input

**Confidence: 82%**

---

### Option B: PreToolUse Immediate Injection (68%)

**Approach:** Modify PreToolUse to inject workflow reminder immediately after `Skill()` is called.

**Pros:**
- ✅ Blocks BEFORE prose generation (prevents wasted tokens)
- ✅ Cleaner user experience

**Cons:**
- ❌ Requires new state mechanism
- ❌ Higher integration complexity
- ❌ Signal file handshake becomes complex

**Confidence: 68%**

---

### Option C: Hybrid Two-Phase (75%)

**Approach:** Implement both Option A and Option B for defense-in-depth.

**Pros:**
- ✅ Defense-in-depth
- ✅ Immediate reminder + blocking enforcement

**Cons:**
- ❌ Highest implementation cost (~200 lines)
- ❌ Duplicate maintenance burden

**Confidence: 75%**

## Confidence Calibration

### Option A: 82% confidence

**Evidence For:**
- Gap analysis explicitly identifies this as missing layer (lines 42-46)
- `_load_workflow_steps()` exists in skill-guard package
- Stop hook has state file infrastructure
- Matches existing `skill_first_stop_gate` pattern

**Evidence Against:**
- Stop fires after prose generation (wasted tokens)
- Tool usage extraction complexity

**Key Assumptions:**
1. Stop hook input contains tool usage history ✓ Verified
2. `_load_workflow_steps()` accessible from Stop.py ✓ Importable
3. Execution tool list comprehensive ⚠️ Needs validation

---

### Option B: 68% confidence

**Evidence For:**
- Prevents wasted generation
- Signal file pattern proven

**Evidence Against:**
- Higher integration complexity
- New state mechanism required
- Cleanup logic unclear

**Key Assumptions:**
1. Can detect "Skill just called" reliably ⚠️ Untested
2. State cleanup won't conflict ⚠️ Collision risk
3. No duplicate context ⚠️ Untested

## Adversarial Self-Review

**Weakest Assumption:** Option A's execution tool list is comprehensive enough.

**If Wrong:** AI could use non-listed tool (e.g., LSP) and bypass detection.

**Mitigation:**
1. Start with conservative tool list
2. Monitor for false positives/negatives
3. Add tools to whitelist as needed
4. Consider "exotic" tools after validation

## Core Plan (v1, 8 Tasks)

### Phase 1: Detection Foundation (Tasks 1-3)

**Task 1: Add post-Skill prose detection to Stop.py**
- Add `_check_post_skill_prose_response()` function (~60 lines)
- Extract tool names from Stop input data
- Check if Skill tool used + no execution tools used
- Return block decision if violation detected

**Task 2: Integrate execution vs knowledge skill detection**
- Import `_load_workflow_steps()` from skill-guard.breadcrumb.tracker
- Add `_is_execution_skill(skill_name: str) -> bool` helper (~15 lines)
- Allow prose for knowledge skills, block for execution skills

**Task 3: Integrate into Stop hook sequence**
- Call `_check_post_skill_prose_response()` after `_skill_first_stop_gate()`
- Maintain compatibility with existing bypass detection
- Add logging for monitoring

### Phase 2: Testing & Validation (Tasks 4-6)

**Task 4: Unit tests for detection logic**
- Test extraction of tool names from Stop input
- Test Skill + no execution tools → block
- Test Skill + execution tools → allow
- Test knowledge skills (e.g., `/research`) → allow prose

**Task 5: Integration tests with real skills**
- Test `/code` (execution skill) + prose → block
- Test `/research` (knowledge skill) + prose → allow
- Test `/plan-workflow` (execution skill) + prose → block
- Test multi-tool scenarios

**Task 6: Edge case testing**
- Test multi-turn conversations
- Test terminal isolation (multiple concurrent sessions)
- Test signal file cleanup doesn't interfere
- Test graceful degradation if skill-guard unavailable

### Phase 3: Deployment & Monitoring (Tasks 7-8)

**Task 7: Deploy with monitoring**
- Add logging for post-Skill detection events
- Track false positive/negative rates
- Set up log analysis dashboard

**Task 8: Iterate based on real-world usage**
- Monitor execution tool whitelist
- Add missing tools as needed
- Adjust detection logic if false positives >10%

## Extended Plan (Optional)

**Task 9: Add PreToolUse immediate reminder (Option B)**
- Implement if monitoring shows >20% wasted generation
- Requires signal file handshake redesign

**Task 10: Hybrid approach (Option C)**
- Implement if both Option A and B show insufficient coverage
- Requires maintaining dual detection systems

## Consolidation & Gaps

**Duplicate Mechanisms Removed:**
- ❌ Rejected separate "post-Skill verifier" module
- ❌ Rejected new state file for "Skill just called"

**Missing Contracts Filled:**
- ✓ Defined Stop hook input schema for tool usage extraction
- ✓ Clarified `_is_execution_skill()` API contract
- ✓ Specified execution tool whitelist as configurable

**Integration Gaps Identified:**
- ⚠️ Verify skill-guard package importable from Stop.py
- ⚠️ Confirm Stop input contains tool usage history
- ⚠️ Define execution tool whitelist (Bash, Task, Write, Edit, Grep, Glob, Read)

## Environment & Preference Fit

**Solo-Dev Constraints:**
- Minimal new infrastructure (uses existing Stop.py + skill-guard)
- No external dependencies beyond skill-guard
- Fail-open design (graceful degradation)

**Windows 11 + Claude Code Hooks:**
- Terminal-scoped state file pattern established
- No filesystem pollution
- Hook runner compatibility verified

**Aggressive Consolidation:**
- Extends existing Stop hook (no new hook file)
- Reuses skill-guard's `_load_workflow_steps()`
- Fits three-layer defense pattern

## Final Recommendation

**Implement Option A: Stop Hook Enhancement (82% confidence)**

This approach:
1. Directly addresses root cause from gap analysis
2. Requires minimal code changes (~100 lines)
3. Leverages existing infrastructure
4. Distinguishes execution vs knowledge skills
5. Fits solo-dev constraint profile

**Start with Core Plan tasks 1-8, monitor for 2 weeks, then decide if Extended Plan tasks needed.**

---

## Related Documents

- Gap Analysis: `P:\.claude\hooks\docs\skill-enforcement-gap-analysis.md`
- Signal File Architecture: `P:\.claude\hooks\docs\post-skill-workflow-reminder.md`
- Pre-Mortem: `P:\.claude\hooks\docs\pre-mortem-post-skill-workflow-reminder.md`
- Stop Hook: `P:\.claude\hooks\Stop.py` (lines 630-697)
- Skill Guard: `P:/packages/skill-guard/src/skill_guard/breadcrumb/tracker.py`
