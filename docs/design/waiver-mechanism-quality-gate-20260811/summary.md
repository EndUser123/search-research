# Design Summary — Optimal Waiver Mechanism for Stop-Hook Review Quality Gate

**Design run:** 62d39214
**Date:** 2026-08-11 (revised after 35-issue review)
**Complexity tier:** 2 (standard; touches existing infrastructure, no greenfield)
**Pipeline mode:** full (premise verification + review-revise; all 35 findings addressed)

---

## Headline Recommendation

Replace the current 30-min time-bound review-gate waiver with a **scope-bound waiver that emits non-blocking feedback via `hookSpecificOutput.additionalContext`** on each matched fire. The waiver binds to a named milestone, lists the files in scope, names a concrete `next_review_at`, records `authorized_by`, and appends to a per-fire `consumption_audit`. The gate still fires every turn (preserving anti-loop + detection), but the operator-visible output is non-blocking feedback instead of a block when the waiver matches.

This conforms to two named patterns from the literature (bhekani single-use override tokens; safeguard.sh break-glass) and closes the gaming vector implicit in the current time-bound re-write scheme.

**Critical correction from the review (F-01):** the original draft proposed `decision: warn` as the Stop hook output, but the Grok Build Stop hook does NOT support that value (verified against `~/.grok/docs/user-guide/10-hooks.md:254-262`). The design now uses `hookSpecificOutput.additionalContext`, the only non-blocking feedback mechanism supported by the Stop hook.

---

## What the Problem Actually Is

The current waiver (`gate_diagnostics.py:562-601`) is a **time-bound session-scoped override**. The 30-min freshness window solves the anti-loop failure mode (the gate fires every turn because `invoked_skills` is reconstructed), but it has three issues:

1. **Gaming vector:** the 30-min window allows re-write every 29 min. No audit row binds to a specific work unit.
2. **Wrong override class:** the bhekani pattern explicitly rules out "session overrides that turn off a class of checks for some window."
3. **Wrong output mode:** the break-glass pattern says the bypass should convert `block → warn`-style non-blocking feedback, not `block → allow`. The current mechanism silently short-circuits, losing the detection signal.

**Core tension:** anti-loop requires the gate not re-block on consecutive turns within the same work unit; single-use tokens require a new decision each gate fire. These conflict. The resolution: the gate fires every turn (preserving anti-loop), but its output is downgraded from `block` to `hookSpecificOutput.additionalContext` when a valid waiver context exists. The waiver is not a suppression; it is a **mode change** scoped to (a) specific files, (b) specific skills, (c) a bounded window tied to a named milestone with a concrete `next_review_at`.

---

## What Was Recommended (Key Decisions)

| DEC | Decision | Why |
|---|---|---|
| [DEC-01] | Scope-bound waiver with non-blocking feedback downgrade | Conforms to literature (P5, P6); preserves anti-loop (P1); closes gaming vector (P4) |
| [DEC-02] | Atomic `consumption_audit` write (records ALL fires, not just bypasses — F-18) | Crash/concurrency-safe; enables "close calls" + "bypasses" retrospective analysis |
| [DEC-03] | Expired waiver files NOT auto-deleted | Audit history valuable for retrospective review |
| [DEC-04] | Stop-hook contract change: emit `hookSpecificOutput.additionalContext` (NOT `decision: warn` — F-01) | Break-glass requires non-blocking feedback; verified against the actual Stop hook protocol |
| [DEC-05] | Refactor `_quality_gate_check` into 3 functions (Unit 1a + 1b — F-29) | Mixed concerns threshold in the Coupling & Code-Smell Inventory |
| [DEC-06] | Feature flag env var `GROK_REVIEW_GATE_SCOPED_WAIVER` (3 states: off/shadow/on — F-12) | Reversibility for critical-infrastructure change |
| [DEC-07] | Bypass budget is post-hoc audit signal (not runtime enforcement) | Cross-session state is complex; audit matches break-glass pattern |
| [DEC-08] | Self-authorization permitted with audit; `GROK_SELF_AUTH_ALLOWED=0` env var (F-03) disables | Synchronous operator approval impractical (P11); env var gives operator a per-session escape hatch |

---

## Critical Issues Resolved (from 35-finding review)

1. **F-01 (CRITICAL):** Verified the Stop hook protocol (`10-hooks.md:254-262`) and corrected the design to use `hookSpecificOutput.additionalContext` instead of the unsupported `decision: warn`.
2. **F-02 (CRITICAL):** Fixed Unit 3 pseudocode — 3 mutually exclusive branches (`block` exits, `warn` exits, `allow` falls through to `clear_waiver`); the warn path preserves the waiver file because consumption is tracked in `consumption_audit`, not by deletion.
3. **F-03 (CRITICAL):** Added `GROK_SELF_AUTH_ALLOWED` env var (default: `1`; set to `0` to refuse self-authorization) as the concrete resolution of the self-authorization tension.
4. **F-08 (MAJOR):** Reconciled the two waiver paths — canonical path is `~/.grok/hooks/state/quality-gate-waiver-{session_id}.json` (the path used by `write_waiver()`); the legacy `review-waiver-` glob is updated to read from the canonical path.

