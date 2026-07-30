# Handoff: PGM Payload Fix + Scope Extension

**Status:** Unit 1 SHIPPED + reviewed + all findings fixed. Units 2-5 ready for implementation.
**Date:** 2026-07-29 (revision 3: post-review fixes applied)
**Source:** `/design` run d8173a98, `/check` PASS, `/review` 7 findings all fixed

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
| **1b** | 2, 3, 5 | Day 14+ | See resolved questions below |
| **2** | 4 | Day 28+ | Proxy-labeled FP data |
| **3** | 6 (flag flip) | Day 58+ | Phase-4 activation criteria |
| **4** | — | Future | Separate ADR for blocking mode |

**(Updated rollout after OQ-9/OQ-10 resolution — see below)**

## Resolved questions (operator decisions 2026-07-29)

**OQ-9: RESOLVED — repair-outcome proxy labels (option b).** No manual labeling. Proxy label mapping:
- `RECOMMENDATION_REVISED_AFTER_INSPECTION` → true positive (proposal was ungrounded, model fixed it)
- `RECOMMENDATION_CONFIRMED_AFTER_INSPECTION` → true positive (grounding was missing, model verified)
- `RECOMMENDATION_WITHDRAWN_AFTER_INSPECTION` → true positive (proposal was wrong, model withdrew)
- `EXPIRED_UNRESOLVED` → false positive (model ignored advisory, wasn't actionable)
- Detections without a repair lifecycle (NO_SIGNAL, SIGNAL_BUT_QUALIFYING_SEARCH) → unlabeled, excluded from FP-rate computation

**Implication for Unit 3:** fp_measurement.py must capture the `outcome` field when `gate_decision == "RESOLVED"`. Wilson CI is computed only on the labeled subset (resolved repairs). Phase 4 activation uses proxy-labeled FP rate, not human-labeled.

**Implication for Phase 4:** the ≥50 detections criterion now means ≥50 *resolved* detections (not raw detections). Expired-unresolved count as FPs in the denominator.

---

**OQ-10: RESOLVED — AGENTS.md reads do NOT count as qualifying evidence.** Reading the rules document is not searching the solution space.

**Implication for Unit 2 (significant simplification):**
- `operator_directive` becomes a **tracking-only category** — it appears in telemetry and categorization, but is NOT in `QUALIFYING_CATEGORIES`
- `categorize()` returns `"operator_directive"` for AGENTS.md/CLAUDE.md paths, but `add_evidence()` does NOT promote the repair to `DISCOVERY_PERFORMED` based on this category
- Reading AGENTS.md alone does NOT satisfy grounding — agent must still read skills/packages/hooks/docs/upstream
- **R-5 risk eliminated:** since `operator_directive` isn't qualifying, adding it does NOT change the repair trigger rate. The R-5 concern about "categorization changes alter trigger distribution" no longer applies
- Unit 2 is now lower-risk: it adds observability without changing enforcement semantics. Can ship in Phase 1a alongside Units 1+3 if desired (no baseline-measurement dependency)
- **Updated `QUALIFYING_CATEGORIES`:** remains the existing 5 (`skill`, `package`, `hook`, `docs`, `upstream`). Does NOT grow. The `docs` category already covers AGENTS.md via path regex — that regex should be narrowed to exclude AGENTS.md/CLAUDE.md (so those paths categorize as `operator_directive`, not `docs`)

**Implementation note:** the existing `docs` regex at `relevance.py:152` (`r"(?:^|/)(?:AGENTS|CLAUDE)\.md$"`) currently classifies AGENTS.md as `docs` (qualifying). Unit 2 must move this match to the new `operator_directive` rule BEFORE the `docs` rule, so AGENTS.md reads categorize as `operator_directive` (non-qualifying) instead of `docs` (qualifying). This is the one behavioral change: AGENTS.md reads stop counting as grounding.

## Updated phased rollout

| Phase | Units | When | Gate |
|-------|-------|------|------|
| **1a** (done) | 1 | Day 0 | — |
| **1a baseline** | — | Day 1-14 | Observe post-fix telemetry |
| **1b** | 2, 3, 5 | Day 14+ (or sooner — R-5 risk eliminated) | Day-14 baseline (for Unit 3 telemetry comparison) |
| **2** | 4 | Day 28+ | Proxy-labeled FP rate from repair outcomes |
| **3** | 6 (flag flip) | Day 58+ | ≥50 resolved detections, Wilson CI ≤30% FP, ≥1 REVISED outcome |
| **4** | — | Future | Separate ADR for blocking mode |

## Revision 3: Post-review fixes (2026-07-29)

A `/review` with 2 specialists found 7 verified findings. All fixed:

| Finding | Fix | Commit |
|---------|-----|--------|
| BEH-001: FABRICATED_FATIGUE misses "Should we call it a day?" | Added `call it (a day\|here)` to should-alternative | `0ab0e09` |
| BEH-002: UNNECESSARY_DEFERRAL misses "pick this up later" | Added pronoun-between-verb-and-particle alternative | `0ab0e09` |
| BEH-005: FABRICATED_FATIGUE misses "We could stop" | Added `could` to we-alternative | `0ab0e09` |
| PGM-002: conftest uses wrong field | Updated `make_stop_payload` to use `lastAssistantMessage` | `0ab0e09` |
| PGM-001: SDK snake_case not handled | Added `last_assistant_message` as tier-1.5 fallback | `6cfc5fb` |
| PGM-003: Tier-1 dict only reads .text | Extracted `_extract_text_from_dict()` handling content blocks | `6cfc5fb` |
| BEH-003: NARRATIVE_CLOSURE deletion gap | Documented as structural regex limitation (wiki concept) | `a0ec600` |

PGM `extract_response_text()` now has 5-tier extraction: `lastAssistantMessage` (str/dict) → `last_assistant_message` (str/dict, SDK) → `response` → `messages[-1].content` → `message.content`. 117 tests pass, conftest exercises tier 1.

## Design doc location

Full design doc: `C:\Users\brsth\AppData\Local\Temp\grok-design-d8173a98\grok-design-doc-d8173a98.md` (880 lines, 3 revision rounds). Will be reaped by OS — key decisions are in this handoff.
