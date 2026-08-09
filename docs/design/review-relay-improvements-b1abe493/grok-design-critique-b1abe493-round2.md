# Critical-Friend Review — Variant A: Round 2

**Author role:** Critical-friend reviewer (round 2). Round 1 issued REVISE with 10 specific issues. Round 2 verifies each issue was substantively addressed (not just text-added), examines new premises the revision introduced, and stress-tests the revised framing.

**Source artifact:** `grok-design-doc-b1abe493.md` (Revision 3, ~770 lines)
**Round 1 critique:** `grok-design-critique-b1abe493.md`
**Round 1 verdict:** REVISE (10 issues: A-H plus Issues 1-2)

---

## §1. Verification Summary

| Round 1 Finding | Status | Where addressed |
|---|---|---|
| **F1 — Success metrics measure preservation, not improvement** | **Substantively addressed** | §1 Success Metrics (revised) |
| **F2 — Dumb-pipe is historical accident, not architectural virtue** | **Substantively addressed, with residual concerns** | §2 Architectural Justification + DEC-12 |
| **F3 — Variant B is a bundled strawman** | **Substantively addressed** | §6.2 Option 1B |
| **F4 — Convergence weights unvalidated; "advisory" ≠ harmless** | **Substantively addressed** | §4 DEC-13 + Phase 1.5 |
| **F5 — Falsifiability section missing** | **Substantively addressed** | §1.6 Falsifiability (5 falsifiers) |
| **F6 — Operator reading burden increases, not decreases** | **Substantively addressed** | §4 Dashboard Helper + U-11 |
| **F7 — Coupling inventory undercounts cross-helper coupling** | **Substantively addressed** | §6.3 (re-counted) + U-14 |
| **F8 — Premise #12 is single-point-of-failure** | **RESOLVED with verified receipts** | §6.10 #1 (RESOLVED) |
| **F9 — Partner opt-in adoption is structurally fragile** | **Substantively addressed** | §6.9 Phase 2 + U-12 + REQ-19 |
| **F10 — Section-independence assumption fails** | **Substantively addressed** | §5 analyzeCoupling + U-13 |

**Bottom line:** All 10 round 1 findings were substantively addressed. The design is materially stronger than round 1. Round 2 surfaces **one new architectural inconsistency** (Finding R2-N1, see §3) and **three second-order concerns** about new premises the revision introduced (see §2).

---

## §2. Per-Finding Detail (compact)

### F1 — Success Metrics: **Substantively addressed**

The "0 lines added to relay" metric was demoted from Success Metric to Non-Goal (constraint, not measure). Six user-pain metrics replaced it:
- Re-verification rate (0/session)
- Operator file-read burden (1 file via dashboard)
- Time-to-convergence (≤50% of baseline)
- Partner prompt adoption (≥95% in 30 days)
- Section-split wall-clock (≤50% of whole-doc)
- Existing test suite (100% pass)

**Residual concern:** four of these metrics are **contingent on partner adoption succeeding**. If partner adoption fails (<50% read rate), `re-verification rate` and `time-to-convergence` cannot be measured cleanly because the sidecar isn't being used by all partners. The metrics measure "did the sidecar move the needle" only when partners adopt. The design should acknowledge this dependency chain (it doesn't), but the metrics themselves are honest about what's being measured. Confidence: H.

### F2 — Dumb-Pipe Justification: **Substantively addressed, with residual concerns**

Five arguments + Graceful Migration Path + DEC-12 decision rule added. Evaluation:

