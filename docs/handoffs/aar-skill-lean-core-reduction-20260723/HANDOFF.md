---
thread_id: d1e4b7f3-9a2c-4d8e-b5f6-3c7a1e9d2b08
parent_handoff_path: none
current_session_id: 019f76e8-eae4-7cc1-9c70-2fe3729812f1
current_terminal_id: console_019f76e8
produced_at: 2026-07-23T16:00:00Z
status: complete
handoff_type: investigation
accurate_as_of_head: (uncommitted — ~/.grok changes are not tracked)
---

## Objective

Reduce AAR SKILL.md from 838 lines to ≤600 lines (the test-enforced limit)
by extracting detail into reference files, restoring the lean-hybrid design
where SKILL.md is the always-loaded routing core and details live in
`references/*.md` loaded on trigger.

## Status

COMPLETE — the extraction plan was implemented and verified in the current
working tree.

## Resolution (2026-07-26)

The AAR core was reduced to **555 lines** by extracting the detailed
run-directory/preprocessing procedure, report format/accounting contract, and
wiki-promotion procedure into registered reference files:

- `C:\Users\brsth\.grok\skills\aar\references\run-directory-and-preprocessing.md`
- `C:\Users\brsth\.grok\skills\aar\references\report-format.md`
- `C:\Users\brsth\.grok\skills\aar\references\wiki-promotion.md`

`__lib/reference_loader.py` now maps them to explicit triggers:
`current_session_aar`, `report_generation_required`, and
`headline_lesson_present`. The core retains the routing contract and concise
invariants; deterministic lifecycle work remains in the AAR helper modules.

Verification:

- `python -m pytest -q` in the AAR skill: **569 passed**
- `python -m pytest -q` in the close skill: **293 passed**
- `python -m py_compile __lib/reference_loader.py __lib/completion_receipt.py`: pass
- `git diff --check`: pass in both skill repositories

## Producing context

- Date: 2026-07-23
- Session: 019f76e8-eae4-7cc1-9c70-2fe3729812f1
- Origin: while adding question 11 (uncaptured knowledge audit), the test
  `test_default_effective_instruction_size_is_reduced` failed because
  SKILL.md is 838 lines vs the 600-line limit. This is pre-existing debt
  from accumulation over many sessions, not caused by today's ~18-line addition.
- The operator asked "why defer fixing the debt?" and there was no good answer.

## Problem

The AAR skill has a **lean-hybrid architecture** (Phase 1): SKILL.md is the
always-loaded core; details live in `references/*.md` loaded only when triggers
fire. The test `test_default_effective_instruction_size_is_reduced` enforces
≤600 lines as the budget for the always-loaded core.

Current state: **838 lines — 238 lines over budget.**

### Section-by-section breakdown

| Lines | Section | Extraction candidate? |
|---|---|---|
| 153 | Step 0 — Run directory + evidence resolution | **YES** — Python/PowerShell boilerplate for running the preprocessor is pure implementation detail. Replace with a 5-line summary + pointer to a reference. |
| 80 | Step 0.5 — Deterministic preprocessing | **YES** — packet artifact list, source authority hierarchy, failure handling table. All detail that can live in a reference. Keep 3-line summary + trigger. |
| 79 | Phase 9.5 — Automatic wiki promotion | **YES** — full procedure (retirement check, write concept, run pipeline, report). Can be a reference loaded on a trigger like `headline_lesson_present`. |
| 80 | §triggers | **PARTIAL** — trigger list stays in core (loader reads it). But the full-mode promotion list and the "weak detector signal is not a trigger" paragraph can be compressed. |
| 45 | Phase 9 — Report | **PARTIAL** — the report format template (lines 579-680) is large. The §Findings example and format spec can go to a reference. |
| 42 | Rules (always loaded) | **KEEP** — these are always-loaded invariants. But rules 3a/3b (secret exposure triage + containment) are 20 lines of detail that can move to `operational-safety.md` reference (already exists). |
| 43 | Phase 4 — Pattern synthesis + layered root-cause | **PARTIAL** — double-loop analysis (15 lines) can go to `epistemic-calibration.md` reference. |
| 26 | Phase 5 — Value accounting | **KEEP** — compact, core |
| 27 | Phase 1 — Contract reconstruction | **KEEP** — compact, core |
| 21 | Phase 2 — Typed episode ledger | **KEEP** — compact, core |
| 15 | Phase 3 — Decision history | **KEEP** — compact, core |
| 16 | Phase 6 — Opportunity discovery | **KEEP** |
| 12 | Phase 7 — Continual-improvement governance | **KEEP** |
| 17 | Phase 8 — Routing | **KEEP** |
| 14 | Source-fidelity rules | **KEEP** |
| 13 | Windows/PowerShell isolation | **KEEP** |
| 10 | Examples | **KEEP** |

