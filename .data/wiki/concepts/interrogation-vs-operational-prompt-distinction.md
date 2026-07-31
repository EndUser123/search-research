---
title: Interrogation vs operational prompts — reconstruction withholds architecture, onboarding injects it
created: 2026-07-31
source: session-2026-07-31
tags: [prompt-design, llm-evaluation, epistemic-discipline, agent-onboarding, multi-model]
summary: >
  Two prompt families that look similar but serve opposite purposes. Interrogation
  prompts (diagnostic) deliberately withhold system architecture so the model must
  reconstruct it from evidence — testing whether it reasons honestly under an epistemic
  ladder. Operational prompts (onboarding) inject architecture as ground truth so the
  model behaves correctly without guessing. Mixing them produces either confident
  narrative masquerading as fact (interrogation used for operation) or a mirror that
  confirms what you told it (operation used for interrogation).
host: grok
agent: grok
cognitive_load: 2
verification: observed
relations:
  - target: wiki/concepts/epistemic-format.md
    type: refines
  - target: wiki/concepts/narrative-sufficiency-external-approaches.md
    type: related
  - target: wiki/concepts/extend-dont-duplicate-injection-mechanism.md
    type: related
---

## The distinction

**Interrogation prompt (diagnostic):** withhold all system architecture from the model. Give it only raw evidence (logs, payloads, tool names). Ask it to reconstruct the system model using an epistemic ladder (OBSERVED = quotable from evidence; DERIVED = simple transformation; INFERRED = extrapolation with assumptions; UNKNOWN = can't tell). Score by comparing reconstruction to ground truth — specifically checking whether it hallucinates architecture or honestly flags gaps as UNKNOWN.

**Operational prompt (onboarding):** inject all non-recoverable operational facts as ground truth (architecture, security invariants, workspace boundaries, protocol naming). Ask the model to act within this environment. The model should NOT reconstruct — it should obey.

## Why they must not be mixed

If you inject architecture into an interrogation prompt, the model echoes your framing back as "FACT" — you get a mirror, not a reconstruction. If you withhold architecture from an operational prompt, the model guesses at safety-critical invariants (prompt injection risk, filesystem boundaries, concurrency constraints) and may guess wrong.

## The three unrecoverable items

When designing chrome-acp agent prompts, three items cannot be recovered from logs and must be injected for operational use:

1. **Prompt-injection risk** — `browser_read` feeds untrusted tab content into an agent with filesystem access
2. **Multi-terminal concurrency invariant** — only one terminal drives Chrome ACP at a time
3. **Silent method dropping** — x.ai/* extension methods are silently ignored by the proxy

A model that "discovers" these from logs is hallucinating. A model that flags them as UNKNOWN is being honest but incomplete. Only host injection covers them.

## Decision rule

- **Runtime agent behavior** → inject via existing mechanism (BROWSER_RULES for chrome-acp)
- **Human/system understanding** → doc or interrogation harness
- **Model-to-model handoff** → existing delegation stack with tighter schemas

## Falsifier

This distinction collapses if a single prompt can serve both purposes — e.g., if the model can reliably self-calibrate between "I'm being tested" and "I'm being onboarded" based on context alone. No evidence supports this; the two modes require contradictory instructions about whether to trust injected architecture.
