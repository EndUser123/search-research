# Adversarial-Logic Specialist Review: premortem_tldr_hooks_20260325

**Reviewer**: adversarial-logic
**Date**: 2026-03-25
**Document**: `P:/.claude/hooks/evidence/premortem_tldr_hooks_20260325.md`
**Confidence Floor**: 75% (Tier 3 static analysis)

---

## Executive Summary

The pre-mortem document is well-structured and identifies plausible failure modes. However, it contains **5 logical errors**, **3 race condition description gaps**, and **4 implementation gap claims that lack evidentiary support**. The keystone risk identification (T4 terminal_id mismatch) is correct but the cascade logic has a flaw.

---

## 1. Logical Errors

### L1: T1 → T2 Cascade Assumes Lock Timeout Causes Corrupted Write

**Location**: Step 2.5, Cascade Analysis

**Claim**: "Lock timeout fires during session end → Cleanup runs without releasing lock properly → Next session reads partially-written state file → Corrupted summary or data loss"

**Problem**: This cascade conflates two distinct failure modes:
1. Lock timeout (T1) is a *detection* failure, not a *cause* of corruption
2. The actual write race (T2) would require the rename to occur *before* the timeout fires

The cascade assumes the lock timeout fires mid-operation, but portalocker timeouts typically fire *after* the lock holder fails to release (indicating a deadlock/hang), not during a successful operation. If the lock times out, the *next* session would wait for the lock, not read a corrupted file.

**Impact**: Cascade analysis overstates risk coupling between T1 and T2.

**Suggested Fix**: Separate T1 (timeout detection) from T2 (write race). T1 is a *symptom* of T2, not a cause.

---

### L2: KC3 Threshold (5% False Positive Rate) Is Non-Verifiable

**Location**: Step 0.7, Kill Criterion KC3

**Claim**: "If orphan detection false positive rate > 5% → disable orphan detection"

**Problem**: The pre-mortem itself admits in Step 3.8 that orphan detection classification is unclear ("confirmed 98 wired, but classification unclear"). There is no baseline measurement of what "false positive" means for orphan detection. Without a ground-truth list of real orphans, the 5% threshold is numerically precise but operationally meaningless.

**Evidence Standard**: Tier 4 (unverified claim). No evidence cited for how 5% was derived or how it would be measured.

---

### L3: Base Rate Attribution (1-2% Failure) Lacks Citation

**Location**: Step 3.5, Reference Class Forecasting

**Claim**: "Base rate: 1-2% failure rate for file-based session state in similar hooks over 6 months."

**Problem**: The document provides no citation for this base rate. "Similar hooks" is undefined. The three reference implementations cited (SessionEnd_cleanup, SessionStart_hook_health_check, evidence_store) are *also* TLDR hooks' own implementations, not external reference class data.

**Evidence Standard**: Tier 4 (unverified claim). This is exactly the kind of generic statistic that CLAUDE.md warns against citing without evidence.

---

### L4: Success Theater Detection Table Has Internal Contradiction

**Location**: Step 3.6, Success Theater Detection

**Claim**: Table shows "98 orphans detected" as a vanity metric, yet Step 3.8 shows orphan detection as "PARTIAL — confirmed 98 wired, but classification unclear."

