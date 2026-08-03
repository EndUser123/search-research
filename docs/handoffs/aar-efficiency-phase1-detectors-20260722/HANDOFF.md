---
thread_id: aar-efficiency-phase1-detectors
parent_handoff_path: P:/docs/handoffs/aar-narrativization-hook-20260722/HANDOFF.md
current_session_id: 019f8507-6395-7bc0-87a9-9122e28d68c8
current_terminal_id: console_896ff2fb-4053-4c04-9d6a-74e4
produced_at: 2026-07-23T02:00:00Z
status: CLOSED
handoff_type: implementation
accurate_as_of_head: b3fb5225caa69e4759ca6697df715b6b6214259d
---

# HANDOFF — Phase 1: AAR efficiency detectors + foundation fixes

## 1. Objective

Build the detector foundation: 5 efficiency-waste detectors, the aggregator, exception safety, and secret-exposure triage. Red-team findings C2, H1, H2, M1 are resolved here. Phase 2 (hooks + report format) depends on this being done and tested.

## 2. Status

**IMPLEMENTED (2026-07-23)** — TASK-00, TASK-01, TASK-02 complete. TASK-03 deferred (optional). Phase 2 is unblocked.

## 3. Producing context

- **Parent handoff:** `P:/docs/handoffs/aar-narrativization-hook-20260722/HANDOFF.md` (original design + research)
- **Phase 2 handoff:** `P:/docs/handoffs/aar-efficiency-phase2-hooks-20260722/HANDOFF.md` (hooks + report — blocked on this)
- **Red-team run:** session 019f8507, subagent 019f8bfd-6f9c-7ff0-a087-f13d20809501

## 4. Read-first list

1. Parent handoff (above) — design rationale, /www research sources, AgentDiet taxonomy
2. `~/.grok/skills/aar/__lib/detectors.py` — existing detector pattern + `ALL_DETECTORS` tuple
3. `~/.grok/skills/aar/__lib/aggregators.py` — existing aggregators (note: `all_aggregates()` is currently dead code — see TASK-02b)
4. `~/.grok/skills/aar/__lib/full_preprocessor.py` — where detectors are called (line ~261)
5. Wiki: `llm-agent-token-waste-categories.md` — AgentDiet 3-category taxonomy
6. Wiki: `dead-code-detection-workflow.md` — vulture for finding dead code

## 5. Verified facts

- [FACT] `run_all_detectors()` at `detectors.py:1898-1901` has NO try/except wrapper. Verified by red-team reading the actual source code. One detector crash kills the entire AAR pipeline.
- [FACT] `all_aggregates()` at `aggregators.py:282-303` is defined and tested but never called by `full_preprocessor.py`. Dead code. Verified by red-team.
- [FACT] The `Signal` dataclass has no field for cost proxies (only `kind`, `event_indices`, `detail`, `severity`, `detector`, `falsifier`, `group_key`). The `amplified_cost_proxy` formula from the parent handoff cannot be stored without a schema change.
- [FACT] Stop hooks DO fire under Grok Build via plugin `hooks/hooks.json` dispatch. Red-team C1 was a false positive — refuted by `~/.grok/active-surface.last.md` which lists PGM's Stop hook as firing.

## 6. Current state

**Implemented (2026-07-23):**
- TASK-00: `run_all_detectors()` now wraps each detector in try/except (line ~1903). One failing detector logs warning and pipeline continues.
- TASK-01: 5 efficiency detectors added (`detect_context_rederivation`, `detect_redundant_verification`, `detect_retry_storm`, `detect_oversized_read`, `detect_expired_context`) with all red-team H2 threshold corrections applied. 22 tests in `test_efficiency_detectors.py`, all passing. 32 total detectors (was 27).
- TASK-02: `all_aggregates()` (was dead code) now wired into `full_preprocessor.py` line ~270. New `aggregate_efficiency_waste()` in `aggregators.py`. `aggregates.json` artifact written alongside `signals.json`.

**Not implemented:**
- TASK-03 (secret exposure severity triage) — optional, independent, deferred.

**Test results:** 562 passed (up from 540), 1 pre-existing failure (SKILL.md line count, unrelated).

## 7. Task packets

### TASK-00 (PREREQUISITE): Fix `run_all_detectors` exception safety