| Argument | Evidence-based? | Strength |
|---|---|---|
| **1. Transport contract stability** | Yes — cites 7+ iterations since 2026-08-08 | Partial — stability ≠ virtue (could mean the contract is good OR it hasn't been challenged) |
| **2. Future requirements can be met with sidecars** | **No** — assertion without demonstration | **Weak** — doesn't engage with the cross-section-correlation / adaptive-lease requirements that the original critique flagged |
| **3. Smart-pipe migration has 10:1 higher future cost** | **No** — fabricated number | **Weak** — "at least 10:1" is asserted without calculation; "every partner integration depends on opaque contract" is a constraint, not an argument |
| **4. Workspace convention — skills orchestrate smart, transports execute dumb** | Yes — cites `wiki/concepts/llm-handoff-best-practices.md` | Strong — legitimate workspace pattern |
| **5. The invariant is testable** | Yes — `git diff` empty is one-line assertion | Partial — testable ≠ justified (cheap to verify, but verifying preservation doesn't tell you preservation is right) |

**Overall:** Mixed. Two of five arguments are evidence-based (4 and 1). Two are weak (2 and 3, both preference dressed as fact). Argument 5 is true but trivial. The DEC-12 decision rule ("ship dumb-pipe first, migrate only when (a) skill-side mechanism has been a production bottleneck for ≥30 days AND (b) at least one future requirement has materialized") is the strongest addition — it converts the question from "is dumb-pipe good?" to "when should dumb-pipe yield?", which is the right framing.

**Residual concern:** Argument 3's "10:1 cost ratio" is fabricated. A number asserted as fact without derivation. The argument would be stronger as "the cost ratio is qualitatively high, because refactoring the relay to inspect findings is irreversible and breaks every partner integration; adding sidecars is reversible and additive" — without the 10:1.

The architectural inconsistency in §3 below also bears on this finding.

### F3 — Variant B Strawman: **Substantively addressed**

Option 1B is now in the alternatives table: "Inspecting-Pipe for Findings Only — Isolated." It isolates finding inspection (the cheapest smart-pipe change) while keeping convergence score and section-split skill-side. The pros/cons are honest about blast radius. The selection criterion cited ("lowest future cost and risk") is a legitimate long-term framing. The fair comparison now exists.

**Verdict:** Fix is real, not text-added. Confidence: H.

### F4 — Weight Validation: **Substantively addressed**

Three mechanisms added:
1. **DEC-13** ("MUST NOT use score as sole signal") — the contract language is real, not advisory. Cross-check requirement against zero new findings OR all findings upheld/resolved OR operator override is enforceable.
2. **Phase 1.5 validation gate** — score contributes 0 to coordinator decisions until weights are validated on ≥3 test proposals. This is a real gate, not deferred.
3. **Phase 1.5 predicate in decision rule** — "AND Phase 1.5 validation has completed for this weight set" is a hard clause.

**Residual concern:** Phase 1.5 requires ≥3 historical review sessions with clear converged/stuck/active outcomes. If the workspace doesn't have 3 such sessions (or the discrimination isn't clean), the design says "tune via REVIEW_RELAY_WEIGHTS env override and re-validate" but doesn't specify what happens if 5 re-validations also fail. The fallback is unbounded re-validation loops. Should be bounded.

### F5 — Falsifiability: **Substantively addressed**

Five concrete falsifiers in §1.6, each with observation + when + action trigger:
- **F-1** (sidecar doesn't move metric): 5 production sessions, re-introduction rate unchanged → revert U-1 or escalate
- **F-2** (score is inverted): 5 production sessions, converged <0.7 AND stuck >0.85 → re-tune or revert to heuristic-only
- **F-3** (per-section parallel slower): real 4-section design doc, >50% of whole-doc baseline → re-tune N cap or revert
- **F-4** (multi-coordinator collision): collision observed → default-on session_id with process.pid+timestamp
- **F-5** (Premise #12 was structurally unworkable): RESOLVED — premise did not fire

Combined-falsifier rule: "If ≥3 regress or fail to improve over baseline, comprehensive rollback to Phase 0."

**Quality check (each falsifier):**
- Concrete and observable? ✓ for F-1, F-2, F-3; F-4 is observation-based but only fires if the operator happens to launch two coordinators
- When to check? ✓ for F-1 (after Phase 2), F-2 (after Phase 1.5), F-3 (4-section test proposal); ✗ for combined-falsifier (no explicit "when")
- What to do if it fires? ✓ all five; F-1, F-2, F-3, F-4 each have a specific revert or re-tune action

**Verdict:** Substantively addressed. The combined-falsifier rule has an action trigger but no explicit "when to check" — minor gap. Confidence: H.

### F6 — Operator Reading Burden: **Substantively addressed**

`__lib/dashboard.mjs::status(bucket)` consolidates findings + score + merged state + review meta into a single JSON output. `deriveNextAction()` returns one of four actions ("declare ready_for_parent_review", "await next actor's rebuttal", "mediate dispute", "continue relay"). Operator runs one Node.js one-liner and reads one JSON, instead of reading 4 sidecar files.

**Residual concern:** The dashboard's contract is underspecified for missing files. `next_action` derivation reads `findings.open`, `score.score`, `merged.score_min` — but the design doesn't specify what these helpers return when their sidecar files don't exist. If `readFindingsSummary()` returns `null` instead of `{open: 0, ...}` when no findings.jsonl exists, then `findings.open === 0` throws TypeError. The contract should specify "empty summary defaults" for each sidecar.

### F7 — Coupling Inventory: **Substantively addressed**

Re-counted honestly:
- Touch points for finding schema change: 4 (over threshold of 3) — flagged
- Touch points for score schema change: 4 (over threshold) — flagged
- Mixed concerns: NOT OK (was "OK (separation clean)" originally) — flagged
- Schema versioning mitigation: `__lib/schema.mjs` with `findings.v1` / `convergence.v1` / `merge.v1` schemas + `validate(record, schema_name)` — structural fix, ~80 LoC

**Verdict:** Honest re-counting + structural fix. Confidence: H.

### F8 — Premise #12 Single-Point-of-Failure: **RESOLVED**

Source-code receipts verified against `P:/packages/codex-external-delegation/src/review-relay.mjs`:
- Line 964: `allowed_writes: ["manifest.json", "proposal-v1.snapshot", "turns/**", "events/**", "handoff-candidate.v1.json"]` — `turns/**` IS in the allow-list
- Line 1377: `forbidden_writes: manifest.write_policy.forbidden_writes` — passed to partner input, advisory
- Line 393: only `artifact_root_only: true` is validated by the relay (path-level enforcement of allowed_writes/forbidden_writes does NOT exist — confirmed via grep for `validatePath`/`validate_write`/`writeGuard` returning no matches)

**Verdict:** Variant A is structurally workable from a write-policy perspective. Partners CAN write `findings.jsonl` to `<bucket>/turns/<n>/active/` because `turns/**` is in `allowed_writes`. Skill-written sidecars (`convergence_history.jsonl`, `merged-findings.jsonl`) at `<bucket>/` are permitted by the `artifact_root_only: true` check.

The Finding 8 verification is independently confirmed against the source. **F-5 falsifier (Premise #12 was structurally unworkable) is RESOLVED — premise did not fire.**

### F9 — Partner Adoption: **Substantively addressed**

Three mechanisms added:
1. **Default-on partner prompt** (Phase 2 PR updates partner prompts to read `previous_findings_path` whenever non-null, even if empty) — eliminates the opt-in asymmetry
2. **Multi-pool propagation PR** (single PR updates Codex, Grok, Pi, OpenCode partner prompts; reviewed against the partner-prompt test suite)
3. **Adoption metric** (partner template logs `findings_sidecar_read_attempted: true` to scratchpad; dashboard helper reads these logs and reports adoption rate)

Threshold escalation rule: "Adoption rate <50% for 7 consecutive days → partner-prompt redesign escalation." Open Question #7 explicitly notes that 95% threshold is **not yet validated** on real partner pools; first 30 days produce empirical distribution.

**Verdict:** Substantively addressed. The default-on choice + multi-pool PR + adoption metric are the right triad. The 95% threshold being aspirational is honest, not hidden. Confidence: H.

### F10 — Section Coupling: **Substantively addressed**

`split.analyzeCoupling()` detects cross-section references (term_reference, contract_reference, example_reference) and computes a weight (cross-section mentions / section's total references). If any section has ≥30% weight, `splitProposal` returns `{ok: false, reason: "cross_section_coupling_detected"}` and the coordinator falls back to whole-proposal review. If `opts.force_split === true`, the split proceeds with a coupling report embedded in the partner prompt as a "context preamble."

**Verdict:** Substantively addressed. Confidence: H. (See §3 below for the 30% threshold being arbitrary.)

---

## §3. New Premises Introduced by the Revision

Round 1's critique did not examine these — they're new in Revision 3. Each is examined for whether it introduces new coupling, complexity, or unexamined assumptions.

### R2-P1 — `dashboard.mjs` as a new abstraction layer

The dashboard consolidates 4 file reads (findings, score, merged, review meta) into 1 JSON output. As more helpers are added in future revisions, the dashboard's `status()` will likely become the central read path for operator status, and `deriveNextAction()` will encode more workflow decisions.

**Concern: god-object risk.** Six months from now, every new helper integrates with the dashboard because "the operator checks the dashboard." Changes to any helper's file format break the dashboard. The dashboard becomes coupled to every helper. This is a structural concern, not immediate.

**Mitigation suggestion:** document the dashboard's contract in `__lib/dashboard.mjs` header — specifically, "the dashboard reads 4 files; adding a 5th file requires an explicit opt-in by the operator and a documented reason." This is a one-line rule that prevents accidental god-object growth.

### R2-P2 — `schema.mjs` versioning module

The schema versioning introduces a maintenance discipline: every future format change requires a version bump, a validator update, and mixed-version handling.

**Concern: dual-maintenance cost.** Schema versions accumulate indefinitely unless explicitly retired. Each version requires its own test. Validation code grows. This is the standard cost of versioning — it's the right tradeoff for a multi-touch-point schema, but it's worth naming.

**Mitigation:** the design should specify a deprecation policy ("version N+1 ships; version N supported for 90 days; after 90 days, version N records skipped with warning"). The current design doesn't specify this.

### R2-P3 — `split.analyzeCoupling()` 30% threshold

The 30% threshold is asserted in §5: "A section is 'coupled' if ≥30% of its references point to another section." The design acknowledges it's a "lightweight" heuristic but provides no empirical basis.

**Concern: arbitrary threshold.** 30% is a guess. False-positive (over-detection) → falls back to whole-proposal (conservative, OK). False-negative (under-detection) → splits a coupled document, produces incoherent findings (costly).

**Verdict:** Addressable, not blocking. The threshold is a tunable parameter and the design already documents the false-positive/false-negative trade-off honestly. Round 3 (post-implementation) should tune the threshold based on first 5 production uses.

### R2-P4 — Phase 1.5 deadline

Phase 1.5 validates convergence weights on ≥3 test proposals before Phase 2 ships partner prompts. Until validation completes, the score contributes 0 to coordinator decisions. This is a real gate, not deferred.

**Concern: historical proposals availability.** The workspace may not have 3 historical review sessions with clear converged/stuck/active outcomes. The design says "different shapes, different complexities" but doesn't say "or generate new test proposals if 3 historical ones don't exist." If the workspace has 0-2 historical sessions, Phase 1.5 cannot complete with the existing data.

**Verdict:** Minor gap. The fallback should be specified: "If <3 historical sessions exist, generate test proposals with known-good and known-stuck outcomes, run validation on those." Adding this is one line.

---

## §4. New Architectural Inconsistency (introduced by Revision 3)

### Finding R2-N1 — The "0 lines added" claim is incompatible with `previous_findings_path` on the tick surface

**Where this lives:**
- **Non-Goal:** "No new lines in `src/review-relay.mjs`." (constraint)
- **Opaque-field discipline:** "`previous_findings_path` joins the relay's existing set of opaque string fields: `previous_result_path`, `previous_result_actor`, `previous_result_hash`. The relay treats all of these as pass-through strings."
- **Component 1:** "`previous_findings_path` is an additional input field on the tick surface... The relay does not parse this field — it passes it through to the partner like every other input."

**The tension:**

I verified the relay's partner-input construction at `P:/packages/codex-external-delegation/src/review-relay.mjs:1361-1378`. The partner input is built with **explicit named fields**:

```javascript
const input = {
  schema_version: TURN_INPUT_SCHEMA_VERSION,
  review_id: manifest.review_id,
  manifest_hash: manifest.manifest_hash,
  ...
  previous_result_path: previousTurn?.result_path || null,
  previous_result_actor: previousTurn?.actor || null,
  ...
};
```

There is no generic pass-through mechanism. Each field is sourced from either the manifest (static config), the relay's internal state (`previousTurn`), or constants. The relay's `tickReview({ artifactRoot, actor, clock })` signature (line 1400) accepts no arbitrary fields from the controller.

Furthermore, `previous_result_path` is **NOT** a controller-injected field — it is sourced from the relay's own `previousTurn?.result_path` (line 1374). The analogy the design draws ("the relay already passes `previous_result_path` opaquely") is therefore not quite accurate: the relay passes a *self-sourced* field through, not a *controller-injected* field.

**Implications for the "0 lines added" claim:**

To add `previous_findings_path` to the partner input, the relay must:
1. **Source the value** from somewhere — either (a) extend the manifest schema to include a `findings_path` per actor, (b) add state tracking for the findings path in the relay's own turn records, or (c) accept it via a controller-injected mechanism that doesn't currently exist.
2. **Write the value** into the partner input object — adding one line to the construction at line 1374 area.

Both require relay code changes. At minimum: **1 line in the input construction + state tracking**. The "0 lines added to review-relay.mjs" claim is therefore inconsistent with the "additional input field on the tick surface" claim, **unless** the design routes `previous_findings_path` through a controller-side mechanism (e.g., coordinator patches input.json post-claim, or partner reads a sidecar the coordinator writes outside the relay's input.json).

**DEC-12 already provides the resolution path:** "If the optimal long-term solution requires a relay change, this constraint yields. See §2 Architectural Justification for the framework that decides when."

**Recommendation:**

The design should explicitly choose one of three resolutions and document it in §3:

**Resolution A (preferred):** Route `previous_findings_path` through a controller-side sidecar — coordinator writes `<bucket>/turns/<n>/active/tick-context.json` (containing the findings path and any other coordinator-sourced fields), partner prompt template instructs partner to read this sidecar after reading input.json. **Zero relay changes.** This is consistent with the "0 lines added" claim and the dumb-pipe invariant. The cost: partner prompt gets one more line ("also read `<tick-context-path>` if it exists").

**Resolution B:** Acknowledge that adding `previous_findings_path` to the tick surface requires 1-2 relay lines (state tracking + input construction). Update Non-Goal from "0 lines added" to "minimal relay additions justified by §2 framework." This is honest but slightly weakens the "dumb-pipe preserved" framing.

**Resolution C:** Add a generic pass-through mechanism to the relay (e.g., `manifest.opaque_extensions: { "previous_findings_path": "<path>" }` declared in manifest, relay spreads into partner input). This is ~5-10 relay lines but establishes a general pattern for future fields. Cleaner long-term but more code.

The design should pick one before implementation. As written, the "0 lines added" and "additional tick field" claims are mutually exclusive.

**Why this matters:** This is a load-bearing inconsistency, not a wording nit. The dumb-pipe justification (Finding 2) rests on "0 lines added." If the design actually requires 1-5 relay lines, the architectural-justification arguments should be updated to reflect that. DEC-12 already provides the framework for "when the constraint yields" — the design should declare what triggers the yield.

---

## §5. Pre-Mortem Round 2 (3 NEW failure scenarios)

The round 1 critique listed 8 scenarios. The following are NEW scenarios that the revision itself introduced — failure modes the new code (dashboard, schema versioning, Phase 1.5 gate, analyzeCoupling) opens up.

### R2-Scenario 1 — Dashboard becomes god-object (12 months out)

`__lib/dashboard.mjs::status()` is the operator's primary read path. Every new helper, every new sidecar, every new failure mode eventually gets integrated into the dashboard because "the operator checks the dashboard." `deriveNextAction()` grows from 4 actions to 8 to 12. The dashboard becomes coupled to every helper's file format. Changes to any helper's schema break the dashboard. The schema-versioning in `schema.mjs` partially mitigates this (the dashboard can read multiple versions), but doesn't address the architectural coupling.

**Trigger:** Three rounds of new helpers added to the dashboard without an explicit "this helper doesn't belong in the dashboard" decision rule.

**Mitigation:** Add to the dashboard's header: "This helper reads 4 sidecar files. Adding a 5th file requires an explicit opt-in by the operator and a documented reason. The dashboard is not a general-purpose orchestrator."

### R2-Scenario 2 — Schema versioning dual-maintenance (24 months out)

`schema.mjs` ships with `findings.v1`, `convergence.v1`, `merge.v1`. The team adds `findings.v2` because of a new finding state. Then `findings.v3`. Then `convergence.v2`. Each version needs its own validator. Each version needs to handle mixed-version files (some records v1, some v2). The team never retires old versions because "someone might be reading them." Validators grow. Tests grow. The team eventually has 4+ versions of each schema, and validators for each. The "schema versioning" that was supposed to reduce coupling now produces coupling between versions.

**Trigger:** No deprecation policy specified at schema-versioning design time. Six months in, v1 has 12% of records, v2 has 88%. v3 ships. v1 is no longer being written but old records still exist.

**Mitigation:** Specify a deprecation policy at schema-versioning design time: "version N+1 ships; version N supported for 90 days; after 90 days, version N records skipped with warning." Without this policy, schema versions accumulate indefinitely.

### R2-Scenario 3 — Phase 1.5 stalls entire rollout (6 months out)

Phase 1.5 requires ≥3 historical review sessions with clean converged/stuck/active outcomes. If the workspace has 0-2 such sessions (because the workspace is small or new), Phase 1.5 cannot complete with existing data. The fallback is "tune via REVIEW_RELAY_WEIGHTS env override and re-validate" — but re-validation requires the same 3 sessions. The loop is unbounded. Phase 2 (partner prompts) and Phase 3 (section-split) cannot ship. The team has shipped dormant helpers (Phase 1) but cannot ship value (Phase 2/3).

**Trigger:** The workspace has <3 historical review sessions, OR 3 sessions exist but their convergence outcomes are ambiguous (unclear whether they were "converged" or "stuck").

**Mitigation:** Specify the fallback at design time: "If <3 historical sessions with clear outcomes exist, generate test proposals with known-good and known-stuck outcomes, run validation on those. If even synthetic proposals don't discriminate, escalate to user with 'no validation possible — keep heuristic-only' decision."

---

## §6. Falsifiability Check (Round 2)

The §1.6 falsifiability section is real and concrete. Re-checking each:

| Falsifier | Observation? | When to check? | Action if fires? | Concrete? |
|---|---|---|---|---|
| **F-1** | ✓ re-introduction rate unchanged | ✓ after Phase 2, 5 production sessions | ✓ revert U-1 or escalate | ✓ |
| **F-2** | ✓ converged <0.7 AND stuck >0.85 | ✓ after Phase 1.5, 5 production sessions | ✓ re-tune or revert to heuristic | ✓ |
| **F-3** | ✓ parallel >50% of whole-doc baseline | ✓ on real 4-section design doc | ✓ re-tune N cap or revert | ✓ |
| **F-4** | ✓ collision observed | ✗ no time bound — fires only when collision happens | ✓ default-on session_id | ✓ |
| **F-5** | ✓ premise did not fire (RESOLVED) | ✓ already checked | N/A — resolved | ✓ |

**Quality assessment:**
- **Concrete and observable?** Yes for all five. F-4 is observation-based but the collision may never fire in practice — the falsifier is sound but its triggering depends on operator behavior.
- **When to check?** Four of five have explicit time bounds. F-4 doesn't (it's reactive). The combined-falsifier rule ("if ≥3 regress, comprehensive rollback") has no explicit "when to check."
- **What to do if it fires?** All five have specific actions. F-1, F-2, F-3 each have a real re-tune or revert path. F-4 has a default-on fix that's structural, not just "investigate."

**One gap:** the **combined-falsifier** rule for the whole design says "if ≥3 regress or fail to improve, comprehensive rollback" but doesn't say when this is checked. Should be tied to Phase 4 (validation phase): "After 5 production sessions, measure all 5 user-pain metrics. If ≥3 regress or fail to improve over baseline, comprehensive rollback to Phase 0."

---

## §7. Verdict

**Verdict: PROCEED — with one architectural inconsistency to resolve before implementation begins.**

### What holds
- **All 10 round 1 findings** were substantively addressed, not just text-added.
- **Premise #12** (single-point-of-failure) is RESOLVED against source code.
- **Falsifiability** is concrete and actionable (5 falsifiers + combined rule).
- **DEC-12** is a strong migration decision rule that converts "is dumb-pipe good?" into "when should dumb-pipe yield?"
- **Phase 1.5 gate** is real, not deferred.

### What needs resolution before implementation

**R2-N1 (architectural inconsistency):** The "0 lines added to relay" Non-Goal is incompatible with `previous_findings_path` as an "additional input field on the tick surface." The design should explicitly choose one of three resolutions before implementation:
- **Resolution A** (preferred): route `previous_findings_path` via coordinator-side sidecar (zero relay changes)
- **Resolution B**: acknowledge 1-2 relay lines and update the Non-Goal language
- **Resolution C**: add a generic pass-through mechanism (~5-10 relay lines)

Whichever is chosen, document it explicitly in §3 (Component 1).

### What can be tracked during implementation (second-order, not blocking)

- **R2-P1** — Dashboard god-object risk: add a "5th file opt-in rule" to dashboard header
- **R2-P2** — Schema versioning deprecation policy: specify "90-day support window" in `__lib/schema.mjs`
- **R2-P3** — 30% coupling threshold is arbitrary: tune after first 5 production uses
- **R2-P4** — Phase 1.5 historical-session fallback: specify synthetic-proposal fallback if <3 historical sessions exist
- **R2-F6** — Dashboard null-handling: specify "empty summary defaults" for missing sidecar files in `__lib/dashboard.mjs` header
- **R2-F4.5** — Combined-falsifier rule needs explicit "when to check" (Phase 4)
- **R2-Arg3** — Argument 3's "10:1 cost ratio" is fabricated; consider rewording to "the cost ratio is qualitatively high because..."

### Confidence

- **High** on the 10 round 1 findings being substantively addressed.
- **High** on Premise #12 being structurally workable (verified against source).
- **High** on the framing fixes being real, not text-added.
- **Medium** on R2-N1 — this is a real architectural inconsistency, but DEC-12 already provides a framework for resolving it.

### Recommendation

**PROCEED** — the design is ready for implementation **after** R2-N1 is resolved. The resolution is a one-paragraph addition to §3 specifying which of the three paths is taken. Once that's documented, the implementation can begin with U-1 (findings.mjs), U-2 (convergence.mjs), U-11 (dashboard.mjs), U-14 (schema.mjs), and U-15 (Phase 1.5 validation) as the Phase 1 deliverables.

### Note on process

The correctness reviewer's 0-findings sign-off reflected implementation correctness. The framing review (rounds 1 and 2) catches what correctness review doesn't: unexamined premises, metrics that measure preservation instead of value, architectural inconsistencies between claimed constraints and proposed mechanisms. Round 2 closes the framing work; implementation can begin after R2-N1 is resolved.