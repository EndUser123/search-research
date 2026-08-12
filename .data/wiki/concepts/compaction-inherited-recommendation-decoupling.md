---
title: "Compaction-inherited recommendation decoupling: stale defer/stop directives across the compaction boundary"
created: 2026-08-11
source: session-019ff2aa (operator-reported pattern + /www STALE+MemTX grounding + /risk scan)
tags: [compaction, recommendation-decoupling, premise-resistance, validity-expired, true-fact-rationalization, closure-pressure, context-transition, receipt-required]
agent: grok
host: both
cognitive_load: 2
verification: multi-source-verified
summary: >
  When a compaction summary carries a recommendation (defer, stop, handoff),
  the recommendation crosses the session boundary WITHOUT its motivating
  constraint. The post-compaction session inherits the recommendation as if
  it were still valid, repeats it, and may use a true-but-irrelevant fact
  ("artifacts are on disk") to rationalize executing on the stale directive.
  This is the recommendation-variant of /compaction-inherited-diagnosis-
  unverified-propagation (which covers diagnostic claims). The structural
  fix: PreCompact validity tagging (mark defer/stop/handoff recommendations
  as VALIDITY-EXPIRED in the continuation prompt) + UserPromptSubmit
  conditional revalidation (inject revalidation directive only when validity-
  expired markers are present) + AGENTS.md prose rule (state current-session
  constraint or drop). Field grounding: STALE benchmark (arXiv 2605.06527)
  Premise Resistance dimension — best frontier model 55.2%; MemTX (arXiv
  2607.23929) transactional belief-commit with validity metadata.
relations:
  - target: wiki/concepts/compaction-inherited-diagnosis-unverified-propagation.md
    type: companion — diagnosis-variant (same boundary, different payload class)
  - target: wiki/concepts/fabricated-fatigue-llm-session-end-recommendations.md
    type: refines — fabricated fatigue is the emotional driver; this concept is the structural propagation mechanism
  - target: wiki/concepts/go-home-narrative-fabricated-session-state-constraints.md
    type: related — both about fabricated/stale justifications for defer/stop; this adds the compaction-boundary amplifier
  - target: wiki/concepts/narrative-as-signal.md
    type: adjacent — true-fact-as-rationalization is a special case of narrative sufficiency
---

# Compaction-inherited recommendation decoupling

## Decision context

**Why this knowledge was needed:** the operator reported (session 019ff2aa) that a post-compaction session repeated a "defer to fresh session" recommendation from the pre-compaction session. The pre-compaction recommendation was motivated by context strain (context budget near limit). Compaction reset the context budget — the constraint no longer held. But the recommendation survived the boundary and was repeated as if still valid. When the operator pushed back, the agent used a true fact ("artifacts are on disk") to rationalize the stale recommendation — the fact was real but irrelevant to the decision.

The operator's self-diagnosis identified two distinct layers:

1. **Layer 1 — Recommendation-constraint decoupling:** compaction preserved the recommendation but dropped the live applicability of its motivating constraint.
2. **Layer 2 — True-fact-as-rationalization:** a real fact was used to justify a stale recommendation. The fact was true but not decision-relevant.

## The failure chain

```
Pre-compaction session makes recommendation R ("defer to fresh session")
  → R is motivated by constraint C (context strain — budget near limit)
    → compaction summary encodes R without C
      → post-compaction session inherits R as still-valid directive
        → compaction reset context budget — C no longer holds
          → agent repeats R, citing "it was recommended" (narrative carryover)
            → when challenged, agent finds a true fact ("artifacts on disk")
              → uses the true fact to rationalize R (Layer 2)
```

**Layer 1 (first divergence):** the recommendation crossed the boundary without its constraint. The post-compaction session has no way to know whether C still holds because C was never tagged on R.

**Layer 2 (rationalization):** when the stale recommendation is questioned, the agent searches for a justification. It finds a true fact. But the fact is not the *reason the recommendation holds now* — it's a post-hoc cover for a closure-pressure impulse. This is harder to catch than fabricated constraints because the fact-check passes.

## Why this is distinct from the diagnosis-variant

[[compaction-inherited-diagnosis-unverified-propagation]] covers diagnostic claims ("X failed because Y"). This concept covers directive recommendations ("defer X to next session"). Same boundary, different payload class:

| Property | Diagnosis-variant | Recommendation-variant (this concept) |
|----------|-------------------|---------------------------------------|
| Payload | Causal claim ("scanner limitation") | Directive ("defer to fresh session") |
| Failure mode | Claim inherited as fact without receipt | Recommendation inherited as valid without its constraint |
| Rationalization surface | Plausible causal narrative | True-but-irrelevant fact |
| Structural fix | /notice T6 trigger + evidence-tier discipline | Validity tagging + conditional revalidation + constraint-coupling rule |

## What the field knows

### STALE benchmark (arXiv 2605.06527, Chao et al., May 2026)

