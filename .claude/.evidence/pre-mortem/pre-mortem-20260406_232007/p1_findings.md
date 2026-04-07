# Phase 1 Findings: skill_forced_eval Re-enablement

## Triage Classification
**hook + code** — The target involves hook registration changes in registry.py, Python source code modifications in skill_forced_eval.py (sys.path manipulation), and symlink replacement of skill_execution_state.py.

## Dispatched Specialists
- **adversarial-security**: Symlink security, sys.path manipulation, import path injection
- **adversarial-logic**: Hook registration ordering, import sequencing, conditional logic
- **adversarial-io-validation**: Path validation, state file operations, symlink I/O
- **adversarial-compliance**: Module path schema, package structure, registration contract

---

## Specialist Findings Summary

### adversarial-security
**Domain:** Security vulnerabilities in symlink handling, path manipulation, import integrity

**Key findings:**
- [MEDIUM] SEC-001 — Symlink target path injection via drive letter normalization (/p/ vs P:/) (skill_execution_state.py symlink)
- [LOW] SEC-002 — sys.path manipulation without namespace protection (skill_execution_state.py:280)
- [LOW] SEC-004 — Arbitrary skill_name used in filesystem path construction without validation (skill_execution_state.py:186)
- [INFO] SEC-003 — No symlink validation or integrity checking (symlinked files)

### adversarial-logic
**Domain:** Logic errors in hook registration, import ordering, conditional checks

**Key findings:**
- [HIGH] LOGIC-001 — Hook registration ordering inversion — skill_forced_eval (priority 0.5) registered AFTER core hooks despite requiring early execution (registry.py:690-697)
- [MEDIUM] LOGIC-002 — Conditional sys.path.insert without duplicate check creates path shadowing (skill_forced_eval.py:26-28)
- [LOW] LOGIC-003 — Package directory sys.path manipulation at module import time creates non-deterministic ordering (registry.py:40-47)

### adversarial-io-validation
**Domain:** I/O operations, state file handling, directory operations

**Key findings:**
- [HIGH] IO-005 — Symlink-based module import without target validation (registry.py:40-47, skill_execution_state.py symlink)
- [MEDIUM] IO-001 — TOCTOU race condition in state file write (skill_forced_eval.py:318-326)
- [MEDIUM] IO-003 — mtime-based TTL validation vulnerable to clock skew (skill_forced_eval.py:353-358, 407-410)
- [MEDIUM] IO-007 — sys.path manipulation at module import time (registry.py:40-47)
- [LOW] IO-002 — Directory iteration doesn't handle permission errors (skill_forced_eval.py:82-105)
- [LOW] IO-004 — File read operations lack explicit encoding error handling (skill_forced_eval.py:154-156, 349)
- [LOW] IO-006 — State directory creation has hidden fallback (skill_forced_eval.py:55-63)

### adversarial-compliance
**Domain:** Package structure compliance, hook registration contract, module path schema

**Key findings:**
- [CRITICAL] COMP-001 — Module path schema violation — package imports hooks but isn't a hook (skill_forced_eval.py:35-37)
- [HIGH] COMP-002 — Manual sys.path manipulation bypasses package structure (skill_forced_eval.py:26-28)
- [HIGH] COMP-003 — Hook registration uses package path but module structure is invalid (registry.py:693-697)
- [MEDIUM] COMP-004 — Zero test coverage despite QA findings from 2026-04-02
- [MEDIUM] COMP-005 — Previous compliance issues UNRESOLVED (tilde paths, directory creation) (skill_forced_eval.py:40-43)
- [MEDIUM] COMP-006 — Duplicate module creates maintenance burden (exists in both hooks/ and packages/)
- [LOW] COMP-007 — sys.path manipulation comment doesn't justify architectural violation (skill_forced_eval.py:24-25)

---

## Consolidated Findings

### Logical Gaps & Inconsistencies

1.1. [HIGH] (source: adversarial-logic) — Hook registration ordering inversion breaks skill enforcement layer system (registry.py:690-697, skill_forced_eval.py:420)
   - **Problem:** skill_forced_eval has priority=0.5 but is registered AFTER core hooks via _try_import_hook(), potentially executing after skill_enforcer
   - **Impact:** Violates documented layer order where skill_forced_eval should enumerate skills before skill_enforcer processes invocation

