# GTO Analysis Report: search-research

**Generated:** 2026-03-26 22:28:43
**Project Root:** `P:\packages\search-research`
**Analysis Type:** Monorepo subdirectory (viability check bypassed)

## Health Score

- **Overall:** 56.0%
- **Status:** warning
- **Metrics:** 4 dimensions
  - **test_coverage:** 7.8%
  - **documentation:** 39.9%
  - **dependencies:** 80.0%
  - **code_quality:** 99.9%

## Summary

- **Total Gaps:** 14
- **Critical:** 0
- **High:** 2
- **Medium:** 0
- **Low:** 12

## Gaps by Category

### code_marker

- [LOW] Code marker found: unknown (P:\packages\search-research\API_DIFFERENCES.md:200)
- [LOW] Code marker found: unknown (P:\packages\search-research\LOGGING_TEST_SUMMARY.md:39)
- [LOW] Code marker found: unknown (P:\packages\search-research\core\security.py:201)
- [LOW] Code marker found: unknown (P:\packages\search-research\skills\all\complete_three_layer_implementation.py:84)
- [LOW] Code marker found: unknown (P:\packages\search-research\skills\all\search_executor.py:93)
- ... and 7 more

### dependency_missing

- [HIGH] Imported but not declared in dependencies (None:None)

### missing_test

- [HIGH] Missing test for P:\packages\search-research\src\daemons\unified_semantic_daemon.py — expected P:\packages\search-research\tests\src\daemons\test_unified_semantic_daemon.py (None:None)

## Recommended Next Steps


### Tests

1. 1.1 [GAP-0000-TEST] [~22min] Missing test for P:\packages\search-research\src\daemons\unified_semantic_daemon.py — expected P:\packages\search-research\tests\src\daemons\test_unified_semantic_daemon.py


### Code_Quality

2. 1.2 [GAP-0000-DEPENDENCY] [~22min] Imported but not declared in dependencies
3. 1.3 [GAP-0000-CODE_MARKER] [~2min] Code marker found: unknown (P:\packages\search-research\API_DIFFERENCES.md:200)
4. 1.4 [GAP-0002-CODE_MARKER] [~2min] Code marker found: unknown (P:\packages\search-research\LOGGING_TEST_SUMMARY.md:39)
5. 1.5 [GAP-0004-CODE_MARKER] [~2min] Code marker found: unknown (P:\packages\search-research\core\security.py:201)
6. 1.6 [GAP-0005-CODE_MARKER] [~2min] Code marker found: unknown (P:\packages\search-research\skills\all\complete_three_layer_implementation.py:84)
7. 1.7 [GAP-0007-CODE_MARKER] [~2min] Code marker found: unknown (P:\packages\search-research\skills\all\search_executor.py:93)
8. 1.8 [GAP-0008-CODE_MARKER] [~2min] Code marker found: unknown (P:\packages\search-research\core\chs\critical.py:26)
9. 1.9 [GAP-0009-CODE_MARKER] [~2min] Code marker found: unknown (P:\packages\search-research\core\cks\unified.py:235)
10. 1.10 [GAP-0010-CODE_MARKER] [~2min] Code marker found: unknown (P:\packages\search-research\core\cks\commands\cks_migrate.py:574)
11. 1.11 [GAP-0011-CODE_MARKER] [~2min] Code marker found: unknown (P:\packages\search-research\core\cks\integration\cks_integration_module.py:1642)
12. 1.12 [GAP-0016-CODE_MARKER] [~2min] Code marker found: unknown (P:\packages\search-research\core\cks\integration\commands\cks_knowledge_integration.py:860)
13. 1.13 [GAP-0017-CODE_MARKER] [~2min] Code marker found: unknown (P:\packages\search-research\core\backends\local\lsp_backend.py:56)
14. 1.14 [GAP-0018-CODE_MARKER] [~2min] Code marker found: unknown (P:\packages\search-research\contrib\semantic_daemon\daemon_client.py:42)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

0 - Do ALL Recommended Next Actions (14 items)
    Total estimated effort: 1.1 hours
