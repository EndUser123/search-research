# Pre-Mortem: BLOCKED_ROOT_PATTERN Message Handler in violation_reporter.py

**Target**: `P:\.claude\hooks\violation_reporter.py` — Added `BLOCKED_ROOT_PATTERN` case in `format_violation_message()`
**Date**: 2026-04-01
**Analysis Type**: Single-file enhancement (message improvement only)

---

## Step 0: Project Constraints (from CLAUDE.md)

- Fail fast, surface problems immediately
- Truthfulness > agreement
- Evidence-first verification
- Solo dev context: ROI over risk-aversion

## Step 0.7: Kill Criteria

- If > 30 minutes spent on this pre-mortem, abandon and proceed
- If adversarial findings require > 2 hours to address, defer remaining items

---

## Step 1: Failure Scenario

**"It's 6 months later and this FAILED. Why?"**

The BLOCKED_ROOT_PATTERN message handler was implemented to improve error messages, but:
- The error message still shows confusing output
- The wrong paths are shown as allowed
- The correction block points to wrong location
- The change introduces new bugs

---

## Step 1.5: Fix Side Effects (What NEW risks does this fix introduce?)

1. **Hardcoded allowlist**: The allowed paths are hardcoded in the message handler, not loaded from `directory_policy.json`. If the policy changes, the error message becomes stale/wrong.
2. **Correction path assumption**: Uses `P:/.claude/{filename}` as fallback correction, which may not be appropriate for all file types.

---

## Step 2: Brainstorm 10+ Failure Causes

### People
1. **Stale allowlist display**: Developer updates `directory_policy.json` but forgets to update the hardcoded list in `violation_reporter.py`
2. **Wrong mental model**: Users see `.claude` in allowed list and think they can write anywhere under `.claude`

### Process
3. **No integration test**: No test verifies the message format matches the policy
4. **Manual sync requirement**: Allowlist in two places (JSON config + Python code) must be kept in sync

### Tech
5. **Hardcoded paths mismatch**: `allowed_root_patterns` in JSON has 6 entries, hardcoded list must match exactly
6. **Case sensitivity edge case**: `__csf` vs `__CSF` — does path matching handle case correctly?
7. **Trailing slash handling**: `docs` vs `docs/` — policy uses `rstrip("/")` but message doesn't verify
8. **Correction path wrong type**: Suggests `P:/.claude/{filename}` for all blocked files, regardless of file type

---

## Step 2.5: Cascade Analysis

**RISK-001 (Stale allowlist)**: Likelihood = 2 (medium)
- And then what? User sees misleading error message
- And then what? User confused about correct path
- And then what? Wasted time, frustration

**RISK-002 (Hardcoded mismatch)**: Likelihood = 1 (low)
- And then what? Error message shows wrong allowed paths
- And then what? User doesn't trust the system
- And then what? Workaround behavior established

---

## Step 2.6: AI/LLM-Specific Failure Modes

- **Context overflow**: If CLAUDE.md is updated with new allowed paths, the hardcoded list in violation_reporter.py becomes stale
- **Forgotten constraint**: "Remember to update violation_reporter.py when changing directory_policy.json" — LLM may forget this implicit dependency

---

## Step 2.7: Temporal Failure Modes

- If context window overflows and is compacted, the constraint that "violation_reporter.py must stay in sync with directory_policy.json" may be lost
- "what was the requirement again?" — the hardcoded list drifts from actual policy

---

## Step 3: Categorize

| ID | Category | Finding |
|----|----------|---------|
| TECH-001 | Tech | Hardcoded allowlist in Python vs JSON config |
| PROCESS-001 | Process | No integration test verifying message matches policy |
| PEOPLE-001 | People | Stale display when policy changes but code doesn't |

---

## Step 3.8: Operational Verification

**EMPIRICAL EVIDENCE REQUIRED**:

- **TECH-001**: Read `violation_reporter.py:319-323` — hardcoded list confirmed
- **PROCESS-001**: Grep for tests — no test verifies message format against policy

---

## Step 4: Risk Ratings

| Risk | Likelihood | Impact | Score | Notes |
|------|------------|--------|-------|-------|
| TECH-001 | 2 (medium) | 2 (medium) | 4 | Hardcoded allowlist will drift |
| PROCESS-001 | 3 (high) | 2 (medium) | 6 | No test = future regression |

---

## Step 5: Prevent Top 3 Risks

1. **PROCESS-001 (Score 6)**: Add integration test that verifies the hardcoded allowed list in violation_reporter.py matches directory_policy.json
2. **TECH-001 (Score 4)**: Extract allowed list from directory_policy.json at runtime instead of hardcoding
3. **PEOPLE-001 (Score 3)**: Document the sync requirement in CLAUDE.md hooks section

---

## Step 6: Warning Signs

- **Warning sign**: Error message shows different paths than what directory_policy.json actually allows
- **Detection**: Run integration test or compare outputs
- **Trigger**: Update violation_reporter.py or directory_policy.json without running test

---

## Preliminary Findings (Pre-Adversarial)

No CRITICAL issues identified — this is a low-risk message improvement.

**MEDIUM risks**:
- Hardcoded allowlist may drift from JSON config
- No test coverage for message format

**Recommended fix**: Load the allowed patterns from `directory_policy.json` at runtime instead of hardcoding.
