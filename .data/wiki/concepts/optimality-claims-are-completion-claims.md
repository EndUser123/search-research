---
title: "Optimality claims are completion claims — verify like any other"
created: '2026-07-21'
source: session-2026-07-21 (self-referential test of /www)
sources:
- P:\.data\wiki\concepts\verification-before-completion-principle.md
- P:\.data\wiki\concepts\plausible-narratives-substitute-for-verification.md
tags: [verification, optimality, epistemic, claim-discipline, llm-behavior, self-review]
summary: >
  Claims of the form "optimal," "best version," "recommended approach," or
  "the right answer" are structurally equivalent to completion claims ("done,"
  "verified," "fixed"). Both assert the writer has evaluated alternatives. Apply
  the same verification discipline: name the metric, name the considered
  alternatives, show the comparison. A claim of optimality without a
  comparison is a plausible narrative, not a verified claim.
agent: grok
host: both
cognitive_load: 2
verification: multi-source-verified
relations:
  - target: wiki/concepts/verification-before-completion-principle
    type: refines
  - target: wiki/concepts/plausible-narratives-substitute-for-verification
    type: related
---

# Optimality claims are completion claims

## The pattern

When an agent (or operator) says "X is the optimal solution" / "use Y — it's the best" / "I recommend approach Z" without supporting evidence, the claim is structurally identical to a "done" or "fixed" or "verified" claim. All three assert that the writer has evaluated alternatives and the chosen one dominates.

The wiki's [[verification-before-completion-principle]] says any completion claim must be backed by a tool call that proves it. The same discipline applies to optimality claims. Without that verification, the "optimal" framing is a [[plausible-narratives-substitute-for-verification]] — the narrative feels right but the model has stopped investigating.

## The gate function for optimality claims

```
BEFORE claiming any option is "optimal," "best," or "recommended":

1. IDENTIFY the metric: what does "optimal" mean here?
   - Cost (build time, runtime, LOC)?
   - Reversibility (how hard to undo)?
   - Alignment with stated operator preferences?
   - Maintenance burden?
   - Scope (fits the bounded problem)?

2. NAME the considered alternatives: at least 2, ideally ≥3.
   - "I evaluated A, B, C."
   - Each alternative must be a real option, not a strawman.

3. SHOW the comparison: a table, a tradeoff matrix, or a paragraph
   that explicitly contrasts the chosen option against the considered ones.

4. STATE the counterfactual: under what conditions would the chosen
   option NOT be optimal? (The falsifier.)
```

If any step is missing, the claim is not "optimal" — it is "preferred" (a preference) or "recommended" (a recommendation under stated criteria). Reframe accordingly.

## What the gate prevents

**Failure mode 1: confident confabulation.** The model produces a detailed, internally consistent recommendation without checking whether the stated metric actually supports it. The recommendation feels right because it's structurally complete — it has a metric, alternatives, a comparison. But the comparison is fictional; the alternatives weren't actually considered.

**Failure mode 2: preference dressed as fact.** "Use X" feels different from "I prefer X." The "optimal" framing collapses a preference into a fact-claim, which the next reader (or the model itself in a future session) will treat as evidence-backed.

**Failure mode 3: stops investigation at "obvious."** Once an optimal recommendation is stated, downstream reasoning treats it as a settled fact. The [[plausible-narratives-substitute-for-verification]] failure mode: the narrative of optimality is itself an answer that blocks further searching.

## Verification approaches by claim type

| Claim shape | Required verification |
|---|---|
| "X is the optimal long-term solution" | Cite the operator's preference file; show at least 2 considered alternatives; state the falsifier (when X would NOT be optimal) |
| "The simplest version is also optimal" | Show the comparison demonstrating parity; or acknowledge it's a tie-breaker, not an optimality proof |
| "X is the recommended approach" | Name the criteria you're optimizing for; show that X dominates on at least one criterion without losing on others |
| "Y would be over-engineering" | Show that Y addresses a problem X doesn't have; quantify the maintenance cost |
| "This is the best version" | Identify the alternatives you rejected; name WHY each was rejected on stated criteria |

## The "transition effort is not a disqualifier" exception

One specific case where optimality can be claimed without a comparison: when the operator has explicitly stated that a criterion (e.g., "transition effort is not a disqualifier") constrains the decision space. In that case, the comparison is implicit: any option violating the stated constraint is eliminated by operator policy, not by the model's analysis.

Example from this workspace: `~/.grok/AGENTS.md` states "optimal long-term over minimal-diff" and "transition effort is not a selection criterion." An agent in this workspace can claim optimality for an option that scores well on optimal-long-term without comparing against "minimal-effort" alternatives — those alternatives are already eliminated by operator policy. The claim is verified by policy citation, not by analysis.

This is the **legitimate escape hatch**: when the operator has done the comparison work upstream and written it into the policy file, downstream agents can claim optimality against that policy without re-running the comparison. The policy file IS the comparison.

## Related

- [[verification-before-completion-principle]] — the principle this refines (extend "verified" to cover "optimal/recommended")
- [[plausible-narratives-substitute-for-verification]] — the failure mode this prevents (the narrative of optimality substitutes for actual investigation)
- [[evidence-first-default-and-needless-confirmation]] — empowerment over prohibition (give agents decision protocols, not blanket verification requirements)

## Auto-related

- [[verification-before-completion-principle]]
- [[operator-collaboration-style-and-leverage]]
- [[llm-handoff-best-practices]]

