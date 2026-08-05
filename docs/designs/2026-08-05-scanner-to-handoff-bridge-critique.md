# Critical Friend Review — Scanner→Handoff Bridge

**Design under review:** `C:\Users\brsth\AppData\Local\Temp\grok-design-50bff7f4\grok-design-doc-50bff7f4.md`
**Summary:** `C:\Users\brsth\AppData\Local\Temp\grok-design-50bff7f4\grok-design-summary-50bff7f4.md`
**Reviewer stance:** Critical friend — challenging **premises**, not implementation. The correctness reviewer already cleared 0 HIGH issues. The implementation plan is well-structured, tests are interleaved, falsifiers are explicit. So this critique assumes the implementation will be executed roughly as designed and asks: *should it be?*

---

## Step 1 — Domain Selection

**Core domains (always included):**
1. Problem framing
2. Optimal long-term vs. simplicity
3. Falsifiability
4. Anchoring
5. Pre-mortem

**Context-derived domains (selected based on what the design touches):**
- **Migration / rollback** — additive flag to live skills, refactor of `__init__.py` + `from_aar.py`, persistent files on disk that outlive a failed rollout.
- **Concurrency / multi-terminal** — multi-agent Windows host with concurrent LLM sessions on shared filesystem; journal filename uses 8-hex session prefix; marker dedup scans handoff tree.
- **Cost / performance** — token blow-up is named explicitly (Category 7); 30-item journal → 30 cold-start readers; journal directory grows unbounded.
- **Provenance / identity** — `current_session_id` and `current_terminal_id` are explicitly overridden from journal into the handoff; the design claims this preserves cross-session chain.
- **User workflow fit** — bridge introduces a new two-step operator ritual (`/todo --journal && /handoff --from-journal`); `/close` integration is HANDOFF, not COMMIT.
- **Observed-vs-invented** — design claims reuse of AAR-report mode pattern, 17-field handoff schema, and `claim_handoff.py` session-id-short convention. Each is a load-bearing claim that was not verified in this document.

**Open-ended domains (detected during reading):**
- Self-dogfooding / self-verification (F-21) — design acknowledges this; the structural fix is sibling validation.
- Wiki-capture bypass — scanner items flag wiki concerns; routing to handoffs may bypass `/wiki` capture.
- AGENTS.md alignment — the "automate user meta-actions" rule argues for auto-invocation; the design preserves manual invocation.
- Subagent coordination — `/close` integration deferred, but multi-agent sessions may have other natural trigger points.

---

## Step 2 — Core Domain Critique

### 1. Problem framing

The design frames the problem as: "scanner items evaporate at session end." Five categories are named; the bridge is the cure. **Problem:** the frame assumes items the LLM *evaluates but does not act on* are a category of work that deserves cross-session durability. They may instead be the LLM's "I am flagging this for visibility, but I am not committing to act" signal. Persisting that signal at the same priority as the LLM's written handoffs is a category error — the LLM's choice to render something as output without writing a handoff for it is *information*, not a bug.

**Reframe:** the gap is not that items evaporate; the gap is that the LLM does not write handoffs for items that *should* be acted on. The bridge persists *all* evaluated items, including ones the LLM chose not to act on. The 20% false-positive rate (F-pos-1) is the design acknowledging this — but the framing pretends it is a bug rate when it may be the design's own contribution to the problem.

**Premise challenge:** if most "evaporating" items are correctly chosen not-to-act by the LLM, the bridge creates a triage burden the operator must police (the very meta-action the design claims to automate). If most evaporating items *are* correctly chosen to-act, the fix is teaching the LLM to write handoffs in-band during evaluation, not adding a separate persistence layer.

### 2. Optimal long-term vs. simplicity

"Two thin extensions" is the simplicity framing. **Long-term view** (12+ months):

