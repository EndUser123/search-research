---
title: "ADR-011: Review-relay dumb-pipe invariant — ship sidecar-first, migrate to inspecting-pipe only on production bottleneck"
created: 2026-08-09
source: /design run b1abe493 on 2026-08-09
tags: [adr, review-relay, architecture, dumb-pipe, inspecting-pipe, migration-rule, decision]
agents: [grok]
host: grok
verification: source-verified
relations:
  - target: wiki/concepts/review-relay-improvements-stable-key-lease-calibration-convergence-detection.md
    type: extends
  - target: wiki/concepts/adversarial-multi-agent-code-review.md
    type: related
  - target: wiki/concepts/llm-handoff-best-practices.md
    type: cites
---

# ADR-011: Review-relay dumb-pipe invariant — ship sidecar-first, migrate to inspecting-pipe only on production bottleneck

## Status

**Accepted** (2026-08-09). Bound to the review-relay system until the migration trigger in "Revert path" fires.

## Context

The review-relay (`P:/packages/codex-external-delegation/src/review-relay.mjs`, 1522 lines) has been a findings-agnostic transport since inception: it moves result content between partner turns opaquely, never parsing or inspecting finding structure. Three architectural improvements were proposed (finding lifecycle tracking, continuous convergence score, per-section parallel review) that could each be implemented either as skill-side sidecars (preserving the invariant) or as relay-level features (breaking it).

The `/design` run (b1abe493) surfaced the load-bearing question: **is the relay's findings-agnosticism an architectural virtue to preserve, or a historical accident ripe for migration?** Premise-verification brief #8 verified the relay has never inspected findings, but did not establish *why*.

## Decision

**Ship the three improvements as skill-side sidecars (Variant A: dumb pipe preserved). Migrate to inspecting-pipe only when both of these conditions hold:**

1. The skill-side mechanism has been a **production bottleneck for ≥30 days** (measured: coordinator overhead exceeds 10% of relay wall-clock, OR sidecar file count exceeds operator dashboard capacity)
2. At least one of these future requirements has materialized:
   - Cross-section correlation (a finding in section 1 references a contract in section 3)
   - Adaptive lease (lease duration depends on finding complexity)
   - Finding provenance (relay-level attribution across multi-partner flows)

Until both conditions fire, the dumb-pipe invariant holds: `src/review-relay.mjs` stays byte-identical, with new behavior in `~/.grok/skills/review-relay/__lib/`.

## Rationale (5 arguments)

1. **Documented stability.** The transport contract (`tick`/`submit`/`inspectState`, lease lifecycle, snapshot hashing, `atomicWriteJson`) has been stable across 7+ design iterations since 2026-08-08. Stability is a documented feature, not an absence of code.

2. **Sidecar pattern meets new requirements.** Convergence score (Component 2) demonstrates this: a numeric convergence signal was added via sidecar + skill helper, no relay change. Future requirements can follow the same pattern at O(requirements) file cost, not O(requirements) relay changes.

3. **Cost ratio favors sidecars.** Refactoring the relay to inspect findings is irreversible (changes what the relay *means*) and breaks every partner integration that depends on the opaque contract. Adding sidecars is reversible (delete a file) and additive (new partners ignore old sidecars). Cost ratio ≥10:1 in favor of sidecars for any specific requirement.

4. **Workspace convention.** Per `[[llm-handoff-best-practices]]` §"Implications for a solution architect operating a fleet": skills are smart (compute, decide, validate); transports are dumb (move bytes, enforce leases, validate hashes). The relay is a transport. Skill-side helpers honor the convention.

5. **Testability.** `git diff src/review-relay.mjs` returning empty is a one-line assertion. Smart-pipe migration requires re-deriving the entire test surface (~520 lines of fixtures).

## Alternatives considered

### Alternative 1: Inspecting-pipe — finding parsing in the relay

**Description:** relay parses findings from each submitted result, maintains per-session state machine, exposes convergence score via `inspectState`.

**Rejected because:**
- Breaks the documented transport contract partners integrate against
- Test surface grows non-linearly (each test fixture needs finding-interpretation re-derivation)
- Couples partner schema to relay schema (today partners can change `findings` shape freely)
- Relay has no semantic understanding of finding overlap; the skill does — score reliability degrades if computed in the relay

### Alternative 2: Isolated inspecting-pipe for findings only (skill-side for score + sections)

**Description:** relay parses findings only (for the state machine), but convergence score and section split remain skill-side. Middle-ground option surfaced by critical friend round 1 (finding 3) as a fairer comparison than the bundled Variant B.

