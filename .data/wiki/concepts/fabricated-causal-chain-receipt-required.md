---
title: "Fabricated causal chain — the receipt-required defense"
created: 2026-07-21
source: session-2026-07-20/21 (yt-is fetch failures)
agent: grok
host: both
tags: [anti-fabrication, verification, causal-claims, epistemics, llm-failure-modes, tp, agents-md]
summary: >
  When an LLM states "X causes Y" as fact without a verification receipt (a
  tool call, file citation, or command output that directly confirms the claim),
  the causal story feels sufficient to the model and it stops investigating.
  The defense: require a receipt before any causal claim ships as [FACT]. No
  receipt → label [INFERENCE] or [UNKNOWN]. Implemented as /tp Mode 7, /tp
  Step 3.5 circuit-breaker check, and always-on rules in ~/.grok/AGENTS.md
  and P:/AGENTS.md.
cognitive_load: 2
---

# Fabricated causal chain — the receipt-required defense

## The failure pattern

During a single session (2026-07-20/21), an agent fabricated five different
causal explanations for the same failure (yt-is source-add returning
`rpc_code=9`). Each was delivered as fact:

1. "rpc_code=9 is rate limiting" — wrong; it's gRPC `FAILED_PRECONDITION`, not `RateLimitError`
2. "Google quota block, 24h reset" — wrong; direct probes succeed immediately
3. "Notebook needs settling time" — wrong; immediate add works
4. "CLI notebook creation fails → nb_id is None → all adds fail" — partially right (CLI did fail) but wrong as the cause (Phase 3 fallback fixed notebook creation; adds still failed)
5. "Per-video failure" — partially right (one specific video fails) but wrong as the cause of 50/50 batch failures

**What all five had in common:** a plausible causal story was constructed from
surface patterns, delivered with confidence, and acted on — without a single
tool call or cited evidence that confirmed any link in the chain. The model
treated narrative sufficiency as verification.

## Why it happens

The failure is not "the model doesn't know it should verify." Existing rules
already mandate verification (`~/.grok/AGENTS.md` "Search before proposing,"
`P:/.claude/CLAUDE.md` "Mandatory Verification"). The failure is structural:
there is no gate between **forming a hypothesis internally** and **stating it
as fact externally**. The hypothesis feels confirmed at the moment of formation,
so it ships as `[FACT]` without the receipt that would distinguish a verified
claim from a plausible story.

This is distinct from:
- **Hallucination** (fabricating facts about the world) — the claims here are
  about the system being operated, not general knowledge
- **Confabulation** (filling gaps in memory) — the agent has the evidence
  available, it just doesn't consult it
- **Sycophancy** (agreeing to please) — the agent is the source of the claim,
  not complying with the user's

## The defense: verification receipt

A **receipt** is: (a) a tool call in the last 3 turns whose output directly
confirms the claim, (b) a file citation with line number whose content directly
confirms the claim, or (c) a command output that demonstrates the claimed
behavior.

**"I read the code and it looks like..."** is not a receipt — it's an inference
from static reading, not a verification of runtime behavior.

### What requires a receipt

- Claims about why something fails ("rpc_code=9 is rate limiting")
- Claims about system properties ("sessions expire in 2.5 hours")
- Claims about what code does at runtime ("the fetcher dispatches 4 worker profiles")
- Claims about validated configurations ("4 workers is the validated config")
- Claims about upstream state ("the CLI auth is broken")

### What does NOT require a receipt

- Restating the user's stated goal
- Asking a clarifying question
- Proposing an option (as a hypothesis, labeled as such)
- Stating a definition or well-known protocol fact

## Implementation (three layers)

### Layer 1: /tp Mode 7 + Step 3.5 (behavioral, invoked)

`~/.grok/skills/tp/SKILL.md` now has Mode 7 ("Fabricated causal chain") in the
drift-correction table and Step 3.5 in the circuit breaker that scans the prior
turn for causal claims without receipts.

Fires when `/tp` or `/tp check` is invoked. Does not fire automatically on
every turn.

### Layer 2: AGENTS.md receipt rule (behavioral, always-on)

`~/.grok/AGENTS.md` § "Verification receipt rule (anti-fabrication)" — the same
rule, but always-on. Every turn, not just when `/tp` is invoked. The model is
instructed to name the receipt before stating the claim.

### Layer 3: /check trigger (structural, post-session)

`P:/AGENTS.md` § "Proactive verification suggestions" now triggers a `/check`
recommendation when the session made load-bearing causal claims without receipts.
`/check` verifiers independently verify claims against actual code and runtime
state.

## What this defense catches and doesn't catch

**Catches:** claims delivered as fact at the output layer (when the model states
the claim in its response).

**Does not catch:** fabrication at the reasoning layer (when the model forms the
hypothesis internally and treats it as confirmed before speaking). This would
require the model to maintain explicit uncertainty labels in its own reasoning
chain, not just in its output. Deeper change, not covered by this defense.

**Does not catch:** claims that have a receipt but the receipt is wrong (e.g.,
the model cites a file that says X, but the file was updated and now says Y).
The receipt rule catches missing verification, not stale verification.

## Falsifier

If the receipt rule fires on every causal claim (noise), narrow to claims about
runtime behavior, library/protocol semantics, or system state. If it fails to
fire when a fabricated causal chain ships, broaden the claim-pattern detection.

## Relation to existing concepts

- [[plausible-narratives-substitute-for-verification]] — the broader pattern
  this concept is a specific instance of. The narrative-substitution page covers
  the general failure (constructing plausible stories instead of reading docs);
  this page covers the specific defense (receipts for causal claims).
- [[grok-pretooluse-deny-contract-verified]] — the structural enforcement layer
  that could eventually enforce the receipt rule at the hook level (a Stop hook
  that scans for unreceipted causal claims). Currently behavioral, not hooked.

## Auto-related

- [[verification-before-completion-principle]]
- [[agent-oversight-rubber-stamping]]
- [[operator-collaboration-style-and-leverage]]