- Journals accumulate. The `/close --cleanup` to prune journals older than N days is HANDOFF (Unit 9). Without it, `P:/.data/state/todo-journals/` becomes unbounded. Operator must remember to clean. Meta-action again.
- The handoff store grows faster. Each scan produces ~5–10 clusters → 5–10 handoffs per session. Over 6 months: thousands of journal-derived handoffs. The bounded marker scan (`P:/docs/handoffs/todo-*/`) is O(N) where N grows monotonically.
- The 17-field schema is reused. F-pos-3 admits this may be too heavy. If F-pos-3 fires, the bridge needs a `handoff_type: scanner-action` variant — a third sub-mode of `/handoff` alongside transcript and AAR. Mode detection grows.
- The "auto-fire at /close" integration is deferred. Once it ships, the bridge runs every close — which means journals appear even when the operator did not want them (e.g., mid-investigation closes, abandon-and-restart closes).

**Optimal long-term alternative:** make `/todo`'s Step 1 evaluation *write handoffs in-band* for items it considers actionable. No journal layer. No marker dedup. No `/close` integration. The LLM already has the write capability; the design adds a translation layer instead of using it.

**Premise challenge:** the design chose persistence-layer simplicity over evaluation-layer change. That choice is reversible but the cost of reversing later (after journals and handoffs accumulate) is high. Shipping the simpler design *now* may foreclose the better design.

### 3. Falsifiability

Falsifiers are explicit and thresholded. **Issues:**

- **F-pos-1 (20% false-positive rate) is too lenient.** A 20% rate means 1 in 5 journal-derived handoffs is operator-visible noise. The grounding cites "AGENTS.md automate user meta-actions" but 20% is far above the threshold at which a system stops being automated and starts being a meta-action to police. A 5% threshold would be more honest. The 20% threshold is set high enough that the design is unlikely to fail — that is a movable goalpost smell.
- **F-pos-2 (≤2 duplicates per 90 days) contradicts the dedup design.** The design hashes normalized titles — lowercase, whitespace-collapsed, trailing-stripped. But scanner items get rephrased: "Fix hook stderr" becomes "Fix the hook stderr output" becomes "Stderr in hooks not empty." Each is a different hash. S2 will likely fail not because dedup is wrong but because the dedup scope (case + whitespace) is too narrow. The design admits this is a known limitation but the falsifier threshold does not reflect it.
- **F-pos-4 (zero usage over 3 months → solves a non-problem)** is the most important falsifier and it has no enforcement. If operators forget to invoke (which is the entire meta-action problem the bridge claims to solve), the falsifier fires — but only after 3 months of silent non-use. That is reactive, not proactive.
- **F-pos-3 (17-field schema too heavy) requires v0.2.** Shipping a heavy schema when an admitted failure mode exists is a sign the schema was chosen for reuse, not fit.

**Premise challenge:** the falsifiers look rigorous but are calibrated to pass. A 5% false-positive threshold and a 30-day no-usage cutoff would catch the design's own failure modes earlier.

### 4. Anchoring

The design is heavily anchored to the AAR-report mode pattern. **Load-bearing claim:** "the journal file is structurally identical to an AAR report's item list." **This is a forced analog, not a structural identity.**

- AAR items are retrospective (what happened in past sessions). Scanner items are prospective (what to do next).
- AAR's dependency grouping is by *domain*. Journal's dependency grouping is by `{source, path-prefix, section}`. The design admits these are different — so the "reuse" is "uses the same dispatcher" rather than "same shape."
- The 17-field handoff schema was designed for retrospective-action handoffs (what to learn from past work) and standard project handoffs. Scanner handoffs are *new-work* handoffs. The schema inheritance assumes the field set fits; F-pos-3 admits it may not.
- AAR mode was added to `/handoff` in v0.1 to handle cross-session retrospective output. The journal mode is a parallel use case (cross-session prospective routing) bolted onto the same dispatcher.

**Premise challenge:** the anchor "reuse AAR pattern" is the design's strongest rhetorical move but its weakest technical one. The two modes have different item shapes, different grouping rules, different lifecycle (AAR handoffs close after the lesson is captured; scanner handoffs stay open until the work is done). Sharing a dispatcher is not reuse — it is co-location. The cost is mode-detection complexity, ambiguity handling, and a schema that fits one use case and stretches for the other.

