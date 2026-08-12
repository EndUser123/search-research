---
title: "Ship-py check phase produces false positives from 20B model dispatch"
session_id: 019ff5f3-9a28-7db1-89c4-581d67f75db3
status: OPEN
produced_at: 2026-08-12
last_updated_at: 2026-08-12T15:30:00Z
assignee: unassigned
chronicity: chronic
---

# Ship-py check phase blocks on fabricated syntax errors from 20B model

## Problem

The `/ship-py` check phase dispatches `nim-openai-gpt-oss-20b` for session-grounded
verification. This model fabricates syntax errors that don't exist, producing
false-positive FAIL verdicts that block the pipeline. This is the **same
documented defect** that caused the trace phase to be downgraded from BLOCK
to WARN (ship-py SKILL.md, "Trace downgrade design note", 2026-08-12).

## Evidence (session 019ff5f3, 2026-08-12)

The check phase FAILED with this concern:
> "In cluster.py the diff ends with an incomplete import line 'from s' which
> would raise a syntax error during import"

Verified mechanically that this is false:
- `py_compile.compile(cluster.py, doraise=True)` → OK (compiles cleanly)
- All 4 nlm-bulk-ingest scripts compile
- 22 regression tests pass (13 bug-fix tests + 9 extract tests)
- Live end-to-end ingest of 1,019 @moondevonyt videos succeeded (1019/1019 sources)

The model hallucinated a syntax error on three consecutive run-all attempts,
each time claiming a different non-existent defect ("missing import time",
"truncated split_oversized", "incomplete 'from s' line").

## Root cause

The check phase dispatches the same unreliable 20B model that trace was
downgraded for. The fix applied to trace (BLOCK → WARN, requiring mechanical
verification to confirm) was not applied to check.

## Fix needed

Apply the trace-phase downgrade pattern to the check phase:

1. **Option A (narrow):** downgrade check-phase model-dispatched logic findings
   from FAIL to WARN, requiring mechanical verification (`py_compile`,
   test execution) to confirm a real defect before blocking.
2. **Option B (structural):** route check-phase dispatch through a stronger
   model (the `reasoning` lane, per the trace fix), not the `critic` lane
   that currently selects the 20B model.
3. **Option C (verification-grounded):** for any "syntax error" or "import
   error" claim, the orchestrator runs `py_compile` on the cited file before
   accepting the finding. If compilation passes, the finding is auto-rejected.

Option C is the most robust — it catches the specific failure mode (fabricated
syntax errors) mechanically, regardless of which model produced them.

## Files to change

- `C:\Users\brsth\.grok\skills\ship-py\__lib\check_dispatch.py` — the dispatch
  and parse logic for the check phase
- `C:\Users\brsth\.grok\skills\ship-py\__lib\ship_orchestrator.py` — the
  check phase runner (may need the verification gate)
- `C:\Users\brsth\.grok\skills\ship-py\SKILL.md` — document the check-phase
  false-positive pattern (parallel to the trace downgrade note)

## Acceptance criteria

- [ ] `py_compile` on cited file runs before accepting any syntax-error finding
- [ ] False-positive syntax errors are auto-rejected, not blocking
- [ ] Test case: a clean file with a fabricated "syntax error" finding does
      not block the pipeline
- [ ] SKILL.md documents the check-phase downgrade
