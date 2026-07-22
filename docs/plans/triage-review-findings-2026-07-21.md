# Plan: Triage /review findings from session 2026-07-21

**Date:** 2026-07-21
**Author:** Session 019f8523-d9f7-73c3-9e25-9e6c417cfccd (post /check + /review)
**Source:** `P:/.artifacts/console_ec84a662-c26f-40e0-b5f0-3b1d/grok-review/session-20260721/20260721-093508/FINDINGS.md`
**Verdict prior to this plan:** `pass_with_limitations` (session work complete; pre-existing issues surfaced)

---

## Goal

Decide, for each finding surfaced by `/review` of session 2026-07-21, whether to fix now / defer / accept as legacy. Produce a sequenced action list that future sessions can pick up.

**Success criteria:**
1. Every finding has a documented disposition (fix-now, fix-later, accept-as-legacy, defer-until-needed).
2. The fix-now items form a single coherent work item with file:line anchors.
3. The user has approved the disposition set (this plan is the user-facing artifact).

---

## Background

The session produced 2 new CLIs (`verify_handoff.py`, `migrate_handoff.py`), edited 2 SKILL.md files (`tp/SKILL.md`, `handoff/SKILL.md`), fixed 6 handoff frontmatter files, and added a Hard Constraint #7 (drift discipline) to `/handoff/SKILL.md`.

`/review` ran 2 specialist agents (correctness, integrity) and surfaced 12 findings. The session's auto-fix-and-reverify cycle addressed 4 critical session-introduced bugs (B-1, B-2, B-3, B-4). The remaining 8 findings are either pre-existing or lower-priority suggestions.

`list_handoffs.py --head 13f19d20c70f...` now reports **0 HEAD-drift, 0 no-head-field**. The drift problem the session was scoped to address is fixed.

---

## Findings + recommended dispositions

| ID | Severity | Title | Disposition |
|---|---|---|---|
| **B-1** | bug | migrate_handoff.py silent fail when no handoff_type anchor | ✅ FIXED (cycle 1) |
| **B-2** | bug | verify_handoff.py --update corrupts handoff with whitespace-padded SHA | ✅ FIXED (cycle 1) |
| **B-3** | bug | verify_handoff.py --update had no provenance recording | ✅ FIXED (cycle 2) |
| **B-4** | bug | Both CLIs used Path.write_text without atomic rename | ✅ FIXED (cycle 2) |
| **I-1** | critical | Hard Constraint #7 (Drift discipline) is advisory, not enforced | **FIX NOW** — design a SessionStart hook |
| **G-1** | gap | design-skill's 13 body sections don't match BODY_REQUIRED_SECTIONS | **FIX NOW** — rename sections |
| **G-2** | gap | 16-vs-15 mandatory fields doc/code drift | **FIX NOW** — update doc |
| **G-3** | gap | validate_assignment_fields doesn't check `assigned_at >= produced_at` | **FIX NOW** — add check |
| **S-1** | suggestion | Regex over-matches backticked code identifiers | **FIX NOW** (quick polish) |
| **S-2** | suggestion | Bare-path regex can't match leading ~ at start-of-string | **DEFER** — zero impact in practice |
| **S-3** | suggestion | CITATION_HEADINGS substring check false-positives on Unverified facts | **DEFER** — string substitution works around it |
| **S-4** | suggestion | tp/SKILL.md Step 1.5 numbering is misleading | **FIX NOW** (quick polish) |

**Summary:** 8 fix-now / 1 fixed-already / 2 defer / 0 accept-as-legacy.

---

## Implementation approach

Sequenced by dependency: validator changes first, then CLIs, then docs, then skill contract, then design.

### Stage 1: Validator fix (G-3) — ~10 minutes

