# Handoff: PGM Payload Fix + Scope Extension

**Status:** Unit 1 SHIPPED (payload fix live). Units 2-5 ready for implementation.
**Date:** 2026-07-29
**Source:** `/design` run d8173a98

## What shipped this session

**Unit 1: PGM payload bug fix** — `stop_detect.py:extract_response_text()` was reading `("response", "last_assistant_message")` instead of `lastAssistantMessage` (camelCase). PGM has been silently dead since it shipped — every real session hit the empty-text guard and produced zero detections. Fixed by reordering to the canonical 4-tier pattern (`lastAssistantMessage` → `response` → `messages[-1].content` → `message.content`). Same fix applied to `behavioral_check.py` and `wiki_persistence_check.py` earlier in this session. All 117 existing tests pass + updated test fixture.

**Files changed:**
- `~/.grok/plugins/proposal-grounding-monitor/scripts/stop_detect.py` — `extract_response_text()` rewritten
- `~/.grok/plugins/proposal-grounding-monitor/tests/test_stop.py` — test fixture updated for camelCase

## What remains (Units 2-5)

### Unit 2: Add `operator_directive` qualifying category
**File:** `~/.grok/plugins/proposal-grounding-monitor/scripts/relevance.py`
- Add `"operator_directive"` to `QUALIFYING_CATEGORIES` frozenset (line 40)
- Add regex to `categorize()` (before the existing `docs` rule) matching `AGENTS.md` and `CLAUDE.md` paths → returns `"operator_directive"`
- Add `"operator_directive"` to `state.py:282` qualifying-evidence gate (or replace inline set with `relevance.QUALIFYING_CATEGORIES`)
- **NOTE:** This LOWERS the repair trigger rate (more reads count as qualifying). Must measure baseline AFTER Unit 1 fix but BEFORE Unit 2. Phase 1b only.
- **NOTE:** `prior_decision` category was dropped from the design — zero `prior-decision-*.md` files exist in the wiki. Do not add it.

### Unit 3: FP measurement telemetry
**File:** `~/.grok/plugins/proposal-grounding-monitor/scripts/fp_measurement.py` (new)
- `log_stop_decision(response, gate_decision, qualifying_searches, session_id, env)` writes one JSONL record per `detect()` call
- Schema: `{record_id, ts, session_id, gate_decision, response_excerpt_200, qualifying_searches, proposal_signal_type, repair_opened, outcome}`
- Wire-in: call from `stop_detect.py:detect()` in ALL 5 branches: FAIL_OPEN (before env_ok guard), RESOLVED, NO_SIGNAL, SIGNAL_BUT_QUALIFYING_SEARCH, ADVISORY_EMITTED
- Log directory: `Path(data_dir).parent / "proposal-grounding-monitor" / "telemetry" / f"fp-log-{session_id}.jsonl"` (same directory as existing `stop.jsonl`)
- TTL: 30 days. Add `sweep_fp_logs(env, max_age_seconds)` to `state.py`, call from `cleanup.py:main()` at SessionStart
- **This is coverage telemetry, NOT FP-rate evaluation.** Wilson CI requires labels (see OQ-9).

### Unit 4: One new proposal pattern behind feature flag
**File:** `~/.grok/plugins/proposal-grounding-monitor/scripts/relevance.py`
- Add ONE new tuple to `PROPOSAL_SIGNALS`, gated by `os.environ.get("PGM_SCOPE") == "extended"` (default: legacy/off)
- **Do NOT add patterns matching "best approach", "right architecture", or "correct approach"** — these were dropped in PGM's GR-2 fix after ~12/13 FPs
- Day 58 deletion deadline: if flag not flipped by Day 58, delete the pattern

### Unit 5: Version bump + README update
- Bump `plugin.json` version 0.1.1 → 0.2.0
- Update README § "Version": remove "orphaned" claim; add v0.2.0 release notes
- Update README to document `PGM_SCOPE` env var

## Phased rollout (from design)

| Phase | Units | When | Gate |
|-------|-------|------|------|
| **1a** (done) | 1 | Day 0 | — |
| **1a baseline** | — | Day 1-14 | Observe post-fix telemetry |
| **1b** | 2, 3, 5 | Day 14+ | Day-14 baseline check |
| **2** | 4 | Day 28+ | Labeling protocol exists (OQ-9) |
| **3** | 6 (flag flip) | Day 58+ | All Phase-4 activation criteria met |
| **4** | — | Future | Separate ADR for blocking mode |

## Open questions for operator

- **OQ-9:** Labeling protocol for FP measurement. Options: (a) operator weekly review of fp-log samples, (b) use repair outcomes as proxy labels (REVISED=false positive, CONFIRMED=true positive). Blocks Phase 4 activation.
- **OQ-10:** Substantive vs ceremonial reads — counting bare AGENTS.md reads as grounding may train ceremonial compliance. Affects Unit 2 design.

## Design doc location

Full design doc: `C:\Users\brsth\AppData\Local\Temp\grok-design-d8173a98\grok-design-doc-d8173a98.md` (880 lines, 3 revision rounds). Will be reaped by OS — key decisions are in this handoff.
