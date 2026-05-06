## Triage Classification
code — Python bug fixes in the /ai-pcli skill (parallel_llm.py, ai_cli.py, SKILL.md, reference stubs)

## Dispatched Specialists
- adversarial-logic: pure logic correctness of each fix
- adversarial-io-validation: file I/O, path validation, external calls
- adversarial-quality: maintainability, soundness, tech debt
- adversarial-testing: test coverage, missing scenarios

## Specialist Findings Summary

### adversarial-logic
**Domain:** Boolean logic, conditional branches, regex patterns
**Key findings:**
- LOGIC-001 [LOW]: is_pi detection is correct — cmd_name extraction is consistent with intent
- LOGIC-002 [LOW]: PTY noise filter "Warning:" addition is correct; minor edge case where real "Warning:" stderr would be treated as noise (very rare)
- LOGIC-003 [LOW]: TimeoutError isinstance guard already in place (pre-existing fix)
- LOGIC-004 [LOW]: regex "Nice to have" fix is correct
- LOGIC-005 [LOW]: ling-2.6-1t-free alias addition is trivially correct
- LOGIC-006 [MEDIUM]: SKILL.md config path change may break migration — old path ai-cli-recipe.json may exist with user data; new path ai-pcli-recipe.json may not exist yet

### adversarial-io-validation
**Domain:** Path validation, file operations, external calls
**Key findings:** No significant issues found. Config path fix is correct. Stub reference files cause no I/O harm. No TOCTOU bugs found.

### adversarial-quality
**Domain:** Maintainability, structural quality, best practices
**Key findings:** All 6 bug fixes are technically sound. Stub reference files are appropriate placeholders. No maintainability concerns.

### adversarial-testing
**Domain:** Test coverage, missing scenarios
**Key findings:**
- TEST-PCLI-001 [HIGH]: No test for is_pi detection (cmd_name="pi" vs "pi:kimi" variants)
- TEST-PCLI-002 [HIGH]: No test for PTY noise filter "Warning:" classification
- TEST-PCLI-003 [HIGH]: No test for TimeoutError handler (terminate/kill sequence)
- TEST-PCLI-004 [HIGH]: No test for priority section regex parsing in _aggregate_llm_results
- TEST-PCLI-005 [MEDIUM]: No test for ling-2.6-1t-free alias resolution
- TEST-PCLI-006 [MEDIUM]: No test for _load_ai_cli_config missing/malformed file handling
- TEST-PCLI-007 [LOW]: No integration test for quota fallback chain
- TEST-PCLI-008 [LOW]: No boundary tests for calc_timeout

## Consolidated Findings

### Logical Gaps & Inconsistencies
1.1. [LOW] (source: adversarial-logic) — PTY noise filter treats any "Warning:" as PTY noise (line 255). A real stderr containing only "Warning:" (extremely rare) would be misclassified. Low risk because real warnings always have context text.

### Hidden Assumptions & Fragile Dependencies
2.1. [MEDIUM] (source: adversarial-logic) — SKILL.md config path change from ai-cli-recipe.json to ai-pcli-recipe.json assumes the new path exists or will be created. If users previously saved config via /ai-cli (sibling skill), their config is at the old path and invisible to /ai-pcli. The config display currently shows "No saved configuration found" for both missing old and new paths — no graceful fallback.

### Missing Obvious Actions / Best Practices
3.1. [HIGH] (source: adversarial-testing) — Zero test coverage for all 7 bug fix code paths. Existing tests (2 files, 7 cases) cover only OpenCode model aliases — pi alias resolution, PTY noise filtering, TimeoutError handling, and regex parsing are completely untested.
3.2. [HIGH] (source: adversarial-testing) — No parametrized test for is_pi detection covering "pi" and "pi:kimi" variants
3.3. [HIGH] (source: adversarial-testing) — No test for PTY noise filter "Warning:" classification with mock subprocess
3.4. [HIGH] (source: adversarial-testing) — No test for TimeoutError handler termination sequence
3.5. [HIGH] (source: adversarial-testing) — No test for _aggregate_llm_results priority section regex parsing
3.6. [MEDIUM] (source: adversarial-testing) — No test for ling-2.6-1t-free alias resolution
3.7. [MEDIUM] (source: adversarial-testing) — No test for _load_ai_cli_config missing/malformed file handling

### Risks and Edge Cases
4.1. [LOW] (source: adversarial-logic) — If future code changes cmd_name to be set from resolved executable path (not command[0]), is_pi detection would break silently. The current design is intentional but fragile to refactoring.
4.2. [LOW] (source: adversarial-testing) — calc_timeout boundary conditions (0KB, 1MB, 2MB) are untested

### Concrete Recommendations
5.1. [HIGH] Add parametrized test for is_pi detection (adversarial-testing)
5.2. [HIGH] Add mock test for PTY noise filter "Warning:" classification (adversarial-testing)
5.3. [HIGH] Add test for TimeoutError handler terminate/kill sequence (adversarial-testing)
5.4. [HIGH] Add test for _aggregate_llm_results priority section regex (adversarial-testing)
5.5. [MEDIUM] Add test for ling-2.6-1t-free alias resolution (adversarial-testing)
5.6. [MEDIUM] Add test for _load_ai_cli_config file missing/malformed handling (adversarial-testing)
5.7. [MEDIUM] Consider adding fallback from ai-pcli-recipe.json to ai-cli-recipe.json in config loading (adversarial-logic)

### Open Questions / Unknowns
6.1. [LOW] (source: adversarial-logic) — Does P:/claude/ai-cli-recipe.json exist with actual user config? If so, migrating to new path should be considered.
6.2. [LOW] (source: adversarial-logic) — Was ai-cli-recipe.json ever populated, or has it always been absent?