- goal: Add try/except wrapper to `run_all_detectors()` so one detector crash doesn't kill the pipeline. This MUST be done before adding any new detectors.
- in scope: `~/.grok/skills/aar/__lib/detectors.py:run_all_detectors()` (lines 1896-1901)
- out of scope: anything else
- files / anchors: `detectors.py:1898` — the `for det in ALL_DETECTORS:` loop
- acceptance: wrap each `det(materialised)` call in try/except; on exception, log to evidence sink and continue. Existing test suite passes.
- falsifier: a detector that raises causes the entire preprocessor to crash
- verification level required: UNIT_TEST

```python
for det in ALL_DETECTORS:
    try:
        out.extend(det(materialised))
    except Exception as e:
        # Log but don't crash
        import sys
        print(f"WARNING: detector {det.__name__} failed: {e}", file=sys.stderr)
```

### TASK-01: Add 5 efficiency detectors (corrected per red-team)

- goal: Add `detect_context_rederivation`, `detect_redundant_verification`, `detect_retry_storm`, `detect_oversized_read`, `detect_expired_context` to `detectors.py`. Register in `ALL_DETECTORS`.
- in scope: `~/.grok/skills/aar/__lib/detectors.py`
- out of scope: aggregator (TASK-02), report format (Phase 2), hooks (Phase 2)
- files / anchors: `detectors.py`, `ALL_DETECTORS` tuple at end of file

**Red-team corrections applied:**

| Detector | Original threshold | Corrected (per red-team H2) |
|---|---|---|
| `detect_context_rederivation` | Same file read >=3x | >=3x BUT exclude state-file paths (`~/.grok/sessions/`, `P:/.artifacts/`, `_run.json`, `active-surface.last.md`) |
| `detect_redundant_verification` | Same validator >=3x without edits | >=3x BUT exclude `pytest --reruns` output (legitimate flaky-test retry) |
| `detect_retry_storm` | >=4 calls, hash similarity >0.7, severity HIGH | >=4 calls BUT normalize `offset`/`limit`/`path`-difference fields before hashing. **Downgrade severity from HIGH to MEDIUM** until empirical FP rate measured. |
| `detect_oversized_read` | >10KB result, no limit param | >10KB BUT exclude schema dumps (`.data/wiki/concepts/*.md`), AAR reports, and config files the operator needs to read whole |
| `detect_expired_context` | File read in first 1/3, never re-referenced | Same BUT exclude foundational reads (AGENTS.md, CLAUDE.md, handoff files — these inform all subsequent work without being "referenced" in tool calls) |

**Cost proxy dropped (red-team M1):** Do NOT compute `amplified_cost_proxy`. The `Signal` dataclass has no field for it, and the formula's inputs (`file_size`, `remaining_turns`) are not available at detection time. Instead, use `Signal.group_key` for grouping (e.g., `group_key = f"read_file:{path}"`) and let the LLM report step produce the heatmap from grouped signals.

- acceptance: each detector produces signals on this session's transcript; 5 positive tests + 5 negative tests (falsifier non-empty per detector design contract)
- falsifier: detectors fire on legitimate patterns excluded above
- verification level required: UNIT_TEST

### TASK-02: Wire aggregator into preprocessor + add efficiency aggregator