---

## What Was Rejected (with one-line reasoning)

- **Option 0: Do nothing.** Gaming vector remains; violates two named anti-patterns from literature.
- **Option 2: Single-use consumed tokens.** Each gate fire would consume a token; agent must re-mint each turn — operationally equivalent to gate re-blocking, gaming vector re-introduced.
- **Option 3: Operator-gated approval channel.** Deferred to OQ-04; requires synchronous operator availability. Current design accepts self-authorization with audit (and the `GROK_SELF_AUTH_ALLOWED=0` env var) as the practical default.
- **`decision: warn` Stop hook output.** Verified FALSE against `~/.grok/docs/user-guide/10-hooks.md` — not a supported decision value. Replaced with `hookSpecificOutput.additionalContext`.

---

## File-by-File Change Inventory

| File | Action | LOC delta (est.) | Unit |
|---|---|---|---|
| `~/.grok/hooks/scripts/quality_gate/gate_diagnostics.py` | Modify (replace `_quality_gate_check` + add 2 helpers; 3-state feature flag) | +75, -25 | Unit 1a + 1b |
| `~/.grok/scripts/waiver_gate.py` | Modify (rewrite schema + new flags + `GROK_SELF_AUTH_ALLOWED` support + canonical path) | +55, -10 | Unit 2 |
| `~/.grok/hooks/scripts/quality_gate/main.py` | Modify (update call site + 3-branch emission logic) | +25, -5 | Unit 3 |
| `~/.grok/hooks/scripts/quality_gates_frontmatter.py` | Modify (update `build_block_message` + add `write_scoped_waiver` helper + path reconciliation) | +30, -10 | Unit 4 |
| `~/.grok/hooks/tests/test_quality_gates_frontmatter.py` | Modify (add 11 tests, update 3 existing) | +220, -20 | Unit 4 |
| `~/.grok/AGENTS.md` | Modify (update trigger case + env var + path) | +12, -3 | Unit 5 |
| `~/.grok/scripts/bypass_budget.py` | New (Unit 6a minimum-viable; Unit 6b deferred) | +60 | Unit 6a |
| `~/.grok/hooks/state/quality-gate-warns-{session_id}.jsonl` | New (per-session, append-only; rotation: 30-day cleanup, 10 MB hard cap → truncate-and-rotate) | N/A | Unit 3 |
| `P:/docs/handoffs/main-py-quality-gate-refactor-2026-08-11/HANDOFF.md` | New (handoff for the pre-existing main.py refactor backlog — F-20) | +30 | F-20 (deferred) |

**Total:** ~507 LOC added, ~73 removed across 9 files. No new schema migration; old waiver files become "ignored" when read.

---

## Implementation Plan Summary

- **Unit 1a** (gate_diagnostics.py): refactor `_quality_gate_check` into 3 functions, no behavior change. `COMMIT_THIS_SESSION`.
- **Unit 1b** (gate_diagnostics.py): populate the stubs with the new mechanism; add 3-state feature flag; canonical path. `COMMIT_THIS_SESSION`.
- **Unit 2** (waiver_gate.py): rewrite schema with 4 new required flags + `GROK_SELF_AUTH_ALLOWED` + canonical path. `COMMIT_THIS_SESSION`.
- **Unit 3** (main.py): update emission to 3 mutually exclusive branches; emit `hookSpecificOutput.additionalContext` on non-blocking feedback. `COMMIT_THIS_SESSION`.
- **Unit 4** (quality_gates_frontmatter.py + tests): update block message + 11 new tests. `COMMIT_THIS_SESSION`.
- **Unit 5** (AGENTS.md): update trigger case + env var + path. `COMMIT_THIS_SESSION`.
- **Unit 6a** (bypass_budget.py): minimum-viable utility (schema-coverage check + bypass-budget count). `COMMIT_THIS_SESSION` (F-14 — required to verify success metric).
- **Unit 6b** (bypass_budget.py extensions): threshold tuning + visualization. `HANDOFF`.
- **`P:/docs/handoffs/main-py-quality-gate-refactor-2026-08-11/HANDOFF.md`** (F-20): handoff for the pre-existing main.py refactor backlog.

Rollout is staged: feature flag `off` → `shadow` → `on` → remove flag after 1 month. The 3-state flag (DEC-06) allows intermediate safety where the new mechanism runs and logs but the legacy mechanism decides.

---

## Premise Verification Summary

