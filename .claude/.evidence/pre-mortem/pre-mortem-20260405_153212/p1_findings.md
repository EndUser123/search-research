## Triage Classification
hook — Modified two Stop hook files (Stop_hypothesis_as_fact_gate.py, hypothesis_as_fact_detector.py) plus test refactor and memory doc

## Dispatched Specialists
- adversarial-logic: regex pattern logic, test NameError bug, hedge detection, pattern ordering
- adversarial-testing: test collection, stub quality gate, stale cache
- adversarial-compliance: NameError, ASCII vs curly apostrophe regex, blockquote stripping
- adversarial-io-validation: silent exception swallowing, log failures, stdout assumptions

## Specialist Findings Summary

### adversarial-logic
**Domain:** Pattern logic and control flow
**Key findings:**
- [MEDIUM] HEDGE_WORDS 'typically' not detected by substring matching (hypothesis_as_fact_detector.py:136-158)
- [LOW] Pattern break-on-first-match could suppress more specific patterns (hypothesis_as_fact_detector.py:346-360)
- [HIGH] NameError: 'all_passed' undefined in __main__ block (test_stop_hypothesis_as_fact_refactor.py:130)

### adversarial-testing
**Domain:** Test coverage and quality
**Key findings:**
- [HIGH] StopHook_premortem_quality_gate.py is a non-functional stub (always returns allow)
- [HIGH] Stale __pycache__/critique_io.cpython-314.pyc from deleted module
- [MEDIUM] test_critique_io_concurrent.py not verified in pytest collection
- [LOW] Stub hook has no documentation on expected behavior

### adversarial-compliance
**Domain:** Code correctness and standards
**Key findings:**
- [HIGH] NameError: 'all_passed' undefined (test_stop_hypothesis_as_fact_refactor.py:130)
- [MEDIUM] MECHANISM pattern only matches curly apostrophe (U+2019), not ASCII apostrophe — 'doesn't' would not match (hypothesis_as_fact_detector.py:113)
- [LOW] Blockquote regex strips entire line including attribution content (Stop_hypothesis_as_fact_gate.py:187)

### adversarial-io-validation
**Domain:** File I/O and external call safety
**Key findings:**
- [MEDIUM] Silent exception swallowing in _log_decision() — disk-full/permissions errors silently dropped (Stop_hypothesis_as_fact_gate.py:168-170)
- [MEDIUM] LOG_DIR.mkdir() lacks error handling before write (Stop_hypothesis_as_fact_gate.py:135)
- [LOW] os.fdopen(1) assumes stdout always available (Stop_hypothesis_as_fact_gate.py:331)
- [LOW] Fallback imports fail silently — gate fails open when verification engine unavailable (Stop_hypothesis_as_fact_gate.py:34-48)

## Consolidated Findings

### Logical Gaps & Inconsistencies
1.1. [HIGH] (source: adversarial-compliance, adversarial-logic) — NameError: `all_passed` referenced at test_stop_hypothesis_as_fact_refactor.py:130 but never defined. Fix: initialize `all_passed = True` before test calls and update __main__ block.

### Hidden Assumptions & Fragile Dependencies
2.1. [MEDIUM] (source: adversarial-compliance) — MECHANISM regex `doesn'?t` uses curly apostrophe (U+2019) only. ASCII 'doesn't' would not match. Affects: hypothesis_as_fact_detector.py:113. Fix: `doesn['\u2019\u0027]?t`.
2.2. [MEDIUM] (source: adversarial-logic) — HEDGE_WORDS contains 'typically' but substring matching in `_detect_hedge()` cannot find it. Inflates confidence for mechanism claims using this hedge. Fix: verify substring matching checks `if hedge_word in sentence_lower` against HEDGE_WORDS keys.
2.3. [LOW] (source: adversarial-logic) — `_detect_mechanism_claims()` breaks on first pattern match per sentence; overly broad earlier patterns suppress more specific later ones. Fix: collect all matching patterns or reorder by specificity.
2.4. [LOW] (source: adversarial-compliance) — Blockquote regex `^>.*$` strips entire line including attribution/callout content. May lose legitimate text context. Fix: `re.sub(r"^>\s*", "", text)` to strip only the marker prefix.

### Missing Obvious Actions / Best Practices
3.1. [HIGH] (source: adversarial-testing) — StopHook_premortem_quality_gate.py is a non-functional stub — always returns allow. Pre-mortem quality enforcement is absent. Fix: implement quality gate validating HIGH/CRITICAL findings have file:line citations.
3.2. [HIGH] (source: adversarial-testing) — Stale `__pycache__/critique_io.cpython-314.pyc` from deleted module. Fix: `rm -rf P:/.claude/skills/pre-mortem/lib/__pycache__`.
3.3. [MEDIUM] (source: adversarial-testing) — test_critique_io_concurrent.py not verified in pytest collection. RISK-001 (sessions.json corruption) has no automated coverage. Fix: run `pytest --collect-only` to verify collection.

### Risks and Edge Cases
4.1. [MEDIUM] (source: adversarial-io-validation) — `_log_decision()` silently swallows exceptions — disk-full or permissions errors would not be logged or reported. Gate decisions are not auditable under failure conditions. Fix: increment a `_log_failure_count` counter; surface in gate result.
4.2. [MEDIUM] (source: adversarial-io-validation) — `LOG_DIR.mkdir()` has no error handling between mkdir and subsequent file write. Concurrent parent-dir deletion could raise unexpectedly. Fix: wrap entire body in try/except OSError.
4.3. [LOW] (source: adversarial-io-validation) — `os.fdopen(1)` assumes fd=1 always available. Redirected/closed stdout would silently drop warning. Fix: try/except with sys.stderr fallback.
4.4. [LOW] (source: adversarial-io-validation) — Verification engine fallback imports fail silently — gate always returns allow when engine unavailable. Fix: log warning once per session when degraded.

### Concrete Recommendations
5.1. (source: adversarial-compliance) — Fix regex at hypothesis_as_fact_detector.py:113: add ASCII apostrophe to all contraction patterns: `['\u2019\u0027]`
5.2. (source: adversarial-testing) — Delete orphaned pycache: `rm -rf P:/.claude/skills/pre-mortem/lib/__pycache__`
5.3. (source: adversarial-logic) — Fix test __main__ block NameError: initialize `all_passed = True` before test calls
5.4. (source: adversarial-io-validation) — Wrap _log_decision in try/except OSError with failure counter
5.5. (source: adversarial-testing) — Implement quality gate in StopHook_premortem_quality_gate.py per ADR-20260329

### Open Questions / Unknowns
6.1. (source: adversarial-logic) — Was the NameError in the test file pre-existing or introduced by the refactor? The work changed return-bool-to-None but the __main__ block was not updated.
6.2. (source: adversarial-compliance) — Was the MECHANISM ASCII apostrophe gap verified against a real LLM output corpus? The false-positive incident used curly quotes.
6.3. (source: adversarial-testing) — Does TEST-003 (concurrent test not collected) affect RISK-001 coverage? Needs pytest collection verification.