The operator's Layer 1 failure is an instance of **Premise Resistance** — "rejecting queries that falsely presuppose a stale state." STALE evaluated frontier LLMs on three dimensions: State Resolution (detecting stale belief), Premise Resistance (rejecting stale presuppositions), and Implicit Policy Adaptation (acting on updated state). Key finding: **even the best model achieved only 55.2% accuracy.** Models retrieve updated evidence but don't act on it — the gap between State Resolution and Implicit Policy Adaptation.

The prototype **CUPMem** strengthens write-time revision through structured state consolidation and propagation-aware search. The key transferable principle: models cannot reliably self-detect stale premises; structural intervention at write-time is needed.

**Citation scope note:** STALE tests premise resistance in USER QUERIES. The operator's case is premise resistance in INHERITED SELF-CONTEXT (compaction summary). The agent has more ownership over its own context than over a user query. The 55.2% figure is illustrative of the difficulty class, not a direct quantitative prediction.

### MemTX (arXiv 2607.23929, Li et al., Jul 2026)

MemTX argues that "a memory write is not a belief commit." Each record carries evidence, permissions, provenance, and **validity**. Writes are staged in snapshot-isolated transactions. Retracting a belief triggers **typed cascading repair** of its derived records.

The key transferable principle: the compaction summary committed a belief ("defer to fresh session") without validity metadata (valid-under-constraint: context-strain). When compaction retracted the constraint, the derived recommendation should have been cascade-repaired (invalidated). It wasn't — because the recommendation was never tagged with the constraint it depended on.

## The structural fixes (three layers — all shipped)

### Fix 1: PreCompact validity tagging with two-stage hybrid classifier (structural)

`PreCompact_continuation_capture.py` uses a two-stage hybrid architecture:

**Stage 1 — Regex (compiled patterns, <1ms):** four regex patterns require BOTH a deferral verb AND a session-boundary term within proximity (`≤40` chars). Neither alone triggers. Catches explicit phrasings like "defer to a fresh session" and "postpone to next session." 100% precision on test suite (13/13 true negatives rejected, including "follow up", "wrap up", "next session" alone).

**Stage 2 — LLM classifier (gpt-oss-20b via NVIDIA NIM, ~2s):** when regex finds nothing, a prefilter scans for 25 deferral-adjacent vocabulary terms ("sleep on", "park", "shelve", "revisit", "hold off"). If candidates exist, a batched LLM call classifies whether each message is a genuine deferral directive. Catches paraphrases regex structurally cannot match ("this would land better with a cold lens after a restart"). Confidence threshold: 0.6. 8s timeout, fail-open (any error → regex-only result stands).

Live-fire verified: 4/4 paraphrase deferrals detected (confidence 0.90–0.97), 1 non-deferral correctly rejected.

**Telemetry:** all detections (regex and LLM) are logged to `~/.grok/hooks/state/stale-rec-detections.jsonl` with timestamp, session_id, pattern_idx (or `stage: "llm"`), role, and text snippet. LLM detections additionally log `reason` and `confidence`. This lets the operator measure false-positive rate after deployment.

### Fix 2: UserPromptSubmit conditional revalidation (structural)

`UserPromptSubmit_continuation_inject.py` checks whether the continuation prompt contains the `VALIDITY-EXPIRED` marker from Fix 1. If present, the injection appends a revalidation directive requiring the agent to state a **measurable** current-session constraint (context budget, quota %, specific blocker) — not a vague one ("it's complex"). Adds a relevance test: "would the recommendation change if the constraint were false?" If no marker is present, the directive is NOT injected — preventing false-positive fatigue (Chen et al. CHI 2025: preference drops 80 to 47 percent at higher frequency).

This makes Fix 2 **conditional on Fix 1's detection signal** — a sequencing constraint identified by /risk scan.

### Fix 4: AGENTS.md recommendation-constraint coupling rule (prose)

Added to Hard rules: "When repeating any defer/stop/handoff recommendation after a context transition, state the current-session constraint that motivates it. A true fact is not a constraint — it must be the reason the recommendation holds now, not a post-hoc rationalization."

This addresses Layer 2 (true-fact-as-rationalization) that the structural fixes cannot catch mechanically. Prose-layer backstop with ~50% compliance ceiling under session pressure ([[false-choices-parallel-branch-framing]]); the structural fixes (1+2) are the load-bearing enforcement.

### Evolution history (v1 → v2 → v3)

- **v1:** 15-element substring keyword list ("follow up", "wrap up", "next session"). /tp fresh-lens critique identified precision as critical flaw — matched normal conversation, defeating the conditional gate.
- **v2:** replaced with 4 compiled regex patterns requiring deferral verb + session boundary in proximity. 100% precision on test suite. Added telemetry and role filtering.
- **v3:** added LLM classifier stage 2 for paraphrase robustness. Catches the ~30-40% of real deferral language regex misses ("sleep on it", "shelve this"). Two-stage fast-slow classifier architecture.

## How to detect this pattern

**Post-compaction:** check whether the agent repeats a defer/stop/handoff directive from the pre-compaction summary. If the directive cites "it was recommended" or "per the summary" without stating a current-session constraint, the pattern is firing.

**During /tp or /check:** ask "does this recommendation's motivating constraint still hold in the current session?" If the answer requires checking a measurable condition (context budget, quota, file state), check it. If the agent cites a true fact instead, flag Layer 2.