A more honest anchor: `/handoff` has grown two specialized modes that look similar but are structurally different. Consider whether the dispatcher should be parameterized (one core, two adapters) rather than mode-detected.

### 5. Pre-mortem — three failure scenarios the analysis missed

**Scenario A — The flood.** Operator runs `/todo --journal --deep --journal-min-severity low` for inspection during a debug session. They intended a dry-run but forgot `--dry-run`. The journal file lands with 200+ items. `--max-items 50` protects the *handoff write*, but the journal file is already on disk. The operator is now responsible for either deleting it or letting it sit. No automatic cleanup until `/close --cleanup` ships (Unit 9, HANDOFF). The bridge enables the very pattern it cannot safely handle.

**Scenario B — The stale journal.** Operator runs `/todo --journal` in session A on Monday. They do not invoke `/handoff --from-journal`. On Wednesday, in session B, they discover the journal file via `/handoff list`. They run `/handoff --from-journal <stale-path>`. Handoffs are written — but the items reference files that have moved, processes that have changed, and decisions that have been superseded. `accurate_as_of_head` drift is "handled by existing AAR-mode discipline" — but AAR-mode was designed for retrospective drift, not prospective drift on a multi-day delay. The bridge becomes a staler-than-AAR handoff source with no signaling mechanism.

**Scenario C — The provenance laundering.** The journal records the originating `/todo` session_id and terminal_id. The handoff inherits those as `current_session_id` / `current_terminal_id`. But the items in the journal were derived from *scanner output* (16 sources: hunts, friction logs, harvest obligations, etc.) — the LLM did not invent them. Provenance should arguably trace to: the scanner source that produced each item, the git commit at evaluation time, and the LLM's reasoning for *not* acting on it in-band. The design preserves session ID but discards the actual provenance chain. A future session reading the handoff sees "this came from /todo in session X" but cannot reconstruct which scanner source produced it or why it was deemed important enough to persist but not important enough to act on.

The per-component Failure Mode analysis covers journal-write failure, dedup races, schema drift, and permission errors. It does not cover these three, which are *usage-pattern* failures — the design enables them but does not guard against them.

---

## Step 3 — Context-Derived Domain Critique

### Migration / Rollback

The rollback path (Unit 8) is documented and uses `git revert` (not `reset --hard` — correct per the no-destructive-git rule). **But:** `--journal` writes journals even after a successful revert if the operator forgets the rollback path is "the journal writes should also be reverted." There is no script to bulk-delete journals created during the failed run, no script to mark journal-derived handoffs closed in bulk, and no audit step to confirm the journal tree is consistent with the code state. The rollback is documented; the operational cleanup is not.

**Premise challenge:** additive flags are reversible in principle but the *artifacts* they create (journals, handoffs with `<!-- todo-journal: -->` markers) are persistent. A "revert and forget" leaves orphan handoffs that the marker scan will still consider during future dedup. The design should include a rollback script: `git revert` + journal delete + handoff close + marker re-scan.

### Concurrency / Multi-terminal

The 8-hex session-id prefix (32 bits) gives ~4.3B values; the design claims collision probability ≤1 in 2^32 per day per terminal. **But:** the collision analysis assumes one terminal per session. On a multi-terminal Windows host with several LLM sessions running concurrently on different terminals *and* on the same terminal in different worktrees, the "per terminal" qualifier hides two real collision modes:

- Two terminals in the same second produce different timestamps → no collision (good).
- Two terminals in the same second with the same 8-hex session prefix → collision. Probability per pair: 1 in 2^32. But "terminals running concurrently" can be 5–10 at peak; pair-wise collision probability grows.
- The same terminal restarting in the same second (worktree, fresh session) with the same 8-hex prefix → collision.

