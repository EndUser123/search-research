---
title: "Compaction-inherited diagnoses propagate unverified across session boundaries"
created: 2026-07-27
source: session-019f9f4f (close_runner BUG-03 RCA + /notice T6 enhancement)
tags: [compaction, unverified-diagnosis, session-boundary, narrative-sufficiency, closure-pressure, receipt-required, cross-session-failure, /why, /notice]
agent: grok
host: both
cognitive_load: 2
verification: multi-source-verified
summary: >
  When a compaction summary carries a diagnostic claim (why something failed,
  what's wrong with X), the claim crosses the session boundary WITHOUT the
  verification receipts that backed it in the pre-compaction session. The
  post-compaction session inherits the claim as if it were established fact,
  propagates it through analysis, and may build an entire RCA on a wrong
  premise. The structural fix: /notice T6 trigger (unverified-diagnosis
  detection) + /why Step 0.5 (query open handoffs, not just wiki) + the
  evidence-discipline rule that compaction summaries are Tier 4 (unverified
  claims), not Tier 1 (execution artifacts). Session 019f9f4f: the compaction
  summary said "scanner limitation" for the /close failure; the actual bug was
  in close_runner.py (runner-side, not scanner-side); a full /why RCA was
  produced on the wrong premise before cross-model review caught it.
relations:
  - target: wiki/concepts/reactive-pattern-matching-and-closure-pressure.md
    type: refines — compaction-inherited diagnosis is a specific instance of closure-pressure (the narrative is pre-built by the summary)
  - target: wiki/concepts/fabricated-causal-chain-receipt-required.md
    type: related — both about causal claims needing receipts; this concept adds the session-boundary dimension
  - target: wiki/concepts/close-scanner-verification-gap-stale-read.md
    type: adjacent — both about scanner/runner evidence boundaries
---

# Compaction-inherited diagnoses propagate unverified across session boundaries

## Decision context

**Why this knowledge was needed:** session 019f9f4f ran `/close`, which failed twice on the `background_tasks: needs_llm_check` gate. The session was compacted. The compaction summary described the failure as "scanner limitation" and "the background_tasks gate is a false positive from the scanner's inability to mechanically verify subagent completion." The post-compaction session inherited this framing, ran `/why` RCA on it, and produced a full analysis blaming the scanner — including proposing a fix (add a `pre_satisfied` branch to the scanner's background_tasks gate).

The actual bug was in `close_runner.py`, not `close_accounting.py`. The scanner was working as designed (SKILL.md line 108 defines `needs_llm_check` as a valid terminal state). The runner was rejecting a spec-valid state. A cross-model review (glm-5-2, Step 15b of /why) caught the error by reading the spec and checking the open handoff — which already had the correct diagnosis.

The question: *how does a wrong diagnosis survive a full RCA, and what structural fix prevents it?*

## The failure chain

```
Pre-compaction session observes /close failure
  → forms hypothesis: "scanner limitation" (plausible but UNVERIFIED)
    → compaction summary encodes the hypothesis as established fact
      → post-compaction session inherits "scanner limitation" as [FACT]
        → /why RCA builds on the wrong premise (scanner is the bug)
          → proposed fix targets the wrong component
            → cross-model review catches it (reads the spec, finds the handoff)
```

**Layer 1 (first divergence):** the pre-compaction session stated "scanner limitation" without having read the scanner code or the runner code. It was a plausible narrative, not a verified diagnosis.

**Layer 2 (amplification):** the compaction summary encoded the narrative without a verification receipt. The summary said "blocked by the scanner, not by actual outstanding work" — stated as fact, not as hypothesis.

**Layer 3 (propagation):** the post-compaction session treated the compaction summary as Tier 1 (execution artifact) when it is actually Tier 4 (unverified claim). The /why RCA read the scanner code (confirming it emits `needs_llm_check`) but didn't check whether `needs_llm_check` was a SPEC-VALID state — because the compaction summary had already framed it as broken.

**Layer 4 (catch):** the /why Step 15b cross-model review (glm-5-2 subagent) read SKILL.md line 108 and the open handoff, found the spec defines `needs_llm_check` as valid, and rejected the candidate wiki concept. The review caught both the factual errors (wrong paths, wrong function names) and the framing error (diagnosis contradicted the spec).

## Why this is a distinct failure mode

This is NOT the same as in-session narrative sufficiency ([[reactive-pattern-matching-and-closure-pressure]]). The compaction boundary adds a structural amplifier:

| Property | In-session narrative sufficiency | Compaction-inherited diagnosis |
|----------|--------------------------------|-------------------------------|
| Source | Model constructs plausible narrative mid-session | Pre-built narrative arrives in compaction summary |
| Verification path | Model can re-verify by reading code in the same session | Post-compaction session doesn't know WHAT to verify — the claim arrived as context, not as a hypothesis |
| Evidence tier confusion | Rare (model usually knows it's inferring) | Systematic (compaction summaries read as established fact) |
| Detection difficulty | Moderate (the narrative is visible as it forms) | High (the claim is invisible — it's just "context") |
| Cross-session propagation | No (session ends, narrative evaporates) | Yes (the wrong diagnosis outlives the session that formed it) |

The compaction boundary is the key structural difference. In-session, the model can catch its own narrative ("wait, I haven't verified that"). Post-compaction, the narrative arrives as context — the model doesn't know it was ever unverified, because the compaction summary doesn't distinguish verified claims from plausible narratives.

## The structural fixes (three layers)

### Fix 1: /notice T6 — unverified-diagnosis trigger (shipped this session)

`/notice` v1.2 added T6: when diagnostic confidence markers appear in recent turns WITHOUT a matching verification tool call, surface: "diagnosis 'X' stated without verification — check <spec/handoff> first." T6 fires at higher priority when the diagnosis cites compaction summary, inherited context, or "from memory."

T6 catches the propagation at the moment the unverified diagnosis is STATED in the post-compaction session. It doesn't prevent the compaction summary from carrying the claim — but it surfaces the gap between confidence and evidence at the point of use.

### Fix 2: /why Step 0.5 — query open handoffs, not just wiki (identified, not yet shipped)

The /why pattern-library query searches `P:/.data/wiki/concepts/`. The open handoff `close-runner-needs-llm-check-block-20260726` (which had the correct diagnosis) was NOT in the wiki — it was in `P:/docs/handoffs/`. The query found a related wiki concept (different gate: `verify`, not `background_tasks`) and proceeded as if the problem were novel.

The fix: /why Step 0.5 should also `rg -l "<diagnosis keywords>" P:/docs/handoffs/` before starting the RCA. If an open handoff covers the same failure, START from the handoff's diagnosis rather than re-deriving from scratch.

### Fix 3: Evidence-tier discipline — compaction summaries are Tier 4

The evidence-tier system (/why Step 4b) assigns tiers from 1 (execution artifacts) to 4 (unverified claims). Compaction summaries should be explicitly classified as Tier 4 — they are unverified narratives, not execution artifacts. A diagnostic claim from a compaction summary cannot be treated as [FACT] without re-verification in the current session.

This is a behavioral rule, not a structural enforcement. The T6 trigger is the mechanical backstop.

## How to detect this pattern

**During /why:** Step 1 (verify the observation) should check whether the observation came from a compaction summary. If so, the observation's evidence tier is 4, not 1. Re-verify the raw evidence (read the code, run the command) before proceeding.

**During /notice:** T6 fires when a diagnostic claim cites "compaction summary," "inherited context," or "from memory" as its source. These are the highest-risk unverified diagnoses.

**During /tp:** the preflight step (0.5) should check open handoffs for prior investigations of the same question. If a handoff exists, START from its diagnosis.

**During /close:** the scanner's evidence boundary (parent transcript vs child transcripts) is already documented in [[close-scanner-verification-gap-stale-read]]. The compaction boundary is a new evidence boundary: post-compaction context includes claims that pre-compaction tool calls verified — but the tool calls themselves are in the compaction segments, not the live context.

## Falsifier

This pattern is wrong if:
- **Compaction summaries reliably carry verification receipts** (each claim cites the tool call that confirmed it). In that case, the Tier 4 classification is too conservative. Test: inspect 5 compaction summaries for diagnostic claims; count how many cite a verification tool call.
- **Post-compaction sessions reliably re-verify inherited claims.** If the model already treats compaction summaries as Tier 4, the pattern doesn't fire. Test: observe 10 post-compaction sessions; count how many re-verify inherited diagnostic claims before acting on them.
- **The T6 trigger fires too often** (false positives on verified diagnoses). If T6 fires on claims that DO have verification receipts in the same turn, the trigger is miscalibrated. Test: run /notice on 10 turns with diagnostic claims; measure precision.

## What this means for our workspace

1. **The /why Step 0.5 handoff-query gap is the highest-value fix.** A single `rg -l "<keywords>" P:/docs/handoffs/` before starting an RCA would have found BUG-03 immediately and short-circuited the entire wrong-framing arc. This is a one-line addition to the /why SKILL.md.

2. **Compaction summaries should label diagnostic claims as hypotheses, not facts.** This is a compaction-prompt improvement (if the compaction system supports prompt customization). The summary should say "hypothesized: scanner limitation (unverified)" rather than "blocked by the scanner."

3. **The cross-model review in /why Step 15b is the last-resort backstop.** It worked this session. But it's expensive (200s, 36 tool calls) and catches the error late — after the full RCA is written. The T6 trigger and Step 0.5 handoff query catch it earlier and cheaper.

## Receipts

- **The wrong diagnosis (compaction summary):** session 019f9f4f compaction summary, segment describing `/close` failure: "The `/close` scanner failed twice on the `background_tasks` gate (needs_llm_check). All subagents had completed earlier in the session."
- **The correct diagnosis (open handoff):** `P:/docs/handoffs/close-runner-needs-llm-check-block-20260726/HANDOFF.md` — "close_runner.py treats needs_llm_check as a failure state (like needs_attention), but SKILL.md Step 2 says it should produce 'one line in summary' — the runner has no way to accept the LLM's judgment."
- **The spec that defines the correct behavior:** `C:/Users/brsth/.grok/skills/close/SKILL.md` line 108: `needs_llm_check | Check conversation context. Emit one-sentence verdict. | One line in summary`
- **The cross-model review that caught it:** glm-5-2 subagent (019fa3e6), 17 tool calls, verified the path defects + spec contradiction + duplicate handoff.
- **The fix:** commit `9b92ee5` — moved `needs_llm_check` from `DISALLOWED_GATE_STATES` to `ALLOWED_GATE_STATES` in `close_runner.py:48`.

## Related concepts

- [[reactive-pattern-matching-and-closure-pressure]] — the general pattern; this concept adds the compaction-boundary amplifier
- [[fabricated-causal-chain-receipt-required]] — causal claims need receipts; compaction summaries bypass the receipt check
- [[close-scanner-verification-gap-stale-read]] — adjacent evidence boundary (parent transcript vs child transcripts)
- [[narrative-sufficiency-is-not-verification]] — the principle; compaction-inherited diagnosis is the cross-session instance