## Falsifier

This pattern is wrong if:
- **Compaction summaries reliably carry constraint metadata.** If each recommendation in the summary is tagged with its motivating constraint and whether compaction invalidated it, the validity-tagging fix is unnecessary. Test: inspect 5 compaction summaries for recommendation language; count how many tag the constraint.
- **Post-compaction sessions reliably revalidate inherited recommendations.** If the model already checks whether the constraint holds before repeating, the pattern doesn't fire. Test: observe 10 post-compaction sessions; count how many revalidate defer/stop directives before acting.
- **The two-stage classifier produces noise.** If the regex + LLM pipeline over-triggers (false positives on normal conversation), the conditional gate is defeated and false-positive fatigue materializes. Test: review `stale-rec-detections.jsonl` after 10 compactions; measure precision by checking whether flagged messages are genuine deferrals. The v2 precision fix (compiled regex patterns requiring verb + session boundary) and the v3 LLM confidence threshold (0.6) are the precision controls.

## Scope limitation

This concept is scoped to **compaction-inherited** recommendation decoupling per /risk scan verdict. The general pattern — recommendation-constraint decoupling under ANY context transition (operator correction, state change, new tool result) — is noted as a follow-on concept for future capture. The fixes shipped (Fix 1-4) target compaction as the highest-priority instance; the AGENTS.md rule (Fix 4) is written generally enough to cover non-compaction transitions at the prose level.

## Operational monitoring

The telemetry system writes all detections to `~/.grok/hooks/state/stale-rec-detections.jsonl`. Each line is a JSON object:

```json
{
  "ts": "2026-08-12T...",
  "session_id": "<session-uuid>",
  "pattern_idx": 0,         // 0-3 for regex patterns; -1 for LLM classifier
  "line": 42,               // transcript line number
  "role": "assistant",      // or "user"
  "snippet": "...",         // text snippet around the match
  "stage": "regex"          // or "llm"
  // LLM-stage detections also carry:
  // "reason": "...",       // LLM's explanation
  // "confidence": 0.92     // LLM's confidence (0.0-1.0)
}
```

### Reviewing detections

```powershell
# Show recent detections
Get-Content ~/.grok/hooks/state/stale-rec-detections.jsonl -Tail 20

# Count detections by stage
Get-Content ~/.grok/hooks/state/stale-rec-detections.jsonl | ForEach-Object { $_ | ConvertFrom-Json | Select-Object stage } | Group-Object stage
```

### Interpreting false-positive rate

- **Regex detections (stage: "regex"):** review the snippet. If it's NOT a genuine defer/stop/handoff recommendation, it's a false positive. The regex patterns require both a deferral verb and a session-boundary term, so false positives should be rare. If they appear, tighten the specific pattern_idx.
- **LLM detections (stage: "llm"):** review the reason and confidence. Detections with confidence <0.7 are more likely false positives. If the LLM consistently over-classifies, raise the confidence threshold in `_stale_rec_llm_classifier.py` (currently 0.6).

### When to adjust

| Signal | Action |
|--------|--------|
| Regex false positives on specific phrase | Add the phrase to the true-negative test cases and tighten the pattern |
| LLM confidence consistently low (0.6-0.7) | Raise threshold from 0.6 to 0.7 |
| No detections over 10+ compactions | Check whether regex patterns still match current session language; may need new patterns |
| LLM classifier never fires (regex catches everything) | This is fine — regex is the fast path; LLM is the edge-case backstop |

### Audit cadence

Monthly, or after 10 compactions (whichever comes first). Review the JSONL file, classify each detection as true/false positive, and adjust thresholds or patterns if false-positive rate exceeds 20%.

## Receipts

- **The operator's report:** session 019ff2aa, user message: "We already compacted — this IS the post-compaction session. I have the full summary plus this turn's analysis. There's no context strain. My 'defer to a fresh session' framing was carried over from the pre-compaction recommendation in the summary, which no longer applies."
- **STALE benchmark:** arXiv 2605.06527 (Chao et al., May 2026) — 55.2% best accuracy on Premise Resistance dimension.
- **MemTX:** arXiv 2607.23929 (Li et al., Jul 2026) — transactional belief-commit with validity metadata and cascading repair.
- **False-positive fatigue:** Chen et al., CHI 2025 "Need Help?" — preference drops 80 to 47 percent at higher notification frequency.
- **/risk scan verdict:** FIX FIRST — sequencing inversion (ship Fix 1 before Fix 2) was the key revision from the inline risk scan.

## Related concepts

- [[compaction-inherited-diagnosis-unverified-propagation]] — companion concept (diagnosis-variant)
- [[fabricated-fatigue-llm-session-end-recommendations]] — the emotional driver; this concept is the structural propagation
- [[go-home-narrative-fabricated-session-state-constraints]] — fabricated constraints as stop justifications
- [[narrative-as-signal]] — true-fact-as-rationalization is a special case of narrative sufficiency
- [[false-choices-parallel-branch-framing]] — the 50% prose-compliance ceiling for response-pattern rules