### Extraction plan (238 lines to cut)

| Priority | What | Lines saved | Where it goes |
|---|---|---|---|
| 1 | Step 0 (preprocessor boilerplate) | ~120 | New `references/run-directory-and-preprocessing.md` |
| 2 | Phase 9.5 (wiki promotion procedure) | ~65 | New `references/wiki-promotion.md`, trigger: `headline_lesson_present` |
| 3 | Rules 3a/3b (secret exposure detail) | ~20 | Append to existing `references/operational-safety.md` |
| 4 | Report format template (lines 579-680) | ~40 | New `references/report-format.md` — SKILL.md keeps section list, reference has the template |

**Total: ~245 lines extracted → SKILL.md drops to ~593 lines.** Under the 600 limit.

## Files to change

| File | Change |
|---|---|
| `~/.grok/skills/aar/SKILL.md` | Extract detail, replace with summaries + pointers |
| `~/.grok/skills/aar/references/run-directory-and-preprocessing.md` | **New** — Step 0 + 0.5 detail |
| `~/.grok/skills/aar/references/wiki-promotion.md` | **New** — Phase 9.5 detail |
| `~/.grok/skills/aar/references/report-format.md` | **New** — Phase 9 report template |
| `~/.grok/skills/aar/references/operational-safety.md` | Append rules 3a/3b detail |
| `~/.grok/skills/aar/__lib/reference_loader.py` | Add new ReferenceSpecs + triggers |
| `~/.grok/skills/aar/__lib/output_validator.py` | May need to accept reference-loaded report format |

## Constraints

1. **Always-loaded content must stay in SKILL.md:** the §ten-questions (all 11), the trigger list, the rules (compressed), the phase routing tables, the §triggers gate.
2. **Test must pass:** `test_default_effective_instruction_size_is_reduced` checks ≤600 lines.
3. **No content loss:** extracted content must be reachable via references. SKILL.md summaries must be sufficient for the default lean invocation.
4. **reference_loader.py must stay in sync:** new references get new ReferenceSpecs + triggers.
5. **output_validator.py:** if report format validation references the template, it may need to know where the template moved.

## Risks

- **Trigger wiring for new references:** wiki-promotion and report-format need triggers. If no detector emits them, they never load and the content is lost at runtime. Need to add trigger conditions or make them always-loaded (defeats the purpose).
- **Breaking the preprocessor path:** Step 0's Python boilerplate is load-bearing for the `aar_step0.py` pattern. Moving it to a reference is fine for documentation but the pattern must stay discoverable.
- **Report-format validation:** output_validator.py currently has REQUIRED_SECTIONS. The format template is what tells the LLM what sections to emit. If it's not always-loaded, the LLM may not produce the right sections.

## Read-first list

1. `~/.grok/skills/aar/SKILL.md` — the file to shrink (838 lines)
2. `~/.grok/skills/aar/__lib/reference_loader.py` — where to register new references
3. `~/.grok/skills/aar/__lib/output_validator.py` — REQUIRED_SECTIONS + report validation
4. `~/.grok/skills/aar/tests/test_reference_loader.py` — the tests that must pass

## Acceptance criteria

1. `python -m pytest tests/test_reference_loader.py -v` — all 15 tests pass (including line-count)
2. `python -m pytest tests/ -v` — full suite passes (563 tests)
3. No content lost: every extracted section is reachable via a reference file
4. reference_loader.py has entries for all new references
5. SKILL.md is ≤600 lines

## Suggested next invocation

```
Reduce AAR SKILL.md from 838 to ≤600 lines by extracting Step 0/0.5, Phase 9.5,
rules 3a/3b, and the report template into reference files. Read the handoff at
P:/docs/handoffs/aar-skill-lean-core-reduction-20260723/HANDOFF.md for the
extraction plan with line counts.
```

## Other outstanding streams

- **AAR uncaptured-knowledge audit** — DONE this session. Handoff at
  `aar-uncaptured-knowledge-audit-20260723`. Adds question 11 + conditional
  report section + cross-model-audit trigger + reference file.
