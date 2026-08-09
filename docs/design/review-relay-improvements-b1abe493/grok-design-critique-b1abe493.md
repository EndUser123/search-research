# Critical-Friend Review — Variant A: "Dumb Pipe Preserved"

**Author role:** Critical-friend reviewer (not code reviewer). Challenging **premises**, not implementation. The correctness reviewer signed off with 0 critical/major/minor/nit findings; I take that as given and look at what was *not* examined.

---

## Selected Critique Domains

### Core domains (always included)

1. **Problem framing** — what problem is the design actually solving?
2. **Optimal long-term vs simplicity** — is the "smallest diff" framing justified, or under-engineering?
3. **Falsifiability** — what observation would prove this design wrong?
4. **Anchoring** — what unexamined belief is the whole design resting on?
5. **Pre-mortem** — what would failure look like 6 months from now?

### Context-derived domains (selected because the design touches them)

- **Observed-vs-invented** — does the design fit existing workspace patterns (handoff lifecycle, sidecar files, convergence tracking) or invent a parallel pattern?
- **Concurrency / multi-terminal** — N parallel relays, session_id collision avoidance, multi-coordinator overlap
- **Migration / rollout** — phased opt-in, dormant helpers, partner opt-in asymmetry
- **Open-ended domain (detected in §4):** **Behavioral coupling under partner opt-in** — a structural risk not covered by the standard domain list, but central to whether this design delivers value.

I deliberately do **not** include Security, Cost/Performance, or Provenance/Identity as standalone domains — they are touched on but the design handles them adequately; spending a section on them would dilute the load-bearing critiques. They are mentioned inside pre-mortem instead.

---

## §1. Problem Framing

**The design says** (§1 Goal): *"Improve review-relay coordination in three measurable ways while keeping the relay itself an opaque-pipe transport."*

**The actual problem** (from the wiki concept that motivated this design, `review-relay-improvements-stable-key-lease-calibration-convergence-detection.md` Decision Context): a single proposal went through 7+ relay sessions producing 42 findings across 16 turns. Three *user-facing* pain points emerged:

1. Partners re-verifying previously agreed corrections
2. Coordinator having to read 7 result JSONs manually to know convergence state
3. No way to run section-focused reviews faster

