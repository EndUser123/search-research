# Implementation Plan: Documentation Enhancements Phase 2

## Task Breakdown

### Phase 1: Core Infrastructure (2 tasks, 30 min)

1. **Create new module files** (15 min)
   - Create `doc_coverage.py`
   - Create `docstring_checker.py`
   - Create `doc_preview.py`
   - Create `doc_search.py`
   - Create `api_changelog.py`
   - Create `doc_linter.py`

2. **Update doc_command.py with flags** (15 min)
   - Add `--coverage-report`, `--coverage-module`
   - Add `--check-docstrings`, `--docstring-style`
   - Add `--preview`, `--validate-links`
   - Add `--search`
   - Add `--api-diff`
   - Add `--lint`
   - Add handler methods for each flag

### Phase 2: Implementation (12 tasks, 3.5 hours)

3. **Implement DocCoverageReporter** (30 min)
   - `__init__` with caching
   - `generate_coverage_report()` using AST
   - `get_undocumented_apis()`
   - Public API detection (`_is_public`)
   - Output formatting (JSON/TTY)

4. **Implement DocstringQualityChecker** (45 min)
   - `__init__` with style detection
   - `check_file()` AST walking
   - Placeholder detection
   - Format validation (Google/NumPy/Sphinx)
   - Section checking (Args, Returns, Raises)
   - Suggestion generation

5. **Implement DocPreviewGenerator** (30 min)
   - `__init__` with markdown check
   - `generate_preview()` with markdown package
   - `validate_for_preview()` using XRefValidator
   - Code block validation
   - Fallback for missing markdown package

6. **Implement CKSDocumentationSearch** (30 min)
   - `__init__` with CKS initialization
   - `search()` method
   - `semantic_search()` with query expansion
   - Result formatting with excerpts
   - Graceful fallback when CKS unavailable

7. **Implement APIChangelogGenerator** (60 min)
   - `__init__` with summarizer
   - `generate_diff()` git diff parsing
   - `detect_breaking_changes()` signature comparison
   - `compare_docstrings()` doc diff detection
   - ChangelogEntry formatting

8. **Implement DocumentationLinter** (60 min)
   - `__init__` with config
   - `lint_file()` main method
   - `check_spelling()` with pyspellchecker
   - `validate_structure()` heading checks
   - Terminology validation
   - Fallback when dependencies missing

### Phase 3: Integration (2 tasks, 45 min)

9. **Wire up CLI handlers** (30 min)
   - `_coverage_report_handler()`
   - `_check_docstrings_handler()`
   - `_preview_handler()`
   - `_search_handler()`
   - `_api_diff_handler()`
   - `_lint_handler()`

10. **Output formatting** (15 min)
    - Table formatter for TTY output
    - JSON formatter for machine output
    - Error message formatting
    - Progress indicators for long operations

### Phase 4: Testing (6 tasks, 60 min)

11. **Test DocCoverageReporter** (10 min)
    - Test coverage calculation accuracy
    - Test public/private detection
    - Test module aggregation

12. **Test DocstringQualityChecker** (10 min)
    - Test placeholder detection
    - Test format validation
    - Test missing section detection

13. **Test DocPreviewGenerator** (10 min)
    - Test markdown rendering
    - Test link validation
    - Test fallback behavior

14. **Test CKSDocumentationSearch** (10 min)
    - Test search query execution
    - Test CKS unavailable handling
    - Test result formatting

15. **Test APIChangelogGenerator** (15 min)
    - Test diff parsing
    - Test breaking change detection
    - Test signature comparison

16. **Test DocumentationLinter** (15 min)
    - Test spell checking
    - Test structure validation
    - Test terminology enforcement
    - Test fallback behavior

## Dependencies

```
Phase 2 (Implementation) depends on:
  ├── Phase 1 (Infrastructure) - must complete first

Phase 3 (Integration) depends on:
  ├── Phase 2 (Implementation) - all implementations ready

Phase 4 (Testing) depends on:
  ├── Phase 3 (Integration) - integration complete
```

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| CKS API different than expected | Test early, have fallback |
| AST parsing edge cases | Use proven patterns from research |
| Large codebase performance | Add caching, show progress |
| Optional deps missing | Graceful degradation tested |

## Success Criteria

1. All 6 features accessible via `/doc` flags
2. Each feature returns meaningful output
3. CKS integration uses existing infrastructure
4. Optional dependencies degrade gracefully
5. Tests provide >80% coverage
6. No regressions in existing `/doc` functionality

## Implementation Order

The features can be implemented in parallel order:

| Batch | Features | Can Parallelize? |
|-------|----------|------------------|
| Batch 1 | Coverage, Docstring Checker | Yes (different modules) |
| Batch 2 | Preview, Search | Yes (different modules) |
| Batch 3 | API Diff, Linter | Yes (different modules) |

## Estimated Timeline

| Phase | Tasks | Time |
|-------|-------|------|
| Phase 1 | 2 tasks | 30 min |
| Phase 2 | 6 tasks | 3.5 hours |
| Phase 3 | 2 tasks | 45 min |
| Phase 4 | 6 tasks | 60 min |
| **Total** | **16 tasks** | **5-6 hours** |

## Rollout Plan

1. Implement Batch 1 (Coverage, Docstring)
2. Test and verify
3. Implement Batch 2 (Preview, Search)
4. Test and verify
5. Implement Batch 3 (API Diff, Linter)
6. Full integration test
7. Update documentation

## Post-Implementation

1. Update `/doc` help text
2. Add examples for each new flag
3. Update CHANGELOG.md
4. Consider adding to lazy mode suggestions
