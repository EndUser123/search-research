---
title: "Causal mechanism claims require source inspection before durable write"
created: 2026-07-25
source: session-019f96f5
tags: [receipt-rule, causal-claims, durable-write, wiki-authoring, failure-mode, anti-fabrication, cross-host]
summary: >
  The general "Claims require receipts" rule (AGENTS.md) already forbids
  presenting inference as fact. This concept adds a specific high-risk
  surface form: when writing a CAUSAL MECHANISM claim ("X happens because
  the scanner greps the parent transcript") into a DURABLE artifact (wiki
  concept, handoff, commit message, ADR), the agent must READ THE SOURCE
  before writing — not infer the mechanism from observed behavior and
  present the inference as the mechanism. The falsifier is the operator
  asking "explain clearly" or "what's your evidence": if the agent's
  response would require reading the source for the first time, the
  original claim was inference presented as fact. Worked example (the
  incident that surfaced this rule, 2026-07-25): agent wrote a wiki concept
  claiming the close scanner "can't see /check subagent transcripts"
  (mechanism) based on observing that the scanner reported a verification
  gap despite /check running. Operator asked "explain clearly." Agent read
  close_accounting.py for the first time and discovered (a) the mechanism
  claim was correct (lines 422-510 read only parent transcript), but (b)
  the related claim that "verifiers ran tests" was wrong (verifiers ran
  git/static checks, not pytest). The mechanism half survived; the
  worked-example half collapsed. The pattern: inferring mechanism from
  behavior is sometimes right and sometimes wrong, and the agent cannot
  distinguish without reading the source. Fix: source-inspection receipt
  BEFORE the durable write, not after operator pushback. Trigger: about
  to write "X happens because <mechanism>" into a wiki concept, handoff,
  or commit message → stop and read the source first. If you can't cite
  line numbers, you don't have the receipt.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - session-019f96f5 (the incident — close-scanner-verification-gap-stale-read concept)
  - C:\Users\brsth\.grok\skills\close\__lib\close_accounting.py:422-510 (the source read after pushback)
  - C:\Users\brsth\.grok\AGENTS.md "Claims require receipts" rule
relations:
  - target: wiki/concepts/plausible-narratives-substitute-for-verification.md
    type: refines — adds the causal-mechanism + durable-write surface form
  - target: wiki/concepts/go-home-narrative-fabricated-session-state-constraints.md
    type: related — sibling in the closure-pressure family; that concept covers anthropomorphic stop-narratives, this covers unreceived causal mechanisms. Both substitute feeling/narrative for receipt/measurement.
  - target: wiki/concepts/close-scanner-verification-gap-stale-read.md
    type: documented-by — that concept's correction incident is the worked example here
  - target: wiki/concepts/fabricated-causal-chain-receipt-required.md
    type: related — same failure class (causal claim without receipt)
---

# Causal mechanism claims require source inspection before durable write

## Decision context

**Why this concept was needed:** the `~/.grok/AGENTS.md` "Claims require receipts" rule is general — it forbids presenting inference as fact across all claim types. But the rule is enforced irregularly because the failure surface is broad. This concept names a specific high-risk surface form where the rule consistently fails: **causal mechanism claims written into durable artifacts.**

The trigger is narrow but the cost is high: a wrong causal mechanism in a wiki concept misleads every future session that reads it. The fix is narrow too: read the source before writing, not after the operator asks "explain clearly."

## The high-risk surface form

Three conditions together raise the risk that an inferred causal claim ships as fact:

1. **The claim is a causal mechanism** — "X happens because <how the system works internally>"
2. **The artifact is durable** — wiki concept, handoff, ADR, commit message, skill doc
3. **The agent has observed the behavior but not read the source** — inference from input/output, not from code

When all three are true, the agent has a plausible narrative (the behavior was observed) and a closure-pressure incentive (the artifact is being written now). The combination reliably produces inference-as-fact.

## The falsifier question

The operator's "explain clearly" / "what's your evidence" / "show me the receipt" is the canonical test. If the agent's honest answer would require reading the source for the first time, the original claim was inference presented as fact. The question is not hostile — it is the structural test the rule needs.

## Worked example — the incident that surfaced this rule (2026-07-25)

**Setup:** session 019f96f5 ran `/check` (6 verifiers PASS) then `/close`. The close scanner reported `VERIFICATION_GAP` despite the verifiers. The operator asked me to "explain clearly."

**The inferred mechanism (shipped without source inspection):**
> "The scanner can't see /check subagent transcripts because it greps only the parent transcript."

