---
thread_id: review-relay-improvements-impl-20260809
parent_handoff_path: none
current_session_id: 019fe673-8b5c-7ee0-a22e-f1765ae9860b
parent_session: none
current_terminal_id: grok
produced_at: 2026-08-09T14:00:00Z
last_updated_by: 019fe673-8b5c-7ee0-a22e-f1765ae9860b
last_updated_at: 2026-08-09T14:00:00Z
status: open
handoff_type: implementation
accurate_as_of_head: 5dc6597
---

# Review-relay improvements implementation (15-unit plan, 4 phases)

## Objective

Implement the three architectural improvements to the review-relay system designed in `/design` run b1abe493 (2026-08-09). All three preserve the dumb-pipe invariant (0 LoC in `src/review-relay.mjs`) per ADR-011.

## Scope bounds

- **In scope:** 15 implementation units across 4 phases
- **Out of scope:** smart-pipe migration (only fires after 30-day production bottleneck per ADR-011)
- **Authority docs:**
  - Design: `P:/docs/design/review-relay-improvements-b1abe493/grok-design-doc-b1abe493.md` (585 lines, 77KB)
  - ADR: `P:/docs/adrs/ADR-011-review-relay-dumb-pipe-invariant.md`
  - Wiki concept: `P:/.data/wiki/concepts/review-relay-improvements-stable-key-lease-calibration-convergence-detection.md` (already-implemented context)
  - Source: `P:/packages/codex-external-delegation/src/review-relay.mjs` (1522 lines, NOT MODIFIED)

## Status

