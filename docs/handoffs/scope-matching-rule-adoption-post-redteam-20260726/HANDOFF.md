---
thread_id: scope-matching-rule-adoption-post-redteam-20260726
parent_handoff_path: none
current_session_id: 019f9bfe-1b89-7602-9384-0212224ff30b
current_terminal_id: P%3A%5C
produced_at: 2026-07-26T22:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 599fbf40a543bc70b3f7fe8494c4205cf3f66c22
---

# Scope-matching rule adoption — post-red-team: pick the structural mechanism, not the prose rule

## Objective

Implement the scope-matching verification discipline findings through a **structural mechanism** (not a prose AGENTS.md rule), with measurement baseline established before or alongside adoption, and the nemorton-class directive-non-execution failure separated from scope-matching failures. This handoff captures the analysis, red-team verdict, and the four concrete recommendations that emerged, so a fresh session can execute without re-deriving.

## The one-sentence summary

A 3-specialist red-team (glm-5-2 × 3, 16 findings, BLOCK verdict) found that the originally-proposed prose AGENTS.md rule is the wrong intervention class — it inherits anti-pattern #1 from the workspace's own enforcement wiki, contradicts the concept's own summary conclusion (line 8), and the "Path A vs Path B" decision frame concealed the real question. The structural mechanism the concept's own analysis endorses (AAR Q11 feedback loop) is the right path.

## Why this needs a fresh session (not session-continuation)

The red-team's WORKFLOW-1 finding (closure-pressure recursion) applies to *all four* recommendations: designing verification-discipline mechanisms under closure pressure IS the layer-1 failure class the mechanisms target. The session that produced 7+ layer-1 failures and a 4-turn theory-substitution incident cannot cleanly design the fix for those failures — the operator-as-external-verifier framing (documented in the revised concept) is the structural fix, and the fresh session IS that verifier.

## Background — the four stages this session produced

**Stage 1 (research synthesis):** `/www` research on LLM verification scope-matching produced `scope-matching-verification-discipline.md`. Research synthesis (Findings 1-4, misconceptions, receipts) is verified and survives.

**Stage 2 (concept revision after /tp critique):** go-mimo-v2-5 found three problems. Revision addressed all three: (a) reclassify all 5 near-misses as layer-1 failures, (b) REJECT the originally-proposed scope-receipt block as the model-authored-ledger anti-pattern, (c) reframe the operator as the structural external verifier. Committed in `339cdf9`. Research synthesis preserved verbatim; only interpretation/mapping/recommendations changed.

**Stage 3 (proposal):** Session-end /tp proposed adopting scope-matching as AGENTS.md rule, with three revisions from a prior /tp critique (glm-5-2). Recommended Path A (adopt now) over Path B (fresh session), with self-disclosed bias.

**Stage 4 (red-team BLOCK):** 3-specialist red-team (all glm-5-2) produced 16 findings, 5 root-cause clusters, verdict **BLOCK**. The /tp immediately after agreed with the verdict ("8/8 findings survive verification; my prior /tp was too soft"). This handoff captures the post-red-team state.

## The four recommendations (verified — execute these, not the prior proposal)

### 1. Adopt the concept's findings as the analysis layer; reject the prose rule as load-bearing

**Source:** RC-1 (BLOCK, amplified 4× across specialists). CROSS-1, CROSS-2, SCOPE-3, WORKFLOW-2, WORKFLOW-5.

**Evidence (verbatim citations):**
- `P:/.data/wiki/concepts/best-practices-enforcement-mechanism-grok-build.md` line 44: *"Behavioral rule in AGENTS.md — already exists ('Claims require receipts'); insufficient because prose is advisory and breaks under context momentum (proven: the incident occurred with the rule on the books)."*
- Same file, lines 104-112 (anti-pattern table): *"Stronger-verb prose rule ('MUST verify') — Advisory; breaks under context momentum."*
- `P:/.data/wiki/concepts/scope-matching-verification-discipline.md` line 8 (concept summary): *"the gap is not absence of layer 2 but failure to systematize operator catches."*
- Same file, line 159 (recommendation): *"Adopt scope-matching as a named AGENTS.md workflow step (Option B). Before any completion claim, enumerate the claim's scope as a checklist..."*
- **Contradiction:** line 8 points to operator-catch systematization; line 159 recommends the prose rule. Line 8 is the analysis conclusion; line 159 is the prescription. The prescription contradicts the analysis.

