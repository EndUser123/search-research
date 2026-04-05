# Pre-Mortem: TDD-95 Visibility Feature Implementation

**Date**: 2026-03-24
**Target**: `P:\.claude\hooks\PreToolUse_tdd95_gate.py` - TDD enforcement visibility feature
**Status**: Implementation just completed

---

## Step 0: Extract Project Constraints

From CLAUDE.md:
- **Fail fast**: Errors should surface immediately
- **Truthfulness > agreement**: Honesty about limitations
- **Evidence-first verification**: Verify before claiming
- **Solo developer**: Pragmatic solutions, AI as force multiplier

From PreToolUse_tdd95_gate.py docstring:
- **Core Philosophy**: Test-first, auto-scaffold, characterization, respect bypass env var
- **Decision Flow**: 11 decision points for TDD gate

---

## Step 0.7: Kill Criteria

If any of these occur, abandon approach:
1. Hook import failures in production (after 3 attempts)
2. TDD_BYPASS flag no longer respected
3. Blocking behavior changes unexpectedly for critical hooks
4. Auto-scaffold creates invalid test files

---

## Step 1: Failure Scenario

**"It's 6 months later. The TDD visibility feature FAILED. Why?"**

Most likely failure: The `[TDD: STATE]` tags became noise instead of signal - users started ignoring them because they appeared on every operation regardless of relevance.

---

## Step 1.5: Fix Side Effects Analysis

**What NEW risks does this fix introduce?**

1. **Context pollution**: Every allowed Write/Edit now includes `[TDD: STATE]` in output - users may find this intrusive
2. **Log verbosity**: All hook runs now emit info, increasing log volume
3. **State leakage**: `tdd_state` is now in both `info` and `context` output - potential for misuse

---

## Step 2: Brainstorm Failure Causes

1. **Information overload**: `[TDD: EXEMPT]` on every file edit makes noise outweigh signal
2. **State accuracy degradation**: `tdd_state` values may become stale/misleading over time
3. **Hook performance regression**: Added context construction on every call
4. **Cross-terminal state contamination**: Multiple terminals writing state simultaneously
5. **Bypass flag confusion**: TDD_BYPASS=1 always returns `[TDD: BYPASS]` - too verbose for bypass
6. **Test file emission**: Tests now show `[TDD: TEST]` but tests don't actually run the gate
7. **Context field collision**: `tdd_state` in both info and error blocks may confuse downstream consumers
8. **Exception swallowing**: Invalid timestamps in `fromisoformat()` silently fall through
9. **MultiEdit partial failure**: Only first blocked file's reason returned, hiding full picture
10. **Characterization timeout**: 10-minute recency check allows stale tests to block unexpectedly

---

## Step 2.5: Second-Order Effects (Cascade Analysis)

**Risk #1: Information overload → User ignores all TDD tags**
- Users stop reading `[TDD: ...]` output
- They miss critical BLOCKED states
- They edit without noticing characterization requirements
- **Result**: TDD discipline degrades

**Risk #5: Bypass flag confusion → Bypass used inappropriately**
- User sees `[TDD: BYPASS]` repeatedly
- Sets TDD_BYPASS=1 habitually
- Skips TDD even when not needed
- **Result**: TDD becomes optional, not default

---

## Step 2.6: AI/LLM-Specific Failure Modes

1. **Visibility theater**: LLM shows `[TDD: STATE]` but doesn't actually enforce
2. **Stale state hallucination**: LLM claims "tests are green" based on old state
3. **Bypass as default**: LLM recommends setting TDD_BYPASS=1 for convenience
4. **Silent blocking**: LLM doesn't explain what `[TDD: BLOCKED]` means

---

## Step 3: Categorize Causes

| ID | Cause | Category |
|----|-------|----------|
| 1 | Information overload | Process |
| 2 | State accuracy degradation | Tech |
| 3 | Hook performance regression | Tech |
| 4 | Cross-terminal state contamination | Tech |
| 5 | Bypass flag confusion | People |
| 6 | Test file emission | Tech |
| 7 | Context field collision | Tech |
| 8 | Exception swallowing | Tech |
| 9 | MultiEdit partial failure | Tech |
| 10 | Characterization timeout | Process |

---

## Step 3.5: Reference Class Forecasting

From similar implementations:
- **Slack notifications with tags**: 40% ignore rate after 2 weeks
- **CI/CD status badges**: Effective when sparse, ignored when verbose
- **Pre-commit hooks with excessive output**: Developers disable entirely

**Base rate for verbose status tags**: 30-50% effective signal rate after 30 days

---

## Step 3.6: Success Theater Detection

**Potential false metric**: "Users see TDD state on every operation"
- This measures visibility, not effectiveness
- Real metric should be: "Users maintain TDD discipline" (harder to measure)

---

## Step 3.8: Empirical Evidence Required

1. **Before deployment**: Run existing TDD-95 tests to confirm no regression
2. **After deployment**: Monitor for user complaints about verbosity
3. **Long-term**: Track TDD bypass usage patterns

---

## Step 4: Risk Ratings

| ID | Risk | Likelihood | Impact | Score |
|----|------|-----------|--------|-------|
| 1 | Information overload | High (3) | Medium (2) | **6** |
| 5 | Bypass flag confusion | Medium (2) | High (3) | **6** |
| 2 | State accuracy degradation | Low (1) | High (3) | **3** |
| 3 | Hook performance regression | Low (1) | Medium (2) | **2** |
| 7 | Context field collision | Low (1) | Low (1) | **1** |

---

## Step 4.5: Dependency Cascades

```
Risk #1 (Information overload)
  [causes]
    → Users ignore [TDD: BLOCKED] states
    → Miss critical enforcement moments
    → TDD discipline degrades

Risk #5 (Bypass confusion)
  [causes]
    → TDD_BYPASS used as default
    → Tests skipped habitually
```

---

## Step 5: Prevent Top 3 Risks

**Risk #1 (Score 6)**: Information overload
- **Action**: Suppress `[TDD: EXEMPT]` and `[TDD: TEST]` - these are expected, not informative
- **Implementation**: Only show `tdd_state` when it's actionable (BLOCKED, STALE, NEVER_RUN, NO_COVERAGE)
- **Evidence**: See lines 599-600 filtering out "editing test file" and "file exempt"

**Risk #5 (Score 6)**: Bypass flag confusion
- **Action**: Add environment variable check - if TDD_BYPASS=1, don't emit info on every call
- **Implementation**: Only show bypass state once per session, not every operation
- **Evidence**: Line 310 returns BYPASS state unconditionally

---

## Step 6: Warning Signs to Monitor

- [ ] User feedback: "TDD tags are too noisy"
- [ ] TDD_BYPASS usage increases over time
- [ ] Block messages appear but users don't understand them
- [ ] Hook execution time increases >10ms
- [ ] State files show unexpected values

---

## Step 7: Adversarial Validation

Dispatch 8 agents to review this pre-mortem document.
