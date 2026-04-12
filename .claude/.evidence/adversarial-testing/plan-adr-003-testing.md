# Adversarial Testing Review: plan-adr-003-recap-session-reconstruction

## Scope

Plan: C:/Users/brsth/.claude/plans/plan-adr-003-recap-session-reconstruction.md
Test suite: P:/.claude/skills/recap/tests/test_recap.py
Production code: P:/.claude/skills/recap/__init__.py

CRITICAL FINDING: NONE of T1-T9 exist in the test suite.

---

## Findings

### TEST-001: T1 has no test -- fallback trigger not verifiable
Severity: HIGH

T1 (Chain returns subagent-only -> Fallback triggers) is not tested. No test constructs a mock
chain result with all-subagent entries. test_recap.py has no import of walk_session_chain,
SessionChainEntry, or _load_all_sessions_via_history_index. _load_all_sessions_via_history_index()
at line 1268 calls walk_session_chain() but no test exercises that path. Acceptance criterion
T1 passes cannot be satisfied.

Recommendation: Add TestChainTraversal.test_subagent_only_chain_triggers_fallback. Mock
walk_session_chain() to return entries all pointing to subagent paths. Assert valid_entries
is empty, triggering ALL-invalid fallback branch.

### TEST-002: T2 has no test -- prior session from summary block not verifiable
Severity: HIGH

T2 (Chain fails, session summary present -> Prior session shown in recap) is not tested.
CHANGE-003 (fallback summary parsing) and CHANGE-004 (_summarize_session extraction) have no
coverage. _summarize_session() tests (lines 342-384) test last_goal from regular content only.
No test emits a ## Last Session Summary block with **When:** and **Duration:** fields.
Fallback path in _load_all_sessions_via_history_index() is completely untested.

Recommendation: Add test_summarize_session_extracts_summary_block. Construct entries containing
session summary block with When and Duration fields. Assert last_goal contains prior session
marker. Add test for quality gate rejection: Duration=0 or content starting with # falls
through to mtime fallback.

### TEST-003: T3 has no test -- mtime-based fallback not verifiable
Severity: HIGH

T3 (No session summary block -> Falls back to most-recent transcript by mtime) is not tested.
All tests use make_transcript() to create single files -- no test creates multiple transcript
files with different mtimes. No test verifies fallback to mtime scan. MAX_MTIME_GAP_SECS=120s
logic is not exercised.

Recommendation: Add test_no_summary_block_falls_back_to_mtime. Create two transcript files
with different mtimes via os.utime on tmp_path. Simulate no session summary block. Assert
fallback selects the more recent file.

### TEST-004: T4 has no test -- main-session vs subagent distinction not verifiable
Severity: HIGH

T4 (Chain returns valid main-session transcript -> Subagent paths filtered, chain used directly)
is not tested. _is_subagent_transcript() does not exist yet (CHANGE-001 specifies it must be added).
No test creates a chain with mixed main-session and subagent entries. No test verifies path
classification for subagent paths vs main session paths. Windows path handling is especially
risky and untested.

Recommendation: Add TestIsSubagentTranscript. Test: subagents/agent-xyz.jsonl -> True;
transcript.jsonl -> False; Windows backslash paths -> correctly classified.

### TEST-005: T5 has no test -- chain order preservation not verifiable
Severity: HIGH

T5 (Mixed chain -> Valid entries preserved in chain order, subagent dropped) is not tested.
No test constructs chain [A (main), B (subagent), C (main)] and asserts result [A, C].
Preserve chain order of valid ones invariant in D1 has no coverage. If implementation uses
set-based deduplication or loses ordering during filtering, no test detects it.

Recommendation: Add test_mixed_chain_preserves_order. Mock chain [valid1, subagent, valid2,
subagent, valid3]. Assert result is [valid1, valid2, valid3].

### TEST-006: T6 has no test -- dual-content precedence not verifiable
Severity: HIGH

T6 (Both summary block AND current-session work -> Both shown) is not tested. No test creates
transcript with both session summary block (prior session) AND post-summary entries (current
session). D4 rule Show BOTH, do not truncate has no verification. Implementation could
truncate to summary-only or post-summary-only and no test would catch it.

Recommendation: Add test_dual_content_shows_both_summary_and_current. Assert recap output
contains both prior session marker and current session content.

### TEST-007: T7 has no test -- stale summary fallback not verifiable
Severity: HIGH

T7 (Session summary present but stale -> Falls back to mtime) is not tested. No test creates
session summary block with Duration=0 or missing When field. Quality gate condition
duration_mins > 0 in CHANGE-003 is not exercised.

Recommendation: Add test_stale_summary_falls_back_to_mtime. Assert fallback to mtime scan
when Duration=0 or When field is missing.

### TEST-008: T8 has no test -- Windows path separator handling not verifiable
Severity: HIGH

T8 (Windows path separators -> _is_subagent_transcript() correctly classifies) is not tested.
No test creates Path with Windows-style separators. D3 invariant robust to Windows/Unix
path separators has no coverage. Subagent filtering could fail on Windows.

Recommendation: Add test_is_subagent_transcript_windows_paths. Test Windows backslash paths
with subagents component -> True; main session path -> False.

### TEST-009: T9 has no test -- malformed summary block quality gate not verifiable
Severity: HIGH

T9 (Malformed summary block with extra headings -> Quality heuristic rejects, falls back to mtime)
is not tested. No test creates session summary block whose content starts with #. Quality gate
content does not start with # has no test coverage.

Recommendation: Add test_summary_block_rejected_if_content_starts_with_hash. Assert it falls
through to mtime fallback.

### TEST-010: T1-T9 coverage summary -- zero test infrastructure for plan core scenarios
Severity: CRITICAL

The test suite covers peripheral functions but completely omits all scenario tests for the
plan three core bugs:
1. Chain traversal returning subagent transcripts (CHANGE-002)
2. Session summary block never parsed (CHANGE-003, CHANGE-004)
3. Fallback to mtime scan when chain fails (CHANGE-003)

test_recap.py imports: _extract_content, _extract_semantic_content, _is_transcript_file,
_summarize_session, extract_sessions_from_transcript, format_recap, load_transcript_entries
-- none of the chain/summary/filter functions. No test mocks walk_session_chain() return value.
No test creates multiple transcript files with different mtimes. No test parses a
## Last Session Summary block.

The plan cannot be validated by its own acceptance criteria. Every T1-T9 test case is missing.

## Missing Scenarios Not Covered by T1-T9

1. Empty chain: walk_session_chain returns [] -- true empty case, T1 does not test it explicitly
2. Subagent path edge cases: subagents as filename component, agent- different casing, spaces
3. Summary block at different positions: appears after line 200/entry 50
4. Multiple summary blocks: multiple ## Last Session Summary sections in one transcript
5. Malformed Duration: ~2h missing minutes, spacing variants -- regex not tested
6. Non-JSON lines in fallback scan: json.loads in try/except skipping not tested
7. Very old vs very recent mtime gap: MAX_MTIME_GAP_SECS=120s boundary not tested
8. Concurrent transcript writes: identical mtimes within 1 second -- sort stability not tested
9. Full /recap flow integration test: complete flow with mocked prior session not tested

---

## Status: FAIL

The test suite does not cover any of the 9 plan-specified test cases (T1-T9). Implementation
cannot be validated against its own acceptance criteria. All findings are HIGH or CRITICAL.

open_questions: None -- the gap is unambiguous.

overall_assessment: Complete test coverage void for plan ADR-003. Existing test_recap.py
tests peripheral parsing utilities but has zero coverage for the three core changes
(chain filtering, session summary parsing, fallback to mtime).