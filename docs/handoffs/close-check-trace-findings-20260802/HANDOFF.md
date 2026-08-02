---
title: close-check TRACE REPORT findings — 7 logic errors (4 HIGH, 3 MEDIUM)
thread_id: close-check-trace-findings-20260802
created: 2026-08-02
status: OPEN — implementation deferred
priority: HIGH (H1 affects correctness of session readiness verdict)
current_session_id: 019fb933-040b-7720-a257-e364f5df726f
last_updated_by: grok
last_updated_at: 2026-08-02T00:30:00Z
---

# Handoff: close-check TRACE REPORT findings

## Context

close-check-2's /trace subagent produced a full TRACE REPORT with 7 logic errors in close-check.rhai. These are real code-quality bugs discovered by manual trace-through verification. The trace subagent that failed silently in run 1 produced this report in run 2.

## Findings

### HIGH severity

**[H1] Silent total sweep failure → false READY verdict**
- `close-check.rhai:247` + `:265-282` + `:306-311`
- When all 3 sweep agents return `success=false`, every counter stays at 0. `session_fail_count=0` and `fail_count=0` → verdict becomes "READY TO CLOSE". The workflow reports success while having detected nothing.
- Fix: Add a fail-closed guard before verdict: count successful agents; if fewer than jobs.len(), set verdict to BLOCKED.

**[H2] Cross-file contradiction on nim-* model safety** — ALREADY FIXED
- Was: command wrapper vs workflow comments disagreed on nim-* safety.
- Status: resolved by commits `d323b03` + `2572c88` + registry updates. Can close this finding.

**[H3] FREE_A / FREE_C default collision violates provider-diversity intent**
- `close-check.rhai:65-67`
- When args are missing, FREE_A and FREE_C both default to "minimax-m3". Two simultaneous spawns hit the same provider.
- Fix: Change FREE_C default to a third distinct provider, or use a literal provider-diverse trio.

**[H4] Verdict count can exceed reported findings count**
- `close-check.rhai:270-282` vs `:285-302`
- A check with status="fail" and empty findings increments fail_count but adds nothing to any findings list. Verdict says "N findings" but report sections show 0.
- Fix: Push check name into unclassified_findings when status != "pass" and findings is empty.

### MEDIUM severity

**[M1] Phase 2 silent subagent drop on sweep agent failure**
- `close-check.rhai:265-304`
- When agent returns success=true but output.checks is missing/null, no count, no classification, no error logged.
- Fix: Add diagnostic logging when r.success is true but r.output.checks is missing.

**[M2] report_path captured once, file overwritten twice**
- `close-check.rhai:372` captures `p`, then `:540` and `:626` overwrite the file without updating `p`.
- The `complete()` call returns the path from the FIRST write, which may be stale content.
- Fix: Re-assign `p` on every write, or build the complete report and write once at the end.

**[M3] lifecycle-skill-coverage duplicates critical-code-trace semantics**
- CHECK 3 (lifecycle-skill-coverage) and CHECK 4 (critical-code-trace) both track /trace.
- Can produce divergent statuses: CHECK 3 pass (/trace ran), CHECK 4 fail (critical code not traced).
- Fix: Remove /trace from CHECK 3's skill list; let CHECK 4 own it.

## Acceptance criteria

- [ ] H1: fail-closed guard prevents false READY when all agents fail
- [ ] H3: FREE_C default is a third distinct provider
- [ ] H4: checks with empty findings still appear in report
- [ ] M1: failed-but-success agents log a diagnostic
- [ ] M2: report_path reflects final write
- [ ] M3: /trace removed from CHECK 3, owned by CHECK 4
- [ ] H2: already fixed — no action needed
- [ ] All changes smoke-checked via workflow validate_only

## Read-first list

- `C:\Users\brsth\.grok\workflows\close-check.rhai` — the workflow with all 7 bugs
- `C:\Users\brsth\.grok\commands\close-check.md` — the command wrapper
- close-check-2 report (in workflow scratch/pre-close-report.md) — full TRACE REPORT with line numbers