**OPEN - implementation-ready.** Design loop complete (reviewer PROCEED, critical friend PROCEED round 2). ADR-011 committed (`5dc6597`). All premise-verification gaps resolved (premise #12 confirmed: `allowed_writes` at review-relay.mjs:964 includes `turns/**`, so partners CAN write `findings.jsonl`).

## Producing context

- Date: 2026-08-09
- Session: `019fe673-8b5c-7ee0-a22e-f1765ae9860b`
- Trigger: `/design review-relay-improvements` complete; `/tp session` recommended handoff
- Host: Grok Build
- Confidence: H (design loop reached PROCEED consensus across 2 rounds)

## Acceptance criteria

The implementation is complete when ALL of:

1. All 5 Phase 1 + Phase 1.5 units shipped (U-1, U-2, U-11, U-14 + weight validation gate)
2. All 4 Phase 2 units shipped (U-4, U-5, U-12 + adoption instrumentation)
3. All 3 Phase 3 units shipped (U-3, U-13 + coupling detection)
4. `pnpm --filter codex-external-delegation test` passes 100% unchanged
5. `git diff src/review-relay.mjs` returns empty (dumb-pipe invariant held)
6. ≥1 production session has used each of the 3 components
7. All 5 user-pain metrics from the design's Success Metrics section are measurable (re-verification rate, operator file-read burden, time-to-convergence, partner prompt adoption rate, section-split wall-clock speedup)

## Implementation plan (from design doc)

### Phase 1 — dormant helpers (ship first, no behavior change)

| Unit | Description | Files | Est LoC |
|---|---|---|---|
| **U-1** | findings.mjs lifecycle FSM + tests | New: `~/.grok/skills/review-relay/__lib/findings.mjs`, `~/.grok/skills/review-relay/tests/test_findings.mjs` | ~180 + ~100 test |
| **U-2** | convergence.mjs score computation + tests | New: `~/.grok/skills/review-relay/__lib/convergence.mjs`, `tests/test_convergence.mjs` | ~120 + ~80 test |
| **U-11** | dashboard.mjs (consolidates 4 files → 1 for operator reading) + tests | New: `__lib/dashboard.mjs`, `tests/test_dashboard.mjs` | ~80 + ~50 test |
| **U-14** | schema.mjs versioning for findings/score/dashboard records + tests | New: `__lib/schema.mjs`, `tests/test_schema.mjs` | ~60 + ~40 test |

### Phase 1.5 — weight validation gate (before any production use)

Run convergence weight validation against ≥3 historical sessions from `P:/.data/wiki/concepts/coding-model-pool-tier-1-tier-2.md` and the 2026-07-XX review-relay sessions. Tune weights via `REVIEW_RELAY_WEIGHTS` env override if default (0.5/0.3/0.2) underperforms.

**Gate:** do not proceed to Phase 2 until weights produce score ≥0.7 on converged runs AND ≤0.85 on stuck runs across the validation set.

**Fallback if <3 historical sessions exist:** document why (early in deployment), use the default weights, and flag for revalidation after 5 production sessions.

### Phase 2 — partner adoption (default-on)

| Unit | Description | Files | Est LoC |
|---|---|---|---|
| **U-4** | SKILL.md documentation (3 new sub-sections: finding lifecycle, convergence score, per-section parallel review) | Modify: `~/.grok/skills/review-relay/SKILL.md` | ~180 |
| **U-5** | Partner prompt update with concrete `{{previous_findings_path}}` template + test | Modify: `~/.grok/skills/review/SKILL.md`; New: `tests/test_partner_prompt_template.mjs` | ~30 + ~50 test |
| **U-12** | Partner adoption instrumentation (logs `read_attempted: true` to scratchpad) | New: helper in partner prompt or skill hook | ~40 |

**Adoption metric:** ≥95% of partner turns read `previous_findings_path` (when non-null) within 30 days of Phase 2 ship.

### Phase 3 — section split (opt-in)

| Unit | Description | Files | Est LoC |
|---|---|---|---|
| **U-3** | split.mjs + merge.mjs + tests | New: `__lib/split.mjs`, `__lib/merge.mjs`, `tests/test_split.mjs`, `tests/test_merge.mjs` | ~150 + ~100 + ~100 + ~80 test |
| **U-13** | split.analyzeCoupling() — detects ≥30% cross-section reference density, falls back to whole-doc above threshold | Part of U-3 | ~50 |

**Default N=4 sections, max 6.** Coordinator decides when to invoke.

### Phase 4 — measurement + decision

After 5 production sessions using the new helpers, collect metrics and decide:

- Are user-pain metrics improving?
- Should convergence_score appear in result.json (currently sidecar only — U-10 NEEDS_USER_DECISION)?
- Has the skill-side mechanism become a production bottleneck? (If yes + cross-section/adaptive-lease/finding-provenance requirement materialized, ADR-011's migration rule fires → smart-pipe promotion.)

### Out of scope or DEFERRED

- **U-6** — relay source changes: **NONE** (by design invariant)
- **U-7** — existing tests pass unchanged: validation step, not a unit
- **U-8** — wiki concept revision: HANDOFF to operator (design doc is source of truth)
- **U-9** — end-to-end 4-section test run: DEFERRED until Phase 3 ships and a representative proposal is available
- **U-10** — score in result.json vs sidecar: NEEDS_USER_DECISION (default: sidecar only per DEC-3)
- **U-15** — per-helper rollback language: documentation, not code

## Open question for implementer (R2-N1)

**The previous_findings_path tick-input inconsistency:** the design says "0 lines added to review-relay.mjs" but also proposes `previous_findings_path` as a new tick input field. Critical friend round 2 verified (source read of `review-relay.mjs:1361-1378`) that tick inputs are built with explicit named fields from relay state — no controller-injection mechanism.

**Three resolutions (default applied — pick one at U-1 time):**

1. **Coordinator-side sidecar (RECOMMENDED — true 0 relay lines).** Coordinator writes previous_findings_path to a location the partner reads, without going through the tick surface. Honors dumb-pipe invariant strictly.
2. **Acknowledge 1-2 relay lines.** Add `previous_findings_path` as a named tick input field. Honest about invariant bending.
3. **Generic pass-through mechanism.** Add a generic "opaque input fields" mechanism to the tick. More upfront work but cleaner long-term abstraction.

**Default if not revisited:** option 1 (coordinator-side sidecar).

## Risks (from design's failure mode analysis)

1. **Sidecar proliferation** — each new requirement adds a file. Dashboard helper must keep up. Mitigation: U-11 dashboard.mjs consolidates.
2. **Partner non-adoption** — if partner prompts don't read findings.jsonl, lifecycle tracking is infrastructure without benefit. Mitigation: Phase 2 default-on + U-12 adoption metric.
3. **Convergence weight miscalibration** — DEC-13 contract: score MUST NOT be sole coordinator signal. Phase 1.5 validates.
4. **Section-split on coupled docs** — U-13 `split.analyzeCoupling()` detects ≥30% cross-section density; falls back to whole-doc above threshold.
5. **Dashboard god-object risk** — every new helper integrates with dashboard. Mitigation: keep dashboard.mjs <100 LoC; refactor if it grows beyond status/deriveNextAction.

## Falsifiers (from design §1.6)

- **F-1:** After Phase 2 ships, 5 production sessions show re-introduction rate unchanged from 42-finding/16-turn baseline → sidecar is infrastructure without benefit → revert U-1 or redesign partner prompt.
- **F-2:** After Phase 1.5 validation, converged runs score <0.7 AND stuck runs score >0.85 → score is inverted → re-tune via REVIEW_RELAY_WEIGHTS; if fails, revert to heuristic-only.
- **F-3:** 4-section split review wall-clock >50% of whole-doc baseline → speedup claim fails → re-tune N cap; if still slow, revert.
- **F-4:** Two operators launch coordinators on same proposal path without `opts.session_id` → silent collision → switch to default-on session_id.
- **Combined:** ship U-1..U-5, run 5 production sessions, measure all 5 metrics. If ≥3 regress or fail to improve → comprehensive rollback to Phase 0.

## Notes for fresh session

- **Read first:** `P:/docs/design/review-relay-improvements-b1abe493/grok-design-doc-b1abe493.md` (full design)
- **Then:** `P:/docs/adrs/ADR-011-review-relay-dumb-pipe-invariant.md` (the load-bearing decision)
- **Don't modify:** `P:/packages/codex-external-delegation/src/review-relay.mjs` (dumb-pipe invariant — ADR-011)
- **Resolve R2-N1 first:** before starting U-1, decide which of the 3 tick-input resolutions to use. Default is option 1 (coordinator-side sidecar).
- **Phase 1.5 gate is mandatory:** do not skip weight validation even under time pressure. DEC-13 contract depends on it.
- **Test command:** `pnpm --filter codex-external-delegation test` must pass 100% after every unit.