- goal: (a) Wire the existing `all_aggregates()` into `full_preprocessor.py` (it's currently dead code — red-team H1). (b) Add the efficiency aggregator that groups signals by tool name.
- in scope: `~/.grok/skills/aar/__lib/full_preprocessor.py` (add aggregator call after `run_all_detectors`); `~/.grok/skills/aar/__lib/aggregators.py` (add efficiency aggregator function)
- out of scope: report rendering (Phase 2)
- files / anchors: `full_preprocessor.py:~261` (after `run_all_detectors` call); `aggregators.py:ALL_AGGREGATES`

**Input contract for efficiency aggregator:**
- Input: full signal list + event list
- Filter: process ONLY signals whose `kind` starts with an efficiency-detector name (not USER_CORRECTION, SECRET_EXPOSURE, etc.)
- Output: `{tool_name: {total_calls, succeeded, failed, redundant_count}}` — stored as `group_key` values on aggregate signals

- acceptance: aggregator produces structured output from detector signals; dead `all_aggregates()` is now called
- falsifier: aggregator miscounts (e.g., counts a successful retry as redundant) or processes non-efficiency signals
- verification level required: UNIT_TEST

### TASK-03: Secret exposure severity triage

- goal: Add a post-detection step that checks whether a `secret_exposure_in_tool_output` signal represents remote or local-only exposure.
- in scope: `~/.grok/skills/aar/SKILL.md` rule 3a (already has the triage text); optionally a helper function
- out of scope: removing the detector
- files / anchors: `~/.grok/skills/aar/SKILL.md` rule 3a (lines ~742-752); `~/.grok/skills/aar/__lib/secret_engine.py`
- acceptance: when a secret_exposure signal fires, the orchestrator runs `git ls-files --error-unmatch <path>`. If gitignored/untracked, severity downgraded to LOW.
- falsifier: a real remote exposure is downgraded to LOW because the git check has a bug
- verification level required: UNIT_TEST

**Red-team note:** `secret_engine.py` is currently a pure pattern-matcher. Adding a git check means extending its contract to include side-effecting filesystem checks. The implementer should decide: (a) add the git check to `secret_engine.py`, or (b) add it as a post-detection filter in the orchestrator. Option (b) is cleaner — keeps the engine pure.

## 8. Open decisions

None. All red-team findings have been triaged:
- C1 (hooks don't fire): **FALSE POSITIVE** — refuted by active-surface snapshot
- C2 (no try/except): **CRITICAL** → TASK-00 (must fix first)
- C3 (Stop hook payload): **Phase 2 concern** — not in this handoff
- H1 (dead aggregator): → TASK-02 (wire it)
- H2 (false positives): → TASK-01 thresholds corrected
- M1 (cost proxy): → dropped, use group_key instead
- M2 (state isolation): → Phase 2 concern
- Additional (wrong file path in TASK-01): corrected — hook file lives in plugin `hooks/stop/`, not `P:/.claude/hooks/`

## 9. Hard constraints

1. TASK-00 MUST be done before TASK-01 (exception safety is a prerequisite for adding detectors).
2. All detector severities default to MEDIUM until empirical FP rate is measured.
3. Do NOT compute token cost estimates — use behavioral pattern proxies only.
4. Do NOT modify the `Signal` dataclass schema.

## 10. Cross-reference couplings

- Parent: `aar-narrativization-hook-20260722` (design + research)
- Phase 2: `aar-efficiency-phase2-hooks-20260722` (hooks + report — blocked on this)
- Wiki: `llm-agent-token-waste-categories.md`, `dead-code-detection-workflow.md`
- Code: `detectors.py:ALL_DETECTORS`, `aggregators.py:all_aggregates`, `full_preprocessor.py:~261`

## 11. Other outstanding streams

- Phase 2 (hooks + report): blocked on this handoff
- `aar-config-updates-20260722`: tool-fallbacks doc (independent)
- `file-editing-protocol-merge-20260722`: protocol merge (independent)

## 12. Explicit non-goals

- Do NOT build Stop hooks (Phase 2)
- Do NOT add report format changes (Phase 2)
- Do NOT compute token cost estimates
- Do NOT modify the Signal dataclass

## 13. Resumption protocol

1. Read this handoff + the parent handoff.
2. Start with TASK-00 (exception safety fix — one-line change).
3. Run existing test suite to confirm no regression.
4. Implement TASK-01 (5 detectors with corrected thresholds).
5. Implement TASK-02 (wire aggregator + add efficiency aggregator).
6. Implement TASK-03 (secret triage — optional, independent).
7. Run `vulture ~/.grok/skills/aar/__lib/` to check for new dead code.

## 14. Suggested next invocation

```
/go Implement AAR efficiency detectors Phase 1. Follow handoff at
P:/docs/handoffs/aar-efficiency-phase1-detectors-20260722/HANDOFF.md.
Build order: TASK-00 (exception safety) first, then TASK-01 (5 detectors),
then TASK-02 (aggregator wiring), then TASK-03 (secret triage).
Run vulture after implementation to check for dead code.
```

## 15. Last user message (verbatim)

> /handoff add the red-team findings to the handoff file, or create a phase 1 / phase 2 via two linked handoff files. Think of something optimal but all items need to be accounted for.

## 16. Epistemic labels

- [FACT] run_all_detectors has no try/except (verified by red-team reading source)
- [FACT] all_aggregates() is dead code (never called by full_preprocessor.py)
- [FACT] Signal dataclass has no cost-proxy field
- [FACT] Stop hooks fire under Grok Build (C1 refuted by active-surface snapshot)
- [INFERENCE] MEDIUM severity for all detectors until empirical validation is the right default
- [UNKNOWN] Whether the exclusion lists in TASK-01 are complete

## Dependencies

- **Requires:** nothing — can start immediately
- **Blocks:** Phase 2 (aar-efficiency-phase2-hooks-20260722) — hooks need tested detectors
- **Non-blocking to:** aar-config-updates, file-editing-protocol-merge