**Drift:** The design treats the *user-facing* pain points as the goals but reframes the success criterion as **"relay source is byte-identical"** (§1 Success Metrics, §1 Failure Conditions). The metric table reads like "preserve the relay" rather than "reduce operator/partner pain." This is a textbook example of **constraint substitution** — the means (don't touch the relay) becomes the end (the success metric). Two of the five success metrics measure preservation, not improvement. The design's framing of "success" leaks the load-bearing premise (preserve dumbness) into the measurement layer.

**The right framing** would be: "Zero partner re-introductions of resolved findings, zero operator reads of result JSONs to assess convergence, ≥2x wall-clock speedup on 4-section proposals." The constraint is the *means*, not the *measure*.

---

## §2. Optimal Long-Term vs. Simplicity

### What is the optimal long-term solution?

**The optimal long-term solution is the one that survives future requirements without paying the cost twice.** Reading the design holistically:

- Future requirement: cross-section finding correlation (Section 3's finding depends on Section 1's terminology)
- Future requirement: adaptive lease (extend when score is approaching 0.85)
- Future requirement: finding provenance (which partner raised which finding first, weighted by seniority)
- Future requirement: convergence prediction (not just current state, but trajectory)

Every one of these **requires** relay-level intelligence. The dumb-pipe choice forces each future improvement to either (a) add another sidecar (the design's pattern, accumulating complexity), or (b) finally break the invariant. If (b) is inevitable, (a) is **delaying** the structural change, not avoiding it. The "future cost" is paid twice — once in sidecar complexity now, once in relay changes later.

The "dumb pipe" property was historically justified (nothing required intelligence — verified by premise-verification brief #8, which states the relay *has never* inspected findings because nothing asked it to). It was not architecturally justified. The writer preserves the **historical accident** as if it were **intentional design**.

### Is "smallest diff" optimal here?

**No, in two specific places:**

1. **The "Variant B strawman"** in §6.2 defines the inspecting-pipe alternative as "Add finding parsing to the relay AND maintain a finding state machine AND expose convergence score via `inspectState` AND make sections first-class in the controller." That's a **bundled** alternative — every possible smart-pipe change at once. A real Variant B would be one or two of those changes in isolation, e.g., "relay parses findings only, score computation stays in skill." The writer defined Variant B narrowly to make A look good. The alternatives table is not a fair comparison; it's a strawman followed by a preferred choice.

2. **The three improvements are coupled by implementation but independent by problem.** Finding lifecycle tracking, convergence score, and per-section parallel review solve **three separate user pains**. The design ships them together as one PR. If lifecycle tracking ships successfully but the score is uncalibrated, the rollout can't proceed without reverting one while keeping the others — but the design binds them as "one feature." An optimal long-term solution would **decouple** them so each can ship, validate, and roll back independently. The phased rollout (§6.9) gestures at this but the file-change inventory (§7) ships all helpers in one PR.

### What is currently missing that the optimal long-term solution requires?

- **A migration plan from dumb-pipe to smart-pipe** if future requirements force it. The design has a "rollback" section for §6.9 that says "removing findings.jsonl write from partner prompt = revert to current behavior" — but that ignores that **future requirements will demand the smart-pipe version**, and the rollout has no roadmap for getting there.
- **An empirical basis for the convergence weights.** The 0.5 / 0.3 / 2.0 split is **admitted** as "reasoned but not empirically validated" (§6.10 Open Question #5, DEC-9). The tuning recipe (§4) is operator-facing and requires 5 production runs to validate. But the design ships before validation — a classic "ship the metric, then calibrate the metric" anti-pattern. The first 5 production runs use unvalidated defaults, and the metric drives coordinator decisions on those runs. If the weights are wrong, **the wrong decision is made on real work**, not on test proposals.
- **A cross-section dependency model** for the per-section parallel review. Section-split assumes sections are content-independent. Design docs are typically **not** independently reviewable (Section 3's "finding" depends on Section 1's "contract"; Section 5's "outcome" depends on Section 2's "approach"). The design notes this in premise #11 but the mitigation is "regenerate section files each iteration" — that mitigates *edit drift*, not *semantic coupling*. Two sections can be perfectly aligned textually and still require cross-referencing during review.

### Coupling & code-smell inventory check

The design's own §6.3 inventory says **"OK, None"** on every metric. Reading the table closely:

- **DRY violations: "None"** — but the design introduces *three* new sidecar file formats (`findings.jsonl`, `convergence_history.jsonl`, `merged-findings.jsonl`+`merged-convergence.json`) plus three new helpers (`findings.mjs`, `convergence.mjs`, `split.mjs`+`merge.mjs`). These are coupled by **shared input data** (both `convergence.mjs` and the merge step read `findings.jsonl`; both `findings.mjs` and the relay's existing submit flow write to the bucket). Touching `findings.jsonl`'s schema requires coordinated updates in `findings.mjs`, `convergence.mjs`, partner prompts, and the merge step. That's ≥4 touch points for a schema change — over the §6.3 threshold. The "OK, None" verdict is **wrong by the design's own criteria**.

- **Mixed concerns: "OK (separation clean)"** — but `__lib/convergence.mjs` reads `result.json` (relay output), `findings.jsonl` (Component 1), and writes `convergence_history.jsonl`. The merge helper reads N section-review dirs (each is a relay bucket). Both helpers sit in the same `__lib/` namespace and are version-coupled. The "separation clean" verdict is technically true for *one helper at a time* but the helpers are **tightly coupled by shared data and shared coordinator workflow**.

### Summary

The "simplest version" (don't touch the relay, sidecars everywhere) is **under-engineering**, not optimal. The design's preservation-first framing delays the inevitable structural change. The Coupling & Code-Smell Inventory undercounts by ignoring cross-helper coupling.

---

## §3. Falsifiability

The design has **internal** falsifiability (the success metrics in §1) but the metrics are **preservation-flavored**, not improvement-flavored. Let me name falsifiers that the design does not list:

### Falsifier 1 — Sidecar pattern doesn't move the metric

Run a 6-turn review with the new helpers enabled. **If partners still re-introduce previously-resolved findings at a rate comparable to the baseline (the 42-finding/16-turn session), the design's central improvement failed.** The sidecar is a *vehicle*; partners must read it AND choose to honor it. The design assumes "make state visible → partners honor it." That's a behavioral assumption. Falsifier: ship U-1, run 5 production sessions, measure re-introduction rate. If rate is unchanged, the design delivered **infrastructure without benefit** — and the 1330 LoC of new helpers are pure cost.

### Falsifier 2 — Convergence score is inverted

Run 5 production sessions. **If converged runs (status `ready_for_parent_review`) score <0.7 on average AND stuck runs score >0.85, the score is inverted.** The default weights (0.5/0.3/0.2) are made up. The "tuning recipe" requires 5 production runs to validate, but those 5 runs *use* the unvalidated weights. If the weights are wrong, the score drives the coordinator to **declare early on stuck proposals and continue on converged ones** — exactly the wrong behavior. The score is "advisory" but the coordinator reads it (§4 §4 convergence_score readout), so advisory ≠ harmless.

### Falsifier 3 — Per-section parallel is slower, not faster

Run a 4-section split review on a real design doc. **If parallel wall-clock is NOT ≤25% of whole-doc baseline, the speedup claim fails.** Real-world parallelism has overhead: merge step, communication, partner prompt bloat, score computation, lease coordination across N sessions. The 25% target assumes near-linear speedup; realistic is 35-50% of baseline. Falsifier: if measured speedup <2x, the component delivers **coordination overhead, not speedup**.

### Falsifier 4 — Multi-coordinator collision F-02 actually fires

The collision avoidance for parallel coordinators (`opts.session_id`) is **opt-in**. **If operators forget to pass it and the collision materializes, the design fails silently** — both coordinators write to the same bucket, findings interleave, scores collide. The "default is safe for common case" claim is true only if the common case is **exactly one coordinator per proposal**, which is not the case for the workspace's multi-terminal pattern.

### Falsifier 5 — Premise #12 is "yes, forbidden" and the design didn't allow for it

Open Question #1: does `write_policy.forbidden_writes` block the sidecar write? If yes, U-1 cannot ship without **either** modifying the relay (violates invariant) **or** adding an explicit allow-rule (modifies the relay, violates invariant). The design says "Read source before coding U-1" — that's an open invariant violation, not a plan. **If premise #12 is "yes forbidden," the dumb-pipe invariant is incompatible with finding lifecycle tracking**, and Variant A is structurally unworkable. The design does not acknowledge this possibility.

The design is **partly falsifiable** (metrics exist) but the metrics measure preservation, not value. The pre-mortem below names more.

---

## §4. Anchoring

What premise did the writer bring in that wasn't examined?

### Anchor 1: "Dumb pipe is good" (the load-bearing axiom)

The premise-verification brief #8 explicitly says the relay is findings-agnostic *because nothing required it to look*. The writer treats this as **architectural virtue** ("the dumb-pipe invariant that has held since the relay was created" — §6.2 Option 1, my emphasis). It's not. It's a historical accident. Treating accident as virtue is the textbook **invented constraint** failure mode.

The unexamined belief: *"The relay being dumb is intentional, and adding intelligence would be wrong."* There's no argument for that. The §6.2 strawman argument is "Variant B violates dumb-pipe invariant" — that's an assertion of preference, not a justification. The actual argument for dumbness would have to address: what future requirements does dumbness enable? (None that I can name.) What costs does dumbness impose? (Sidecar accumulation, partner opt-in asymmetry, no cross-section correlation, no adaptive lease.)

### Anchor 2: "Partners will opt in"

The design relies on partners reading `findings.jsonl`. Old partners ignore it. The improvement only materializes if **all** partners opt in. There's no enforcement mechanism — partners can silently ignore the sidecar and the design "works" but delivers **zero benefit**. The design treats opt-in as a deployment detail, but opt-in is the **load-bearing adoption mechanism**. This is the classic "we shipped it but nobody uses it" failure mode. Compare with `wiki/concepts/design-choice-audit-challenge-every-decision-against-first-principles.md` line 38: *"Why wire review-relay? → I carried it forward from a prior session without re-examining fit"* — same anchoring pattern: carrying forward an assumption without examining whether it fits the new context.

The unexamined belief: *"Partners that benefit from lifecycle state will read it."* The actual evidence: the 42-finding session showed partners were already failing to track state from `previous_result_path` — they had access to the previous result and still re-verified. Adding another sidecar doesn't fix the underlying behavior; it adds another file partners can ignore.

### Anchor 3: "Convergence is a single number"

The score collapses three components (overlap, coverage, depth) into one. But convergence is **multi-dimensional**. A proposal can have high overlap (no new findings) but low depth (superficial engagement). A proposal can have full actor coverage but one actor producing shallow reviews. The single number **hides** this. The design claims "score distribution for offline tuning" as the response (§4), but offline tuning of an aggregated score cannot recover the lost dimensions. The aggregation is **irreversible information loss**.

The unexamined belief: *"A weighted sum is the right form for convergence."* The POIROT pattern cited as inspiration explicitly avoids single-number aggregation (per `domain-knowledge-brief.md` §2: "weighted consensus derived from structured peer interrogation, private voting, and proximity weighting" — multiple dimensions, not one number). The design borrows the name but discards the mechanism.

### Anchor 4: "Section independence"

Per-section parallel review assumes sections are content-independent. Design docs are **rarely** independently reviewable. Section 3's "the contract MUST validate inputs" depends on Section 1's "the contract is the JSON schema in Appendix B." A reviewer of Section 3 cannot validate the finding without Section 1. Splitting reviews breaks this. The design notes premise #11 but the mitigation is "regenerate section files each iteration" — that mitigates *edit drift*, not *semantic coupling*.

The unexamined belief: *"Section boundaries are review boundaries."* The premise is wrong for design docs where sections reference each other. The 25% wall-clock target depends on this premise being right.

### Anchor 5: "Make prior state visible → partner behavior changes"

The mechanism that prevents re-verification is **partner behavior**, not the sidecar file. A sidecar is a vehicle; the behavior is reading it AND choosing to honor it. The design says partners are *instructed* to consult the sidecar with explicit examples — but partners who would have ignored `previous_result_path` will ignore the sidecar. The design assumes "new file = new behavior," which is unverified.

---

## §5. Pre-Mortem (6 months from now)

Imagine this design shipped, partners adopted it (best case), and the system is in production. Failure scenarios the per-component failure-mode analysis (§6.4) missed:

### Failure scenario 1: The "dormant helpers" became tech debt

Phase 1 ships `findings.mjs` + `convergence.mjs` + tests. No partner uses them yet. Six months later, the helpers are 6 months old, the tests are green, but the helpers have **never been called from a production workflow**. They become maintenance burden — bug fixes for code no one uses, dependency updates for libraries only the helpers import, and the implementer has forgotten the design rationale. Phase 2 update to partner prompts may or may not happen. This is the "we shipped it but nobody uses it" path. The design has no metric for **adoption** (only for behavior change after adoption).

### Failure scenario 2: The convergence score misleads the coordinator

Default weights 0.5/0.3/0.2 ship. Coordinator reads the score. On the first 5 production runs, the score says 0.9 on a proposal where the partner is silently dropping findings (high overlap, low depth, low coverage — but the math weights overlap highest, so the score is high). Coordinator declares `ready_for_parent_review` based on a 0.9 score. Parent review finds 12 hidden findings. The "advisory" framing was supposed to prevent this, but the coordinator reads the score and trusts it. **Advisory ≠ harmless** — humans (and LLMs) treat numerical signals as evidence.

### Failure scenario 3: Per-section parallel review produces invalid reviews

A 4-section design doc has Section 1 defining "validation contract" used in Sections 2, 3, 4. The split splits the proposal into 4 files. Each partner reviews their section. Section 1's reviewer finds "validation contract should require nonce" — but Sections 2-4 already depend on the original contract. When merged, finding "F-001 from section 1" is treated as a real finding, not a cross-section artifact. Coordinator proceeds with merged findings as if they were coherent. Result: a finding that was **valid in section 1 only** becomes a **whole-proposal finding** when merged.

### Failure scenario 4: Premise #12 is "yes, forbidden" — invariant breaks

Open Question #1 (`write_policy.forbidden_writes` blocks partner writes outside active scratchpad) is the design's **single-point-of-failure premise**. If the answer is yes-forbidden, U-1 cannot ship without modifying the relay. The design treats this as "verify before coding" — that's an open invariant violation, not a plan. If the answer is yes-forbidden, Variant A is **structurally unworkable** and the entire design pivots to Variant B. The design does not have a contingency plan.

### Failure scenario 5: Multi-coordinator collision F-02 in production

Operator runs two coordinators on the same proposal (perhaps to compare model pools). Both compute the same `reviewKey`. Both write `findings.jsonl` to the same bucket. Findings interleave. Scores collide. Partners see interleaved history. The `opts.session_id` parameter was meant to prevent this but operators forgot to pass it (default behavior preserves "single coordinator per proposal"). The silent collision corrupts the lifecycle state and the convergence history. Rollback requires manual surgery.

### Failure scenario 6: The O(N) coordinator complexity

N parallel relays means **N independent lease cycles, N score computations, N convergence decisions**. With N=4, the coordinator runs 4x the lease management. With N=6 (the cap), it's 6x. The coordinator code that orchestrates this is **more complex than any single relay run**. The "skill-side helper" framing understates the coordination complexity. The "bound N at 6" cap is arbitrary and not justified.

### Failure scenario 7: Operator now reads MORE files, not fewer

The wiki concept's pain point was "operator had to manually read 7 result JSONs." The design adds `findings.jsonl` AND `convergence_history.jsonl` AND `merged-findings.jsonl` AND `merged-convergence.json`. Operator now has **5+ files to read** to assess a single review. The score was supposed to reduce this — but the score lives in `convergence_history.jsonl`, which the operator must read to interpret the score's components. **Operator's reading burden increased, not decreased.** The §1 success metric "Coordinator declares convergence with non-zero score" doesn't measure operator effort.

### Failure scenario 8: Premise #10 (pattern citations) turn out to be unverified

`domain-knowledge-brief.md` claims the patterns are real and verified. If subsequent research shows they aren't (the premise-verification brief flagged this as INFERENCE in #10), the entire "design inspiration" framing collapses. Helper files were named generically to dodge this, but the **architectural choices** (single-number score, per-section parallel, finding FSM) were borrowed from patterns that may not exist as described. If the cited patterns are wrong, the design's mechanisms are ungrounded.

---

## §6. Context-Derived Domain: Observed-vs-Invented

The workspace already has patterns for some of these problems. Let me name them and assess whether Variant A fits or invents a parallel pattern.

### Pattern in workspace: Handoff lifecycle (open → claimed → in-progress → resolved)

`P:/docs/handoffs/.../HANDOFF.md` carries an `investigation_state:` block with state transitions. The state machine is validated at write time, not at read time. Claim/release is via a script. This is a **different shape** than the proposed `findings.jsonl` FSM. The handoff pattern uses **status transitions in a single document** (not append-only JSONL). It also uses **claim-by-script** for multi-terminal safety, not session_id-in-path. The design invents a new mechanism when an existing one would have sufficed.

**Verdict:** the finding FSM could reuse the handoff pattern's claim/release discipline. The design's `by_actor` field is essentially the handoff's `claimed_by` field. **The design reinvents state-machine discipline that the workspace already has.**

### Pattern in workspace: Convergence heuristic in `~/.grok/skills/review-relay/SKILL.md:438-446`

The existing heuristic (verified by premise-verification brief #5) already answers the convergence question in plain English: converged/stuck/active. The operator's complaint was "I have to manually read 7 result JSONs." The score replaces **manual reading of result JSONs** with **manual reading of convergence_history.jsonl + score interpretation**. Net operator burden is roughly the same; the form changed (number + breakdown vs. natural-language heuristic). 

**Verdict:** the score is a **re-expression** of an existing heuristic in numerical form, not a new capability. The workspace already had the answer; the design changed the format without addressing the underlying complaint (operator effort).

### Pattern in workspace: Multi-coordinator overlap (F-05)

The premise-verification brief flags F-05 as a known risk. The existing workspace pattern for multi-terminal safety is **claim-by-script** (handoff claim). The design's `opts.session_id` is a different mechanism — opt-in parameter for path-collision avoidance. It does not address the **operator's** overlap problem (two coordinators launched unaware of each other), only the **system's** collision problem (same reviewKey from same path).

**Verdict:** the design invents a path-collision mechanism when the workspace already has a coordination mechanism. The session_id approach is necessary if handoff-claim doesn't fit, but the design doesn't compare the two.

### Pattern in workspace: Parallel coordinator on P:\

The workspace pattern for parallel work is **worktrees** (`P:/.data/wiki/concepts/git-worktree-multi-terminal-best-prategies.md`) or **session-scoped state files** (terminal IDs in filenames). The per-section parallel review launches N independent relays — but they share the same bucket root via the registryBucket helper. The design does not consider whether N parallel coordinators should use worktree isolation.

**Verdict:** the design's parallel-section pattern doesn't fit the workspace's parallel-work pattern. Worktrees would isolate section-reviews cleanly; the design's session_id-in-path is a partial substitute.

### Summary of observed-vs-invented

The design **invents three patterns** that the workspace already has equivalents for:
1. Append-only state-machine in `findings.jsonl` (handoff lifecycle exists)
2. Numerical convergence score (existing heuristic exists)
3. Path-collision avoidance (claim-by-script exists)

Each invention is **defensible** (the existing pattern doesn't fit exactly), but the design doesn't compare against them. An optimal long-term design would either **reuse** the existing pattern or **justify** why a new one is better. Variant A justifies nothing.

---

## §7. Context-Derived Domain: Concurrency / Multi-Terminal

### Parallel section relays

The design launches N independent relay sessions in parallel. Each session uses its own `reviewKey` (path-derived, different per section). **But the lease lifecycle is per-session, not coordinated.** Section A's lease expires while Section B is still active. The coordinator must wait for all N to converge (per §5 F-07 worst-of-N rule) — but with N independent leases, the coordinator's wait time is `max(lease_remaining across sections)`, not the merged time.

The design says "each section has independent lease; other sections proceed" (§6.4 Component 3 recovery row). But the coordinator decision rule (§4) waits for all N. If section B is stuck and section A converges, section A's lease expires while waiting for B's eventual convergence. **N parallel relays have N lease cycles but 1 coordinator decision.** This is a coordination bug.

### Multi-coordinator overlap F-05

The design addresses reviewKey collision via `opts.session_id` (opt-in). It does not address **the operator launching two coordinators on the same proposal path** (the premise-verification brief flagged this). The `session_id` approach assumes operators remember to pass it. **Operators forget. Multi-terminal workflows on this host are exactly the case where forgetting happens.**

The workspace pattern for multi-terminal safety is **claim-by-script** (handoff claim, terminal IDs in filenames). The design's session_id approach is necessary but not sufficient. A coordinator that doesn't claim its session has no protection against a sibling coordinator.

### Sidecar file race

`findings.jsonl` and `convergence_history.jsonl` are written by the coordinator, not by the relay. The relay's `forbidden_writes` covers partner writes; the design does not verify it covers coordinator writes. If the relay's write_policy permits coordinator writes to the bucket root but forbids coordinator writes to other turns' directories, the sidecar works. If not, the design hits the same wall as premise #12 (UNKNOWN).

**Verdict:** the design's concurrency model assumes single-coordinator, sequential turns. Multi-coordinator, parallel-section workflows are not robustly designed. The session_id patch is insufficient.

---

## §8. Context-Derived Domain: Migration / Rollout

### Phased rollout ships dormant code

Phase 1 (§6.9) ships `findings.mjs` + `convergence.mjs` + tests as "dormant helpers." Dormant helpers are tech debt in waiting. The next 6 months of maintenance burden (dependency updates, security patches, bug fixes) apply to code that delivers **zero value** until Phase 2 ships. The design has no deprecation trigger if helpers stay dormant — they just persist.

**Verdict:** the phased rollout is reasonable for **risk reduction** but unreasonable for **value delivery**. An optimal design would either (a) ship helpers and partner prompts together in one PR, accepting the higher rollout risk, or (b) defer the helper code until partner prompts are ready to use it. Splitting them creates a window of pure cost.

### Partner opt-in asymmetry

Partners that opt in read the sidecar; partners that don't ignore it. The design does not specify what happens when **some partners opt in and others don't**. Scenario: actor A reads `findings.jsonl`, actor B ignores it. Turn 1: A writes a finding as `open`. Turn 2: A reads it, transitions to `upheld`. Turn 3: B writes the same finding as `open` again (because B doesn't read the sidecar). Turn 4: A sees two `open` records for the same `finding_id`. The FSM validator rejects the second `open` (state machine: open can only be entered from nothing). B's turn fails validation. **B has to fix it and re-submit. Another lease cycle. Another 600s.**

The design does not address this case. The opt-in asymmetry is **structurally fragile** — partial adoption produces invalid state.

### Schema migration cost

`RESULT_SCHEMA_VERSION` is bumped only when partners need new fields (§1 Non-Goals). The design adds `previous_findings_path` to the tick surface — but **does not bump the schema version** because the relay doesn't parse it. This is the wrong call. The schema version exists to signal **to partners** that the input surface changed. Partners reading `previous_findings_path` need to know it's there. By not bumping the schema, the design hides a new field from partners that might want to use it but don't know to check.

**Verdict:** the rollout's "no schema change" framing is **false** — the input surface gained a field. Partners that aren't told will miss it.

---

## §9. Open-Ended Domain: Behavioral Coupling Under Partner Opt-In

This domain is not in the standard list but it is central to whether the design delivers value. I name it explicitly because skipping it would be a structural omission.

### The problem

The design's three improvements all rely on **partners changing behavior**:
- Finding lifecycle: partners must read `findings.jsonl` to honor prior state
- Convergence score: coordinator must read `convergence_history.jsonl` to use the score
- Per-section parallel: coordinator must invoke `splitProposal` to enable

None of these are enforced. All are opt-in. The design treats opt-in as a deployment detail; **opt-in is the load-bearing adoption mechanism**. The design ships infrastructure for behavior change but does not measure whether the behavior changed.

### Why the existing heuristic already works

The workspace's existing convergence heuristic (§5 in premise-verification brief, SKILL.md:438-446) is **in the skill's prompt**, not in the relay's code. It works because the coordinator is an LLM that reads its own skill prompt. The heuristic has been in production since 2026-08-08 (per §1 evidence-brief note). No one has reported it failing. The heuristic is **behavior-coupled, opt-in, but proven** — because the prompt instructs the coordinator to use it.

The new helpers (findings.jsonl, convergence_history.jsonl) are also behavior-coupled and opt-in. But they require **partners** to honor the sidecar, not just the coordinator. Partners are external models (Codex, Grok, Pi, OpenCode per SKILL.md default user interface). Partner opt-in is **harder** than coordinator opt-in because:
- Partners are launched by the coordinator; their prompts are templated
- Partner prompts may not be updated when the sidecar is added
- Partner model behavior is variable — some may read sidecars, some may not

The design does not verify whether partner prompts are updated. Phase 2 §6.9 says "Update SKILL.md and partner prompts" — that's the only mention. If partner prompts are updated inconsistently across model pools, opt-in is partial and the failure mode of §8.1 (asymmetric state) materializes.

### What this means

The design's success depends on **a coordination problem outside its scope** — making partner prompts adopt the new behavior consistently across model pools. This is **not a software problem; it's an operational problem**. The design does not have a plan for it.

### Recommendation

Add to the design:
1. **Partner prompt update mechanism** — how does the new template propagate to all model pools?
2. **Adoption metric** — measure not just re-introduction rate but **sidecar-read rate** (does the partner call `read(previous_findings_path)` at all?). Without this, you can't tell adoption from behavior change.
3. **Default-on** vs **default-off** for partner behavior — the design treats opt-in as default-off. If default-on, partners always read the sidecar (even when empty); the design works because the sidecar is part of the contract, not an enhancement.

---

## §10. Verdict

**Verdict: REVISE.**

The design's framing is **partially sound** — the three improvements are real user pains and the sidecar pattern is a reasonable decomposition. But the design rests on **unexamined premises** that, if false, break the design:

1. **The dumb-pipe invariant is treated as architectural virtue when it's a historical accident.** The design's central constraint ("relay source is byte-identical") is preserved at the cost of accumulating sidecar complexity. An optimal long-term solution would either embrace the invariant with a stronger justification, or migrate toward smart-pipe incrementally.

2. **The Variant B strawman makes the comparison unfair.** A real inspecting-pipe alternative would isolate one or two relay changes (e.g., just finding parsing). Bundling every smart-pipe change into one "Variant B" makes Variant A look like the only reasonable choice.

3. **The convergence score ships with unvalidated weights.** "Advisory" ≠ harmless. The coordinator reads the score; the score drives decisions; unvalidated weights drive wrong decisions on real work.

4. **Per-section parallel review assumes section independence** that design docs often lack. The 25% wall-clock target depends on a premise that may be wrong.

5. **The opt-in asymmetry is structurally fragile** and not addressed.

6. **Premise #12 (write_policy.forbidden_writes) is a single-point-of-failure** for the entire design. If forbidden, Variant A is structurally unworkable.

### Specific issues to address before implementation

- **Issue A:** Add a falsifiability section with concrete observation-based falsifiers (not just preservation metrics). Include §3's five falsifiers.
- **Issue B:** Justify the dumb-pipe invariant architecturally, or migrate toward smart-pipe incrementally. The current justification ("violates invariant") is preference, not argument.
- **Issue C:** Decouple the three improvements into independent shippable units. Each can ship, validate, and roll back independently.
- **Issue D:** Validate convergence weights on test proposals **before** shipping the score. Or ship the heuristic as the only convergence signal and add the score as Phase 4 (after metrics exist).
- **Issue E:** Add a partner prompt propagation mechanism and an adoption metric. The design's success depends on partner behavior change, which is outside the design's scope.
- **Issue F:** Resolve premise #12 before committing to U-1. The design's first unit is blocked on an unknown.
- **Issue G:** Redefine the "success metrics" to measure **user-pain reduction**, not preservation. Specifically: "0 re-introductions" (good), "score ≥ 0.85" (the score is the means, not the goal), "relay source empty" (this is a constraint, not a metric).
- **Issue H:** Justify the `min`-of-N merge rule or replace it with a coupling-aware aggregation. The current rule assumes section coupling that may not exist.

### Recommendation format

- **REVISE.** The design has a framing issue — preservation is treated as virtue, the alternatives are strawmanned, and the success metrics measure constraint satisfaction rather than user-pain reduction. Address Issues A-H before implementation. Confidence: HIGH on the diagnosis, MEDIUM on the specific issues (some may resolve differently under the writer's framing).

### Note on process

The correctness reviewer signed off with 0 findings because they reviewed **the implementation**. The design's correctness is fine; its **framing** is the issue. A critical-friend review (this document) catches what correctness review doesn't: unexamined premises, strawman alternatives, metrics that measure preservation instead of value, and coupling assumptions that the design perpetuates rather than examines.

---

## Appendices

### A. Sources cited

- `grok-design-doc-b1abe493.md` — the design (593 lines)
- `grok-design-summary-b1abe493.md` — writer's summary (75 lines)
- `premise-verification-brief.md` — premise verification (60 lines)
- `domain-knowledge-brief.md` — pattern research brief (50 lines)
- `grok-design-review-b1abe493.md` — correctness reviewer report (10 lines, 0 findings)
- `P:/.data/wiki/concepts/review-relay-improvements-stable-key-lease-calibration-convergence-detection.md` — motivating wiki concept
- `~/.grok/skills/review-relay/SKILL.md` — existing skill with convergence heuristic at lines 438-446

### B. Premises flagged but unaddressed by the design

From `premise-verification-brief.md`:
- **#8 (load-bearing):** "introducing finding lifecycle tracking requires the relay to start inspecting result content (currently opaque). This is a structural shift, not an incremental change." → The design treats this as solved by sidecars. The brief notes this is the highest-risk premise; the design does not address the brief's framing.
- **#10:** "The 'ReviewingAgents/POIROT/GPT Researcher' pattern names in the wiki concept may not be real paper names." → `domain-knowledge-brief.md` claims they are real. The design uses them as design inspiration but the mechanisms borrowed are not the patterns' actual mechanisms (single-number score is not POIROT's actual mechanism).
- **#11:** "Per-section parallel review would require either (a) splitting the proposal file into N section-files before relay start, or (b) adding a section-aware dispatch primitive to the relay." → The design picks (a) but doesn't compare it against (b) properly.
- **#12 (UNKNOWN):** `write_policy.forbidden_writes` may block partner writes. → Design flags this as Open Question but treats it as a verification task, not a structural risk.

### C. Open questions the design adds

- Does the 25% wall-clock target account for cross-section coupling? (§5 Failure Scenario 3)
- Does the operator's reading burden increase or decrease? (§5 Failure Scenario 7)
- Is the convergence score a re-expression of the existing heuristic in numerical form? (§6 Pattern 2)
- Does the design's success depend on partner behavior change that's outside its scope? (§9)
---

## Response to Critical-Friend Review — Revision 3 Disposition

**Author:** Writer A (Variant A — Dumb Pipe Preserved)
**Verdict received:** REVISE
**Document revised:** grok-design-doc-b1abe493.md

### Per-finding disposition

Using the user's numbered mapping (Finding 1 = Issue G, Finding 2 = Issue B, Finding 3 = strawman, Finding 4 = Issue D, Finding 5 = Issue A, Finding 6 = operator burden, Finding 7 = Issue C, Finding 8 = Issue F, Finding 9 = Issue E, Finding 10 = Issue H):

| Finding | Critical friend's claim | Disposition | Where addressed in revised doc |
|---|---|---|---|
| **1** | Success metrics measure preservation, not improvement | **addressed** — replaced preservation metrics with user-pain-reduction metrics; "0 lines added to relay" demoted to Non-Goal | §1 Success Metrics (revised) |
| **2** | Dumb-pipe is historical accident, not architectural virtue | **addressed** — chose option (a) with architectural justification + graceful migration path. 5 arguments with citations; DEC-12 encodes the decision rule for when to migrate | §2 "Architectural Justification for Dumb-Pipe Preservation" + §2 "Graceful Migration Path" + DEC-12 |
| **3** | Variant B is a strawman | **addressed** — added fair middle option (Option 1B: inspecting-pipe for findings only, score+section still skill-side) | §6.2 Option 1B |
| **4** | Convergence weights unvalidated; "advisory" ≠ harmless | **addressed** — chose option (c): both. Strengthened DEC-7 → DEC-13 ("MUST NOT use score as sole signal"); added Phase 1.5 validation gate | §4 Coordinator Decision Rule (revised) + DEC-13 + Phase 1.5 in §6.9 |
| **5** | Falsifiability section missing (Issue A) | **addressed** — added §1.6 Falsifiability with 5 concrete observation-based falsifiers | §1.6 Falsifiability |
| **6** | Operator reading burden increases, not decreases | **addressed** — added __lib/dashboard.mjs consolidating all sidecars into single JSON output with 
ext_action derivation | §4 "Operator Reading Burden: Dashboard Helper" + U-11 |
| **7** | Coupling inventory undercounts cross-helper coupling | **addressed** — re-counted honestly: 4 touch points for finding schema change, 4 for score schema; added __lib/schema.mjs versioning module as structural fix | §6.3 (revised) + U-14 |
| **8** | Premise #12 is single-point-of-failure for Variant A | **addressed** — RESOLVED via direct source read. llowed_writes includes 	urns/** (line 964); partners CAN write findings.jsonl. Skill-written sidecars not subject to write_policy. **Variant A is structurally workable by construction.** | §6.10 #1 (revised as RESOLVED) |
| **9** | Partner opt-in adoption is structurally fragile | **addressed** — added default-on prompt (vs default-off), multi-pool propagation PR in Phase 2, adoption metric in dashboard, threshold escalation rule | §6.9 Phase 2 + U-12 + REQ-19 + §6.10 #7 |
| **10** | Section-independence assumption fails on coupled docs | **addressed** — chose option (b): added split.analyzeCoupling() with ≥30% weight threshold for fallback to whole-proposal review | §5 splitProposal Step 1 + U-13 + REQ-18 |

### Self-discovered issues during revision (N-02, N-03)

- **N-02:** The Phase 1 rollout shipped dormant helpers with no deprecation trigger. Added Phase 1.5 to Phase 4 sequence with explicit metrics collection — dormant code now has a value-delivery deadline.
- **N-03:** The §8 Rollback section said "removing findings.jsonl write from partner prompt = revert to current behavior" — but the coordinator-side helpers (dashboard, convergence) had no rollback. Added per-helper rollback language in §6.9.

### Pushback (won't change)

The critical friend is **correct** that the original Option 1 was a bundled strawman. The fair Option 1B is now in the alternatives table. I am **not** changing the choice from Variant A to Variant 1B, because §2 Architectural Justification argues that even isolated finding inspection breaks the contract for downstream consumers (handoff writers, external partner integrations). The decision is evidence-based, not preference-based.

### What did NOT change

- The relay source code remains untouched (src/review-relay.mjs line count unchanged)
- The 7+ requirement trace matrix structure
- The existing tests in 	ests/review-relay.test.mjs
- The esult.status enum semantics (eady_for_parent_review is still a status enum, not a boolean — premise #3 still holds)

### Document size impact

- Lines: ~430 → ~570 (+140)
- New LoC estimate: ~1330 → ~1830 (+500)
- New artifacts: 4 REQs, 3 DECs, 6 implementation units, 2 test files, 2 helpers, 1 dashboard, 1 schema module
- Relay LoC delta: 0 (still — invariant held through Revision 3)

### Verification of critical-friend issues

| Issue | Verified at |
|---|---|
| A — Falsifiability | §1.6 Falsifiability table (5 falsifiers) + combined-design-falsifier |
| B — Dumb-pipe | §2 Architectural Justification (5 arguments) + Graceful Migration Path + DEC-12 |
| C — Decoupling | U-11 (dashboard), U-13 (coupling analyzer), U-14 (schema module) — 3 new decoupled units |
| D — Weights | Phase 1.5 in §6.9 + DEC-13 ("MUST NOT") + REQ-15/REQ-16 |
| E — Partner adoption | §6.9 Phase 2 multi-pool + U-12 + REQ-19 + §6.10 #7 |
| F — Premise #12 | §6.10 #1 RESOLVED with source-code receipts |
| G — Metrics | §1 Success Metrics (revised) — preservation metrics removed, user-pain metrics added |
| H — min-of-N | §5 splitProposal Step 1 coupling analysis + U-13 + REQ-18 (coupling-aware fallback) |
