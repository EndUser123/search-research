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
| Capability-shaped reuse search | /replacement-before-investigation | Add capability-decomposition variant |
| Research vs decision separation | /evidence-scope-discipline | Apply at research-output layer |
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

**Relationship to existing rules:** /correction-response-discipline-
anti-binary-swing covers hook and operator corrections (identify the
narrow valid kernel, separate from overreach). This rule extends the same
discipline to peer-review and external-LLM feedback specifically. The
CRITIC principle (external evidence required for relabeling) applies here:
agreement without independent verification is not validation.

## Third-round additions (from deeper root-cause analysis)

A third external LLM review identified that rules 11-12 fix what happens
*after* a bad conclusion is discovered, but not what *prevents reaching it*
in the first place. The systemic root cause: important epistemic rules exist
mostly as advisory prose rather than enforced state transitions and evidence
contracts. Four additions address the upstream causes.

### 6. Decision state machine — making "provisional" structurally impossible

**The problem:** qualifiers like "provisional," "likely," and "probably" are
used to disguise that a recommendation has crossed an evidence boundary.
"FORK (provisional), but two decisive things haven't been checked" is a
contradiction that prose rules cannot prevent.

**The fix:** an explicit decision state machine with transition conditions:

```
DISCOVERY → CANDIDATE_IDENTIFIED → EVIDENCE_INCOMPLETE → SPIKE_REQUIRED → CANDIDATE_VALIDATED → DECISION_READY → terminal state
```

Unknowns capable of reversing the choice prevent transition to DECISION_READY.
This is now enforced in `/www` Step 3.1b as the recommendation field's
constraint — the only legal output when a blocking unknown exists is
`SPIKE_REQUIRED`.

### 7. Search-completeness falsifier — discover the killer counterexample

**The problem:** the decision-level red-team (item 3) asks "what would make
this unnecessary?" but doesn't require *searching for it*. The agent names the
counterexample, then proceeds without running the search that would find it.

**The fix:** before closing discovery, (1) name what existing thing would
reverse the decision, (2) formulate the search most likely to find it,
(3) run that search, (4) only then close discovery. This is now enforced in
`/www` Step 3.1b.

### 8. Evidence scope: receipt type must match claim type

**The problem:** "Claims require receipts" doesn't specify that the receipt
type must match the claim type. Reading a file line proves the file says X,
but does not prove the runtime behavior is Y. "I independently verified it"
can become ritualized when the verification method is mismatched.

**The fix:** receipt type must match claim type:
- Textual/source claims → source-file receipts
- Code-mechanism claims → code-path evidence
- Runtime claims → live runtime evidence
- UX claims → observation in the real UI
- Causal claims → evidence capable of distinguishing competing explanations

Now an AGENTS.md hard rule.

### 9. Decision gate invariant — no NEW without evidenced reuse discovery

**The problem:** the existing "search before proposing" rule exists but was
violated inside a research task. Adding another prose reminder doesn't fix
the underlying problem — the agent searched within the proposed solution frame
and felt research was complete.

**The fix:** a transition invariant, not an instruction: no NEW/BUILD/FORK
recommendation may be emitted until reuse/alternative discovery has evidence
of completion across 5 dimensions (direct products, adjacent products,
capability-level implementations, platform-native mechanisms, existing
workspace solutions). If the search was product-shaped only, the only legal
output is `DISCOVERY_INCOMPLETE` or `SPIKE_REQUIRED`. Now an AGENTS.md hard
rule and enforced via the Decision Integrity Check's "Alternatives discovered"
and "Best reusable candidate" fields.

## Root-cause hierarchy

The three rounds of external critique map to a clean hierarchy:

```
Surface errors (missed repo, overclaimed causality, stale revisions)
    ↓
Immediate cognitive causes (solution-frame anchoring, inference inflation)
    ↓
Process cause (research optimized for validating, not comparing decision space)
    ↓
Systemic cause (rules as advisory prose, not enforced state transitions)
```

Rules 11-12 address level 2. Items 6-9 address level 4 — the systemic layer
where the rules become structural constraints, not behavioral hopes. The
honest assessment: items 6-9 are the ones that would have prevented the
original failure. Rules 11-12 are the ones that fix it once discovered.

## Mechanical enforcement layer (built 2026-08-08)

The deepest layer from the external LLM's analysis — moving from "LLM should
remember epistemic discipline" to "the system makes epistemically invalid
transitions difficult" — is now implemented as a deterministic Stop hook:

- **Validator** (`hooks/scripts/decision_contract.py`): parses YAML
  decision-contract artifacts and checks state-transition invariants.
  Does NOT make research judgments — only checks whether the evidence
  contract for the claimed state is satisfied.
- **Stop hook** (`hooks/Stop_decision_contract_gate.py`): detects
  decision artifacts in model output and blocks invalid transitions
  with precise error messages. Keys on artifact shape, not skill name.