**Rejected because:** even isolated finding inspection breaks the contract for downstream consumers (handoff writers, external partner integrations). The decision rule above (ship dumb-pipe first, migrate on bottleneck) handles the case where this isolation turns out to be needed — but the default is no inspection.

### Alternative 3: Do nothing

**Rejected because:** the 42-finding/16-turn session that motivated this design repeats. Partners re-verify previously resolved findings; coordinator has no convergence signal beyond the binary status enum.

## Consequences

### Positive

- Relay source stays byte-identical → existing test suite (520+ lines) passes unchanged
- Partner integrations remain backward-compatible
- Three architectural improvements ship without transport-layer risk
- Migration path documented; if future requirements force inspection, the wire format (`findings.jsonl`) is the contract, only the parser location moves

### Negative

- Operator reads `convergence_history.jsonl` and `findings.jsonl` via dashboard helper instead of via `inspectState` directly (extra indirection)
- Partner prompts grow by ~200 tokens (findings.jsonl reading instructions)
- Skill-side helpers accumulate: 6 new modules (`findings.mjs`, `convergence.mjs`, `split.mjs`, `merge.mjs`, `dashboard.mjs`, `schema.mjs`) totaling ~1830 LoC

### Neutral

- Convergence score is advisory; coordinator may override
- Section-split is opt-in; coordinator decides when to invoke

## Shelf life / assumptions at risk

- **Assumption:** the workspace convention "skills smart, transports dumb" continues to hold. If a future fleet-wide architectural shift inverts this (e.g., transports become stateful orchestrators), the dumb-pipe invariant may need re-evaluation.
- **Assumption:** sidecar file accumulation remains tractable. If the number of sidecar files grows beyond operator dashboard capacity (current: 4 files, dashboard-consolidated to 1), the migration trigger fires.
- **Time bound:** this ADR is bound to the review-relay system. If the relay is retired or substantially rewritten, the ADR is moot.

## Known failure modes

1. **Sidecar proliferation.** Each new requirement adds a sidecar file. Dashboard helper must keep up. Mitigation: dashboard.mjs consolidates; if it becomes a god-object, refactor.
2. **Partner non-adoption.** If partner prompts don't read `previous_findings_path`, lifecycle tracking is infrastructure without benefit. Mitigation: Phase 2 ships default-on partner behavior with adoption metric (≥95% within 30 days).
3. **Convergence weight miscalibration.** Weights (0.5/0.3/0.2) ship unvalidated. Mitigation: DEC-13 contract — score MUST NOT be sole coordinator signal; Phase 1.5 validates against ≥3 historical sessions before Phase 2.
4. **Section-split on coupled docs.** `split.analyzeCoupling()` detects ≥30% cross-section reference density; above threshold falls back to whole-doc review.

## Revert path

**Reverting a single component:** each helper is opt-in. Removing `findings.jsonl` write from partner prompt = revert to current behavior. No data loss; no schema migration.

**Reverting the entire decision (migrating to inspecting-pipe):**
1. Add a parallel relay-side parser gated by manifest flag `write_policy.findings_state_machine: "skill" | "relay"` (default `"skill"`)
2. Ship side-by-side for ≥30 days
3. Promote `"relay"` to default only after skill-side mechanism proves insufficient in production
4. Keep `findings.jsonl` as the wire format throughout; only parser location moves

**Cost of revert:** bounded. The wire format is the contract; parser location is implementation. Worst case: 1-2 relay source changes + 1 manifest flag.

## Falsifier

This decision is wrong if:

- After shipping all three components (Phase 1-3 complete) and running 5 production sessions, ≥3 of the user-pain metrics regress or fail to improve over baseline (re-verification rate, time-to-convergence, operator file-read burden, partner adoption rate, section-split wall-clock). Trigger: comprehensive rollback to Phase 0.
- The skill-side mechanism becomes a documented production bottleneck for ≥30 days AND no inspecting-pipe migration is planned. Trigger: this ADR's decision rule fires — migrate.

## Source

- `/design` run b1abe493 (2026-08-09), design doc at `C:/Users/brsth/AppData/Local/Temp/grok-design-b1abe493/grok-design-doc-b1abe493.md`
- Premise verification brief (9 [FACT]s with grep receipts against `src/review-relay.mjs`)
- Critical friend round 1 (REVISE → 10 findings addressed) + round 2 (PROCEED with one implementer caveat)
- Reviewer consensus (0 critical/major across 2 rounds)