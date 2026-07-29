---
thread_id: a1b2c3d4-e5f6-7890-abcd-ef1234567001
parent_handoff_path: none
current_session_id: 019f9f4f-7f5b-7a71-9eaf-8f43ba9f8fb9
current_terminal_id: noterm
produced_at: 2026-07-29T23:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: c717d2f1c433135887eca243b85206ff4763f1e4
---

# Handoff: Session-health skill design + /behave improvement + verdict-integrity controls

## Objective

Three interrelated work streams from session 2026-07-29: (1) design and implement a `/session-health` skill for session quality monitoring, (2) improve behavioral analysis by building a Grok-native `/behave` equivalent with decision-transition auditing, and (3) add verdict-integrity controls to prevent unsupported claims from changing design verdicts.

## Status

OPEN — design complete for session-health; improvement spec complete for /behave; wiki concept shipped for verdict-integrity. Implementation not started for any of the three.

## Producing context

Date: 2026-07-29. Session: 019f9f4f-7f5b-7a71-9eaf-8f43ba9f8fb9. Host: grok. This session was a continuation from a compacted session covering capability graph architecture, search tool migration, and PostToolUse research.

## Read-first list (ordered)

1. `P:/docs/designs/2026-07-29-session-health-skill-design.md` — the design doc (v0.4, PROCEED after 3 critical friend rounds + 1 external /tp review)
2. `P:/.data/wiki/concepts/decision-transition-auditing-verdict-integrity-controls.md` — wiki concept with 8 control gaps + 11-area improvement spec
3. `C:/Users/brsth/.claude/plugins/cache/local/cc-skills-analysis/1.0.123/skills/behave/SKILL.md` — the external /behave skill being improved
4. `C:/Users/brsth/.grok/skills/tp/reference/session-review-protocol.md` — the extracted reusable protocol (v3.5)
5. `P:/.data/wiki/scripts/capabilities.py` — capability registry runtime API
6. `P:/.data/wiki/scripts/audit_finding_coverage.py` — finding-to-skill coverage audit

## Verified facts

