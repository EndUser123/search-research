---
title: "Cross-workspace pyright blind spot: files outside P: escape /check deterministic pre-check"
created: 2026-07-29
source: session-019fa94d (KSC _mark_row incident)
tags: [check, pyright, scope, cross-workspace, dead-code, missing-definition, gap]
host: grok
agent: grok
verification: observed
cognitive_load: 2
summary: >
  /check Step 0.9 runs pyright on changed .py files, but only on files
  tracked in the evidence packet's scope_files — which derive from P:\
  workspace file-edit tracking. Files outside P:\ (e.g., D:\.code\)
  escape the deterministic pre-check entirely. A method definition
  (_mark_row) accidentally removed during batch edits on KSC at
  D:\.code\ was not caught by pyright because pyright was never run
  on that file. The bug surfaced at runtime when the user ran the app.
relations:
  - target: wiki/concepts/textual-tui-pitfall-checklist.md
    type: complements
  - target: wiki/concepts/io-safety-review-lens.md
    type: related
  - target: wiki/concepts/dead-code-detection-workflow.md
    type: extends
---

# Cross-workspace pyright blind spot: files outside P: escape /check

## Decision context

During session 019fa94d, the Keep-Smaller-Copy TUI app at
`D:\.code\Keep-Smaller-Copy\app.py` went through 6 reviews and multiple
batch-fix waves. During one of the edits, the `_mark_row` method
definition was accidentally removed from the class — but its 5 callers
in `_do_process_worker` remained. The app crashed at runtime when the
user ran a Copy operation: `'KeepSmallerCopyApp' object has no attribute '_mark_row'`.

None of the 6 `/review` passes or 6 `/check` passes caught it. The
question: which skill SHOULD have caught it, and why didn't it?

## What each tool could and couldn't do

| Tool | Would catch `_mark_row` missing? | Why / why not |
|------|----------------------------------|---------------|
| **pyright** (in `/check` Step 0.9) | ✅ Yes — flags undefined attributes on `self` | But wasn't run on `D:\.code\` because scope_files derive from `P:\` transcript tracking |
| **vulture** (in `/check` Step 0.9) | ❌ No | Vulture finds *defined-but-unused* code. `_mark_row` was *called-but-undefined* — the inverse |
| **ruff F-rules** | ❌ No | Ruff doesn't do cross-method attribute analysis on `self` |
| **`/review` correctness lens** | ✅ Could — if reviewer traces method definitions | 6 reviews focused on the *changes being made*, not on whether prior edits accidentally removed definitions |
| **Runtime test** | ✅ Yes — if copy/move path exercised | No test exercised the copy/move I/O loop (the `ksc-atomic-copy-test` handoff addresses this) |

## Root cause: scope_files only tracks P:\

The `/check` evidence packet's `scope_files` bucket is built by
`preprocessor.py` from the transcript's tool-call records. The
`search_replace` tool records `target_path` — which for KSC was
`D:/.code/Keep-Smaller-Copy/app.py`. So the path WAS in scope_files.

The gap is in Step 0.9 itself: the PowerShell code extracts `scopeFiles`
and runs `pyright --outputjson @pyFiles`. If `scopeFiles` included
the `D:\.code\` path, pyright should have run on it. The likely failure:
the evidence packet's `scope_files` didn't include the KSC path because
it was filtered or the preprocessor missed it, OR pyright ran but the
output wasn't surfaced because the path didn't match the `P:\` prefix
assumption in downstream processing.

[INFERENCE]: The scope_files tracking may have included the path, but
pyright may not have flagged it if the method was removed in the same
edit batch that the `/check` was verifying — making the "last known good"
state already broken.

## What this means for our workspace

1. **`/check` Step 0.9 must explicitly run pyright on ALL changed `.py`
   files** regardless of whether they're under `P:\` or not. The
   preprocessor already tracks non-P:\ paths (KSC at `D:\.code\` appears
   in file_edits). The gap is in Step 0.9's extraction logic.

2. **vulture can't catch missing definitions** — only unused ones. This
   is a vulture limitation, not a bug in our integration. The pitfall
   checklist should note this.

3. **Runtime tests are the last line of defense** for "called but
   undefined" bugs. The `ksc-atomic-copy-test` handoff is critical.

4. **Batch atomic-edit scripts are high-risk** for accidental method
   removal. The 24-fix script and R5 fix both used `str.replace` on
   large blocks. A single off-by-one in the old_string match could
   swallow an adjacent method definition.

## Falsifier

If `/check` Step 0.9 is verified to run pyright on `D:\.code\Keep-Smaller-Copy\app.py`
and pyright reports `_mark_row` as undefined BEFORE the runtime crash,
then the blind spot is elsewhere (e.g., the pyright output wasn't
surfaced to the operator or verifier). If pyright doesn't report it
even when run on the correct file, then pyright itself has a blind spot
for dynamically-dispatched methods on Textual App subclasses.

## Receipts

- `D:/.code/Keep-Smaller-Copy/app.py`: `_mark_row` called at 5 sites
  (lines ~1154, ~1187, ~1192, ~1197, ~1208) but `def _mark_row` not
  found — confirmed via grep after user reported the error.
- `/check` Step 0.9 contract: `P:/.grok/skills/check/SKILL.md` lines
  ~180-230 — runs pyright on `$pyFiles` from `scopeFiles`.
- The fix: re-added `_mark_row` method (this session, last turn).

## Related

- [[textual-tui-pitfall-checklist]] — broader patterns
- [[dead-code-detection-workflow]] — vulture scope (defined-but-unused only)
- [[io-safety-review-lens]] — same principle: the right lens must be applied
