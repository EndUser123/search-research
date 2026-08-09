# HANDOFF: Ship-py remaining gaps — test quality, refactor consistency, verdict enforcement

## Status
OPEN — ready to implement

## Objective
Fix the remaining ship-py gaps surfaced during three honest /ship-py verification runs this session. These are test-quality bugs, phase-consistency issues, and enforcement-strength gaps that the review agents found but the fix-loop cap (2 iterations) didn't reach.

## Context
- Session 019fe25d ran ship-py honestly three times
- Each run spawned real review agents who found real bugs
- 16 total bugs found across runs; 8 fixed during session; 8 remain
- The anti-fabrication architecture is shipped (polling loop, suspicion gates, transition chain, path validation, receipt status validation)
- The remaining gaps are quality and consistency issues, not specification-gaming vectors

## Remaining items

### Test quality (from reviewer 2, 709s/101 tool calls)

1. **test_pauses_at_review_when_no_review_findings** — `_execute_phase` patched without `return_value=0`. Works by accident because current PHASE_ORDER happens to skip the right phases. If anyone adds a deterministic phase between check and review, it crashes with TypeError (MagicMock not JSON serializable). Fix: `patch('phases.run_all._execute_phase', return_value=0)`.

2. **test_pause_emits_findings_path** — asserts only `result == 0`. Never checks the findings path appears in output. The test would pass even if the canonical path feature was removed entirely. Fix: use `capsys` to capture stdout and assert the canonical path string appears.

3. **Test state isolation** — tests don't use a shared `tmp_artifacts` fixture. Real state files at `P:/.artifacts/ship-py/test-session/state.json` can leak between tests. Adopt the `tmp_artifacts` fixture pattern from `test_ship_orchestrator.py`.

### Phase consistency (from reviewer 1)

4. **refactor.py silently passes when findings file is missing** — unlike risk.py which blocks. When `has_code_files=True` but no findings file exists, refactor.py falls through to empty default. Fix: block rather than silently passing (match risk.py contract).

5. **correction_classifier.py uses substring match for no_detector_types** — `[ft for ft, det in detector_map.items() if "NO DETECTOR" in det]` is fragile to renaming. Fix: use a structured marker (tuple or separate dict).

### Enforcement strength (from reviewer 1)

6. **Verdict phase only warns on chain breakage** — `chain_warning` is added to summary but doesn't change the return code. A broken chain at verdict time should be a hard block (return 2), not a warning. Fix: block SHIP DONE when chain is broken.

7. **_format_version field is decorative** — written by `save_state()` but never read by `load_state()`. No migration logic exists. Fix: either add migration logic or remove the field.

8. **Polling-loop timeout has no retry cap** — re-invocation retries indefinitely with no exponential backoff. Fix: add retry counter and hard block after N timeouts.

## Acceptance criteria
- All 8 items fixed
- 55+ tests pass (current baseline)
- New test: `test_pauses_at_review` uses `return_value=0` (no MagicMock crash)
- New test: `test_pause_emits_findings_path` actually asserts the path string
- refactor.py blocks on missing findings (matches risk.py)
- verdict.py blocks on broken chain (returns 2, not 0)

## Key files
- `~/.grok/skills/ship-py/tests/test_run_all.py` — items 1, 3
- `~/.grok/skills/ship-py/tests/test_run_all_integration.py` — item 2, 3
- `~/.grok/skills/ship-py/__lib/phases/refactor.py` — item 4
- `~/.grok/scripts/correction_classifier.py` — item 5
- `~/.grok/skills/ship-py/__lib/phases/verdict.py` — item 6
- `~/.grok/skills/ship-py/__lib/phases/_shared.py` — item 7
- `~/.grok/skills/ship-py/__lib/phases/run_all.py` — item 8

## Suggested next invocation
```
/go Read P:/docs/handoffs/ship-py-remaining-gaps-20260808/HANDOFF.md and fix all 8 items. Run tests after each fix.
```

## References
- FINDINGS.md at `P:/.artifacts/ship-py/019fe25d-6979-7892-82ae-ebf68232312a/FINDINGS.md` — review findings from this session
- `P:/.data/wiki/concepts/polling-loop-continuation-controller-design-decision.md` — design decision with falsifiers
- `P:/.data/wiki/concepts/specification-gaming-in-llm-agent-pipelines.md` — diagnosis
