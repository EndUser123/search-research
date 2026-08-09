---
title: "Decision integrity in research: blocking unknowns, solution-frame reset, and decision-level red-teaming"
created: 2026-08-08
source: session-019fdf3d (external LLM critique)
tags: [research-quality, epistemic-discipline, decision-making, blocking-unknown, solution-frame, red-team, decision-integrity-check]
summary: >
  External LLM critique identified three genuinely novel patterns missing from
  our research pipeline: (1) the distinction between blocking unknowns
  (recommendation depends on resolution) and carryable unknowns (proceed with
  uncertainty), (2) the Decision Integrity Check template (forces reuse search,
  adversarial framing, and cheapest-falsification before recommendation), and
  (3) decision-level red-teaming (challenging the choice itself, not just
  implementation durability). These are structural additions to /www and the
  PECD loop, not new prose rules.
agent: grok
host: grok
cognitive_load: 3
verification: externally-grounded
relations:
  - target: wiki/concepts/pecd-loop-iterative-proposal-evidence-critique-deepen.md
    type: refines
  - target: wiki/concepts/replacement-before-investigation-pattern.md
    type: related
  - target: wiki/concepts/evidence-scope-discipline.md
    type: related
  - target: wiki/concepts/narrative-as-signal-anti-dismissal-rule.md
    type: related
---

# Decision integrity in research: blocking unknowns, solution-frame reset, and decision-level red-teaming

## Origin

An external LLM reviewed a /www research artifact on a YouTube workspace
extension and identified that "the research process was optimized to complete
and strengthen the proposed solution, rather than to maximize the quality of
the decision." The critique proposed 7 root causes and a 10-point
"Research-to-Decision Discipline."

This concept captures the **three items genuinely novel to our workspace**
(the rest are already covered by existing rules — the gap is enforcement,
not knowledge).

## The three genuinely novel patterns

### 1. Blocking unknown vs carryable unknown

**The problem:** our research artifacts routinely say "needs live verification"
and then proceed to recommend implementation. The `[UNKNOWN]` label doesn't
distinguish between unknowns that don't affect the recommendation and unknowns
that invalidate it.

**The distinction:**

| Label | Meaning | Action |
|-------|---------|--------|
| `[UNKNOWN]` | Carryable — recommendation doesn't depend on resolving this | Proceed with labeled uncertainty |
| `[BLOCKING-UNKNOWN]` | Recommendation falls apart if this is wrong | STOP — spike or falsification required before downstream commitment |

**The rule:** *A downstream recommendation cannot exceed the confidence of
its weakest decision-critical inference.* If the recommendation depends on
an unverified assumption about feasibility, architecture, build-vs-reuse,
authority, or the primary execution path, the recommendation is SPIKE, not
PROCEED.

**Relationship to existing labels:** this refines the existing `[UNKNOWN]`
label by splitting it. It does not replace `[INFERENCE]` or `[FACT]` — it
adds a decision-criticality dimension.

### 2. Decision Integrity Check template

A required output section for every substantial research artifact. Structural,
like the EGDP template or the close summary format — it constrains the output
format, not the thinking.

```text
DECISION INTEGRITY CHECK

Outcome sought:              <restate without proposed mechanism>
Proposed solution assumed:   <what the request assumed>
Alternatives discovered:     <what else exists>
Best reusable candidate:     <strongest non-NEW option>
Decision-critical unknowns:  <what could change the recommendation>
Cheapest live falsification:  <cheapest experiment that resolves a critical unknown>
What evidence reverses this:  <what would make us choose differently>
Recommendation:              PROCEED | SPIKE | MODIFY | REUSE | BLOCKED
```

**Why each field earns its place:**
- "Outcome sought" forces solution-frame reset (restate without mechanism)
- "Best reusable candidate" forces reuse search before NEW
- "Decision-critical unknowns" forces blocking-vs-carryable classification
- "Cheapest live falsification" forces experiment-over-prose-research
- "What evidence reverses this" forces decision-level red-team

### 3. Decision-level red-teaming

Our /www disconfirmation phase challenges whether findings are correct
(implementation-durability). It does not challenge whether the *choice*
is correct (decision-quality).

**Implementation-level red-team (existing):**
- "Could the API change?"
- "Could the data source break?"
- "Is the architecture durable?"

**Decision-level red-team (new):**
- "What existing project would make building this unnecessary?"
- "What requirement does the proposed mechanism fail despite satisfying the APIs?"
- "What evidence would make a different approach preferable?"
- "What causal conclusion have I made without direct evidence?"
- "Which recommendation would I reverse if one assumption were false?"

Both types are needed. The decision-level red-team goes in the PECD loop's
Critique phase and in /www's disconfirmation pass.

## What the critique said that we already have

| Critique point | Existing coverage | Gap |
|----------------|------------------|-----|
| Evidence → inference → decision collapse | `[FACT]`/`[INFERENCE]`/`[UNKNOWN]` vocabulary | Enforcement at decision boundaries |
| Capability-shaped reuse search | [[replacement-before-investigation]] | Add capability-decomposition variant |
| Research vs decision separation | [[evidence-scope-discipline]] | Apply at research-output layer |
| Insufficient adversarial pass | /www disconfirmation phase | Add decision-level questions |

