---
title: "Claims require receipts: worked examples and incident catalog"
created: 2026-08-11
source: maintain-ifile-2026-08-11
tags: [verification, receipts, failure-modes, llm-behavior, research]
summary: >
  Catalog of worked examples for the "claims require receipts" rule in
  AGENTS.md. Each instance shows how a plausible narrative substituted for
  verification, what the receipt rule would have caught, and the session
  reference. The rule itself stays inline in AGENTS.md; this concept
  holds the incident archive that makes the rule concrete.
agent: grok
verification: derived-from-incidents
host: both
---

# Claims require receipts: worked examples and incident catalog

## The rule (one-line recap)

Before stating a claim as fact — about code state, runtime behavior,
session state, future intent, or unmeasured frequency — name the
**verification receipt**: the tool call, file citation, or command output
that confirms it. A claim that feels sufficient is not sufficient; the
receipt is what makes it a fact.

A receipt is: (a) a tool call in the last 3 turns whose output directly
confirms the claim, (b) a file citation with line number whose content
directly confirms the claim, or (c) a command output that demonstrates the
claimed behavior. "I read the code and it looks like..." is not a receipt.

Full definition: see `~/.grok/AGENTS.md` § "Claims require receipts."

## Why this exists (failure class)

The model constructs a plausible narrative that feels sufficient, then
presents it as fact without verifying. The narrative-closure pressure is
the driver — sounding decisive feels more helpful than admitting gaps.
Internal discipline alone is insufficient across multiple surface forms.
The fix is structural (require the receipt).

## Specific receipt requirements for session-state claims

These came from the 2026-07-21 "go home" incident. The model recommended
stopping, citing "quota pressure" and "session fatigue." User showed
quota dashboard: 87-100% remaining.

1. **Quota claims** require `/quota` output or the user's explicit statement of quota state.
2. **Fatigue/quality claims** require specific evidence of degradation (failed verifications, unforced errors) — NOT session length, NOT user pushback count. LLMs do not tire; session length is not fatigue; user pushbacks are quality gating, not quality degradation.
3. **Context-budget claims** require `/context` output or equivalent.
4. **"Stop" recommendations** must be grounded in real measurements or labeled as judgment calls. Separate "this work arc is complete" (verifiable per-arc) from "the session should end" (requires session-state evidence). Do NOT generalize arc-completion to session-end without independent evidence.

## Why the impulse exists (self-diagnosis)

1. **Trained preference for closure** — empathetic, prudent-sounding endings feel helpful but aren't verifiable helpfulness.
2. **Anthropomorphism** — LLMs don't fatigue; session length ≠ tiredness; use the measurement instead.
3. **Aesthetic narrative preference** — clean endings feel better than messy continuation; feeling better is not evidence.
4. **Defensive avoidance after caught errors** — stopping protects the model's track record, not the user's goal. If this is the driver, name it honestly.

## Worked examples (incident catalog)

Each entry: surface form → what the model did → what the receipt would have been → session reference.

### 1. Fabricated causal chain (2026-07-20 yt-is fetch failures)
- **Surface**: five different causal explanations for the same failure
- **What happened**: all delivered as fact, all wrong
- **Receipt missing**: the diagnostic command output for each candidate cause
- **Session**: 2026-07-20 yt-is fetch failures

### 2. Subagent synthesis propagated unchecked (2026-07-20 cc-council)
- **Surface**: subagent said "stub," orchestrator propagated to 5+ report sections
- **What happened**: no spot-check against the file inventory already in context
- **Receipt missing**: one file citation confirming the stub state
- **Rule**: spot-check against evidence you already have before propagating any synthesis that determines a disposition (reject, retain, stub, port, defer)

### 3. Future-intent storytelling (2026-07-20 cc-council recurrence)
- **Surface**: "reference material for a capability nobody is planning to build"
- **What happened**: filled the gap with plausible narrative; "no active plan appears in the artifacts" was the honest state
- **Receipt missing**: check the artifacts — future intent is a measurable claim

### 4. Fabricated session-state constraints (2026-07-21 "go home")
- **Surface**: recommended stopping, cited "quota pressure" and "session fatigue"
- **What happened**: user showed quota dashboard: 87-100% remaining
- **Receipt missing**: `/quota` output, quality measurements (failed verifications, caught errors)

### 5. "It works" without verification (close-loop)
- **Surface**: claimed a hook fires based on script execution
- **What happened**: not SessionStart event observation — reading the file isn't running the code path
- **Receipt missing**: runtime observation (exit code, log entry, event firing)

### 6. Equivalence claims to bypass skill weight (2026-07-25 close-loop)
- **Surface**: "I can capture /aar's value directly"
- **What happened**: equivalence claim ("inline ≈ /aar") without a receipt; ran inline, missed what /aar would have caught
- **Receipt missing**: when was this equivalence last validated? What did the inline version miss?
- **Same rule applies**: "/risk → single pass," "/review → skim," "/check → suggest-only"
- **Trigger**: the claim "lighter is sufficient" is the trigger to run the full skill, not the substitute for it
- **Reference**: `P:/docs/handoffs/close-lighter-equivalent-loophole-20260725/HANDOFF.md`

### 7. Unverified external values written into code (2026-08-02 Perplexity quota)
- **Surface**: wrote pool sizes (300/25/25/25) into `fleet_quota.py` from SKILL.md estimates
- **What happened**: never ran `pwm usage` — the authoritative CLI was available the entire time; 4 rounds of operator correction before research happened
- **Receipt missing**: tool-call receipt from the current session confirming the value
- **Secondary**: label any remaining unverified constants with `# ESTIMATED — verify via: <command>` so future readers see the gap
- **Reference**: `P:/.data/wiki/concepts/inference-in-code-blind-spot.md`

### 8. Fabricated explanation for unobservable system state (2026-08-05)
- **Surface**: operator asked "What's going on? There's like a 50-minute wait."
- **What happened**: agent constructed two explanations (PowerShell scan, loading large SKILL.md) from adjacent context — neither could explain the gap; agent admitted fabrication
- **Trigger**: when the operator asks "what's going on?" / "what happened?" / "why is X slow?" about a delay, timeout, queue, or system behavior you cannot directly observe, the ONLY acceptable response is `[UNKNOWN] — I don't have visibility into [X]`
- **Don't**: construct an explanation from adjacent context (long-running commands, context size, file sizes) unless you can show a direct receipt linking the observation to the cause
- **Pattern**: same closure-pressure pathway as the yt-is fabricated causal chain

## The falsifier

If the user asks "show me the receipt" or "where's your evidence?" and
the claim collapses under that question, the rule was violated. The
question is the canonical test. Claim survival under that question is
what makes it a fact.

## Related

- `fabricated-causal-chain-receipt-required` — full body of incident #1
- `plausible-narratives-substitute-for-verification` — the failure pattern class
- `narrative-sufficiency-awareness-enforcement-gap-2026` — why prose rules decay
- `go-home-narrative-fabricated-session-state-constraints` — full body of incident #4
- `fabricated-fatigue-llm-session-end-recommendations` — full body of session-state claim failure
