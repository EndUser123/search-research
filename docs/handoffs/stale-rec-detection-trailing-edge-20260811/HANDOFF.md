# Handoff: Stale-Recommendation Detection — Trailing-Edge Items

## Status: CLOSED
## Last updated: 2026-08-12T06:15:00Z
## Session: 019ff2aa-2db1-7030-a845-aac243d05ffe
## Author: grok

## Objective

The stale-recommendation detection system (Fix 1-4 for compaction-inherited
recommendation decoupling) shipped through v3 (regex + LLM classifier). A /tp
"did we forget anything?" pass identified three trailing-edge items that were
proposed, analyzed, but never implemented or captured. This handoff ensures
they survive the session boundary.

## Context

The system has three layers:
- **Fix 1** (PreCompact validity tagging): two-stage hybrid classifier (regex + LLM)
- **Fix 2** (UserPromptSubmit conditional injection): fires only when Fix 1 detects stale recs
- **Fix 4** (AGENTS.md prose rule): recommendation-constraint coupling

Wiki concept: `[[compaction-inherited-recommendation-decoupling]]`
Commits: `11155be`, `e9a3c0e`, `0fb7080`, `ab9fc24`

## Open items

### CLOSED 2026-08-12: All three items implemented, tested, and pushed.

- **Item 1 (Fix 3 / T14):** DONE — commit `281fbaa` (~/.grok). /notice v2.6 with T14 trigger.
- **Item 2 (Test integration):** DONE — commit `281fbaa` (~/.grok). 2 integration tests in test_continuation_pipeline.py, both pass.
- **Item 3 (Operational monitoring):** DONE — commit `fc45c07` (P:). JSONL schema, review commands, threshold adjustment, audit cadence added to wiki concept.

### Item 1: Fix 3 — /notice T7 trigger (proposed, silently dropped)

**What:** Extend /notice from T6 (unverified-diagnosis detection) to T7
(stale-recommendation detection). When a defer/stop/handoff recommendation
appears in a post-compaction turn AND cites pre-compaction context as its
motivation, surface: "recommendation 'X' carried from pre-compaction —
current-session constraint not stated. Revalidate or drop."

**Why it matters:** Fix 1+2 fire on the FIRST post-compaction turn (one-shot
injection). If the agent repeats a stale recommendation on turn 3 or later,
the injection has already fired and deleted. T7 is the mid-conversation catch
that /notice provides.

**Detection signal:** defer/stop/handoff language + "from the summary" / "as
noted" / "per the recommendation" + no current-session tool call establishing
the constraint.

**Original analysis:** /www research output, "Fix 3" section. Confidence:
MEDIUM. /notice fires mid-conversation and is advisory; it catches but doesn't
prevent.

**Acceptance criteria:**
- /notice SKILL.md documents T7 trigger
- T7 fires on stale-recommendation repetition in post-compaction turns 2+
- T7 does NOT fire when the agent states a measurable current-session constraint

### Item 2: Test relocation and architecture

**What:** Tests currently live in `P:/tmp/test_fixes.py` and `P:/tmp/test_llm_live.py`
(ephemeral). They need:
1. A new `test_stale_rec_detection.py` in `~/.grok/hooks/tests/` — unit tests
   for regex patterns, LLM classifier prefilter, classify_messages, fail-open
   behavior
2. Extension of existing `test_continuation_pipeline.py` — integration test for
   the VALIDITY-EXPIRED marker flow (PreCompact writes marker → PostCompact
   arms → UserPromptSubmit reads and injects → file deleted)

**Stop hook correction:** "extend the existing" is transition-effort-biased.
The optimal architecture is BOTH: a new unit test file for detection components
AND integration test extension for the marker flow. These test different failure
modes and should not be conflated.

**Acceptance criteria:**
- `~/.grok/hooks/tests/test_stale_rec_detection.py` exists with 14+ test cases
- `test_continuation_pipeline.py` has a test for VALIDITY-EXPIRED marker flow
- `pytest ~/.grok/hooks/tests/` passes with zero failures

### Item 3: Operational monitoring guidance for telemetry

**What:** The telemetry writes to `~/.grok/hooks/state/stale-rec-detections.jsonl`
but there's no guidance for the operator on:
- How to review it (what's the false-positive signal?)
- When to tighten/loosen the LLM confidence threshold (currently 0.6)
- When to add new regex patterns vs. rely on LLM
- How often to audit

**Acceptance criteria:**
- Add an "Operational monitoring" section to the wiki concept
- Document the JSONL schema and interpretation
- Provide a one-liner PowerShell command to check recent detections
- Define the audit cadence (recommend: monthly, or after 10 compactions)

## Prerequisite: PostImplementation gate

The /why root-cause analysis identified that the forgotten-items pattern has a
structural origin: workspace gates are scoped to session lifecycle (/close) and
code lifecycle (/check) but not implementation-wave lifecycle. The
PostImplementation gate fills that gap. Once built, these three items would
have been caught at the wave boundary rather than at a /tp pass after the fact.

The gate design (two-stage: mechanical checks + LLM judgment) is documented in
the session transcript. Measurement of forgotten-items frequency is in progress
(historical session scan: 12/4662 sessions = 0.3% explicit mentions, but
clustering observed — one session had 12 matches).

## Related artifacts

- Wiki concept: `P:/.data/wiki/concepts/compaction-inherited-recommendation-decoupling.md`
- PreCompact hook: `~/.grok/hooks/scripts/PreCompact_continuation_capture.py`
- UserPromptSubmit hook: `~/.grok/hooks/scripts/UserPromptSubmit_continuation_inject.py`
- LLM classifier: `~/.grok/hooks/scripts/_stale_rec_llm_classifier.py`
- AGENTS.md rule: `~/.grok/AGENTS.md` § "Recommendation-constraint coupling across context transitions"
- Tests (ephemeral): `P:/tmp/test_fixes.py`, `P:/tmp/test_llm_live.py`