The design dismisses these with "impossible across concurrent sessions" — but they are not impossible, only improbable. At 1000 journal writes per day across the host, expected first collision is ~77 years (birthday paradox, √2^32 ≈ 65536 days / 365 ≈ 180 years for 1/day; much faster for 1000/day). The collision window is small but non-zero, and the failure mode is silent journal overwrite.

The marker dedup scan is bounded to `P:/docs/handoffs/todo-*/` (good — avoids O(tree size)). But there is no lock on the directory. Two concurrent `/handoff --from-journal` invocations on different terminals, each scanning the same bounded set, each writing their own handoffs — no file-level lock, no per-item lock. If two journals route the same item (same `title_hash`), the marker scan catches it on read but not on write — both can write before either reads. Marker dedup is eventually-consistent, not atomic.

**Premise challenge:** multi-terminal safety is asserted via filename uniqueness, but the dedup mechanism is racy. The design should either (a) add a per-item lockfile in the bounded scan directory, or (b) acknowledge that duplicates are a known consequence of concurrent invocation and tighten the S2 threshold to reflect reality.

### Cost / Performance

The design cites token blow-up explicitly. **But:** the analysis underestimates it.

- 30-item journal → dependency clustering by `{source, path-prefix, section}` reduces to ~5–10 handoffs per scan. (Per the design's own count: ~20–30 items → ~5–10 clusters.)
- If `/todo --journal` runs once per session (operator-driven), that's 5–10 handoffs per session.
- Each handoff is read by future cold-starts. The 17-field schema means ~500–1000 tokens per handoff cold-read.
- A typical session reads 3–5 handoffs cold → 2500–5000 tokens per session just for journal-derived handoffs.
- The bounded marker scan (`P:/docs/handoffs/todo-*/`) adds latency per `/handoff --from-journal` invocation: O(N) where N grows.

The cleanup path is HANDOFF. Without it, journals and handoffs accumulate; the cost grows super-linearly over months.

**Premise challenge:** the design calculates per-invocation cost but not lifecycle cost. A cost model over 6 months (assuming daily use) would likely show that the bridge pays for itself only if the false-positive rate is below 10% *and* the dedup is strong enough to keep the handoff count manageable. The design does not model either assumption.

### Provenance / Identity

The design preserves `current_session_id` and `current_terminal_id` from the journal into the handoff. **Provenance chain:**

- `/todo` invocation in session X writes journal with session_id X.
- `/handoff --from-journal` in session Y reads journal, writes handoff with current_session_id = X (the journal's), not Y.
- Future session Z reads the handoff, sees current_session_id = X, traces to the originating /todo invocation.

This is correct for *cross-session chain continuity* — the design's stated goal. **But:** the design does not preserve:

- The git commit at evaluation time (so future session cannot tell if the items are stale).
- The scanner source version (so future session cannot tell if the scanner that produced the items has changed).
- The LLM's evaluation rationale (so future session cannot tell why items were persisted but not acted on).
- The session's evaluation context (which other items were dropped, which were grouped together — the LLM's *filtering* is not in the journal).

The handoff has a session ID but no evaluation fingerprint. Two sessions that ran `/todo` with identical output but different LLM reasoning produce journals with the same items and different evaluations. The provenance preserved is *who ran the scan* not *what the scan meant*.

**Premise challenge:** provenance is reduced to identity. The design should include a `evaluation_fingerprint` (hash of the LLM's evaluation output, not just the items) or a `rationale` field. Without it, future sessions cannot distinguish "same item, same conclusion" from "same item, different reasoning."

### User Workflow Fit

The bridge introduces a new two-step operator ritual:

```
/todo --journal && /handoff --from-journal <latest-journal>
```

**This contradicts AGENTS.md's "automate user meta-actions" rule** (the same rule the design cites as grounding for F-pos-1). The rule states: "the user should not have to remember to do things the system can do itself."

The design defers `/close` integration (Unit 9) as HANDOFF. Without it, the operator must remember to run the two-step at every session end. The bridge claims to fix "items evaporate" but if the operator forgets to invoke the bridge, items still evaporate — the meta-action problem is unchanged.

**Premise challenge:** the design optimizes for skill non-coupling (no auto-fire) over meta-action elimination (the bridge runs when needed). The two are not the same. AGENTS.md argues the latter. The design should either (a) include `/close` integration as a required COMMIT unit, or (b) add an `/end-session` slash command that runs both steps, or (c) acknowledge the meta-action trade-off explicitly.

### Observed-vs-Invented

The design cites three load-bearing "existing patterns":

1. **AAR-report mode pattern in `/handoff`** — described as "structurally identical" to journal mode. The Dependency Grouping section admits the grouping rule *differs* (AAR by domain, journal by source-path-section). This is not "identical" — it is "uses the same dispatcher with different parameters."
2. **`claim_handoff.py` session-id-short convention** — referenced as the source of the 8-hex prefix. Not verified in this document. If the convention is different (e.g., full UUID, different delimiter, terminal-id not session-id), the journal filename convention breaks.
3. **`references/core-fields.md` 17-field schema** — referenced as the canonical schema for handoff format. Not verified in this document. If the schema has changed since the design was written, the field-inheritance assumption breaks.

**Premise challenge:** the design cites patterns as if they are observed facts but the citations are pointers, not verifications. A preflight-style audit (read `from_aar.py`, `claim_handoff.py`, `references/core-fields.md`) before COMMIT_THIS_SESSION would either confirm or refute the reuse claims. The F-43 test (`test_session_provenance`) catches one field but not the schema-wide assumption.

---

## Step 4 — Open-Ended Domain Detection

### Wiki-capture bypass

Scanner items often flag wiki concerns (stale concepts, contradictions, missing entries). The design routes them all to handoffs. **But:** handoffs are operational, not knowledge. A scanner item that says "wiki concept X is stale" should arguably trigger a `/wiki` capture, not a handoff. The bridge sends it to handoffs by default. Operator must use `--exclude-source` to opt out — but the operator has to know which sources are wiki-related (which requires reading each source's output).

**Premise:** the bridge treats all scanner output as action items. Some are knowledge items. The destination should depend on item type, not source alone. The design could add a `kind: action | knowledge` field to the journal and route knowledge items to `/wiki` instead.

### Self-verification (already acknowledged)

The design flags F-21 (self-dogfooding) and acknowledges the self-verification prohibition. The structural fix is sibling-session validation in Phase 2. **But:** the design still COMMITS the bridge in this session, with self-validation as a Phase 2 follow-up. The unit-8 smoke test is self-administered. The AGENTS.md rule (cannot be sole verifier of own enforcement/authority work) applies — bridge code is enforcement (it decides what becomes durable). The Phase 2 sibling validation should happen before COMMIT, not after.

### Subagent coordination

The design assumes a single LLM session invoking the bridge. **But:** on this host, multiple subagents may run concurrently — `/close` triggers one, manual invocation triggers another. The journal filename uniqueness is probabilistic, not guaranteed. The marker dedup is eventually-consistent. Two concurrent `/todo --journal` invocations on different subagents in the same session produce two journals with overlapping items; routing both produces duplicate handoffs that the marker scan only catches on the third run.

**Premise:** the design is single-agent in assumption but the host is multi-agent. The handoff marker should be session-scoped (e.g., include the journal's filename hash) so concurrent invocations do not collide.

### AGENTS.md alignment summary

The design cites AGENTS.md in DEC-01 (separation of concerns), DEC-07 (no new skill), and F-pos-1 (meta-action threshold). **But it does not cite:**

- "Automate user meta-actions" — directly contradicted by manual invocation.
- "Optimal long-term" — the bridge is chosen for simplicity over the in-band evaluation alternative.
- "Symptom-to-abstraction escalation" — the design is a session-specific fix, not a class-level abstraction.

If the gap is "scanner items evaporate," the class-level fix is "LLM evaluations that decide to act should act in-band." The bridge is the symptom-level fix. The design does not note this distinction.

---

## Step 5 — Verdict

**VERDICT: REVISE**

The design is well-engineered at the implementation level (tests interleaved, rollback documented, falsifiers explicit). It is not yet ready to ship because it has unresolved premise-level concerns:

1. **The evaporation problem may not be a problem.** Persisting items the LLM chose not to act on may create more noise than value. The false-positive rate (F-pos-1 at 20%) acknowledges this but the framing pretends the noise is a bug, not a design choice.

2. **Manual invocation contradicts the meta-action goal.** The bridge ships without `/close` integration; operator must remember the two-step. AGENTS.md's "automate user meta-actions" rule argues the opposite. Either integrate `/close` into this session or document the meta-action trade-off as an explicit choice.

3. **Severity gating default is ungrounded.** The `[INFERENCE]` label is honest about the lack of empirical basis, but shipping with an ungrounded default (high only, --deep widens) means Phase 2 will likely revise the default — possibly after operators have already tuned their workflow around it. Run the baseline measurement *before* shipping, not as a Phase 2 follow-up.

4. **Dedup scope is too narrow to meet S2.** Title normalization catches whitespace/case only. Rephrased items produce new hashes. S2's ≤2 duplicates per 90-day window will likely fail not because dedup is broken but because the design chose a narrow normalization. Either widen normalization (semantic similarity is the long-term answer; near-duplicate detection via n-grams or embeddings is the medium-term) or revise S2 to reflect the actual dedup rate.

5. **The AAR reuse claim is overstated.** The two modes share a dispatcher but have different item shapes, different grouping rules, and different lifecycles. The "structurally identical" claim is rhetorical. Either refactor `/handoff` to have one parameterized dispatcher with two adapters, or stop calling it reuse.

6. **The falsifier thresholds favor the design passing.** 20% false positives is too high; 90-day windows are too long; zero-usage-over-3-months is reactive. Tighten the thresholds and the design will either prove itself or surface its own failure modes faster.

7. **Provenance is reduced to identity.** The handoff gets a session ID but no evaluation fingerprint, no git commit anchor, no scanner source version. Future sessions cannot reconstruct what the LLM's evaluation meant, only who ran it.

8. **Three usage-pattern failures are unguarded.** The flood scenario, the stale-journal scenario, and the provenance-laundering scenario are enabled by the design but not covered by the Failure Mode analysis. The design enables these patterns; it should also guard against them.

**Recommended path forward:**

- Run preflight-style verification of the three "existing pattern" claims (`from_aar.py`, `claim_handoff.py`, `references/core-fields.md`) before COMMIT.
- Add a baseline-measurement unit (run `/todo` for 5 sessions, record severity distribution) *before* the severity default ships — not as Phase 2.
- Move Unit 9 (`/close` integration) from HANDOFF to a preconditioned COMMIT: ship the integration in this session if it can be done cleanly; otherwise explicitly document the meta-action trade-off and let the operator decide.
- Tighten F-pos-1 to 10% (or document why 20% is acceptable).
- Add `evaluation_fingerprint` (hash of LLM evaluation output, not items) to the journal schema for provenance.
- Add a rollback script: `git revert` + journal delete + handoff close + marker re-scan.

The bridge is salvageable. The design is not wrong — it is incomplete on premise-level concerns. Revise, then ship.

---

## Closing note (operator-visible)

The design team has done strong implementation-level work. The 30-finding review cycle produced a thorough, well-traced document. The gap this critique identifies is not in the engineering but in the *framing*: the design asks "how do we persist scanner output?" when the harder question is "should we, and if so, what should we preserve about the LLM's reasoning for not acting on it in-band?" That question is not answered here. Once it is, the bridge will be a much better fit.

Note: this critique assumes the design will execute roughly as planned. If the verification of `from_aar.py`, `claim_handoff.py`, and `references/core-fields.md` reveals that any of the three "reuse" claims is wrong, the verdict should escalate to BLOCK — a design built on three unverified foundations should not commit until the foundations are checked.