**The actual mechanism (after reading `close_accounting.py` for the first time):**
- Lines 422-510: `_scan_implicit_verification()` reads only `chat_history.jsonl` for the session. ✅ Mechanism claim survived.
- Lines 404-414: detect patterns are `pytest`, `python -m pytest`, `python verify_*.py`. ✅ Mechanism survived.
- The wiki concept also claimed "verifiers DID run tests." ❌ This collapsed — verifiers ran git/static checks, no pytest.

**The recovery:** the wiki concept was patched to separate the verified mechanism (scanner can't see subagent transcripts — true) from the overclaim (verifiers ran tests — false). The mechanism half survived because the inference happened to be correct; the overclaim half collapsed because no receipt existed.

**The lesson:** I got lucky on the mechanism half. The inference-from-behavior method produced a correct claim there and a wrong claim in the same concept elsewhere. There is no way to know which half is which without reading the source.

## Why inference-from-behavior feels sufficient (and isn't)

When you observe "scanner reports gap despite /check running," the inference "scanner can't see /check" feels tight — it's the simplest explanation. But "feels tight" is the same signal as "plausible narrative sufficiency," which is the failure mode the receipt rule exists to prevent. The inference has no receipt; it has a feeling.

The receipt is: `close_accounting.py:422` opens `chat_history.jsonl` only. That's a receipt. Without having read it, the claim is `[INFERENCE]`, not `[FACT]` — regardless of how tight the inference feels.

## The rule

**Before writing "X happens because <mechanism>" into a durable artifact:**
1. **Stop.** Recognize the trigger (causal mechanism + durable write).
2. **Read the source.** Open the file that implements the mechanism. Find the lines that do what you're about to claim.
3. **Cite the receipt.** In the artifact, reference the source location (file:lines or function name). If you can't cite line numbers, you don't have the receipt.
4. **Label appropriately.** If the source confirms the claim, ship as `[FACT] — receipt: <file:lines>`. If the source is unavailable, ship as `[INFERENCE]` and say what would verify it.

## Why "after operator pushback" is too late

The pushback-then-read pattern (what this session did) is better than never reading the source, but it has three costs:

1. **The wrong version shipped first.** A future session reading the wiki concept between write and correction would have taken the overclaim as fact.
2. **The correction is visible.** The wiki concept now has a "Honest caveat" block that was forced by operator pushback — a signal to future readers that the original author wasn't sure.
3. **Operator cognitive load.** The operator had to ask "explain clearly." That's exactly the meta-action the "automate user meta-actions" rule says should be eliminated.

The fix moves the source-reading BEFORE the write, eliminating all three costs.

## How to spot the trigger in your own output

Before finishing a wiki concept, handoff, ADR, or commit message, scan for:

- "X happens because..."
- "The system works by..."
- "The mechanism is..."
- "X can't see Y because..."
- "The scanner/gate/hook does X..."

Each is a causal mechanism claim. For each, ask: "Have I read the source that implements this mechanism in this session?" If no, read it before shipping.

## Related to existing rules

This refines (does not replace):

- **"Claims require receipts"** (`~/.grok/AGENTS.md`) — applies to all claims; this concept names the specific surface form where the rule most often fails
- **"Narrative-as-signal"** (`P:/AGENTS.md`) — "the moment you think 'this can't be done because X,' check whether you've read the documentation" — same pattern, generalized
- **"Plausible narratives substitute for verification"** (wiki) — the parent failure class; this concept is the durable-write-specific instance

## Falsifier

This concept is wrong if:
- **Source inspection before durable writes consistently finds the inference was correct** — in that case the rule is overhead; just ship the inference. (Unlikely: the worked example had a 50% collapse rate.)
- **Operators stop asking "explain clearly" because claims are reliably sourced** — in that case the rule is working and becomes self-reinforcing.
- **A future session reads this concept and still ships an unreceived causal mechanism** — the rule needs structural enforcement (a hook that greps wiki concepts for "because" / "mechanism" and demands a `receipt:` field). Not currently implementable reliably; treat as behavioral.

## Cold-start protocol

If you are about to write a wiki concept, handoff, or commit message and you find yourself writing "because <mechanism>":

1. Stop.
2. Open the source file that implements the mechanism.
3. Find the lines.
4. Cite them in the artifact.
5. If you can't find them, the claim is `[INFERENCE]`, not `[FACT]`.

The operator should not have to ask "explain clearly." The receipt should already be in the artifact.

## Related concepts

- [[plausible-narratives-substitute-for-verification]] — the parent failure class
- [[fabricated-causal-chain-receipt-required]] — same failure class, different surface
- [[close-scanner-verification-gap-stale-read]] — the worked example (corrected version)
