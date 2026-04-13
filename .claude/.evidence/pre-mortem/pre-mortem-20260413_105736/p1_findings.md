## Triage Classification
[code] — Python module improvements for GTO skill coverage and quality

## Dispatched Specialists
- adversarial-logic: Pure logic errors in staleness check and threshold handling
- adversarial-quality: Maintainability issues (stdlib frozenset, thresholds)
- adversarial-testing: Test coverage gaps for freshness logic
- adversarial-io-validation: Path validation and file operations

## Specialist Findings Summary

### adversarial-logic
**Domain:** Logic correctness
**Key findings:**
- [blocker] Staleness check uses `entries[0]` (OLDEST) instead of `entries[-1]` (MOST RECENT) — core logic error
- [medium] `_infer_domain_from_gap_type()` duplicates `GAP_TYPE_TO_CATEGORIES` logic — maintenance risk
- [medium] Integer division bug truncates large effort estimates (150min → "2hr" not "2.5hr")
- [medium] Health thresholds (0.20/0.40/0.50) with no documented derivation

### adversarial-quality
**Domain:** Maintainability and technical debt
**Key findings:**
- [MEDIUM] Staleness check uses oldest entry instead of newest — will misclassify fresh coverage as stale
- [LOW] stdlib frozenset is manually maintained and will drift from actual stdlib over time
- [LOW] TREND_WINDOW=5 has no documented derivation
- [LOW] FALSE_POSITIVE_HIGH=0.50 allows 50% false positive rate before triggering HIGH severity
- [LOW] MAX_CHAIN_DEPTH=10 is not documented as an architectural constraint

### adversarial-testing
**Domain:** Test coverage
**Key findings:**
- [HIGH] No test coverage for critical freshness-checking logic
- [HIGH] Staleness check uses OLDEST timestamp instead of MOST RECENT
- [MEDIUM] Health detector thresholds have no documented derivation
- [MEDIUM] MAX_CHAIN_DEPTH=10 has no documented rationale
- [MEDIUM] No integration tests for critical skill suggestion deduplication logic

### adversarial-io-validation
**Domain:** I/O operations and path validation
**Key findings:**
- [blocker] Path validation restricts to sessions_dir but transcripts may be elsewhere
- [high] Skill coverage log path construction may fail on non-standard target_key values
- [high] File operations lack atomic write safety for concurrent terminals
- [medium] No validation that coverage log entries have required fields before access
- [medium] `_get_skill_coverage_path()` constructs paths unsafely with f-strings

## Consolidated Findings

### Logical Gaps & Inconsistencies
1.1. [HIGH] (adversarial-logic, adversarial-testing) — Staleness check uses OLDEST `entries[0]` instead of MOST RECENT `entries[-1]` — skill_coverage_detector.py:631
1.2. [MEDIUM] (adversarial-logic) — `_infer_domain_from_gap_type()` duplicates `GAP_TYPE_TO_CATEGORIES` logic creating maintenance risk — gap_skill_mapper.py:357-381
1.3. [MEDIUM] (adversarial-logic) — Integer division bug truncates effort (150min → "2hr") — next_steps_formatter.py:67-105

### Hidden Assumptions & Fragile Dependencies
2.1. [MEDIUM] (adversarial-io-validation) — Coverage log entries assumed to have required fields without validation before access
2.2. [LOW] (adversarial-quality) — TREND_WINDOW=5 has no documented derivation affecting trend calculations
2.3. [LOW] (adversarial-quality) — FALSE_POSITIVE_HIGH=0.50 allows 50% false positive rate before HIGH severity trigger
2.4. [LOW] (adversarial-quality) — MAX_CHAIN_DEPTH=10 not documented as architectural constraint

### Missing Obvious Actions / Best Practices
3.1. [HIGH] (adversarial-testing) — No test coverage exists for critical freshness-checking logic in `skill_coverage_detector.py`
3.2. [MEDIUM] (adversarial-testing) — No integration tests for critical skill suggestion deduplication logic
3.3. [MEDIUM] (adversarial-io-validation) — Path validation restricts to sessions_dir but transcripts may be elsewhere

### Risks and Edge Cases
4.1. [MEDIUM] (adversarial-io-validation) — File operations lack atomic write safety for concurrent terminals
4.2. [MEDIUM] (adversarial-io-validation) — Skill coverage log path construction may fail on non-standard target_key values
4.3. [LOW] (adversarial-quality) — stdlib frozenset manually maintained — will drift from actual stdlib over time

### Concrete Recommendations
5.1. [HIGH] Fix staleness check: sort by timestamp, use `entries[-1]` for MOST RECENT
5.2. [HIGH] Add test coverage for freshness check logic before deploying the staleness fix
5.3. [MEDIUM] Extract `GAP_TYPE_TO_CATEGORIES` usage so `_infer_domain_from_gap_type()` delegates to it instead of duplicating
5.4. [MEDIUM] Add docstrings with derivation evidence for health thresholds (0.20/0.40/0.50) and MAX_CHAIN_DEPTH=10
5.5. [MEDIUM] Add required-field validation before accessing coverage log entry fields

### Open Questions / Unknowns
6.1. [LOW] (adversarial-io-validation) — What happens when coverage log has entries with missing timestamps? Edge case unhandled.
