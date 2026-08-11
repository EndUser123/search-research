---
title: "Writing a discipline doesn't enforce it: the self-referential gap"
created: 2026-07-21
source: AAR report 12 (console_fa595529, 20260721-aar)
tags: [discipline, self-referential, enforcement, rules, meta-pattern]
host: both
agent: grok
verification: multi-source-verified
cognitive_load: 2
confidence: 0.90
last_verified: 2026-08-11
half_life_days: 730
summary: >
  Writing a rule in a skill file or AGENTS.md that says "always verify
  before claiming" does not make the agent verify. The rule is advisory
  text; enforcement requires a structural mechanism (hook, gate, metric).
  The gap between writing discipline and enforcing it is itself a
  recurring failure mode.
---

# Writing a discipline doesn't enforce it: the self-referential gap

## The pattern

An agent writes a new rule: "Always verify claims before stating them as fact." The rule goes into AGENTS.md or a skill file. Future sessions read the rule. They still make unverified claims.

The gap: **writing the rule is an act of authorship, not an act of enforcement.** The rule becomes text that the model reads, understands, and then violates — because reading text does not structurally prevent the violation.

## Why this happens

1. **AGENTS.md rules are advisory.** They load at session start as context, not as executable constraints. The model can read "never force-push" and still force-push because nothing structurally prevents it.
2. **Skill files are loaded on-demand.** A skill that says "verify after every edit" only fires when the skill is invoked. Between invocations, the rule doesn't apply.
3. **The rule author is also the rule violator.** The same agent that writes "always check" is the one that later skips the check. Writing the rule creates a sense of having addressed the problem without actually addressing it.

## The structural fix

Each rule should declare its enforcement mechanism:

