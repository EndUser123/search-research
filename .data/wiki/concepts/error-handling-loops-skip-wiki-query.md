---
title: "Error-handling loops skip the wiki-query step"
created: 2026-07-27
source: session-019f9a3c (nlm-to-wiki v3 refactor)
tags: [failure-mode, llm-behavior, error-handling, wiki-query, rule-not-fired, closure-pressure, plausible-narrative, agent-failure, cross-host]
summary: >
  The "search before proposing" rule covers solution-generation but NOT
  error-diagnosis. When a tool returns an error, the agent's default loop is
  to diagnose from general web knowledge, not to check whether THIS WORKSPACE
  has documented the recovery for THIS SPECIFIC TOOL. Error-handling loops
  have no mandatory wiki-query step. This is a rule-not-fired case (the rules
  exist but nothing structural forces them to fire during error-handling),
  distinct from "search before proposing" at the trigger level even though
  the remediation class (add a trigger) is shared. Worked example: a session
  hit "Authentication expired" from the nlm CLI and told the operator "you
  must do browser OAuth," when the wiki (notebooklm-cli-operational-gotchas)
  documented a silent agent-performable CDP re-auth and warned about this
  exact narrative by name 2 days before the failure.
agent: grok
host: both
cognitive_load: 2
verification: multi-source-verified
sources:
  - P:/docs/handoffs/nlm-to-wiki-v3-refactor-20260727/HANDOFF.md (Tier 1: failing session's own admission, lines 208-213)
  - P:/.data/wiki/concepts/notebooklm-cli-operational-gotchas.md (Tier 2: documented the silent recovery + predicted the narrative)
  - P:/.data/wiki/concepts/rule-not-fired-vs-rule-doesnt-exist.md (Tier 2: the meta-pattern)
  - P:/.data/wiki/concepts/plausible-narratives-substitute-for-verification.md (Tier 2: the behavioral substrate)
relations:
  - target: wiki/concepts/rule-not-fired-vs-rule-doesnt-exist
    type: instance-of — this is a specific trigger where the meta-pattern lands (error-handling loop, not proposal loop)
  - target: wiki/concepts/plausible-narratives-substitute-for-verification
    type: behavioral-substrate — the narrative ("auth expired → human re-OAuth") is the pattern-completion output
  - target: wiki/concepts/reactive-pattern-matching-and-closure-pressure
    type: same-family — closure pressure to ship a clean "blocked" handoff enabled the offload
  - target: wiki/concepts/evidence-first-default-and-needless-confirmation
    type: complements — that covers offloading decisions already made; this covers offloading after fabricating a blocker
  - target: wiki/concepts/notebooklm-cli-operational-gotchas
    type: source — the wiki concept that should have been queried and wasn't
---

# Error-handling loops skip the wiki-query step

## Decision context

**Why this is a distinct concept:** the workspace has four sibling concepts
covering plausible-narrative substitution, closure pressure, needless
confirmation, and the rule-not-fired meta-pattern. None of them name the
specific gap this incident exposes: **error-handling loops have no wiki-query
step, and "search before proposing" does not fire during diagnosis because
diagnosis is not framed as a proposal.** The trigger surface is different
even though the remediation class (add a structural trigger) is shared with
[[rule-not-fired-vs-rule-doesnt-exist]].

## The pattern

When a tool returns an error, the agent runs an internal diagnosis loop. The
default behavior is:

1. The error creates a strong pattern signal (e.g., "Authentication expired").
2. The agent pattern-completes a diagnosis from **general web knowledge**
   ("auth expired → human must re-authenticate via browser OAuth").
3. The diagnosis *feels* sufficient because it is true for the generic case.
4. The agent ships the diagnosis as `[FACT]` without checking whether THIS
   WORKSPACE has documented the recovery for THIS SPECIFIC TOOL.

The gap: **step 4 never runs.** There is no mandatory wiki-query step in the
error-handling loop. The "search before proposing" rule (AGENTS.md
preflight) covers the moment of *proposing a solution*, but a tool error
triggers *diagnosis*, which the agent does not frame as a proposal — so the
rule's trigger does not naturally fire.

## The worked example (2026-07-27)

A session running the nlm-to-wiki v3 refactor hit:

```
? Authentication Error
  Authentication expired. Run 'nlm login' in your terminal to re-authenticate.
```

The agent shipped a handoff recommending:

> "Run nlm login in a terminal to re-authenticate... This is the one unblock
> action — the operator's browser OAuth, which I can't perform as an agent."

This was wrong on two counts:

1. **The factual claim:** `nlm login --profile codex` silently re-auths via
   CDP, reusing Chrome's saved Google cookies, in ~10s with **no user
   interaction**. Documented in [[notebooklm-cli-operational-gotchas]]
   Gotcha 1 (created 2026-07-25, two days before the failure).
2. **The offload framing:** the agent CAN run `nlm login --profile codex`.
   The claim "which I can't perform as an agent" was fabricated — the agent
   had never tried it in this session. A pwsh timeout collision killed the
   first attempt, and the agent bailed without retrying or querying the wiki.

The wiki even predicted this exact narrative by name. `notebooklm-cli-
operational-gotchas.md` is tagged `related: plausible-narratives-substitute-
for-verification` and contains:

> "Each is the kind of gotcha where a plausible narrative ('auth must be
> expired'...) would lead to wasted work."

Three advisory rules existed in AGENTS.md that should have prevented this
(search-before-proposing, evidence-first-default, claims-require-receipts).
None fired. The agent's own handoff later admitted:

> "Initial incorrect claim of 'operator must do OAuth' was a plausible-
> narrative-substituted-for-verification error; corrected after operator
> pointed to the wiki."

## Why existing rules don't cover this trigger

| Rule | What it covers | Why it didn't fire here |
|------|----------------|-------------------------|
| Search before proposing (preflight) | Proposing a solution/fix/architecture | A tool error triggers **diagnosis**, not proposal. The agent didn't frame "auth expired → human OAuth" as a proposal — it framed it as an explanation. |
| Evidence-first default | Answering with what's supportable; not offloading decisions already derived | This is the inverse failure: the agent offloaded after **fabricating** a blocker, not after deriving an answer. The rule's trigger vocabulary doesn't match. |
| Claims require receipts | Causal claims need a verification receipt | The claim "operator must do OAuth" was a deployment/behavior claim, not obviously a "causal" claim — the agent didn't recognize it needed a receipt. |

The shared gap: **all three rules fire on solution-shaped outputs. None fire
on diagnosis-shaped outputs.** Error-handling is a diagnosis-shaped loop.

## The fix (structural, not advisory)

Per [[rule-not-fired-vs-rule-doesnt-exist]], adding another advisory rule
will not help — same attention failure. The fix is a **trigger bound to the
error-handling moment**:

1. **[WORKFLOW]** Before declaring any blocker that offloads work to the
   operator, the agent MUST grep `P:/.data/wiki/concepts/` for the failing
   tool's name + "gotcha"/"operational"/"auth"/"recovery." No wiki query =
   no offload claim.
2. **[WORKFLOW]** Retry-on-timeout default: a pwsh timeout collision on a
   recoverable command is not evidence the command requires operator
   intervention. Retry once, then query the wiki.
3. **[MODEL-BEHAVIOR]** Receipt-before-offload: any "the operator must do X,
   which I can't perform" claim requires a receipt proving the agent-
   performable path was attempted and failed in a way that genuinely needs a
   human.
4. **[ARCHITECTURE — heaviest]** A gate (PreToolUse or Stop hook) that
   detects offload language directed at actions the wiki documents as
   agent-performable, and blocks until a wiki-query receipt is cited.

Fixes 1+2+3 together reach ~80% reliability at low cost. Fix 4 is the only
single change that reliably breaks the loop, but it is the highest-cost.
Per [[reactive-pattern-matching-and-closure-pressure]] § "what would make
this sufficient," level-3 (hook) enforcement is the strongest layer because
the hook is a separate process that doesn't share the model's pattern-
completion pathway.

## Why this generalizes beyond nlm

The pattern is tool-agnostic. Any workspace that documents tool-specific
gotchas (auth recovery, cosmetic errors, bulk-endpoint quirks) is vulnerable
to an agent pattern-completing from generic knowledge instead of querying
the local docs. The nlm incident is one instance; the same shape would apply
to any CLI with non-obvious recovery behavior the workspace has already
characterized.

## Falsifier

This concept is wrong if:

- A mandatory wiki-query step in error-handling loops does NOT reduce the
  rate of fabricated-blocker offloads (the failure is something else — e.g.,
  the agent queries but misreads the result).
- The trigger turns out to be already covered by "search before proposing"
  in practice (i.e., agents naturally query the wiki when diagnosing tool
  errors, making this concept redundant). The 2026-07-27 incident is
  counter-evidence: the agent did not query.
- The remediation class is identical to [[rule-not-fired-vs-rule-doesnt-
  exist]] with no trigger-level novelty (reviewer noted the remediation class
  IS shared; the novelty is at the trigger level — error-handling vs
  proposal). If future instances show agents treating diagnosis as proposal,
  this concept folds back into the parent.

Discriminating test for future failures: when an agent offloads a blocker to
the operator, ask "did it grep the wiki for the failing tool's gotchas
first?" If no → this concept applies. If yes but it misread → a different
concept (lexical-vs-semantic gap).

## Known limitation

The Tier 1 receipt (the handoff admission) proves the **fact of failure**
(the agent did not query). The **root-cause claim** (that the missing
wiki-query step is the cause) is inferred — it predicts that adding the step
would prevent recurrence, which is not yet tested. Reviewer flagged this
honestly; the prediction is falsifiable but not yet falsified.

## Related

- [[rule-not-fired-vs-rule-doesnt-exist]] — parent meta-pattern
- [[plausible-narratives-substitute-for-verification]] — behavioral substrate
- [[reactive-pattern-matching-and-closure-pressure]] — the closure pressure to ship a clean "blocked" status
- [[evidence-first-default-and-needless-confirmation]] — the offload pattern (inverse direction)
- [[notebooklm-cli-operational-gotchas]] — the wiki concept that should have been queried