**Problem**: The document simultaneously treats the 98 orphan count as a *vanity metric* (implies it's inflated/wrong) and as *partial confirmation* of accuracy. These positions are contradictory. If the 98 is a vanity metric, it provides no evidence of accuracy. If it's partial confirmation, it cannot also be a vanity metric.

**Impact**: Undermines the credibility of the success theater critique.

---

### L5: PR4 (No Rollback) Scored as Impact 3 But No Rollback Exists

**Location**: Step 4, Risk Ratings

**Claim**: PR4 (No rollback procedure) has Impact=3, making it score 6.

**Problem**: The document does not establish what a rollback *would* consist of for session-end hooks. SessionEnd hooks write session state — there is no obvious rollback target (you cannot "undo" a session that has ended). The impact score of 3 (high impact) is assigned without explaining what negative outcome occurs when rollback is missing.

**Evidence Standard**: Tier 4 (speculative impact without mechanism).

---

## 2. Race Condition Description Gaps

### R1: No Description of Lock Timeout Recovery Behavior

**Location**: Step 2, Tech risks (T1), Step 2.5 cascade

**Gap**: The document describes T1 (lock timeout too short) but never explains what happens *after* the timeout fires. Specifically:
- Does the hook exit with error, blocking session end?
- Does it proceed without the lock (potential corruption)?
- Does it retry?

The cascade analysis in Step 2.5 assumes "cleanup runs without releasing lock properly" but portalocker does not work this way — a timeout results in `LockFailed` exception, not a silent continuation.

**Missing Analysis**: What is the actual crash/failure mode when the lock times out? This is the critical question for T1.

---

### R2: No Analysis of Rename-Then-Fsync Ordering

**Location**: Step 2, Tech risks (T2, T3)

**Gap**: The document identifies T2 (atomic write race) and T3 (missing fsync) separately, but the actual crash-safety guarantee requires specific ordering:
1. Write content to temp file
2. fsync() temp file
3. rename() temp to target

The document does not verify the TLDR implementation follows this ordering. It treats T2 and T3 as independent risks when they are actually *sequential dependencies* for atomicity.

**Missing Analysis**: Does the TLDR implementation actually follow the correct ordering? The pre-mortem cannot answer this without reading the implementation.

---

### R3: No Multi-Session Concurrent Write Analysis

**Location**: Step 2, External risks (E3)

**Gap**: E3 (Cross-process lock contention) is scored as low risk (1-2). However, the document does not analyze what happens when two *different Claude Code instances* (separate terminals) run simultaneously and both try to write session state.

The terminal isolation (T4) is supposed to prevent this, but if T4 fails (format mismatch), concurrent writes to the same state file become possible. No analysis of what损坏 occurs in this scenario.

**Missing Analysis**: If terminal_id mismatches cause two sessions to write to the same file, what is the actual corruption outcome? (hint: this requires reading the file_lock.py implementation)

---

## 3. Implementation Gap Claims

### G1: "Implementation Completed and Verified" Contradicts Step 3.8

**Location**: Step 0, Project Constraints header + Step 3.8

**Claim**: Header states "Auto-Detected: Implementation completed and verified in prior session"

**Problem**: Step 3.8 (Operational Verification) shows most critical claims as "NOT TESTED":
- TLDR appears on resume: NOT TESTED
- Terminal isolation works: NOT TESTED
- Atomic write survives crash: NOT TESTED
- File locking prevents races: NOT TESTED

Only orphan detection is "PARTIAL". The header claim of "verified in prior session" directly contradicts the operational verification status table.

**Evidence Standard**: Tier 4 fabrication — the document claims verification that Step 3.8 shows did not occur.

---

### G2: "Reference implementations haven't failed in practice" Is Non Sequitur

**Location**: Step 3.5

**Claim**: "All three reference implementations use the same patterns. If they haven't failed in practice, TLDR hooks likely robust IF patterns are followed exactly."

**Problem**: This reasoning has two flaws:
1. Absence of failure reports ≠ absence of failure modes (observability gap)
2. "IF patterns are followed exactly" is not verified — the pre-mortem does not audit the actual TLDR implementation against the reference patterns

**Evidence Standard**: Tier 4 (speculative). The conclusion depends on an unverified conditional.

---

### G3: "File locking used" Is Presented as Evidence of Correctness

**Location**: Step 3.6, Success Theater Detection

**Claim**: "'File locking used' could timeout without proper handling → Lock timeout leads to silent pass (except block)"

**Problem**: The document correctly identifies that lock timeout is a failure mode, but then does not explain what "silent pass (except block)" means. If a lock timeout blocks session end (as implied), this is NOT silent — it is a hard failure that prevents the user from continuing. The success theater critique undermines its own point by being unclear about what "failure" means.

**Impact**: Cannot distinguish between acceptable blocking behavior and pathological blocking.

---

### G4: Health Check Uses Same File Lock As TLDR — Circular Evidence

**Location**: Step 2.6, AI/LLM-Specific Failure Modes

**Claim**: "Health check uses `__lib/file_lock.py`, TLDR also — consistent"

**Problem**: The document uses "health check and TLDR use the same file_lock.py" as evidence of consistent, robust patterns. However, file_lock.py itself is listed in the pre-mortem's own risks (T1 — lock timeout). The consistency claim does not validate correctness, only uniformity.

**Evidence Standard**: Tier 3 at best (uniform ≠ correct).

---

## 4. Cascade Analysis Quality

### Positive: T4 → P1 Cascade Is Correctly Identified

The keystone risk identification (T4 terminal_id format mismatch causing P1 developer to access wrong state file, causing TLDR data corruption) is logically sound and well-supported by the terminal_id_normalization_mismatch memory entry.

### Negative: Cascade Dependencies Are Not Verified Against Implementation

The cascade diagrams (Step 4.5) show structural dependencies but do not cite implementation evidence. For example, T4 "causes" P1 "causes" TLDR data corruption — but the pre-mortem does not verify that TLDR actually reads session_start.txt on resume (Step 3.8 shows this is NOT TESTED).

---

## 5. Evidence Tier Violations

| Claim | Stated Tier | Actual Tier | Issue |
|-------|-----------|------------|-------|
| "Base rate 1-2% failure" | Implied Tier 2 | Tier 4 | No citation, no reference class defined |
| "98 orphans detected" | Partial | Tier 3/4 | Classification unclear, metric is vanity |
| "Reference implementations robust" | Tier 2 | Tier 4 | Non sequitur, depends on unverified conditional |
| "Implementation verified" | Tier 1 | Tier 4 | Step 3.8 shows NOT TESTED |
| "5% false positive threshold" | Tier 2 | Tier 4 | Non-verifiable without ground truth |

---

## 6. Recommendations

### Must Fix (Logical Errors)

1. **L1**: Separate T1 (lock timeout detection) from T2 (write race). They are independent failure modes, not a cascade.
2. **L3**: Remove the base rate statistic or replace with actual evidence from the three reference implementations.
3. **L4**: Reconcile the contradiction between "98 orphans as vanity metric" and "98 orphans as partial confirmation".

### Should Fix (Evidence Gaps)

4. **G1**: Remove "Implementation completed and verified" from header, or verify and update Step 3.8.
5. **G2**: Replace "robust IF patterns followed" with actual audit of TLDR implementation against reference patterns.
6. **R1**: Add portalocker timeout recovery behavior analysis — what actually happens when LockFailed is raised?

### Could Fix (Clarity Improvements)

7. **L2**: Explain how KC3 5% threshold would be measured, or replace with a qualitative criterion.
8. **L5**: Define what "rollback" means for session-end hooks, or reduce impact score.
9. **G3**: Clarify what "silent pass" means for lock timeout — is it acceptable blocking or pathological?

---

## 7. Signature

```
adversarial-logic specialist review
Confidence floor: 75% (Tier 3 static analysis)
Logical errors found: 5
Race condition gaps: 3
Implementation gap claims: 4
Evidence tier violations: 5
```