| Mechanism | What it does | Reliability |
|---|---|---|
| `rule` (AGENTS.md text) | Advisory; model reads and may follow | Low (relies on model compliance) |
| `hook` (PreToolUse/Stop gate) | Blocks or warns at runtime | High (code executes regardless of model behavior) |
| `metric` (telemetry/observability) | Surfaces violations post-hoc | Medium (detects but doesn't prevent) |
| `config` (default behavior change) | Changes what the system does by default | High (applies without model awareness) |

**The hierarchy:** `config` > `hook` > `metric` > `rule`. A rule alone is the weakest intervention. If the failure recurs despite the rule, the fix is to promote to the next level.

## Evidence

- **R12 L2** (session fa595529): The agent wrote discipline concepts and rules in the same session where it violated them. The session's AAR report itself notes: "Writing a discipline doesn't enforce it."
- **R10 L2** (session 019f819a): "Rule-not-fired is the dominant process failure mode." Rules exist but don't fire. This is the same pattern: rules as advisory text that doesn't bind.
- **This session (019f8507):** The operator's verification-receipt rule in AGENTS.md existed before this session. The agent still made 3 narrativized claims without receipts. The rule was read but not enforced.
- **Session 019fe4c1 (2026-08-09):** The AGENTS.md web-search tool-selection rule listed DDG as priority #1. The agent defaulted to the built-in `web_search` (last resort) instead — six MCP search servers connected, zero used. The rule was loaded in context; it did not fire. The fix was structural: promote `search_web__query` to #1 with an explicit decision-rule prompt ("before using ANY search tool, ask: did I try search_web__query first?"). This session is a fourth instance of the pattern, and the fix followed the hierarchy (rule → config/promotion).

## Counterexample

Some rules DO work as advisory text — specifically when:
- The model has strong prior alignment with the rule's intent
- The failure mode is rare (the rule reminds the model of something it would mostly do anyway)
- The cost of violation is low (reversible, cosmetic)

For high-cost, high-frequency failure modes, advisory text is insufficient.

## Related

- [[rule-not-fired-vs-rule-doesnt-exist]] — the companion pattern: rules exist but don't fire
- [[plausible-narratives-substitute-for-verification]] — specific instance of this pattern in causal claims

## Auto-related

- [[skill-enforcement-layers]]
- [[skill-enforcement-deep-dive]]
- [[I'm-going-to-create-a-hook-to-enforce-discovery-be]]
## Falsifier

This concept is wrong or obsolete if:
- **A "rule-as-advisory" mechanism is shown to be sufficient for high-cost, high-frequency failure modes** — i.e., a peer-reviewed study demonstrates that prose rules achieve enforcement-grade compliance without code/hardware enforcement. The current `external-state-cross-check-as-structural-fix` design test ("stop-hook scanning agent output for hedge words" = "partial" because the actor controls its output) would have to be overturned with evidence.
- **The `config > hook > metric > rule` hierarchy is empirically reversed** — e.g., a study shows that adding a rule to AGENTS.md produces a stronger compliance effect than adding a hook, even after controlling for the rule's tightness. The hierarchy is currently supported by the [[best-practices-enforcement-mechanism-grok-build]] synthesis and prior incident records (R10, R12, 019f8507, 019fe4c1), not by an independent study.
- **The pattern stops recurring in the workspace.** If 100+ future sessions show that every prose rule that gets written is also followed by enforcement, the pattern is resolved. (Low likelihood; the structural mitigation is in place, not the elimination of the pattern.)
- **No further instances of the pattern have been observed in 12 months.** Last-verified soft deadline: 2027-08-11. If the pattern recurs, the falsifier stays open.

## What this means for our workspace

**Reference document — but the structural fix has been built.** The pattern is descriptive; the implementation is in three follow-on concepts:

1. **`best-practices-enforcement-mechanism-grok-build.md`** (2026-07-24) — converts the `config > hook > metric > rule` hierarchy into a 4-property tested Windows architecture: (1) detection from external state, (2) enforcement as block+prompt, (3) `stop_hook_active` termination guard, (4) programmatic over LLM-as-judge validators. This is the architectural blueprint for any new rule that wants to actually fire.
2. **`advisory-vs-mandatory-triggers.md`** — operationalizes the rule-vs-hook split as a mandatory/discretionary taxonomy. Mandatory triggers (high cost, high frequency) get structural enforcement; discretionary triggers (low cost, rare) get prose rules.
3. **`agent-control-plane-enforcement-architectures-2026.md`** — places the hook enforcement layer in the wider control-plane stack (sibling to capability discovery, identity, audit). HF Autonomous Agent incident (July 2026, 17,600 actions, ~4.5 days) is the reference failure: no structural enforcement, single-word bypass.

**Concrete workspace actions this concept has driven (verified to exist):**
- The verification-receipt rule in `~/.grok/AGENTS.md` is paired with the `Stop_psychological_narrative_gate.py` hook — the structural enforcement layer for the prose rule.
- The `deduplication, gzip, and ED25519 signature` requirements in the receipt-identity rule are checked by the `PreToolUse_receipt_identity.py` hook — same pattern.
- The `Context7 > search_web > minimax-search` tool selection order is enforced by `PreToolUse_skill_first_gate.py` and the **`search_web__query` priority promotion** described in the 019fe4c1 incident — the structural fix for the rule-not-firing-as-defaulted-search failure.

**Still open (the pattern continues to need new structural enforcement):**
- The `last_validated` drift trigger recommended by [[user-modeling-for-agentic-clis]] has not been built — the recommendation itself is now an instance of the pattern. (See the [[user-modeling-for-agentic-clis]] re-evaluation note 2026-08-11.)
- The `/refine-operator-model` skill check for stale operator-profile concepts is not implemented.
- The wiki concept itself is a wiki concept, not a hook — and the operator's wiki validator sweep already flagged that the concept is in the "advisory" tier. This is acknowledged; the pattern is by design descriptive, not executable.

**Action for new rules:** if you write a new rule in AGENTS.md or a SKILL.md, ask yourself: *does this rule have a structural enforcement layer?* If no, the rule is at the lowest tier of the hierarchy and will likely fail under closure pressure. The fix is to either (a) promote the rule to a hook (highest-confidence), (b) add a metric/telemetry that surfaces the violation (medium-confidence), or (c) accept the rule as a low-cost advisory and document the failure mode it cannot prevent.
