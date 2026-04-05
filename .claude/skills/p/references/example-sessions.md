# Example Sessions

## Session 1: P1 Success - Tests passing

```
User: /p src/module.py

/p: Detected: Tests exist, 1 file changed
     -> Running P1 (Build)...

[P1] Starting Build...

## Detection
- Scope: src/module.py
- Tests: 42 tests found
- Changed files: 1

## Test Results
42 passed (3.2s)
0 failed
2 warnings (unused imports)

## Coverage
- Line: 87%
- Branch: 76%

---

[P1] Complete: Build
   Tests passing (42/42), 3.2s

### Next Steps

Select an action:
0 -- `/p` -- Continue to P2 (Review)
1 -- `/p --phase=2` -- Run Review only
```

## Session 1b: P2 Success - Review complete (no blocking findings)

```
User: /p src/module.py

/p: Detected: Tests pass, not yet reviewed
     -> Running P2 (Review): Adversarial analysis...

[P2] Starting Review...

## Analysis Scope
- **Target**: src/module.py (245 LOC)
- **Review Mode**: Standard (all 7 agents)
- **Quick Mode**: No (full scope)

## Review Execution
| Agent | Status | Duration |
|-------|--------|----------|
| Security | Complete | 12.3s |
| Performance | Complete | 8.1s |
| Quality | Complete | 15.7s |
| Testing | Complete | 6.4s |
| Compliance | Complete | 9.2s |
| QA | Complete | 11.5s |
| RCA | Complete | 7.8s |

## Findings Summary
- **CRITICAL**: 0 (blocking)
- **HIGH**: 0 (blocking)
- **MEDIUM**: 3 (non-blocking)
- **LOW**: 7 (non-blocking)

## Remaining Issues (Non-blocking)

### MEDIUM
1. PERF-001: N+1 query pattern in fetch_users() - src/module.py:89
2. QUAL-001: Missing docstring for private method _calculate() - src/module.py:134
3. QUAL-002: Inconsistent variable naming (is_active vs isActive) - src/module.py:45

### LOW (7 findings)
See full report: `.claude/findings/adversarial-review-{terminal_id}.json`

---

[P2] Complete: Review
   No blocking findings. 3 MEDIUM, 7 LOW non-blocking issues.

### Next Steps

Choose an action:
0 -- `/p` -- Continue to P3 (Validate) (recommended)
1 -- `/tdd Fix MEDIUM` -- Fix 3 MEDIUM severity findings
2 -- `/tdd Fix LOW` -- Fix 7 LOW severity findings
```

## Session 2: P2 HALT - Blocking findings remain

```
User: /p

/p: Detected: Tests pass, not yet reviewed
     -> Running P2 (Review): Adversarial analysis...
     -> 1 CRITICAL finding (security)
     -> 2 HIGH findings (error handling)
     -> Running TDD loop to fix...
     -> CRITICAL finding remains after fix loop

## Pipeline Status: HALTED

**Status:** HALTED at Phase 2

**Reason:** 1 CRITICAL security finding remains

**Phase Results:**
- Phase 1: Build - PASS
- Phase 2: Review - HALTED

---

### Blocking Findings

1. SEC-001: SQL injection in query_builder() (CRITICAL) - src/db.py:156
2. ERR-001: Missing exception handler in parse_config() (HIGH) - src/config.py:89
3. ERR-002: Uncaught ValueError in validate_input() (HIGH) - src/validate.py:34

### Next Steps

Choose an action:
0 -- `/tdd Fix CRITICAL` -- Fix 1 CRITICAL security finding (recommended)
1 -- `/tdd Fix HIGH` -- Fix 2 HIGH error handling findings
2 -- `/tdd Fix all` -- Fix all findings (iterative fixing loop)

After fixing, re-run: `/p`
```

## Session 2c: P3 Success - Validation complete

```
User: /p src/module.py

/p: Detected: Reviewed, not yet validated
     -> Running P3 (Validate): validation pipeline (15+ stages)...

[P3] Starting Validate...

## Stage Results

### Blocking Stages (must pass)
| Stage | Status | Duration | Notes |
|-------|--------|----------|-------|
| 1.0 Syntax | PASS | 0.8s | No syntax errors |
| 1.5 Naming | PASS | 1.2s | PEP8 compliant |
| 2.0 Type Check | PASS | 3.4s | No type errors |
| 2.2 Integration | PASS | 2.1s | All imports resolve |
| 2.7 Security | PASS | 2.3s | No security issues |
| 3.0 Coverage | PASS | 1.8s | 87% line coverage |

### Non-Blocking Stages (warnings allowed)
| Stage | Status | Findings | Notes |
|-------|--------|----------|-------|
| 2.8 Formatting | WARN | 3 | Line length > 88 |
| 2.9 Duplication | WARN | 1 | Similar code block |

## Summary
- **Blocking Stages**: 12/12 PASS
- **Non-Blocking Warnings**: 6 findings (can proceed)

---

[P3] Complete: Validate
   All blocking stages pass (12/12). 6 non-blocking warnings.

### Next Steps

Select an action:
0 -- `/p` -- Continue to P4 (Publish)
1 -- `/p --fix` -- Auto-fix safe formatting issues
```

## Session 2d: P4 Success - Publish complete

```
User: /p src/module.py

/p: Detected: Validated, no README
     -> Running P4 (Publish): README generation...

## Generated Artifacts
- README.md (usage, installation, API) - Created
- LICENSE (MIT license) - Created
- CHANGELOG.md (version history) - Created

---

[P4] Complete: Publish
   Documentation generated (3 files).

### Next Steps

Select an action:
0 -- `/p` -- Continue to P5 (Certify)
1 -- `cat README.md` -- Review generated documentation
```

## Session 2e: P5 Success - Certification complete

```
User: /p src/module.py

/p: Detected: Published, not certified
     -> Running P5 (Certify): Production QA...

## QA Checklist
- [x] All tests passing (42/42)
- [x] Coverage threshold met (87%)
- [x] README.md present and complete
- [x] LICENSE file present
- [x] No uncommitted changes

## Certification Result
**Status**: PRODUCTION READY
**Certificate ID**: cert-20260217-src_module_py

---

[P5] Complete: Certify
   Production-ready. Added to portfolio index.

### Next Steps

Select an action:
0 -- `/p` -- Continue to P6 (Security scan)
1 -- `/portfolio` -- Generate portfolio artifacts
2 -- `git push` -- Deploy to production
```

## Session 3: Complete Pipeline

```
User: /p

/p: Detected: Reviewed, not yet validated
     -> Running P3 (Validate): All stages pass
     -> Running P4 (Publish): README generated
     -> Running P5 (Certify): Added to portfolio index

## Pipeline Status: COMPLETE

**Status:** ALL PHASES PASSED

**Phase Results:**
- Phase 1: Build - PASS
- Phase 2: Review - PASS (3 findings fixed)
- Phase 3: Validate - PASS
- Phase 4: Publish - PASS
- Phase 5: Certify - PASS

**Summary:** Code is production-ready, added to portfolio index

### Next Steps

1. Commit changes: `git commit`
2. Push to remote: `git push`
```
