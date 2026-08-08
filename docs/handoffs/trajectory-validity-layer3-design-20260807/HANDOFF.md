---
thread_id: trajectory-validity-layer3-design
parent_handoff_path: docs/handoffs/claim-verification-layer3-design-20260807/HANDOFF.md
current_session_id: 019fde3e-9f18-7da2-b836-5f1896e627da
current_terminal_id: console_a8dfe293-484b-49d1-8c12-b6d7
produced_at: 2026-08-07T23:30:00Z
status: open
handoff_type: design
accurate_as_of_head: 23c909c
source_transcript: ~/.grok/sessions/P%3A%5C/019fde3e-9f18-7da2-b836-5f1896e627da/chat_history.jsonl
---

# Handoff: Trajectory-validity Layer 3 — design direction (post-falsification)

## Goal

Design a trajectory-validity gate (GroundEval Silence-track pattern) for the
workspace's documented "claim-without-checking" problem. This replaces the
falsified output-level approaches (keyword detection, decompositional claim
extraction) with a trajectory-level approach: check whether the agent searched
the required evidence space before claiming, not whether the final claim matches
tool events.

## Why this approach (evidence-backed)

The prior session (019fde3e) falsified two output-level approaches and found
the field's taxonomy explains why both failed:

1. **Keyword detection** — 67% FP (assertion-vs-discussion confusion). See
   `[[keyword-detection-recommendations-falsified-67percent-fp]]`.
2. **Decompositional claim extraction** — 0/5 catch on calibration test. See
   `[[layer3-claim-extraction-falsified-trajectory-validity-is-field-standard-2026]]`.

The taxonomy finding (Lin et al. 2025, arxiv 2509.18970): all 5 documented
instances are **Reasoning-stage belief-state hallucinations** — internal
failures that occur before any external behavior executes. Output-level
detection is structurally late; the hallucination has already propagated into
the belief state by the time text is generated.

GroundEval (Flynt 2026, arxiv 2606.22737) provides the trajectory-validity
pattern: *"a correct answer reached through an invalid trajectory still counts
as a failure."* Its Silence track checks *"Did the agent verify every
precondition before deciding?"* — exactly our problem. Key property: scoring
is deterministic from the trajectory alone; the agent's prose is irrelevant.
This sidesteps the assertion-vs-discussion FP that killed keyword detection.

GroundEval's empirical result (§8.1): two frontier LLM judges scored a
state-invalid response 0.90 and 0.85; GroundEval scored it 0.000 because the
agent never fetched the required artifact. LLM-as-judge cannot detect this;
only trajectory checking can.

## What the design must produce

A Stop hook (or PostToolUse chain) that, for specific claim types detected in
the agent's response, checks whether the required evidence space was actually
searched in the turn's tool trace. If not → advisory.

### Candidate claim types + evidence spaces (starting point)

| Claim type | Detection signal | Required evidence space | Trajectory check |
|---|---|---|---|
| Negative existence | "X doesn't exist / we can't do X / there's no way to Y" | Wiki + skills catalog | Was a wiki grep or catalog search in the turn's tool trace? |
| Session-state | "context budget is X / session is at Y% / quota is Z" | `/context` or state probe | Was a state-checking command run this turn? |
| Skill syntax assertion | "X means Y / the syntax for X is Y" | SKILL.md for the named skill | Was the relevant SKILL.md read this turn? |

### Scope (honest)

- **In scope:** Instances 1, 2, 4 (negative existence, session-state, skill
  syntax). These are tractable because each has a deterministic evidence space.
- **Out of scope:** Instance 3 (rate/quota conflation — conceptual error, no
  detection catches "wrong concept"). Instance 5 (external recommendation —
  assertion-vs-discussion is unsolved, falsified at 67% FP).

## What the design must address

1. **Detection signal precision.** The claim-type detection patterns above are
   untested. The retrodiction harness
   (`P:/.agents/scripts/retrodiction_hook_measure.py`) must measure FP rate
   before shipping. Note: even if detection has FP, the *trajectory check* is
   deterministic (the search either happened or didn't), so the failure mode is
   "flagged a non-claim" not "flagged a discussion as assertion." This is a
   different FP profile than keyword detection.

2. **Trajectory access.** The check needs the turn's tool trace. Under Grok
   Build, this is available in the Stop hook's input data (transcript_path →
   chat_history.jsonl). The harness needs to correlate tool calls to the claim
   turn. This is the main implementation work.

3. **Advisory-first enforcement.** Per
   `[[advisory-vs-blocking-enforcement-decision-2026]]`: ship advisory, measure
   FP on ≥50 detections, promote to blocking only if Wilson 95% CI ≤30% FP.

4. **Composition with existing receipt system.** The existing
   `verification_receipt_writer.py` verifies commands were run. This gate
   verifies the *right* commands were run for the *right* claim types.
   Complementary, not conflicting — but the composition must be defined to
   avoid double-signaling.

5. **Measure-first validation.** Before building the gate, run the retrodiction
   harness with the detection patterns over ≥40 sessions to measure: (a) how
   often each claim type appears, (b) what fraction lack the required evidence
   search. This establishes the problem frequency before any build commitment.

## What NOT to do

