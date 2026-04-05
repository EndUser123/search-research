# Adversarial Quality Review: premortem_tldr_hooks_20260325.md

**File:** `P:/.claude/hooks/evidence/premortem_tldr_hooks_20260325.md`
**Date:** 2026-03-25
**Review scope:** Maintainability risks, structural issues, completeness gaps

---

## Executive Summary

The pre-mortem document is well-structured with comprehensive failure mode enumeration (16 items across People/Process/Tech/External categories), explicit kill criteria, and dependency cascade tracing. However, it has three categories of quality problems: (1) structural gaps where critical verification artifacts are missing, (2) maintainability risks where the document could silently become stale or mislead future readers, and (3) completeness gaps where key analysis dimensions are absent or shallow.

The most critical issue: the document's "Operational Verification" section (Step 3.8) admits that **most critical claims have NOT been empirically verified** — yet the document presents risk ratings and prioritization as if they were evidence-based conclusions rather than unverified estimates.

---

## 1. Maintainability Risks

### [HIGH] No test corpus for regex-based orphan detection (T6)

**Location:** Step 2, T6 — `_collect_orphan_hooks() regex incomplete`

The pre-mortem identifies T6 as a key risk (score 6) but provides no evidence that the regex has been characterized against a test corpus. Without real examples of both wired and orphan hooks, there is no way to verify the regex gap is real, measure false positive/negative rates, or validate the fix.

**Impact:** The prevention recommendation ("fix the regex") could introduce new bugs or miss real orphan patterns.

**Recommendation:** Before finalizing this risk, create a test corpus:
- Sample of 10+ actual wired hook names from `settings.json`
- Sample of 10+ orphan hook names from health check output
- Verify the regex gap exists with actual pattern comparisons

### [MEDIUM] Warning sign monitoring has no implementation path (Step 6)

**Location:** Step 6 — Warning Signs to Monitor

The monitoring section lists 5 observable signals:
- "TLDR not appearing on resume" — no detection mechanism documented
- "State file count growing" — `ls state/session_tldr/*.md | wc -l` is a manual command, not an automated alert
- "Orphan count change" — no baseline established for what "normal" looks like
- "Lock timeout errors in logs" — no log parsing or alerting mechanism
- "Disk space decrease" — no automated monitoring

**Impact:** Warning signs become theater — listed but not actionable.

**Recommendation:** Either:
1. Integrate monitoring into health check hook (automated alerts)
2. Remove the section and replace with a single note: "Manual verification only — no automated monitoring implemented"

### [MEDIUM] Reference class forecasting lacks specificity (Step 3.5)

**Location:** Step 3.5 — Reference Class Forecasting

**Claim:** "1-2% failure rate for file-based session state in similar hooks over 6 months"

**Problem:** No citation to where this number comes from. Which hooks? What time period? How was failure defined and measured?

**Impact:** The base rate is used to justify "likely robust IF patterns are followed exactly" — but without evidence, this is speculation presented as analysis.

**Recommendation:** Cite specific hook instances and their failure history, or flag this as [UNVERIFIED ESTIMATE].

### [LOW] Cascade analysis uses directional arrows but no trace evidence

**Location:** Step 2.5 — Cascade Analysis

**Example:** T4 → P1 Cascade: "terminal_id format changes (env_ vs console_)" leads to "SessionStart writes to terminal_A file" leads to "SessionEnd reads from terminal_B file."

**Problem:** No reference to actual code where this mismatch occurs. The terminal_id format issue is a real historical bug (documented in `terminal_id_normalization_mismatch.md`), but this pre-mortem doesn't cite the specific code paths or the actual format variants.

**Recommendation:** Add inline citations: e.g., `terminal_id format: env_ vs console_ (see SessionStart.py:XX)`

---

## 2. Structural Issues

### [HIGH] Kill criteria (Step 0.7) are not connected to monitoring

**Location:** Step 0.7 — Kill Criteria

Five kill criteria are defined:
- KC1: >2 hours without progress
- KC2: >3 unrelated failures
- KC3: orphan false positive rate >5%
- KC4: atomic write fails >10%
- KC5: terminal isolation breaks

**Problem:** None of these kill criteria have corresponding monitoring or detection mechanisms. If KC3 ("orphan false positive rate >5%") were actually trackable, it would require:
1. A known-good list of wired hooks to compare against
2. A way to measure false positives in the health check output
3. A threshold comparison in the hook itself

As written, KC3 is unverifiable — and Step 3.8 confirms this by noting orphan classification is "PARTIAL."

**Recommendation:** Either wire kill criteria into actual monitoring, or explicitly mark them as "manual abort conditions" rather than automated safeguards.

### [HIGH] Step 3.8 "Operational Verification" admits most claims are unverified

**Location:** Step 3.8 — Operational Verification

The document explicitly states:
> "Gap: Most critical claims have NOT been empirically verified."

Yet Steps 4 and 5 produce risk scores and prioritized prevention actions as if the analysis were complete. This is success theater: the document performs analysis rigor but then admits in a single line that the evidence doesn't back the conclusions.

**Impact:** Future readers may cite risk ratings from this document without realizing they are based on speculation, not measurement.

**Recommendation:** Restructure so that risk ratings and prioritization only include items with verification status "CONFIRMED" or "PARTIAL." Items that are "NOT TESTED" should be listed separately as "Verification Required" and excluded from the priority ranking.

### [MEDIUM] Success theater detection (Step 3.6) is self-referential

**Location:** Step 3.6 — Success Theater Detection