**Action:** Do not adopt the prose rule as the load-bearing intervention. The prose rule may exist as advisory documentation if useful, but it is not the structural fix. Adopt the concept's research findings (Findings 1-4 are verified) as the analysis layer.

### 2. Instantiate through the structural mechanism the concept's own analysis endorses

**Source:** RC-1, RC-2, CROSS-1, CROSS-2, WORKFLOW-4.

**Concept's line 161 recommendation:** *"Systematize operator catches via AAR Q11 feedback loop. The AAR blind-spot sub-check already flags 'operator-flagged items without resolution.' Extend it to require a layer-1 feedback item for each catch: 'what named scope-matching check would have caught this?' This closes the loop — each operator catch becomes a layer-1 improvement that prevents recurrence."*

**Enforcement wiki's validated architecture (lines 58-72):** structural = "detection derives from external state the actor cannot self-certify" + "enforcement = block + prompt" via mechanical hook. The AAR Q11 path qualifies because operator catches are external state.

**Critical scope check before implementing:** Read `C:/Users/brsth/.grok/skills/aar/SKILL.md` to verify Q11's actual structure. The concept claims "operator-flagged items without resolution" is already wired — confirm this. Determine whether Q11 is the right home for the "what named check would have caught this?" feedback loop, or whether a new field/mechanism is needed.

**Action:** Design and implement the AAR Q11 feedback loop (or whichever structural mechanism the scope check identifies). This is the load-bearing intervention, replacing the prose rule.

### 3. Establish the measurement baseline before or alongside intervention

**Source:** RC-4 (REVISE), SCOPE-5, CROSS-4.

**Concept's own falsifier (lines 169-171):** *"Test: adopt layer 1, measure near-miss rate over 20 sessions, compare to baseline."*

**Three undefined axes the red-team flagged:**
- **Counter:** what records a near-miss? If the model self-reports, that's the model-authored-ledger anti-pattern the concept itself rejected. The counter must be operator-authored or grep-detectable.
- **Baseline:** no pre-adoption baseline exists. The falsifier is unrunnable without it.
- **Numerator confound:** if operator catches are the counter AND the goal is to reduce operator catches, the measurement's numerator shrinks for two confounded reasons (fewer failures OR less operator vigilance). Separate them.

**Action:** Define the measurement instrument before claiming the intervention works. Specify (a) the counter (operator-authored structured field in session handoff, or grep-detectable signal), (b) the baseline collection procedure (first 20 sessions pre-adoption, or retroactive from handoffs/AARs), (c) the near-miss definition that separates failure-rate from operator-vigilance. Without this, the intervention is unfalsifiable.

### 4. Separate the directive-non-execution failure class from scope-matching failures

**Source:** RC-5 (REVISE), SCOPE-1.

**The conflation:** the session's "7+ layer-1 verification failures" lumped two distinct classes:
- **Scope-matching failures (the original 5):** model made a claim without checking the right scope. Mechanism: enumerate scope → match checks. Applies.
- **Directive-non-execution (the nemorton class):** operator explicitly instructed "run the spawn test," model substituted theory across 4 consecutive turns. Mechanism: enumerate scope → match checks has NO PURCHASE on "I was told to run X and ran Y." Different failure class.

**Why this matters:** applying the scope-matching fix to the nemorton class creates false confidence that the nemorton surface is covered when it is not. The nemorton class is closer to the "Stated-default rule — act, don't ask" or directive-execution family — the model received a directive and did not execute it.

**Action:** Document the separation explicitly. Update the scope-matching concept to scope its mechanism to the scope-matching failure class only. Add a separate concept (or extend an existing one) for the directive-non-execution class. The latter may need its own mechanism — likely a /tp two-lens review at session-close for "did the model execute all operator directives this session?"

## What NOT to do

- **Do not adopt the prose AGENTS.md rule as the load-bearing intervention.** This is the BLOCK finding.
- **Do not frame the decision as "which session adopts the rule."** That was the false binary.
- **Do not propose /tp routing as the structural pair for the prose rule.** Both /tp and /check are discretionary (operator- or model-invoked), so they do not escape the prose-rule anti-pattern. They reproduce the same context-momentum failure mode.
- **Do not skip the measurement baseline.** The concept's own falsifier requires it; without it the intervention is unfalsifiable.
- **Do not conflate the nemorton failure class with scope-matching.** Different mechanisms needed.

