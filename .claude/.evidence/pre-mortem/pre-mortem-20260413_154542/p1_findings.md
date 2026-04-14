# Phase 1 Findings — GTO Test Fixes Session

## Triage Classification
**skill** — GTO v3.1 skill with test suite; work under review is the test-fix session that reduced failures from ~32 to 0 in the GTO test suite.

## Dispatched Specialists
- **adversarial-critic**: Meta-analysis of reasoning quality and process
- **adversarial-compliance**: Import paths, API contracts, schema alignment
- **adversarial-quality**: Maintainability, technical debt, code structure
- **adversarial-testing**: Test coverage, import failures, edge cases

---

## Consolidated Findings

### 1. Logical Gaps & Inconsistencies

1.1. [HIGH] (adversarial-compliance, adversarial-testing) — `adjacent_file_scanner.py:83-86`: `extract_touched_files()` assumes each transcript line has `tool_use` at root level, but valid Claude Code transcripts store `tool_use` inside `turn.content[].type == "tool_use"`. The check `if "tool_use" in turn` always fails on valid transcript format. Result: adjacent file scanner always returns empty list, making Smart Adjacency Scanning (Domain 2) non-functional.
- File: `P:/.claude/skills/gto/__lib/adjacent_file_scanner.py:83-86`

1.2. [HIGH] (adversarial-testing) — `gap_resolution_tracker.py:654-658`: `get_gap_decay_metrics()` uses `replace("Z", "+00:00")` which only handles UTC Z-suffix timestamps. ISO timestamps with other timezone offsets (e.g., `+05:30`, `-08:00`) cause `datetime.fromisoformat()` to throw `ValueError`, silently leaving `days_span = None` even for comparable timestamps.
- File: `P:/.claude/skills/gto/__lib/gap_resolution_tracker.py:654-658`

1.3. [HIGH] (adversarial-testing) — `__lib/__init__.py:115`: `code_marker_scanner` import chains through `scanners.base` from `_shared` package at `~/.claude/skills/_shared/` which does not exist. This causes ALL tests in the suite to fail collection (not just the ones importing gap_resolution_tracker).
- File: `P:/.claude/skills/gto/__lib/__init__.py:115`

1.4. [MEDIUM] (adversarial-compliance, adversarial-quality) — `gap_resolution_tracker.py:419`: Verification records store raw gap IDs (`gap_ids=[gap_id]`) but lookups normalize them via `_normalize_gap_key()`. Raw-stored IDs with ephemeral suffixes (e.g., `TEST-001-1`) won't match normalized lookups, causing repeated re-verification.
- File: `P:/.claude/skills/gto/__lib/gap_resolution_tracker.py:419`

1.5. [MEDIUM] (adversarial-compliance) — `skill_registry_bridge.py:73-79`: `_import_skill_registry` returns `None` inside `ImportError` for CSF without falling through to `_build_fallback_catalog()`. When CSF import fails, the entire skill catalog is empty — GTO skill routing becomes non-functional.
- File: `P:/.claude/skills/gto/__lib/skill_registry_bridge.py:73-79`

1.6. [MEDIUM] (adversarial-quality, adversarial-testing) — `skill_coverage_detector.py:39`: Import uses `from ...__lib.changelog_writer` but `__lib` is a directory without `__init__.py`, so Python's dot-based relative import fails with `ModuleNotFoundError`. The fallback at line 44 is unreachable because the error is caught and `_get_changelog_skills = None` is set silently. CAUSE-004 in work.md: the changelog-based skill de-duplication is broken.
- File: `P:/.claude/skills/gto/__lib/skill_coverage_detector.py:39`

### 2. Hidden Assumptions & Fragile Dependencies

2.1. [MEDIUM] (adversarial-quality) — `adjacent_file_scanner.py:85`: `extract_touched_files()` only checks `tool_use` blocks but not `tool_result` blocks. Files whose path only appears in a `tool_result` (e.g., from a Read tool result) are silently missed, creating incomplete adjacency data.
- File: `P:/.claude/skills/gto/__lib/adjacent_file_scanner.py:85`

2.2. [MEDIUM] (adversarial-testing) — `adjacent_file_scanner.py:91`: Only checks `input_data['file_path']`. Claude Code transcripts may store file paths under `relative_path`, `path`, or nested structures — these are silently skipped.
- File: `P:/.claude/skills/gto/__lib/adjacent_file_scanner.py:91`