- [FACT] `/tp` is 1320 lines — too heavy for additional session-health features (receipt: `wc -l`)
- [FACT] 10-session baseline shows F/U range 0.04-11.06 and P/U range 0.0-0.60 (receipt: `P:/tmp/session_baseline.py` run this session)
- [FACT] `/aar` Phase 4 already computes `operator_signal_delta` with pushback_count, friction_signal_baseline_delta (receipt: `/aar/SKILL.md:147-185`)
- [FACT] `friction_detector.py` (364 lines) uses DIFFERENT patterns than `/tp` Step 0b — only `SyntaxError` overlaps (receipt: grep of ISSUE_PATTERNS)
- [FACT] The verdict-integrity incident: a `/tp review` subagent fabricated a mechanism ("INDEX keywords in numerator"), the orchestrator accepted it as REVISE without verification, and correction only happened because the operator challenged it (receipt: this session's transcript, lines ~L230-L320)
- [FACT] External LLM review of the /behave packet identified 8 control gaps and 8 self-protection patterns in the orchestrator's response (receipt: pasted in prompt_273.txt)

## Current state

### Session-health skill
- Design doc v0.4 at `P:/docs/designs/2026-07-29-session-health-skill-design.md` (881 lines)
- 3 critical friend rounds → PROCEED. 1 external /tp review → REVISE (overturned: 2 of 3 claims were fabricated/overstated)
- 8 implementation units across 3 rollout phases
- 5 consumers identified: /tp, /close, /debrief, /aar, /notice
- `audit_finding_coverage.py` already built — shows 3/7 finding types fully covered, 4 partial

### /behave improvement specification
- Web research identified 7 improvement areas (McCormick 8-pattern taxonomy, HTC calibration, minimum viable falsification, real-time split, detection indicators, co-occurrence, Grok-native evidence)
- External LLM review identified 4 additional control areas (verdict provenance, parent verification, self-protection check, replay fixtures)
- Merged: 11-area improvement spec in `decision-transition-auditing-verdict-integrity-controls.md`
- No Grok-native skill built

### Verdict-integrity controls
- Wiki concept shipped: `decision-transition-auditing-verdict-integrity-controls.md`
- 8 control gaps identified with required additions
- 8 self-protection patterns cataloged (minimization, premature endorsement, vote-counting, rhetorical citation, deferred trigger, scope collapse, confidence decoration, self-congratulation)
- No enforcement mechanism built
- Replay fixture defined but not implemented

## Task packets

### SH-01: Build session_signals.py (Phase 1, Unit 1)
- **Goal:** deterministic transcript signal extraction script
- **In scope:** `session-health/__lib/transcript.py` + `session-health/scripts/session_signals.py` + registry
- **Out of scope:** SKILL.md, consumer integrations, --full mode
- **Files:** `C:/Users/brsth/.grok/skills/session-health/__lib/transcript.py` (new), `C:/Users/brsth/.grok/skills/session-health/scripts/session_signals.py` (new)
- **Acceptance:** F/U and P/U match hand-counted fixture within ±0.05; 13 friction patterns detected; pushback keywords detected
- **Falsifier:** script produces JSON with wrong counts on a known fixture
- **Verification level:** UNIT_TEST

### SH-02: Build SKILL.md + Quick mode (Phase 1, Unit 4)
- **Goal:** operator-invocable skill with `/session-health` quick check
- **In scope:** SKILL.md, capability registration, frontmatter
- **Out of scope:** --full mode, --trend mode, consumer integrations
- **Acceptance:** `/session-health` produces one-line verdict comparing current session to baseline
- **Falsifier:** skill produces no output or wrong baseline comparison
- **Verification level:** LIVE_BEHAVIOR

### BE-01: Build Grok-native /behave equivalent with decision-transition auditing
- **Goal:** behavioral analysis skill with verdict-integrity controls
- **In scope:** new skill with hypothesis-testing + decision-transition auditing + self-protection detection
- **Out of scope:** real-time monitoring (that's /session-health)
- **Acceptance:** skill detects the 8 self-protection patterns in a replay of this session's /tp response
- **Falsifier:** skill fails to detect minimization pattern in the known incident
- **Verification level:** LIVE_BEHAVIOR

### VI-01: Add verdict-integrity gate to /tp and /design
- **Goal:** parent agent must verify claim-to-evidence correspondence before accepting any verdict-changing finding
- **In scope:** /tp SKILL.md Step 3 verification synthesis, /design SKILL.md reviewer→writer routing
- **Out of scope:** hook-based enforcement (deferred)
- **Acceptance:** replay fixture — a subagent returns REVISE with 3 claims, 2 unsupported; parent must reject the unsupported claims and not change the verdict
- **Falsifier:** parent accepts REVISE based on unsupported claims
- **Verification level:** LIVE_BEHAVIOR

## Open decisions

1. **Should the Grok-native /behave be a new skill or folded into /session-health?**
   - Option A: separate skill (`/behave` or `/diagnose-behavior`)
   - Option B: `--full` mode of /session-health
   - Selection criterion: does the operator want to invoke behavioral diagnosis independently of session health monitoring?
   - Currently leading: Option A (separate skill) — behavioral diagnosis is post-hoc and invoked on demand, while session-health is monitoring

2. **Should verdict-integrity controls be behavioral (SKILL.md rules) or mechanical (hooks)?**
   - Option A: behavioral rule in /tp and /design SKILL.md
   - Option B: Stop hook that checks receipt coverage on REVISE/BLOCK verdicts
   - Selection criterion: behavioral rules fire at the moment of dismissal; hooks fire mechanically
   - Currently leading: Option A for v1, Option B for v2

## Hard constraints

- Grok Build only — no external services, no runtime modifications
- Available hook types: command, http only
- Free models preferred for any LLM calls
- AGENTS.md § "Claims require receipts" is the governing rule for verdict-integrity
- The 8 self-protection patterns must be detectable — they are the fingerprints of institutional self-defense

## Cross-reference couplings

- `decision-transition-auditing-verdict-integrity-controls.md` → references /tp Step 3 and /design Step 5.5. Both skills need modification.
- `session-health-skill-design.md` → references /tp Step 0b, /close friction_detector.py, /aar Phase 4, /debrief Lens 3. All 5 consumers need feature flags.
- `/behave` improvement spec → depends on /session-health for real-time signal extraction
- `audit_finding_coverage.py` → defines the coverage gaps that /session-health addresses

## Other outstanding streams

- **Stop hook commit-triggered reblock** — 18 Stop hook blocks this session from the verification receipt system creating new obligations on every commit. Needs investigation but is a hooks infrastructure issue, not related to this work.
- **Context-firewall Layer 1 extract.py** — generalized extraction utility described in `context-firewall-architecture.md`. Three ad-hoc implementations exist (dgemma_read.py, classify_skills_llm.py, session_baseline.py).

## Explicit non-goals

- Do NOT build real-time monitoring in /behave — that's /session-health's job
- Do NOT build hooks for verdict-integrity in v1 — behavioral rule first
- Do NOT merge /behave into /tp — /tp is already 1320 lines
- Do NOT implement all 8 McCormick patterns in v1 — start with the 3 that this session exhibited (BP-001 inference, BP-007 selective reporting, BP-008 authority assumption)

## Resumption protocol

1. Read `P:/docs/designs/2026-07-29-session-health-skill-design.md` (the implementation plan)
2. Start with SH-01: build `session_signals.py` — the design spec is in the doc's Implementation Plan section
3. Verify against the 4 Phase 1 acceptance gates (signal accuracy, calibration stability, compaction census, shadow-mode regression)

## Suggested next invocation

```
/go execute P:/docs/designs/2026-07-29-session-health-skill-design.md
```

Start with Unit 1 (session_signals.py). Use the Phase 1 acceptance gates as verification milestones. The design has been through 4 review rounds + 3 critical friend rounds + 1 external /tp review (overturned). The architecturally significant corrections during review were: friction count 11→13, /aar Phase 4 promoted from no-op to 5th consumer, calibration gate changed from Pearson to saturation check, DRY claim corrected.

## Last user message (verbatim)

> /handoff

## Epistemic labels

- [FACT] Design is v0.4, PROCEED from 3 critical friend rounds
- [FACT] External /tp review REVISE was overturned — 2 of 3 claims fabricated/overstated
- [INFERENCE] The 11-area /behave improvement spec is sufficient to build a Grok-native version — could be wrong if the external review missed a category
- [UNKNOWN] Whether the operator wants /behave as separate skill or /session-health --full mode