The gap is always the same: the rules exist but don't fire under pressure.
The structural fix is the Decision Integrity Check template (item 2 above)
because it's a required output format, not a behavioral rule.

## Integration into existing skills

### /www Phase 3 (synthesis)

Add the Decision Integrity Check as a required output section. The
synthesis subagent must fill every field before the artifact is considered
complete.

### PECD loop Critique phase

Split into two sub-passes:
1. Implementation critique (existing): well-evidenced, not over-engineered
2. Decision critique (new): what would make this unnecessary? What
   assumption reversal reverses the recommendation?

### /tp review

When reviewing research artifacts, check whether blocking unknowns were
correctly identified and whether the Decision Integrity Check is present
and filled.

## Falsifier

This concept is wrong if:
- The Decision Integrity Check becomes boilerplate that gets filled
  mechanically without genuine engagement. Mitigation: the "What evidence
  reverses this" field is the canary — if it's empty or generic, the check
  was theater.
- The blocking-vs-carryable distinction doesn't change any actual
  recommendation. Test: review 3 prior research artifacts and check whether
  any recommendation would have changed from PROCEED to SPIKE.
- The decision-level red-team questions are already covered by existing
  /www phases. Test: run a /www with and without the new questions and
  compare output quality.

## What we rejected from the critique

The 10-point "Research-to-Decision Discipline" was rejected as too long
to fire under pressure (documented ~50% compliance ceiling on prose rules).
The three structural items above are the actionable subset. The remaining
7 points are already covered by existing workspace rules — the gap is
enforcement, not knowledge, and adding more prose rules doesn't close an
enforcement gap.

## Second-round additions (from follow-up critique)

A second external LLM review of a corrected research artifact identified
two additional patterns. Both are genuinely novel — the existing workspace
rules cover cross-file propagation but not intra-artifact reasoning-chain
invalidation.

### 4. Revision invalidation — derived claims as cached state

**The problem:** when a foundational conclusion in a research artifact
changes, downstream statements derived from it (frontmatter summaries,
confidence labels, recommendations, falsifiers, handoff metadata) are
rarely invalidated and recomputed. The artifact ends up with internal
contradictions: the body retracts a claim, but the summary still asserts
it.

**The principle:** research artifacts need state consistency just like
software systems do. Evidence changes are state transitions. Derived
claims are cached outputs. A changed upstream premise should invalidate
downstream caches.

```
Evidence/assumption (changed)
    ↓
Finding (updated)
    ↓ [INVALIDATED — must recompute]
Summary (stale)
Confidence label (stale)
Recommendation (stale)
Falsifier (stale)
Metadata/frontmatter (stale)
```

**The rule:** *When evidence, an assumption, a conclusion, or a
recommendation is materially changed or retracted in a research artifact,
treat all derived statements as stale until revalidated. Search the entire
artifact for the old claim, its synonyms, consequences, confidence labels,
summaries, metadata, and downstream decisions. Recompute them from the
new state rather than patching only the section where the correction
arose.*

**Structural enforcement: a claim ledger.** Before persisting a revised
research artifact, produce a table proving every decision-critical claim
has been propagated:

| Claim | Current state | Previous state | Propagated? |
|-------|--------------|----------------|-------------|
| Side Panel is preferred | UNRESOLVED | HIGH/recommended | summary ✓, confidence ✓, falsifier ✓ |
| Build strategy | reuse-spike | new extension | frontmatter ✓, recommendation ✓ |

A claim with "Propagated? no" blocks persistence.

**Relationship to existing propagation rule:** AGENTS.md's "Propagation
check after policy/config changes" covers cross-file stale references
(model slugs, file paths, skill names). This rule covers intra-artifact
reasoning-chain invalidation within a single research document. Different
layer, same principle.

### 5. Reviewer feedback is a hypothesis, not authority

**The problem:** when an LLM receives substantive criticism from a reviewer,
it may immediately agree ("You were right on all five points") without
independently verifying each point. This replaces anchoring on the original
proposal with anchoring on the reviewer — the desired behavior is to reopen
evidence, not to switch allegiance.

```
CORRECT:
challenge arrives → reopen evidence → independently verify → update belief

INCORRECT:
challenge arrives → agree → adopt reviewer's position wholesale
```

**The rule:** *Reviewer feedback is a hypothesis to test, not an authority
to obey. Independently verify substantive criticism. Classify each point as
CONFIRMED / PARTIALLY CONFIRMED / REJECTED with evidence. Update only to
the extent supported by evidence.*

**Relationship to existing rules:** [[correction-response-discipline-
anti-binary-swing]] covers hook and operator corrections (identify the
narrow valid kernel, separate from overreach). This rule extends the same
discipline to peer-review and external-LLM feedback specifically. The
CRITIC principle (external evidence required for relabeling) applies here:
agreement without independent verification is not validation.
