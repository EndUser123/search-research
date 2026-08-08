---
thread_id: claim-verification-layer3-design
parent_handoff_path: docs/handoffs/recommendation-validation-design-20260807/HANDOFF.md
current_session_id: 019fdc43-c6c8-7f21-9944-e4317943bc08
current_terminal_id: console_a8dfe293-484b-49d1-8c12-b6d7
produced_at: 2026-08-07T22:00:00Z
status: closed-direction-falsified-new-direction-open
handoff_type: investigation
accurate_as_of_head: 4e659ae
source_transcript: ~/.grok/sessions/P%3A%5C/019fdc43-c6c8-7f21-9944-e4317943bc08/chat_history.jsonl
---

# Handoff: Claim verification Layer 3 — design direction

> **STATUS UPDATE (2026-08-07, session 019fde3e):** The design direction
> below ("Claimify-style extraction + deterministic entity matching") is
> **FALSIFIED** for this problem class. Calibration test showed 0/5 catch
> rate on the documented instances. The /www research found the field's
> taxonomy (Lin et al. 2025) classifies all 5 instances as Reasoning-stage
> belief-state hallucinations, which output-level detection cannot catch.
> The new direction is **GroundEval-style trajectory-validity checking**.
> See `P:/.data/wiki/concepts/layer3-claim-extraction-falsified-trajectory-validity-is-field-standard-2026.md`
> for the full falsification + new direction. The handoff body below is
> preserved as the historical record of the falsified direction.

## Goal

Design the workspace's missing Layer 3 (faithfulness checking) for preventing
LLM agents from stating claims as fact without checking available evidence.
This is the broader problem class that the recommendation-validation system
(attempted and falsified this session) was one corner of.

## Context (read these first)

1. `P:/.data/wiki/concepts/claim-without-checking-industry-approaches-2026.md`
   — the /www survey of 5 industry approaches. Identifies Layer 3 as the gap.
2. `P:/.data/wiki/concepts/keyword-detection-recommendations-falsified-67percent-fp.md`
   — why the previous attempt (keyword detection) failed. 67% FP, structural.
3. `P:/docs/handoffs/recommendation-validation-design-20260807/grok-design-doc.md`
   — the original design doc (architecture archive). DEC-02 now marked FALSIFIED.
4. `P:/.data/wiki/concepts/reasoning-first-search-never-claim-without-checking.md`
   — the 5 instances that motivated everything. Only 1/5 was an external
   recommendation; 4/5 are internal-knowledge assertions.

## What was learned this session

### The problem is broader than "unvalidated recommendations"

The 3-lens /tp critique (MiniMax + DeepSeek + GLM-5.2) found that the
recommendation-validation design solved 1 of 5 motivating incidents. The
other 4 (fabricated skill syntax, wrong capability claims, rate/quota
conflation, fabricated budget excuse) are internal-knowledge assertions —
"claiming without checking the wiki/spec/code." Any Layer 3 design must
address the whole class, not just the recommendation corner.

### Keyword detection is falsified for this problem class

67% FP on real session data. Root cause: regex cannot distinguish assertion
("I recommend Aider") from discussion ("the agent said 'recommend Aider'").
This is structural — 14 meta-discussion suppression phrases dropped fire count
59% but FP rate barely moved (68%→67%). See wiki concept for full evidence.

### Claim extraction is more tractable than recommendation detection

Follow-up /www found Microsoft Research's Claimify (ACL 2025): 99% claim
entailment via 4-stage pipeline. The structural difference: claim extraction
is **decompositional** (objective ground truth: "is this proposition entailed
by the source?"), while recommendation detection is **classificatory** (no
objective ground truth: "is this a recommendation or a discussion?").

### The production standard avoids LLM-as-judge for the scoring step

Breeden (2026) uses deterministic entity extraction (350 lines, zero LLM
calls): extract structured entities (case numbers, APIs, file paths,
percentages) → check each against evidence deterministically → per-kind
breakdown for actionable diagnostics. This is the Isonomai touchstone pattern:
the model plans, deterministic code verifies.

### The workspace's existing layers