The document identifies 4 vanity metrics but then uses the same unverified metrics to rate itself. For example:
- "98 orphans detected" — flagged as vanity metric, but no alternative metric proposed
- "Atomic writes implemented" — flagged as potentially incorrect, but no verification method given

**Impact:** The success theater section is descriptive critique without constructive resolution.

**Recommendation:** For each theater item, add: "Instead, measure: [specific observable]"

---

## 3. Completeness Gaps

### [MEDIUM] No rollback procedure for KC4/KC5 failures

**Location:** KC4, KC5 and PR4

KC4: "If atomic write fails >10% of sessions → fall back to synchronous writes"
KC5: "If terminal isolation breaks → immediate rollback"
PR4: "No rollback procedure for hook failures"

**Problem:** The rollback target is "synchronous writes" for KC4 and "immediate rollback" for KC5, but:
- No definition of what "synchronous writes" means in this context (temporary file without atomic rename? direct file write without temp?)
- No rollback procedure is documented — what files to restore, what state to clear
- PR4 is identified as a process gap but no remediation is proposed

**Impact:** If atomic writes or terminal isolation actually fail during a session, there is no documented recovery procedure.

**Recommendation:** Define rollback procedure explicitly: "On KC4 trigger: [procedure]"

### [MEDIUM] No mention of concurrency testing for multi-terminal scenarios

**Location:** P3 — "Single-terminal assumption"

The pre-mortem identifies P3 as a risk (score 6) but doesn't reference any existing concurrency tests or specify what multi-terminal testing would look like.

**Gap:** If the team wanted to verify P3 is resolved, there is no test plan for:
- Running two sessions simultaneously with the same terminal_id
- Verifying state files are isolated between terminals
- Verifying orphan detection accuracy across concurrent sessions

**Recommendation:** Add a "Concurrency Test Plan" section with specific test steps.

### [LOW] No fsync analysis for E1 (OS crash)

**Location:** T3 — "Missing fsync" and E1 — "OS crash during session end"

T3 flags "Missing fsync on session_start" and E1 flags OS crash causing torn writes. But:
- The document doesn't analyze whether `session_start.txt` specifically needs fsync
- The document doesn't reference the actual `session_start.txt` write code path
- The fix side-effect analysis (Step 1.5) mentions atomic writes but not durability via fsync

**Recommendation:** Verify whether `session_start.txt` writes are buffered and whether `os.fsync()` is needed for crash safety.

### [LOW] People/Process failure modes lack process-specific mitigations

**Location:** PR1, PR2, PR3, PR4

The process failures (PR1-PR4) are identified but have no specific remediation beyond the generic "write integration tests" (PR1) and "add to CI" (PR3). For a pre-mortem targeting a solo-developer environment:

**Missing considerations:**
- How does a solo developer add orphan detection to CI without a CI pipeline?
- What's the minimal viable integration test for hook dispatch (PR1)?
- Should TLDR verification be manual or automated for a one-person workflow?

**Recommendation:** Tailor process recommendations to solo-developer constraints rather than borrowing enterprise CI/CD language.

---

## 4. Positive Findings

The following aspects of the pre-mortem are well-executed:

- **Kill criteria are specific and measurable** (KC3 threshold is 5%, KC4 is 10%) — these are the document's strongest elements when compared against actual monitoring
- **Dependency cascade tracing is thorough** — T4 as keystone risk is correctly identified and the cascade logic is traceable
- **Risk matrix with explicit scores** provides a usable output for prioritization discussions
- **Reference class forecasting cites existing implementations** (SessionEnd_cleanup, SessionStart_hook_health_check, evidence_store) — this is good practice

---

## Severity Summary

| # | Severity | Category | Finding | Location |
|---|----------|----------|---------|----------|
| 1 | HIGH | Completeness | Most critical claims NOT empirically verified — yet risk ratings treat them as fact | Step 3.8, Step 4 |
| 2 | HIGH | Maintainability | No test corpus for regex-based orphan detection (T6) | Step 2, T6 |
| 3 | HIGH | Structural | Kill criteria (KC1-KC5) have no monitoring/automation path | Step 0.7 |
| 4 | MEDIUM | Maintainability | Warning sign monitoring has no implementation path | Step 6 |
| 5 | MEDIUM | Maintainability | Reference class forecasting "1-2% base rate" is uncited | Step 3.5 |
| 6 | MEDIUM | Structural | Success theater detection is self-referential without resolution | Step 3.6 |
| 7 | MEDIUM | Completeness | No rollback procedure for KC4/KC5 failures | KC4, KC5, PR4 |
| 8 | MEDIUM | Completeness | No concurrency test plan for multi-terminal scenarios | P3 |
| 9 | LOW | Maintainability | Cascade analysis lacks code-path citations | Step 2.5 |
| 10 | LOW | Completeness | No fsync analysis for session_start.txt durability | T3, E1 |
| 11 | LOW | Completeness | Process recommendations not tailored to solo-developer constraints | PR1-PR4 |

---

## Priority Recommendations

**Before this pre-mortem can be used as a reliable planning artifact:**

1. **Verify or discard T6** — build a test corpus for orphan hook regex detection, or explicitly remove T6 from the risk matrix with a note that the regex gap is unconfirmed
2. **Separate verified from unverified risks** — restructure the risk matrix so only empirically verified items appear in prioritization; move "NOT TESTED" items to a separate "Verification Required" list
3. **Define rollback procedures** for KC4 and KC5 — what exactly does "fall back to synchronous writes" mean, and what is the "immediate rollback" procedure for terminal isolation failures?
4. **Add monitoring implementation** for warning signs or explicitly demote Step 6 from a monitoring plan to a "manual check list"