- **[FACT] premises (4):** P1 (anti-loop fix), P2 (gate fire conditions), P3 (obligation system), P7 (agent can derive correct waiver disposition). All cited with file:line receipts.
- **[RESEARCH] premises (2):** P5 (single-use tokens), P6 (break-glass). Both cited to external sources; `[RESEARCH]` label defined in Premise Labels Reference appendix (F-15).
- **[INFERENCE] premises (3):** P4 (gaming vector), P8 (verified FALSE on Stop hook protocol — see N-01), P11 (promoted from UNKNOWN per F-16).
- **[UNKNOWN] premises (2):** P9 (operator availability), P10 (milestone discipline rate). Both degrade gracefully.

---

## Open Questions

1. **OQ-01:** Is the gaming vector real? [INFERENCE] — measure waiver-rewrite patterns retrospectively.
2. **OQ-02:** ~~Can the Stop hook protocol emit `decision: warn`?~~ RESOLVED FALSE per F-01; design uses `hookSpecificOutput.additionalContext`.
3. **OQ-03:** Do all milestones have a concrete ship-time review point? [UNKNOWN] — instrument post-deploy.
4. **OQ-04:** Should a real operator-approval channel be added? [UNKNOWN] — defer to follow-on design.
5. **OQ-05:** Should waiver files be HMAC-signed? [UNKNOWN] — defer; current threat model doesn't require tamper-evidence.
6. **OQ-06:** Should bypass budget be enforced at runtime? [UNKNOWN] — recommended no (DEC-07).

---

## Risk Profile

- **Critical:** the Stop hook is critical infrastructure. The 3-state feature flag (DEC-06: `off`/`shadow`/`on`) gates the new mechanism for staged rollout and rapid rollback. Shadow mode runs the new mechanism and logs without changing the emitted decision.
- **Medium:** the contract change to `hookSpecificOutput.additionalContext` (DEC-04) affects any future consumers of the Stop hook. None currently on this host; documented in user-guide.
- **Low:** the script change (Unit 2) is fully reversible; the new mechanism is inert when the feature flag is `off`.

---

## Coupling & Code-Smell Inventory Verdict

- **gate_diagnostics.py:** mixed concerns → refactor proposed (DEC-05, split into Unit 1a + 1b). Touch-point count = 5 (above threshold); justified with explicit reasoning (Stop-hook critical infrastructure, all 5 sites are natural contract owners).
- **waiver_gate.py:** clean.
- **main.py:** pre-existing mixed concerns; refactor deferred to `P:/docs/handoffs/main-py-quality-gate-refactor-2026-08-11/HANDOFF.md` (F-20 — chronicity: chronic).
- **quality_gates_frontmatter.py:** clean.

No "refactor before ship" blockers. The refactor in Unit 1a is the minimum to satisfy the mixed-concerns threshold; further refactors of `main.py` are documented in a separate handoff.

---

## Key Takeaway for the Operator

The current 30-min waiver works but is gaming-susceptible and violates two named anti-patterns from the literature. The proposed mechanism — scope-bound waiver with non-blocking feedback via `hookSpecificOutput.additionalContext`, atomic consumption audit, and post-hoc bypass-budget review — closes the gaming vector, conforms to field-tested patterns, and preserves both the anti-loop property and the gate's detection value.

**Critical correction:** the original design's `decision: warn` proposal was verified against the Grok Build Stop hook protocol and found to be unsupported; the design uses the only available non-blocking feedback mechanism.

Self-authorization is accepted as the practical default (synchronous operator approval is deferred to OQ-04), with the `GROK_SELF_AUTH_ALLOWED=0` env var giving the operator a per-session escape hatch, and the audit log enabling retrospective review.

The implementation is staged via a 3-state feature flag (`off`/`shadow`/`on`) to allow safe rollout and rapid rollback.

---

## File References

- **Design document:** `C:\Users\brsth\AppData\Local\Temp\grok-design-62d39214\grok-design-doc-62d39214.md`
- **Review file (updated):** `C:\Users\brsth\AppData\Local\Temp\grok-design-62d39214\grok-design-review-62d39214.md`
- **Summary:** `C:\Users\brsth\AppData\Local\Temp\grok-design-62d39214\grok-design-summary-62d39214.md`
- **Source code (read for context):**
  - `~/.grok/hooks/scripts/quality_gate/gate_diagnostics.py` (lines 540-620)
  - `~/.grok/hooks/scripts/quality_gates_frontmatter.py` (lines 594-647, 670-690, 770-935)
  - `~/.grok/hooks/scripts/quality_gate/main.py` (lines 480-600)
  - `~/.grok/scripts/waiver_gate.py` (full file)
  - `~/.grok/docs/user-guide/10-hooks.md` (lines 252-262 — Stop hook protocol, F-01 verification)
- **Wiki concepts referenced:**
  - [[stop-hook-review-gate-hash-invalidation-loop]] (the anti-loop failure mode)
  - [[mechanical-enforcement-over-behavioral-reminder]] (why the audit-log approach beats prose rules)
  - [[declarative-quality-gates-skills-declare-evidence]] (the gate system this design extends)