- **Do not re-attempt output-level claim extraction.** Falsified (0/5 catch).
- **Do not install GroundEval.** No adapter for Grok Build; enterprise-shaped.
  Extract the Silence-track *pattern*, not the framework.
- **Do not ship blocking enforcement without measurement.** Promotion gate
  requires retrodiction first.
- **Do not try to catch Instance 3 or 5.** Out of scope; both are documented as
  unsolved by the field.

## Open questions for the fresh session

1. **Is the detection-signal → evidence-space mapping complete?** Are there
   other claim types with deterministic evidence spaces worth adding?
2. **How does the trajectory check access the tool trace under Grok Build's
   Stop hook?** The active-surface snapshot shows Stop hooks receive response
   text; does the input data include the tool-call trace, or does the hook
   need to read chat_history.jsonl itself?
3. **Does the detection pattern for "negative existence" avoid the
   assertion-vs-discussion trap?** "We can't do X" as agent assertion vs
   "the agent said 'we can't do X'" as discussion — does scoping to
   first-person agent voice (not quoted) avoid the 67% FP problem? Only
   retrodiction answers this.

## Acceptance criteria for the design

1. Addresses ≥3 of 5 documented instances (1, 2, 4 minimum)
2. Uses trajectory-validity checking (GroundEval pattern), not output-level
   claim extraction
3. Detection patterns are retrodiction-validated on ≥40 sessions before
   shipping
4. Ships advisory-first with a measurement plan for promotion to blocking
5. Latency budget defined (the trajectory check is deterministic, ~10ms; the
   detection regex is ~50ms; no LLM in the hot path)
6. Composition with existing receipt system is defined

## Artifacts

- `P:/.data/wiki/concepts/layer3-claim-extraction-falsified-trajectory-validity-is-field-standard-2026.md` (the falsification + taxonomy + new direction)
- `P:/.data/wiki/concepts/keyword-detection-recommendations-falsified-67percent-fp.md` (prior falsification)
- `P:/.data/wiki/concepts/reasoning-first-search-never-claim-without-checking.md` (the 5 instances)
- `P:/.agents/scripts/retrodiction_hook_measure.py` (the measurement harness)
- `P:/tmp/calibration_test.py` (the falsification script for the prior approach)
- GroundEval paper: https://arxiv.org/abs/2606.22737
- GroundEval code: https://github.com/tenurehq/groundeval (README read; Silence track pattern is the design unit to extract)
- Lin et al. taxonomy: https://arxiv.org/abs/2509.18970 (§3.1.4, §3.1.5, §3.2.4)

## Changelog

| Date | Author | Change |
|------|--------|--------|
| 2026-08-07 | grok (019fde3e) | Initial handoff — prior direction falsified, trajectory-validity direction identified from /www research |
| 2026-08-07 | grok (019fde3e) | Design completed + measurement-validated over 50 sessions. See `DESIGN.md` in this directory. Instance 2 confirmed as true SILENT catch. |

## Execution Status

Updated: 2026-08-08T00:30:00Z
Session: 019fde3e
Agent: grok

| # | Deliverable | Status | Evidence |
|---|---|---|---|
| 1 | Discovery: transcript format, tool-trace access, Stop hook infrastructure | ✅ DONE | `P:/tmp/probe_transcript_format.py`, `P:/tmp/probe_transcript_detail.py` — confirmed `tool_calls` field in Grok transcripts |
| 2 | Measure-first: retrodiction over 50 sessions with candidate patterns | ✅ DONE | `P:/tmp/trajectory_measure.py` → 54 detections; `P:/tmp/refined_analysis.py` → refined precision analysis |
| 3 | Alternatives gate (architectural profile) | ✅ DONE | DESIGN.md § "ALTERNATIVES GATE" — 3 options evaluated, Option 1 (regex + deterministic) chosen |
| 4 | Design document | ✅ DONE | `DESIGN.md` in this directory — all 6 acceptance criteria addressed |
| 5 | Instance 2 validation | ✅ DONE | Detection at `019fd698:43` "we cannot verify Cohere's monthly quota" — SILENT, confirmed as the exact documented failure |
| 6 | Implementation (Tasks 1-4) | ❌ NOT STARTED | DESIGN.md § "Implementation plan" — 4 tasks, dependency order: parser → detection → hook → deploy |

### Key findings during execution

- **The Grok transcript records tool calls** in `assistant.tool_calls` (top-level field, not nested in `content` blocks like Claude format). The existing `build_turn_tool_events.py` parser is Claude-format and dormant under Grok — a format adapter is the implementation work.
- **The broad NEGATIVE_EXISTENCE pattern is too noisy** (14% precision): 68% of detections are file/code claims where the evidence space is the file system, not the wiki. The refined capability pattern (`we/I + can't + verify/check/do`) raises precision to 69% and reduces volume by 68%.
- **Instance 2 (Cohere quota) was the only true SILENT catch** in 50 sessions — but it was a high-value catch that cascaded into the entire Layer 3 investigation.
- **SESSION_STATE detection missed Instance 4** because the fabricated claim was phrased as "too deep" not as a percentage. The refined pattern now includes the "too deep/approaching limit" variant.
- **Stop_claim_judge.py already exists** for state/prediction claims (LLM-based). The trajectory gate targets a DIFFERENT claim class (capability claims) using a DIFFERENT method (deterministic trajectory check). Complementary, not overlapping.