2.3. [MEDIUM] (adversarial-testing) — `gap_resolution_tracker.py:262`: Gap resolution tracker imports from `skill_coverage_detector` which has its own changelog path fallback computed relative to itself. When the primary import fails, each module computes paths differently, breaking skill coverage log lookups.
- File: `P:/.claude/skills/gto/__lib/gap_resolution_tracker.py:262`

2.4. [LOW] (adversarial-quality) — `gto_self_health_detector.py:174`: `_compute_gap_trend` has window-size asymmetry. When exactly 3 history entries exist, `prior_avg` uses 1 entry but `recent_avg` uses 2 entries, skewing trend percentage calculation.
- File: `P:/.claude/skills/gto/__lib/gto_self_health_detector.py:174`

### 3. Missing Obvious Actions / Best Practices

3.1. [HIGH] (adversarial-testing) — `adjacent_file_scanner.py:106`: `FileNotFoundError` returns `[]` silently with no logging. Cannot distinguish "no transcript" from "wrong path" — makes diagnostic extremely difficult.
- File: `P:/.claude/skills/gto/__lib/adjacent_file_scanner.py:106`

3.2. [MEDIUM] (adversarial-quality) — `adjacent_file_scanner` not exported in `__lib.__all__`. Internal module used by `skill_coverage_detector` but with no public API declaration. Tests use `sys.path` manipulation to import directly. Creates confusion about contract surface.
- File: `P:/.claude/skills/gto/__lib/__init__.py:8`

3.3. [MEDIUM] (adversarial-testing) — `gap_resolution_tracker.py:86-91`: `_extract_gap_type()` returns `test_001` for single-segment IDs but `test_gap` for others — inconsistent type key spaces cause gap-type matching to misfire in skill effectiveness scoring.
- File: `P:/.claude/skills/gto/__lib/gap_resolution_tracker.py:86-91`

### 4. Risks and Edge Cases

4.1. [MEDIUM] (adversarial-compliance) — CAUSE-001 (adjacent_file_scanner) is a systemic issue affecting Domain 2 of GTO. Multiple agents independently confirmed it. The fix requires changing how transcript lines are parsed, which affects all callers of `extract_touched_files`.

4.2. [LOW] (adversarial-compliance) — COMP-004 comment in `skill_coverage_detector.py:37` says "two levels up" but code uses three dots. The import actually works (comment is wrong, code is correct) — no functional impact but misleading for future maintainers.

4.3. [LOW] (adversarial-testing) — `test_adjacent_file_scanner.py` and `test_gap_resolution_tracker.py` at `P:/.claude/tests/` are smoke tests that only verify import succeeds. They add no functional value and create confusion about test coverage.

### 5. Concrete Recommendations

5.1. Fix `adjacent_file_scanner.py:83-101` to parse each transcript line as a message object and extract `tool_use` from `content` list (see `session_goal_detector.py:97-105` for correct pattern). Also handle `tool_result` blocks and alternative path fields.

5.2. Fix `gap_resolution_tracker.py:419` to normalize gap IDs before storing: `gap_ids=[_normalize_gap_key(gap_id)]`.

5.3. Fix `skill_registry_bridge.py:73-79` to remove `return None` from CSF `ImportError` block, allowing fallthrough to `_build_fallback_catalog()`.

5.4. Fix `skill_coverage_detector.py:39` to use `importlib.util.spec_from_file_location` for the `__lib` directory (since it's not a package) instead of dot-based relative imports.

5.5. Fix `gap_resolution_tracker.py:654-658` to handle all ISO timezone offsets (not just Z suffix) using `dateutil.parser.isoparse` or regex normalization before `fromisoformat`.

5.6. Fix `__lib/__init__.py:115` to wrap `code_marker_scanner` import in `try/except` with graceful degradation, preventing import cascade failures from blocking the entire test suite.

### 6. Open Questions / Unknowns

6.1. [LOW] (adversarial-compliance) — Whether the `tool_result` block structure in Claude Code transcripts is actually `tool_result.type == "tool_use"` or a different schema — needs verification against a real transcript sample.

6.2. [LOW] (adversarial-testing) — Whether the `scanners.base` import path was intended to reference a shared `_shared` package that should exist at `~/.claude/skills/_shared/`, or whether it's a dead import that should be removed.

6.3. [LOW] (adversarial-quality) — Whether `TREND_WINDOW=5` is the correct constant for gap trend computation — the windows (2 vs up-to-4) suggest an unintended asymmetry.

---

## Phase 1 Completion Gate
- [x] All 4 specialist JSONs available
- [x] All 4 completion markers present
- [x] `p1_findings.md` written
**Status: PASS — proceeding to Phase 2**