1.2. [MEDIUM] (source: adversarial-logic) — sys.path.insert without duplicate check creates path shadowing (skill_forced_eval.py:26-28)
   - **Problem:** Checks exact string match but doesn't detect parent/child path conflicts
   - **Impact:** Import shadowing could resolve to wrong module if multiple hooks directories exist

1.3. [CRITICAL] (source: adversarial-compliance) — Module path schema violation (skill_forced_eval.py:35-37)
   - **Problem:** Package module lives in packages/skill-guard/ but imports from UserPromptSubmit_modules and __lib
   - **Impact:** Package cannot be installed via pip — imports fail outside P:/.claude context

1.4. [HIGH] (source: adversarial-compliance) — Manual sys.path manipulation bypasses package structure (skill_forced_eval.py:26-28)
   - **Problem:** Direct sys.path manipulation instead of proper package dependency management
   - **Impact:** Fragile import chain breaks if hooks directory moves or path order changes

1.5. [MEDIUM] (source: adversarial-compliance) — Duplicate module creates maintenance burden
   - **Problem:** skill_forced_eval exists in both P:/.claude/hooks/UserPromptSubmit_modules/ AND P:/packages/skill-guard/src/skill_guard/
   - **Impact:** Edits to wrong file don't take effect, debugging confusion

1.6. [MEDIUM] (source: adversarial-compliance) — Previous compliance issues UNRESOLVED (skill_forced_eval.py:40-43)
   - **Problem:** COMP-003 (tilde paths) and COMP-004 (directory creation) from prior review not addressed
   - **Impact:** Skills directory resolution may be wrong on Windows with P: drive setup

### Hidden Assumptions & Fragile Dependencies

2.1. [MEDIUM] (source: adversarial-io-validation) — TOCTOU race condition in state file write (skill_forced_eval.py:318-326)
   - **Problem:** Directory could be deleted between mkdir() and write(), causing silent state capture failure
   - **Impact:** Compact immunity feature fails without indication

2.2. [LOW] (source: adversarial-logic) — Package directory sys.path manipulation at module import time (registry.py:40-47)
   - **Problem:** Multi-terminal scenarios race on sys.path.insert(0, ...), creating non-deterministic import ordering
   - **Impact:** Intermittent bugs depending on session load order

2.3. [HIGH] (source: adversarial-io-validation) — Symlink-based module import without target validation
   - **Problem:** skill_execution_state.py symlink could point to arbitrary code if filesystem compromised
   - **Impact:** Local attacker could load malicious code with hook system privileges

2.4. [MEDIUM] (source: adversarial-io-validation) — sys.path manipulation at module import time (registry.py:40-47)
   - **Problem:** sys.path.insert(0, ...) happens at module load time, creating race condition
   - **Impact:** Non-deterministic import ordering in multi-terminal scenarios

2.5. [MEDIUM] (source: adversarial-io-validation) — mtime-based TTL validation vulnerable to clock skew (skill_forced_eval.py:353-358)
   - **Problem:** File mtime compared to time.time() without monotonic clock check
   - **Impact:** Fresh state files deleted if system clock changes backward

2.6. [LOW] (source: adversarial-io-validation) — State directory creation has hidden fallback (skill_forced_eval.py:55-63)
   - **Problem:** _get_state_dir() silently falls back to _FALLBACK_STATE_DIR without logging
   - **Impact:** Terminal isolation breaks — different terminals use different state directories

### Missing Obvious Actions / Best Practices

3.1. [HIGH] (source: adversarial-compliance) — Zero test coverage despite critical QA findings from 2026-04-02
   - **Problem:** QA-001 identified ZERO test coverage; re-enablement added sys.path fixes but no tests
   - **Impact:** All four QA failure modes still untested — regression goes undetected

3.2. [MEDIUM] (source: adversarial-security) — Symlink target path injection via drive letter normalization
   - **Problem:** Symlink uses lowercase /p/ path, manipulable on case-sensitive filesystems
   - **Impact:** Arbitrary code execution if symlink target replaced with malicious file

3.3. [LOW] (source: adversarial-io-validation) — Directory iteration doesn't handle permission errors (skill_forced_eval.py:82-105)
   - **Problem:** iterdir() may raise PermissionError, crashing the hook
   - **Impact:** Hook crashes on permission issues, poor error messages