- **`/www` template** (`skills/www/SKILL.md` Step 3.1b): text template
  replaced with structured YAML artifact template.

**Five invariants mechanically enforced:**
1. OPEN decision-reversing unknowns → DECISION_READY blocked (must be SPIKE_REQUIRED)
2. All 4 discovery classes (direct, adjacent, capability, workspace) must have real receipts
3. Search-completeness falsifier must be executed with receipts
4. Evidence type must match claim type (live_ui claim needs live_ui evidence, not document)
5. Receipts must be real citations, not placeholders

SPIKE_REQUIRED remains the costless fallback — the gate never blocks it.
30 unit tests + 6 acceptance tests through real hook dispatch path.
Commit: `8677fbc` in `~/.grok`.

## Evidence audit and remediation (2026-08-08)

An evidence-only audit (external LLM review) identified that the initial
implementation was a credible validator prototype but not yet a functioning
preventive control. Three trivial bypass paths, one material bypass, and
unverified dispatch path.

**Root cause of the gap:** the initial rating of SUBSTANTIALLY_COMPLETE was
generous. The central preventive boundary was optional — a model could
recommend BUILD without emitting a contract, or self-declare `required: false`
to skip enforcement entirely.

### Six bypasses closed (commit `f56c497`)

1. **State/action mismatch** (was MATERIAL): `state: DISCOVERY` +
   `proposed_action: BUILD` now blocked. Terminal action with non-terminal
   state is an invalid transition.
2. **No artifact** (was TRIVIAL): hook now detects terminal-action language
   in prose (BUILD/NEW/FORK/CREATE + recommendation context) and requires
   a contract. Omitting the artifact does not bypass the gate.
3. **`required: false`** (was TRIVIAL): terminal actions are ALWAYS gated
   regardless of the model-declared `required` field.
4. **Missing `evidence_requirements`** (was LOW): absence now blocks —
   omitting the key does not silently skip evidence-type validation.
5. **Flow-style YAML** (was LOW): `<decision-contract>` tags as primary
   extraction method. Formatting style can no longer cause silent
   `NO_ARTIFACT`.
6. **Hook dispatch verification**: active-surface refreshed; hook confirmed
   in Stop section. 9 acceptance tests through real subprocess path.

### Four-level enforcement taxonomy (diagnostic instrument)

The audit produced a reusable diagnostic for auditing enforcement claims:

| Level | What it means | Example |
|-------|--------------|---------|
| 1. Documentation | "You should do X" | AGENTS.md prose rule |
| 2. Required output structure | "You must report X" | SKILL.md template field |
| 3. Deterministic validation | "Invalid X is detected" | Unit-tested validator |
| 4. Runtime authority | "You cannot cross the boundary without valid X" | Hook that blocks the turn |

The root-cause project intended Level 4. The initial implementation delivered
Level 3 with an unverified Level 4 path. The remediation closes the gap to
genuine Level 4 for the decision-gate portion.

### Explicitly open as separate workstreams

- **Revision invalidation (claim ledger)**: ADVISORY ONLY — no mechanical
  enforcement. Stale derived claims can still survive in summaries/confidence
  sections. Separate workstream.
- **Reviewer-as-hypothesis**: ADVISORY ONLY — prose in AGENTS.md + /tp
  protocol. Not followed 9 times during this session's own implementation.
  Separate workstream.
- **Evidence vocabulary**: `causal_discriminating` is incorrectly modeled
  as the same axis as modality types. Should be split into
  `modality` + `discriminates_competing_explanations`. Not yet fixed.

### Final calibration (post-remediation review)

**DECISION_GATE_ROOT_CAUSE_FIX_COMPLETE_FOR_DEFINED_SCOPE** — with one test outstanding.

Implementation: substantially complete. All 6 known bypasses closed. 42 unit
tests + 9 subprocess acceptance tests pass.

**Runtime acceptance: PENDING ONE FRESH-SESSION TEST.** Subprocess tests prove
the registered command implementation behaves correctly. They do not prove the
complete Grok Build dispatch chain (Stop event → hook discovery → dispatcher
invocation → block honored) works end-to-end. The active-surface snapshot
shows the hook is discovered, but configuration evidence is not behavioral
evidence. To close: start a fresh session, attempt a terminal commitment
without a contract, observe the gate block.

### Bypass-surface adversarial testing principle

The audit/remediation process uncovered a reusable engineering principle:

> A control's own bypass surface needs adversarial testing, not just its
> rejection logic.

The first implementation tested: "Does BUILD without alternatives fail?"
It did not test: "Can I avoid the rule entirely?" That distinction is why
3 trivial bypasses survived the initial implementation.

For any future gate, acceptance testing must cover both:
- **Rejection correctness**: does the gate reject an invalid input?
- **Bypass resistance**: can the actor avoid entering the gate, misclassify
  itself out of scope, change state labels, omit required state, or exploit
  the reader/writer boundary?

This principle applies to all hooks, not just the decision-contract gate.
