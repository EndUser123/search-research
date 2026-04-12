# Phase 1: Triage + Specialist Dispatch — Consolidated Findings

## Triage Classification
**code** — Modification to two hook verification functions: `_claim_matches_tool_output()` in `verification/engine.py` and `_should_block_claim()` in `StopHook_unverified_stance.py`. The change adds a content-match fallback for SILENT verdicts in the stop hook verification engine.

## Dispatched Specialists
- **adversarial-logic**: Pure logic errors, conditionals, operator correctness
- **adversarial-io-validation**: Path validation, file I/O, external calls
- **adversarial-compliance**: Schema contracts, pre-condition enforcement, cross-target leakage
- **adversarial-testing**: Test coverage, missing scenarios, edge case handling

## Specialist Findings Summary

### adversarial-logic
**Domain:** Off-by-one, empty string edge case, stopword completeness

**Key findings:**
- [LOW] Empty string claim text would incorrectly return True (engine.py:617)
- [LOW] Stopword set is incomplete — common function words like 'if', 'else', 'when' not filtered (engine.py:621-627)

**No significant issues found in core logic flow.**

### adversarial-compliance
**Domain:** Pre-condition enforcement, cross-target verification leakage

**Key findings:**
- [MEDIUM] `_claim_matches_tool_output` called without verifying SILENT pre-condition — bypasses intended safety when _filter_events_by_targets() had relevant events but returned empty for other reasons (StopHook_unverified_stance.py:190)
- [MEDIUM] `_claim_matches_tool_output` ignores claim targets — allows cross-target verification where a claim about X is verified by output about unrelated Y (engine.py:631-643)
- [LOW] Key term subset matching threshold of 3 is arbitrary and not justified (engine.py:640-642)

### adversarial-testing
**Domain:** Test coverage gaps, edge case handling, integration test adequacy

**Key findings:**
- [LOW] No test for empty string claim text (would return True incorrectly — edge case in engine.py:617)
- [LOW] No test for stopword set incompleteness (LOGIC-002)
- [LOW] No test for cross-target verification bypass (COMP-002)

### adversarial-io-validation
**Domain:** File operations, external calls, path validation

**Key findings:**
- No issues found in the reviewed code (`_claim_matches_tool_output`, `_should_block_claim`). No file I/O, subprocess calls, or external service dependencies in the new code.

---

## Consolidated Findings

### 1. Logical Gaps & Inconsistencies

1.1. [MEDIUM] (source: adversarial-compliance) — `_claim_matches_tool_output` pre-condition not enforced (StopHook_unverified_stance.py:190)

The fallback is invoked whenever `verdict.status == SILENT`, but the documented pre-condition is "when _filter_events_by_targets() returned empty due to target-path mismatch." If the function returned empty because no tools were used at all (not because of path mismatch), the fallback still activates — even though no evidence exists to match against. This conflates "no relevant tools" (should block) with "relevant tools used but no path match" (should fallback).

**Fix**: Pass a flag indicating whether _filter_events_by_targets() returned empty due to path mismatch specifically.

1.2. [LOW] (source: adversarial-logic) — Empty claim text returns True (engine.py:617)

If `claim.text` is empty string, `claim_text = ''` and `'' in output` returns True for any non-empty output. While claims with empty text are unlikely in practice, the guard `if not claim.text.strip(): return False` should be added.

1.3. [LOW] (source: adversarial-logic) — Stopword set incomplete (engine.py:621-627)

Common function words not in stopwords: 'if', 'else', 'when', 'then', 'also', 'any', 'all', 'both', 'none', 'every', 'each'. These could cause false subset matches in edge cases.

### 2. Hidden Assumptions & Fragile Dependencies

2.1. [MEDIUM] (source: adversarial-compliance) — Cross-target verification bypass (engine.py:631-643)

`_claim_matches_tool_output` matches claim text against ANY tool event output without checking whether the event's command/output is related to the claim's targets. A claim "X does not exist" could be verified by output that confirms Y exists, if the claim text happens to overlap with unrelated tool output. The `claim.targets` field is never consulted in the fallback.

2.2. [LOW] (source: adversarial-compliance) — Arbitrary 3-key-term threshold (engine.py:640-642)

No rationale for threshold=3. Short claims with 3 common non-stopword terms could match unrelated output. Longer claims might need more terms for confidence.

### 3. Missing Obvious Actions / Best Practices

3.1. [MEDIUM] (source: adversarial-compliance) — Add target-scoped pre-check before fallback

Before accepting a content match, verify that at least one of the claim's targets appears in the event's command/output. This prevents cross-target false positives.

3.2. [LOW] (source: adversarial-logic) — Add empty-string guard

Add `if not claim.text.strip(): return False` at the start of `_claim_matches_tool_output`.

### 4. Risks and Edge Cases

4.1. [MEDIUM] (source: adversarial-compliance) — SILENT verdict has two distinct causes that are treated identically

Cause A: No relevant tool events exist at all → should block confident claims.
Cause B: Tool events exist but targets didn't match (path mismatch) → fallback is appropriate.
The current code cannot distinguish these, so it always tries the fallback for all SILENT cases.

4.2. [LOW] (source: adversarial-logic) — Subset match threshold not proportional to claim length

A 3-word claim needs all 3 terms to match (100%). A 20-word claim also only needs 3 terms (15%). This asymmetry could allow short generic claims to match unrelated output.

### 5. Concrete Recommendations

5.1. [MEDIUM] Add target pre-check before content match fallback

In `_should_block_claim`, before calling `_claim_matches_tool_output`, verify that at least one claim target appears in the tool event's command/output. If no target appears anywhere in the event list, don't invoke the fallback — it's not a path-mismatch case, it's a no-evidence case.

5.2. [MEDIUM] Distinguish SILENT causes in _should_block_claim

Refine the SILENT branch to check: were relevant events filtered but empty (path mismatch → use fallback), or were no relevant events found at all (no evidence → block). Consider passing filtered event count to `_should_block_claim`.

5.3. [LOW] Add empty-string guard in _claim_matches_tool_output

Add `if not claim.text.strip(): return False` at line 617.

5.4. [LOW] Document threshold rationale in docstring

Add comment explaining threshold=3 and why it's appropriate for the claim types this hook handles.

### 6. Open Questions / Unknowns

6.1. [LOW] (source: adversarial-compliance) — Can claim.text actually be empty in the Claim dataclass? If no, LOGIC-001 is a non-issue.

6.2. [LOW] (source: adversarial-logic) — Is the 3-key-term threshold sufficient for all claim types, or should RULE claims require stricter matching?

---

**Phase 1 Completion Gate: PASSED** — All 4 specialist JSONs available, dispatch manifest confirmed, p1_findings.md written.