3.4. [LOW] (source: adversarial-io-validation) — File read operations lack explicit encoding error handling (skill_forced_eval.py:154-156)
   - **Problem:** UnicodeDecodeError caught by generic handler, no distinction from file missing
   - **Impact:** Cannot diagnose 'file missing' vs 'file corrupted'

### Risks and Edge Cases

4.1. [MEDIUM] (source: adversarial-compliance) — sys.path manipulation comment doesn't justify architectural violation
   - **Problem:** Comment describes workaround instead of fixing root cause
   - **Impact:** Workaround treated as acceptable pattern — technical debt accumulates

4.2. [LOW] (source: adversarial-security) — sys.path manipulation without namespace protection (skill_execution_state.py:280)
   - **Problem:** sys.path.insert(0, ...) without checking if module already exists elsewhere
   - **Impact:** Import confusion could load wrong module

4.3. [LOW] (source: adversarial-security) — Arbitrary skill_name used in filesystem path construction (skill_execution_state.py:186)
   - **Problem:** No validation that skill_name doesn't contain path traversal components
   - **Impact:** Path traversal could expose skill metadata from other skills

### Concrete Recommendations

5.1. [CRITICAL] (source: adversarial-compliance) — Move skill_forced_eval to P:/.claude/hooks/UserPromptSubmit_modules/ OR create proper package structure with own dependencies
   - **Action:** Decide canonical location — if keeping packages/, remove hooks/ dependency; if keeping hooks/, move file

5.2. [HIGH] (source: adversarial-logic) — Move skill_forced_eval registration into core_hook_modules list OR verify skill_enforcer priority >0.5
   - **Action:** Ensure priority ordering by registration sequence or verify priority values

5.3. [HIGH] (source: adversarial-io-validation) — Add module-level integrity check for symlink targets
   - **Action:** Verify __file__ resolves to expected P:/packages/skill-guard/ path after import

5.4. [MEDIUM] (source: adversarial-io-validation) — Wrap state file write in retry loop or raise warning on failure
   - **Action:** Handle directory deletion between mkdir and write, make failure observable

5.5. [MEDIUM] (source: adversarial-io-validation) — Add monotonic clock check for TTL validation
   - **Action:** If mtime > time.time(), treat file as fresh (not stale)

5.6. [MEDIUM] (source: adversarial-compliance) — Delete duplicate module — decide canonical location (hooks/ or packages/)
   - **Action:** Remove one of the two skill_forced_eval.py files

5.7. [MEDIUM] (source: adversarial-security) — Use absolute Windows paths for symlinks OR verify symlink target integrity
   - **Action:** Change symlink to use Windows path P:/packages/... (not /p/)

5.8. [MEDIUM] (source: adversarial-compliance) — Create tests/test_skill_forced_eval.py before deploying
   - **Action:** Address QA-001 through QA-008 from qa-findings-skill-forced-eval.json

### Open Questions / Unknowns

6.1. [HIGH] (source: adversarial-logic) — What is skill_enforcer's priority? If >0.5, LOGIC-001 is not a bug (skill_enforcer.py needs verification)

6.2. [MEDIUM] (source: adversarial-logic) — Why was skill_forced_eval disabled on 2026-04-03? Understanding original breakage informs whether current fix addresses root cause

6.3. [LOW] (source: adversarial-logic) — Are there tests verifying hook execution order? Without order tests, priority-based systems prone to regression

6.4. [MEDIUM] (source: adversarial-io-validation) — What is expected failure mode for state file writes? Current code silently fails — is that intentional?

6.5. [MEDIUM] (source: adversarial-io-validation) — Are there integration tests for multi-terminal isolation with state directory fallback?

6.6. [MEDIUM] (source: adversarial-io-validation) — Why use symlinks instead of proper Python package installation?

6.7. [LOW] (source: adversarial-io-validation) — Why doesn't TTL use monotonic time (time.monotonic()) to avoid clock skew?

6.8. [HIGH] (source: adversarial-compliance) — Which location is source of truth — P:/.claude/hooks/ or P:/packages/skill-guard/?

6.9. [MEDIUM] (source: adversarial-compliance) — If skill-guard is pip-installable, why does it import UserPromptSubmit_modules directly?

6.10. [MEDIUM] (source: adversarial-compliance) — Verify Path.home() expands correctly on Windows with P: drive setup

---

**Specialist Completion Status:** All 4 specialists completed successfully with valid JSON findings.
