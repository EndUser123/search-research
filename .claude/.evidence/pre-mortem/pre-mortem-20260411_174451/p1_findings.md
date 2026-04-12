# Phase 1 Findings — recap skill semantic extraction

## Triage Classification

**skill** — A Claude Code skill with semantic extraction regex patterns and tests. The work under review is the recent fixes to `_find_transcript_dir()`, Python 3.14 lookahead regression, session ID filter logic, and test data updates.

## Dispatched Specialists

- `adversarial-logic` — Pure logic analysis (off-by-one, operators, conditionals)
- `adversarial-quality` — Maintainability, code structure, tech debt
- `adversarial-testing` — Test coverage, missing scenarios, brittle tests

## Specialist Findings Summary

### adversarial-logic

**Domain:** Pure logic correctness

**Key findings:**
- No logical issues found. The work.md was a brief topic description, not a code artifact with logic to analyze.

### adversarial-quality

**Domain:** Maintainability, code structure, technical debt

**Key findings:**
- [HIGH] `_RE_FIX` groups 2 and 3 are dead code — only group 1 is ever accessed in extraction loop
- [MEDIUM] `_filter` function uses unexplained magic numbers (15, 40, 30) without constants
- [MEDIUM] `load_sessions_index` has unreachable dead code after early return
- [LOW] Stale comment about Python 3.14 bug doesn't match actual pattern structure
- [MEDIUM] Missing test coverage for `_filter` function
- [LOW] Missing test coverage for `_unique_truncate` function
- [LOW] `_summarize_session` last_goal extraction may accept non-intent content from mixed blocks

### adversarial-testing

**Domain:** Test quality and coverage

**Key findings:**
- [HIGH] Weak assertions — semantic extraction tests only check `len >= 1`, not actual content
- [HIGH] Brittle regex — requires double asterisks (**), silently fails on single asterisk or other formats
- [HIGH] Untested `## Files Changed` alternative in `_RE_ACTION`
- [MEDIUM] `_filter` function has no dedicated unit tests
- [MEDIUM] `_RE_TOOL` may not handle Windows backslash paths
- [MEDIUM] `format_recap` integration test uses weak OR assertion masking partial failures
- [MEDIUM] User problem extraction truncates at 500 characters
- [LOW] No test for empty semantic extraction results

## Consolidated Findings

### Logical Gaps & Inconsistencies

1.1. [HIGH] (source: adversarial-quality, QUAL-001) — `_RE_FIX` capture groups 2 and 3 are compiled but never extracted. Line 697-698 only accesses `match.group(1)`. The 'root cause' and 'fix applied' pattern alternatives silently drop their matches. (`P:/recap/__init__.py:697-698`)

### Hidden Assumptions & Fragile Dependencies

2.1. [MEDIUM] (source: adversarial-quality, QUAL-002) — `_filter` magic numbers (15, 40, 30) are unexplained. No constants, no tests. Changing them requires guessing.
2.2. [MEDIUM] (source: adversarial-testing, TEST-002) — Regex requires `**` markdown headers. Any Claude Code output format change to single `*`, underlines, or plain text silently breaks extraction.
2.3. [LOW] (source: adversarial-quality, QUAL-004) — Comment at lines 47-49 references `(?=\Z)` bug but patterns use `(?=\n\n|\n\*\*|\Z)` — stale documentation.
2.4. [MEDIUM] (source: adversarial-testing, TEST-007) — User problem search truncates at 500 characters. Problem statements beyond that length are silently missed.

### Missing Obvious Actions / Best Practices

3.1. [HIGH] (source: adversarial-quality, QUAL-001) — Fix extraction loop to access all three `match.group()` values for `_RE_FIX`.
3.2. [HIGH] (source: adversarial-testing, TEST-001) — Add content assertions to semantic extraction tests, not just `len >= 1`.
3.3. [HIGH] (source: adversarial-testing, TEST-003) — Add test for `## Files Changed` extraction pattern.
3.4. [MEDIUM] (source: adversarial-quality, QUAL-003) — Remove unreachable dead code at lines 218-226 in `load_sessions_index`.
3.5. [MEDIUM] (source: adversarial-testing, TEST-004) — Add unit tests for `_filter` function magic numbers.
3.6. [MEDIUM] (source: adversarial-testing, TEST-006) — Split OR assertion in `test_full_pipeline_with_real_transcript` into separate assertions.

### Risks and Edge Cases

4.1. [MEDIUM] (source: adversarial-testing, TEST-005) — `_RE_TOOL` may not extract Windows-style backslash paths.
4.2. [LOW] (source: adversarial-quality, QUAL-007) — Mixed-content entries may accept non-intent text as last_goal.
4.3. [LOW] (source: adversarial-testing, TEST-008) — No graceful degradation test when semantic extraction returns empty.

### Concrete Recommendations

5.1. [HIGH] Update `_RE_FIX` extraction at line 697 to access all groups: `fixes.append((match.group(1) or match.group(2) or match.group(3) or "").lstrip("* "))`
5.2. [HIGH] Strengthen assertions in `test_extracts_problem_pattern`, `test_extracts_fix_pattern`, etc. to verify actual content matches.
5.3. [HIGH] Add test for `## Files Changed` pattern: content containing `## Files Changed\n- path/to/file.py`.
5.4. [MEDIUM] Extract `_filter` magic numbers to named constants with explanatory comments.
5.5. [MEDIUM] Remove dead code block at `load_sessions_index` lines 218-226.
5.6. [MEDIUM] Add `TestFilter` class with unit tests for each filter condition.
5.7. [MEDIUM] Split OR assertion in integration test into separate content assertions.

### Open Questions / Unknowns

6.1. [LOW] (source: adversarial-logic) — The work.md was minimal. Is there more context about what the original bug was that triggered the regex fixes?
6.2. [LOW] (source: adversarial-testing, TEST-002) — Is there a format contract document for Claude Code output? Should semantic extraction patterns be parameterized?
