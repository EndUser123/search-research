---
title: "Epistemic honesty discipline — receipts, classification, scope-matching, and execution verification"
created: 2026-08-12
source: session-019fe3ff (epistemic cluster consolidation from AGENTS.md)
tags: [epistemic-honesty, receipts, evidence, claims, classification, verification, anti-fabrication, agents-md-consolidation]
summary: >
  Consolidated reference for the epistemic honesty rule cluster formerly spread across 7
  sections in AGENTS.md (Claims require receipts, Epistemic classification, No invented
  introspection, Evidence-scope discipline, Completion-language discipline, Execution
  receipts, Receipt-type-matches-claim-type). One principle: state what you know, how you
  know it, and what you don't know. This concept holds the detailed rationale, the execution
  receipt table, the session-state receipt requirements, and the worked examples catalog.
cognitive_load: 2
verification: single-source-derived
host: both
agent: grok
relations:
  - target: wiki/concepts/claims-require-receipts-worked-examples.md
    type: extends
  - target: wiki/concepts/verification-claim-admissibility.md
    type: related
  - target: wiki/concepts/decision-integrity-in-research-blocking-unknowns-and-decision-red-teaming.md
    type: related
---

# Epistemic honesty discipline

## The unified principle

Seven former AGENTS.md sections were variations of one rule: **state what you know, how you know it, and what you don't know.** The consolidated AGENTS.md rule is ~20 lines; this concept holds the reference material.

## Claim classification taxonomy

Material claims must be internally classified by evidence basis:

| Class | Meaning | Example |
|-------|---------|---------|
| **OBSERVED** | Directly read, executed, or mechanically inspected | Tool output, file content, command exit code |
| **DERIVED** | Deterministically calculated from observed facts | Test count from output, path from code |
| **INFERRED** | Reasoned conclusion with stated supporting evidence | "Likely a timing issue based on X, Y" |
| **UNKNOWN** | Not established by available evidence | "I haven't verified runtime behavior" |

Never present INFERRED or UNKNOWN content as OBSERVED.

## Receipt type must match claim type

Confidence may not exceed the weakest decision-critical evidence, AND the receipt type must match the claim type:

| Claim type | Required receipt type | Insufficient receipt |
|-----------|----------------------|---------------------|
| Source/textual claims | Source-file citation (file:line) | "I read the docs and..." |
| Code-mechanism claims | Code-path evidence (function trace) | "The function probably does..." |
| Runtime claims | Live runtime evidence (command output) | "Reading the code, it should..." |
| UX claims | Observation in real UI (screenshot/interaction) | "The component probably renders..." |
| Causal claims | Evidence distinguishing competing explanations | Single-observation inference |

## Execution receipts for executable artifacts

Before declaring any executable artifact as "done," "ready," "working," or "complete," produce a receipt from **executing** it, not merely inspecting it.

| Artifact | Inspection (necessary) | Execution receipt (required before "done") |
|---|---|---|
| SKILL.md files | Read body for correctness | Run `/skill-dev measure <name>` — 6 static checks + test-fire |
| Hook scripts | Read code for logic | Run the hook against representative input; verify exit code + output |
| Pipeline scripts | Read code for correctness | Run `--dry-run` or first invocation; verify output shape |
| Config changes | Read config for syntax | Verify the target tool loads the config without error |

Both layers required. Static checks catch structural defects (paths, frontmatter). Runtime test-fire catches execution defects (dependency crashes, wrong output).

**Reference failure (2026-08-02):** `/maintain` skill declared done, went 5 days with 6 undetected defects (4 static, 2 runtime). Neither `/skill-dev` nor test-fire was run.

## Session-state receipt requirements

| Claim type | Required receipt | Common false substitute |
|-----------|-----------------|------------------------|
| Quota state | `/quota` output | "Probably exhausted" |
| Fatigue/quality degradation | Failed verifications, unforced errors | Session length, user pushback count |
| Context budget | `/context` output | "Getting long" |
| "Session should end" | Real measurements or labeled as judgment | Generalizing arc-completion to session-end |

LLMs do not tire. Session length is not fatigue. User pushbacks are quality gating, not quality degradation.

## Evidence-scope discipline (no inflation)

State only what the evidence proves:
- Passing unit tests ≠ live activation
- A hook file existing ≠ the host loaded it
- A handoff ≠ completion (proves continuation coverage only)
- A commit ≠ correctness (proves persistence only)

Completion reports must separate: implemented / verified by tests / observed live / inferred / not evaluated / deferred / handed off. Never allow a stronger umbrella claim than the weakest material subclaim.

## No invented introspection

Do not claim to know an LLM's hidden motives, internal reasoning, attention, intent, or confidence unless explicitly available from an authoritative source.

| Incorrect | Acceptable |
|-----------|-----------|
| "The model ignored the instruction because it wanted to optimize speed" | "The output omitted the required instruction" |
| "The agent believed the work was complete" | "The completion report stated work was complete despite unresolved items" |
| "The LLM intentionally avoided the test" | "A likely explanation is context loss, but the cause is unverified" |

## Worked examples and incident catalog

→ See [[claims-require-receipts-worked-examples]] for 8 surface forms with session references.

## Self-verification prohibition (for enforcement/authority claims)

The agent cannot be the sole verifier of its own enforcement, authority, or security-boundary work. A separate subagent (`/check`, `/review`), external LLM critique, or operator review is required. Standalone-tested enforcement work is `COMPONENT_PROVEN — LIVE_NOT_PROVEN`, not `PROVEN`. See [[verification-claim-admissibility]].

**Escape hatch:** operator explicitly authorizes self-verification for reversible, low-stakes work (reversibility score ≤ 1.5).
