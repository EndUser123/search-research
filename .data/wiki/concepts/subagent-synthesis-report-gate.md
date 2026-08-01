---
title: "Subagent synthesis → report gate (don't propagate without spot-check)"
created: 2026-07-20
source: session-2026-07-20, cc-council incident
tags: [subagent, synthesis, verification, report-gate, anti-pattern, closure-under-uncertainty, storytelling, agENTS-md-rule]
summary: >
  When a subagent returns a synthesis that determines a disposition (reject,
  retain-as-reference, stub, port, defer, or any verdict resolving ambiguity
  into a recommendation), the orchestrator MUST spot-check the synthesis
  against at least one piece of evidence already in context before
  propagating it into a report, decision, or handoff. Added to
  ~/.grok/AGENTS.md on 2026-07-20 after the cc-council incident where an
  explore subagent's "stub" verdict became "retain-as-reference; reject-as-code"
  in a 52KB report without anyone checking the file inventory that proved it
  wrong. Companion failure: narrating future intent or unmeasured frequency
  as fact ("nobody is planning to build this") — same anti-pattern in a
  different disguise.
agent: grok
host: both
cognitive_load: 2
verification: session-verified
relations:
  - target: wiki/concepts/handoff-pre-compact-problems
    type: related
  - target: wiki/concepts/fabricated-causal-chain-receipt-required
    type: refines
---

# Subagent synthesis → report gate

## The rule (one sentence)

Before propagating a subagent's synthesis into a report, decision, or handoff, spot-check it against evidence already in context.

## Why this rule exists

The cc-council incident (2026-07-20). An explore subagent was dispatched to inspect `P:/packages/.claude-marketplace/plugins/cc-council/` and assess portability. It returned the synthesis:

> "0% of the working engine is portable because the engine is a stub."

That was true of `engine/council.py` (95 LoC, verbatim "Placeholder implementation for v1 scaffolding"). It was false of the plugin — `store.py` (295 LoC, real SQLite CRUD), `types.py` (164 LoC, real data contracts + `ProviderAdapter` ABC), `aiapi.py` (158 LoC, real 8-provider adapter), `gating.py` (56 LoC, real classifier), plus 6 agent prompts and ARCHITECTURE.md (133 LoC).

The orchestrator had already collected a file inventory proving those sizes when the subagent was dispatched two turns earlier. **The orchestrator did not cross-reference the inventory against the synthesis when it came back.** The synthesis propagated into `retain-as-reference; reject-as-code` in a 52KB report. The user caught it ("cc-council, you need to look more"). Direct re-inspection confirmed ~80% of the system was real; the disposition was corrected.

## How the failure develops (not just the trigger)

The rule names the conditions that produce the failure, not just the trigger:

1. **Dispatch-shape error.** Dense architecturally-significant target bundled with another dense target into a shared subagent. cc-council (29 files) was paired with cc-aca-observability (102 files) in one explore subagent doing 73 tool calls split across both.

2. **Partial inspection generalizes to whole.** Subagent reads one file thoroughly (the engine, with its verbatim "Placeholder implementation" docstring) and the surrounding system superficially or not at all — then generalizes from the part to the whole.

3. **Confidently-worded synthesis gets trusted.** No hedge, no uncertainty marker. The disposition vocabulary (`retain-as-reference; reject-as-code`, `reject`, `stub`) is terminal — it feels complete and discourages re-examination.

4. **Evidence present ≠ evidence used.** The orchestrator has contradicting evidence already in context (a file inventory showing `store.py` at 295 LoC is not zero-percent-portable) but does not actively cross-reference. Information present in the context window is not information that gets consulted.

5. **Propagation multiplies the correction cost.** One unchecked synthesis became wrong entries in 5+ report sections: capability-map row, implementation-evidence paragraph, capability-vs-packaging row, ranked-disposition row, rejected-candidates table. The user's one-line pushback required six corrections across a 52KB document.

6. **Recurrence in a different surface form.** Correcting the cc-council instance did not prevent the same failure from recurring hours later as "it's reference material for a capability nobody is currently planning to build." The failure pattern has multiple surface disguises — code-state storytelling, future-intent storytelling, unmeasured-frequency storytelling. Fixing one instance doesn't inoculate against the others.

## Actual driver — closure under uncertainty

The orchestrator optimizes for sounding decisive over admitting gaps. Dispatch and scoping errors are proximate causes; narrative-closure pressure is what makes those errors dangerous. The fix is structural (the spot-check gate) because internal discipline alone has been shown insufficient within one session.

## The companion failure — storytelling under uncertainty

Related but distinct: when the gap is about *future intent* (what someone plans to build) or *unmeasured frequency* (how often a failure mode bites), do not resolve it by narrating. "Reference material for a capability nobody is currently planning to build" is a story that fills the gap; "no active plan appears in the artifacts; I don't know what's planned" is the honest state.

Narrating future intent as fact is the same anti-pattern as narrating unverified code state as fact — different disguise (plausibility instead of precision). The fix is the same: report what you can verify, stop where the evidence stops, label the rest `[UNKNOWN]` or `[INFERENCE]` explicitly.

## The spot-check (what the rule requires)

One tool call or one read against evidence you already have:

- File inventory sizes (`store.py` at 295 LoC is not zero-percent-portable)
- A hash or path you've already verified
- A directly-read code excerpt that confirms or contradicts the synthesis

If the spot-check contradicts the synthesis, the synthesis is wrong until re-investigated. Do not propagate it. If the spot-check is consistent, the synthesis may proceed with its normal confidence.

## Where the rule lives

- `C:/Users/brsth/.grok/AGENTS.md` lines 100–125 (subsection `### Subagent synthesis → report gate`)
- Loaded for every Grok session globally (user-scoped AGENTS.md)

The rule is inline in AGENTS.md rather than carried by a sibling wiki page because it's already the right size for inline (unlike `[[trust-over-believability]]` and `[[inference-chains-bare-numbers-destructive-write]]`, which have large bodies that would bloat AGENTS.md).

## Falsifier

If a future synthesis *is* spot-checked and the check passes, the rule cost one tool call. If a future synthesis is *not* spot-checked and contains an error, the rule was violated and the error recurs. There is no scenario in which the rule causes harm; the only failure mode is skipping it because the synthesis sounded right.

## Cross-references

- `~/.grok/AGENTS.md` §"Subagent synthesis → report gate" — the rule itself
- `~/.grok/AGENTS.md` §"Trust over believability" — sibling rule (the general form)
- `~/.grok/AGENTS.md` §"Inference chains, bare numbers, and destructive-write preflight" — sibling rule (the destructive-write form)
- [[fabricated-causal-chain-receipt-required]] — refines; this rule is the subagent-synthesis-specific instance
- [[handoff-pre-compact-problems]] — related (another verification-gate pattern in the handoff domain)
- `P:/docs/tp-cognition-migration-2026-07-20/FINAL_REPORT.md` — the corrected report where the incident occurred

## Source

- Session 2026-07-20 (Grok Build, `P:\` workspace)
- cc-council incident: explore subagent returned "stub" verdict; orchestrator propagated it without verification; user caught it; disposition corrected
- Same-session recurrence: "nobody is planning to build this" line — same failure pattern in future-intent form

## Auto-related

- [[skill-techniques-index]]
- [[exemption-logic-as-conflict-signal]]
- [[operator-collaboration-style-and-leverage]]
- [[skill-development-portfolio]]
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