**Files:**
- `P:\.grok\skills\handoff\__lib\validators.py` — extend `validate_assignment_fields` (line 574-625) to check `assigned_at >= produced_at` (warn on violation, not error — assignment by past-self shouldn't fail validation, just flag it).

**Verification:** `python -m pytest tests/ -q` — should still pass; existing tests don't exercise this path. Add 1 new test in `tests/test_validator.py` for the timestamp ordering check.

**Falsifier:** if a future handoff gets a `WARN` on legitimate claim-after-production scenarios, the check is too strict; downgrade to advisory.

### Stage 2: Quick polish (S-1, S-4) — ~10 minutes

**Files:**
- `P:\.grok\skills\handoff\__lib\verify_handoff.py` — tighten backticked-path regex to require `/` or file extension.
- `C:\Users\brsth\.grok\skills\tp\SKILL.md` — rename "Step 1.5" → "Step 2.5".

**Verification:** `python -m pytest tests/ -q`; manual smoke test on a handoff with backticked code identifiers.

### Stage 3: Doc/code drift (G-2) — ~5 minutes

**Files:**
- `P:\.grok\skills\handoff\references\core-fields.md` (line 3, 37) — change "16 mandatory fields" → "15 mandatory fields".
- `P:\.grok\skills\handoff\SKILL.md` (3 occurrences) — same change.

**Verification:** grep `"16 mandatory"` returns 0 hits.

### Stage 4: design-skill body sections (G-1) — ~15 minutes

**Files:**
- `P:\docs\handoffs\design-skill-runtime-foundation-20260720\HANDOFF.md` — rename 8 body section headings to match `BODY_REQUIRED_SECTIONS`. Mapping:
  - "Goal (one sentence)" → "Objective (one sentence)"
  - "Last user message (verbatim)" → already correct
  - "What shipped (verified on disk)" → "Current state"
  - "What's pending" → "Open decisions"
  - "Cross-reference couplings (what depends on what)" → already correct
  - "Key evidence" → "Verified facts"
  - "Recommended next actions (priority order)" → "Suggested next invocation"
  - "Open questions for next session" → fold into "Open decisions"
  - "Other outstanding streams" → already correct (optional)

**Verification:** `cd P:\.grok\skills\handoff && python __lib/validate_handoff.py P:/docs/handoffs/design-skill-runtime-foundation-20260720/HANDOFF.md` — should report ≤1 error (the pre-existing thread_id UUID shape).

### Stage 5: Drift enforcement design (I-1) — ~30 minutes via `/design`

This is a real architectural design. Delegate to `/design` skill.

**Brief for /design:**
> Design a Grok-native SessionStart hook that surfaces drift across all open handoffs at session start. The hook should call `list_handoffs.py --head <sha>` (already exists at `P:/.grok\skills\handoff\__lib\list_handoffs.py`), surface the `head:DRIFT` and `head:?` rows prominently, and suggest the remediation command (`/handoff verify <path>`). The hook must coexist with the existing `qmd_patches_session_start.py` hook that runs at SessionStart. Output: a design doc with PR plan + key decisions.

**Verification:** design doc produced; PR plan actionable; key decisions documented.

**Then:** Stage 6 = implementation of the design via `/go`.

### Stage 6: Drift enforcement implementation — ~30 minutes via `/go`

**Inputs:** design doc from Stage 5.
**Files:** new hook script + hook JSON registration + SessionStart manifest update.
**Verification:** simulate a drifted handoff in a test session; observe the hook surfaces it.

---

## Key decisions and rejected alternatives

### Decision: 4 critical bugs (B-1 to B-4) are FIXED, not "defer"

**Rejected alternative:** "Defer B-1 to B-4 to a follow-up session."
**Why rejected:** all 4 were caught by /review in cycle 1-2; they would have shipped to users as silent corruption. Two-cycle fix budget was used, leaving one cycle in reserve. Deferring real bugs to preserve the budget would be a misuse of the budget.

### Decision: G-1 (design-skill body sections) is FIX NOW, not "accept as legacy"

**Rejected alternative:** "Mark design-skill as legacy v0.1; document the exception."
**Why rejected:** the handoff is still actively referenced (cited as parent of proposal-grounding-monitor). Renaming 8 sections is mechanical and verifiable. Marking it as legacy would propagate the schema gap and confuse future sessions reading either the doc or the validator output. The fix is cheap.

### Decision: S-2 and S-3 are DEFER, not "fix now"

**Rejected alternative:** "Fix all 4 suggestions in a polish pass."
**Why rejected:** S-2 has zero impact in practice (handoffs use backticked form, not bare-path-with-leading-~). S-3 false-positives are worked around by changing the section heading to "Verified facts" instead of "Unverified facts" (which no production handoff does). Fixing them would add complexity without proportional benefit. Stage 2 includes only S-1 and S-4.

### Decision: I-1 (drift enforcement) gets `/design`, not inline

**Rejected alternative:** "Write the SessionStart hook inline as part of this session."
**Why rejected:** the design question (when does it fire? what does it surface? what action does it suggest? how does it interact with `qmd_patches_session_start.py`?) is non-trivial and benefits from the full /design write-review-revise loop. Designing inline would produce a worse artifact and skip the critical-friend review.

---

## Risks and mitigations

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Stage 4 (section renames) loses cross-references | Low | Medium | Use `git grep` after rename to verify no other file references the old heading text |
| Stage 5/6 (drift hook) interferes with existing SessionStart hook | Medium | High | Stage 5 design MUST examine `qmd_patches_session_start.py` and propose coexistence; Stage 6 implementation MUST smoke-test both hooks running together |
| Stage 3 (doc fix) misses an occurrence | Low | Low | `grep -r "16 mandatory" P:\.grok\skills\handoff` after edit; should return 0 |
| New validator check (G-3) breaks existing tests | Low | Medium | Stage 1 adds the check as a WARN, not an error; existing tests assert error/warn counts and may need adjustment |
| S-1 regex tightening breaks existing `verify` invocations | Medium | Low | Test on a real handoff with backticked code identifiers before shipping; revert if any legit path stops matching |

---

## Verification (overall)

After Stages 1-4 complete (estimated ~45 min), verify the session work is fully complete:

1. `cd P:\.grok\skills\handoff && python -m pytest tests/ -q` — all tests pass.
2. `python __lib/list_handoffs.py --head 13f19d20...` — 0 drift, 0 no-head-field.
3. `python __lib/validate_handoff.py <each-handoff>` — each handoff reports ≤1 error (the pre-existing thread_id UUID shape).
4. `python __lib/verify_handoff.py <each-handoff>` — exits 0 for all handoffs (drift is current).
5. `grep -r "16 mandatory" P:\.grok\skills\handoff` — 0 hits (G-2 fixed).

After Stages 5-6 complete (~60 min more), drift enforcement becomes structural.

---

## Recommended execution order

1. Stage 1 (G-3 validator) — 10 min
2. Stage 2 (S-1, S-4 polish) — 10 min
3. Stage 3 (G-2 doc fix) — 5 min
4. Stage 4 (G-1 section renames) — 15 min
5. Stage 5 (/design drift hook) — 30 min
6. Stage 6 (/go implement drift hook) — 30 min

**Total:** ~100 minutes across 1-2 sessions.

---

## Open questions for the user

1. **Stage 1 (G-3) warning vs error:** should `assigned_at < produced_at` be a WARN (advisory) or an ERROR (blocking)? My recommendation is WARN (matches existing validator severity conventions for soft violations). Confirm or override.

2. **Stage 5 design scope:** should the SessionStart drift hook also surface missing `source_transcript` fields (i.e., handoffs that haven't been migrated to v0.1.1), or only `head:DRIFT` and `head:?` rows? My recommendation is only drift rows; source_transcript gaps are a separate concern (Stage 4 of the design-skill migration).

3. **Stage 6 deployment timing:** ship the drift hook immediately after design, or wait for ≥1 week of "natural usage" to validate the design? My recommendation is ship immediately (fail-open by default; observable via telemetry; can roll back).

---

## Self-check

- [x] Goal stated in one sentence.
- [x] Implementation approach is per-decision, sequenced by dependency.
- [x] Files to be modified are named with paths.
- [x] Key decisions include rejected alternatives with reasoning.
- [x] Verification steps are concrete (commands + expected output).
- [x] Risks named with mitigation per risk.
- [x] 30-second read verifies the plan is internally coherent.

Plan ready for user approval. After approval:
- Execute Stage 1-4 directly (no skill needed; these are localized fixes).
- Run `/design` for Stage 5 (drift hook design).
- Run `/go` for Stage 6 (drift hook implementation).