| Layer | What exists | Gap |
|---|---|---|
| 1. RAG | Wiki grep (keyword, not semantic) | Misses paraphrases |
| 2. Constrained generation | AGENTS.md rules (receipt rule, epistemic labels) | ~50% compliance under pressure |
| 3. Faithfulness checking | **ABSENT** | This is the design target |
| 4. External verification | /www (manual) | Not automatic |
| 5. Confidence scoring | [FACT]/[INFERENCE]/[UNKNOWN] labels | Same compliance ceiling as Layer 2 |

## The design direction (evidence-backed)

### Candidate architecture: Claimify-style extraction + deterministic entity matching

**Extraction (Layer 3a):** decompose agent output into atomic claims using a
multi-stage pipeline (selection → disambiguation → decomposition). Claimify
proves 99% entailment is achievable. This is LLM-based but runs only on turns
that pass a pre-filter (not every turn).

**Verification (Layer 3b):** for each extracted claim, check against evidence
deterministically:
- Structured entities (file paths, API names, version numbers, percentages):
  exact-match against wiki/code/docs — zero LLM calls
- Semantic claims (architectural assertions, capability claims): wiki grep
  or LLM-as-judge on the extracted claim only (not the full turn)

**This is NOT what was falsified.** The keyword classifier was classificatory
(detect recommendations in full text). This is decompositional (extract
atomic claims) + deterministic (verify entities against evidence). Different
precision profile.

### What the design must address

1. **Latency budget.** Breeden's system runs inline on every response (350
   lines, deterministic). Claimify uses LLM calls (slower). The design needs
   a pre-filter so LLM-based extraction only runs on turns likely to contain
   checkable claims.

2. **What counts as "evidence" for internal-knowledge claims.** For external
   claims, evidence = web/docs. For internal claims (Instances 1-4), evidence
   = wiki concepts, skill SKILL.md files, code. The design must define the
   evidence sources per claim type.

3. **Advisory vs blocking.** Per advisory-vs-blocking-enforcement-decision-2026:
   ship advisory first, measure FP rate on ≥50 detections, promote to blocking
   only if Wilson 95% CI ≤30% FP. Do NOT ship blocking.

4. **The retrodiction harness.** `P:/.agents/scripts/retrodiction_hook_measure.py`
   is the template for measuring FP rate before shipping. Use it.

5. **Scope: all claims or just architectural recommendations?** The 3-lens
   critique said address the whole class. But starting narrower (external
   claims only) may be the right first step — expand after measurement.

## What NOT to do

- **Do not re-attempt keyword-only detection.** Falsified at 67% FP. The wiki
  concept documents why.
- **Do not ship blocking enforcement.** The workspace's promotion gate
  requires measurement first.
- **Do not build without reading the existing wiki concepts.** The falsification,
  the industry survey, and the enforcement-strategy decision all contain
  load-bearing constraints.

## Acceptance criteria for the design

1. Addresses the whole problem class (all 5 instances), not just external
   recommendations
2. Uses decompositional extraction (Claimify-style), not classificatory
   detection (keyword-style)
3. Uses deterministic verification for structured claims (entity matching)
4. Ships advisory-first with a measurement plan for promotion to blocking
5. Retrodiction-validated on ≥40 historical sessions before shipping
6. Latency budget defined and tested

## Open questions for the fresh session

1. Is Claimify available as open source, or does the design need to implement
   the 4-stage pipeline from scratch? (The paper is research-only per MSR.)
2. What pre-filter determines which turns get claim extraction? (Breeden runs
   on every response; we may want narrower.)
3. How does this compose with the existing verification-receipt system (which
   verifies commands were run, not claims are true)?
4. Should the existing PGM (proposal-grounding-monitor) be extended rather
   than building new?

## Artifacts

- `P:/.data/wiki/concepts/claim-without-checking-industry-approaches-2026.md`
- `P:/.data/wiki/concepts/keyword-detection-recommendations-falsified-67percent-fp.md`
- `P:/docs/handoffs/recommendation-validation-design-20260807/grok-design-doc.md`
- `P:/.agents/scripts/retrodiction_hook_measure.py`
- `P:/tmp/retrodiction_v2.txt` (the 67% FP measurement data)

## Changelog

| Date | Author | Change |
|------|--------|--------|
| 2026-08-07 | grok (019fdc43) | Initial handoff — direction identified, design pending fresh session |
