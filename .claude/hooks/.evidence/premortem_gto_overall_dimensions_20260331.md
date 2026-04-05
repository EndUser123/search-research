# Pre-Mortem: GTO `overall`/`dimensions` Promotion Fix

**Date**: 2026-03-31
**Target**: `gto_orchestrator.py:1295-1301` — promote `overall` and `dimensions` to JSON artifact top level
**Analysis**: Bruce Thomson

## Step 0: Constraints
- Fail fast, surface problems immediately
- Truthfulness > agreement
- Evidence-first verification
- Solo dev: pragmatic solutions over enterprise patterns

## Step 0.7: Kill Criteria
- If fix breaks existing GTO test assertions → revert
- If new artifacts are malformed → revert

## Step 1: Failure Scenario
"It's 6 months later and the GTO fix FAILED. Why?"

## Step 1.5: Fix Side Effects
- Could conflict with future artifact schema changes
- May cause backward compatibility issues if downstream consumers expect only `health_report.overall_score`

## Step 2: Failure Causes

| ID | Cause | Category | Principle Violated |
|----|-------|----------|-------------------|
| F-001 | If `health_report` is None, `overall` and `dimensions` not in artifact | Tech | Defensive programming |
| F-002 | Two sources of truth (`overall` vs `health_report.overall_score`) could diverge | Tech | Single source of truth |
| F-003 | New metric types without `name` field excluded from `dimensions` | Tech | Encapsulation |
| F-004 | Non-numeric `score` in metrics would break `dimensions` dict values | Tech | Type contracts |
| F-005 | Artifact path: JSON → `project_root/.evidence/`, Markdown → `~/.claude/.evidence/` | Process | Consistency |
| F-006 | Concurrent artifact writes could corrupt JSON (no atomic write) | Tech | Concurrency isolation |
| F-007 | `_evict_old_artifacts()` could evict wrong artifact in race | Tech | Atomicity |
| F-008 | Old artifacts lack `overall`/`dimensions` — consumers must handle None | Process | Backward compatibility |

## Step 3.5: Reference Class
Similar JSON schema additions in GTO failed when consumers didn't handle missing keys gracefully.

## Step 3.8: Operational Verification
**Code verified**: `gto_orchestrator.py:1295-1301`
- Guard: `if result.health_report:` — correct None check
- Dict comprehension: `m["name"]: m["score"]` — safe if `metrics` is empty list
- Atomic write: `json.dump()` to file handle — not atomic at OS level

## Step 4: Risk Ratings

| ID | Risk | Likelihood | Impact | Score | Notes |
|----|------|-----------|--------|-------|-------|
| F-001 | Missing health_report causes absent fields | 1 | 3 | 3 | Low likelihood — health check enabled by default |
| F-002 | Divergent sources of truth | 1 | 2 | 2 | Low — both derived from same source |
| F-005 | Path inconsistency markdown vs JSON | 2 | 1 | 2 | Medium — confusing but non-breaking |
| F-006 | Concurrent write corruption | 1 | 3 | 3 | Low — sequential execution in Claude Code |
| F-007 | Wrong artifact eviction | 1 | 2 | 2 | Low — sort by mtime, keep 10 |
| F-008 | Backward compat for old artifacts | 3 | 1 | 3 | High likelihood — consumers must handle None |

## Step 5: Top Risks & Actions

**RISK F-008**: Backward compatibility — consumers expect `overall` may get None
- **Action**: Document that `overall`/`dimensions` may be None for old artifacts

**RISK F-005**: Path inconsistency between JSON and markdown artifacts
- **Action**: Consider unifying to single output directory

## Step 6: Warning Signs

| Risk | Warning Sign | Detection | Trigger |
|------|-------------|-----------|---------|
| F-006 | JSON parse error in artifact files | Validate JSON on read | If any artifact fails parse |
| F-007 | Fewer than expected artifacts | Count artifacts after run | If < expected count |

## Step 7: Adversarial Validation
*Completed 2026-03-31*

8 adversarial agents executed in parallel. All findings below verified with evidence.

### Adversarial Findings Summary

| Agent | Critical Findings | High Findings |
|-------|------------------|---------------|
| logic | LOGIC-001 (truthiness guard bug), LOGIC-002 (silent dict drops), LOGIC-003 (non-atomic write), LOGIC-004 (TOCTOU race) | LOGIC-005 (falsy score skip) |
| performance | PERF-001 (non-atomic JSON write corruption) | PERF-002 (TOCTOU eviction race) |
| qa | QA-003 (zero test coverage for fix), QA-005 (no None-handling test) | QA-004 (no path-consistency test), QA-006 (undefined success criteria), QA-007 (F-002/3/4 untested) |
| critic | Risk score asymmetry (F-001=F-008=3, different profiles), F-008 likelihood inflation | Calibration mismatch on path unification priority |
| compliance | **COMP-001 CRITICAL: Schema catastrophe** — `health`→`health_report`, `summary`/`next_steps_summary`/`recommended_next_steps` removed, `overall`/`dimensions`/`*_count` added. Complete restructuring. | COMP-002 (KeyError on missing name), COMP-003 (TypeError on non-numeric score) |
| security | No security vulnerabilities | — |
| testing | No dedicated tests for overall/dimensions promotion | GTO assertions cover runner, not orchestrator |
| quality | No coupling issues | Low technical debt |