## What's already done (don't redo)

- **Concept revision (commit 339cdf9, today):** revised `scope-matching-verification-discipline.md` is the canonical analysis. Research synthesis (Findings 1-4, misconceptions, receipts) is verified. Only the recommendations section (lines 159+) needs further revision per recommendation #1 above (line 8 vs line 159 contradiction).
- **Red-team artifacts:** `P:/.artifacts/red-team/019f9bfe/20260726-211900/{scope-gap,workflow,cross-model}.json` — full finding details with evidence citations.
- **Cross-transport nemotron verification (commits 44d83f6, 137e338):** root cause fully confirmed in `model-tool-calling-capability-matrix.md`. Separate workstream.

## Decision points to surface to the operator

1. **Confirm the intervention class is structural, not prose.** The red-team BLOCK is on the proposal as written; a structural-mechanism proposal would not be blocked. Operator should confirm before design work begins.
2. **Confirm the AAR Q11 path before reading the AAR skill.** If the operator has a different structural home in mind (e.g., a new hook, a /close extension), surface that before scoping the Q11 extension.
3. **Confirm the measurement-baseline approach.** Retroactive (mine handoffs/AARs) vs prospective (start logging now). Prospective is cleaner; retroactive is faster but may not have the data.
4. **Confirm the directive-non-execution class needs its own mechanism.** The separation is correct analytically; whether it needs a separate mechanism or folds into an existing one is an open design question.

## Dependencies

- **Requires:** nothing structural. The concept, red-team artifacts, and enforcement wiki are all in place.
- **Blocks:** confident fleet-wide verification-discipline adoption. Until the structural mechanism lands, the workspace relies on operator vigilance alone.
- **Non-blocking to:** `/tp` pool selection (nemorton investigation resolved separately), cross-transport model matrix (separate handoff).

## Read first (related wiki concepts)

- `scope-matching-verification-discipline.md` — the analysis layer (read Findings 1-4; the recommendations section needs revision per this handoff)
- `best-practices-enforcement-mechanism-grok-build.md` — the anti-pattern list (lines 44, 104-112) and the validated architecture (lines 58-72)
- `analyst-exhibits-pattern-being-analyzed.md` — the meta-pattern of the model exhibiting the failure it's analyzing
- `reactive-pattern-matching-and-closure-pressure.md` — the closure-pressure failure mode
- `plausible-narratives-substitute-for-verification.md` — the theory-substitution pattern

## Cross-reference couplings

- `P:/.data/wiki/concepts/scope-matching-verification-discipline.md` lines 8 vs 159 — the contradiction
- `P:/.data/wiki/concepts/best-practices-enforcement-mechanism-grok-build.md` lines 44, 104-112, 58-72 — anti-pattern + validated architecture
- `C:/Users/brsth/.grok/skills/aar/SKILL.md` — to read for Q11 structure (recommendation #2 scope check)
- `P:/.artifacts/red-team/019f9bfe/20260726-211900/*.json` — full red-team findings with evidence
- `P:/docs/handoffs/nemotron-spawn-failure-investigation-20260726/HANDOFF.md` — nemorton investigation (separate workstream, related via RC-5)
- `P:/docs/handoffs/cross-transport-model-matrix-20260726/HANDOFF.md` — cross-transport testing (separate workstream)

## Other outstanding streams in this session (named, not handed off)

- **Scope-matching rule adoption — this handoff.** The load-bearing one.
- **Cross-transport model matrix** — handed off separately at `cross-transport-model-matrix-20260726/HANDOFF.md`. Mechanically executable; not blocked by this handoff.
- **Receipt-before-write structural hook** — already handed off at `receipt-before-write-workflow-and-hook-20260726/HANDOFF.md`. Trigger: 3 recurrences in 10 sessions.

## Last user message (verbatim)

> should we create a handoff for it, or is it quick and easy to do now?

(followed by "yes" when the recommendation was handoff + one durable write)

## Provenance

Written from session 019f9bfe-1b89-7602-9384-0212224ff30b after a 3-specialist red-team (BLOCK verdict) and a follow-up /tp that agreed with the verdict. The session produced the research, the concept revision, the original proposal, the red-team block, and now this handoff. The red-team artifacts at `P:/.artifacts/red-team/019f9bfe/20260726-211900/` contain the full evidence chain. The handoff is scoped to be mechanically actionable by a fresh session without re-deriving the analysis.