### High-Priority Adversarial Findings

**LOGIC-001 (HIGH — Fix needed)**: Truthiness guard `if result.health_report:` at line 1295 could pass a HealthReport object (not dict) to `.get()` calls, causing AttributeError. Should be `if result.health_report is not None:`.
- Evidence: `gto_orchestrator.py:1295` — type annotation `dict[str, Any] | None` contradicts docstring claiming health_report "is never None"
- Fix: Use identity check, not truthiness

**QA-003 (BLOCKER — Test coverage)**: Zero dedicated tests for `gto_orchestrator.py:1295-1301` overall/dimensions promotion code path.
- Evidence: `test_gto_assertions.py` tests `GTOAssertionRunner`, not the orchestrator artifact promotion
- Fix: Add tests covering: None health_report, empty metrics, non-numeric score, falsy overall_score (0)

**QA-005 (HIGH)**: No test verifies consumers handle None for `overall`/`dimensions` gracefully.
- Evidence: F-008 rated high-likelihood (3) with only documentation action
- Fix: Add integration test simulating old artifact (no overall/dimensions fields)

**PERF-001 (CRITICAL)**: `json.dump()` without temp file + rename — crash/interrupt leaves 0-byte artifact file.
- Evidence: `gto_orchestrator.py:1303` — no atomic write pattern
- Fix: Write to `.tmp` file, then `os.replace()` to target

**LOGIC-004 (MEDIUM)**: `_evict_old_artifacts()` TOCTOU — new artifact created between sort and delete could be incorrectly evicted.
- Evidence: `gto_orchestrator.py:1307, 1319-1334`
- Fix: File lock during glob → delete window, or rename-based marking before delete

**LOGIC-002 (MEDIUM)**: Dict comprehension silently drops metrics without `name` key or with non-numeric `score` values.
- Evidence: `gto_orchestrator.py:1298-1300` — `{m['name']: m['score'] for m in metrics}`
- Fix: Add `if 'name' in m and isinstance(m['score'], (int, float))` guard

**QA-006 (MEDIUM)**: Actions in Step 5 lack concrete success criteria.
- Evidence: "Document backward compat" and "Consider path unification" are vague directives
- Fix: Define acceptance criteria: test that fails if documentation removed, test verifying same output directory

### Findings with Lower Priority (Documented, No Action)

- **LOGIC-003**: Non-atomic json.dump — acknowledged, low risk in sequential execution
- **PERF-002**: TOCTOU eviction race — same as LOGIC-004, same fix
- **PERF-003**: Path inconsistency (JSON vs Markdown) — deferred, non-breaking
- **LOGIC-005**: Falsy health_report (score=0) skips promotion — low probability, documented in F-001
- **QA-004**: No path-consistency test — deferred with PERF-003
- **QA-007**: F-002/F-003/F-004 untested — mitigated by HealthMetric dataclass invariants

### Calibration Notes (From adversarial-critic)

- F-001 (L=1,I=3,S=3) vs F-008 (L=3,I=1,S=3) — same score, different risk profiles. F-008 is a *known* gap, not a probability. Re-score F-008 likelihood to 1 (known issue).
- F-006 atomic write claim was correctly identified as non-atomic at OS level — this is accurate.

## Step 8: Updated Risk Ratings

| ID | Risk | Likelihood | Impact | Score | Change |
|----|------|-----------|--------|-------|--------|
| F-001 | Missing health_report | 1 | 3 | 3 | Unchanged |
| F-002 | Divergent sources | 1 | 2 | 2 | Unchanged |
| F-003 | Missing name in metrics | 1 | 2 | 2 | Unchanged (dataclass mitigates) |
| F-004 | Non-numeric score | 1 | 2 | 2 | Unchanged (dataclass mitigates) |
| F-005 | Path inconsistency | 2 | 1 | 2 | Deferred — no action |
| F-006 | Non-atomic write | 1 | 3 | 3 | Unchanged (sequential exec) |
| F-007 | TOCTOU eviction | 1 | 2 | 2 | Unchanged |
| F-008 | Backward compat | 1 | 1 | 1 | **Reduced from 3** (known issue, not probability) |

## REMAINING ITEMS

| Step | Status | Gap | Priority |
|------|--------|-----|----------|
| 5 | 🔴 Critical | COMP-001: Schema catastrophe — `health`→`health_report`, `summary` fields removed, complete restructuring | CRITICAL |
| 5 | 🔴 Partial | LOGIC-001 (truthiness guard), COMP-002 (KeyError on missing name), QA-003/005 (test coverage) | HIGH |
| 6 | ✅ Addressed | Warning signs documented | Low |
| 7 | ✅ Complete | 8 adversarial agents executed | Complete |
