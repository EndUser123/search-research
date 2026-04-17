# Package Assessment Plan: search-research

**Created**: 2026-03-26
**Status**: IN PROGRESS
**Goal**: Ensure all features work optimally and identify gaps/opportunities

---

## Phase 1: Discovery & Gap Analysis

### Step 1.1: GTO Analysis (PRIMARY)
**Skill**: `/gto`
**Purpose**: Identify all gaps, tasks, and opportunities
**Command**: `/gto P:/packages/search-research`
**Output**: `.claude/skills/gto/.evidence/gto-outputs/gto-report-latest.md`
**Status**: [x] COMPLETED

**What it finds:**
- Feature gaps (missing functionality)
- Test coverage gaps
- Documentation gaps
- Code quality issues
- Integration problems

---

### Step 1.2: Architecture Assessment
**Skill**: `/arch`
**Purpose**: Evaluate architectural decisions and patterns
**Command**: `/arch P:/packages/search-research --focus backends,routing,unified-api`
**Output**: `P:/packages/search-research/.claude/analysis/arch-assessment.md`
**Status**: [x] COMPLETED
**Depends on**: Step 1.1 (prioritize areas flagged by GTO)

---

## Phase 2: Verification

### Step 2.1: Feature Verification
**Skill**: `/verify`
**Purpose**: Confirm critical paths work correctly
**Command**: `/verify P:/packages/search-research --focus features`
**Output**: `P:/packages/search-research/.claude/analysis/verification-report.md`
**Status**: [x] COMPLETED (PARTIAL - 2 issues found, both test bugs not code bugs)

**Key findings** (emitted as RSN, not file write):
- 86/87 router tests pass; 1 failure is test expectation bug (not code bug)
- MCP server tests have import path bug (src/ vs core/)
- Core routers import and function correctly

**RSN findings from /verify**:
```
Recommended Next Steps

1. Missing Obvious Actions / Best Practices
   1a. [HIGH] MCP test import path bug: uses src/ instead of core/ (tests/test_mcp_server.py:14) — Manual fix: 5 min
   1b. [MEDIUM] Test expectation bug: expects empty results but router correctly falls back to web (tests/test_unified_router.py:810) — Manual fix: 5 min

0 — Do ALL Recommended Next Steps
```
**Depends on**: Step 1.1 (verify areas flagged by GTO)

**Critical paths to verify:**
- [ ] SearchRouter (FAST mode)
- [ ] ResearchRouter (COMPREHENSIVE mode)
- [ ] UnifiedRouter (mode switching)
- [ ] All 8 local backends (CDS, Grep, CHS, CKS, KG, RLM, Persona, MultiLang)
- [ ] Web backends (Tavily, Serper, Exa) with graceful degradation
- [ ] MCP server tools (local_search, web_search, unified_search, cks_*)
- [ ] Semantic daemon (Windows named pipe)

---

### Step 2.2: Test Coverage Analysis
**Skill**: `/t`
**Purpose**: Validate test coverage and find gaps
**Command**: `/t P:/packages/search-research --coverage`
**Output**: `P:/packages/search-research/.claude/analysis/test-coverage-report.md`
**Status**: [x] COMPLETED

**Key findings**:
- 1,309 total tests, 32/32 unified router tests pass (100%)
- Overall coverage ~5% (large vendor/integration suite)
- Core router coverage: unified_router 28%, router_async 12%
- Pre-existing MCP server ImportError (3 tests fail)
- Low coverage in `task_manager.py` (0%) and `sync_wrapper.py` (0%) — deprecated wrappers

**RSN findings**:
```
## Recommended Next Steps

### Domain: tests
1.1 [~30min] Fix MCP server import structure — pre-existing ImportError breaks 3 tests (core/mcp_server.py)

### Domain: code_quality
1.2 [~1hr] Increase router_async coverage — 266 lines uncovered (12%), mostly web provider error paths
```

**Depends on**: Step 2.1

---

## Phase 3: Quality Deep-Dive

### Step 3.1: Code Quality Analysis
**Skill**: `/analyze`
**Purpose**: Unified code quality assessment
**Command**: `/analyze P:/packages/search-research --focus maintainability,complexity,dead-code`
**Output**: To be saved to `P:/packages/search-research/.claude/analysis/code-quality-report.md`
**Status**: [ ] PENDING
**Depends on**: Phase 1 & 2 complete

---

### Step 3.2: Adversarial Review (OPTIONAL)
**Skill**: `/adversarial-review`
**Purpose**: 8-agent parallel review for deep issues
**Command**: `/adversarial-review P:/packages/search-research`
**Output**: `.claude/.evidence/critique/critique-YYYYMMDD_HHMMSS/`
**Status**: [ ] PENDING
**Depends on**: Step 3.1
**Note**: Only run if Phase 1-2 surface significant issues

---

## Phase 4: Remediation

### Step 4.1: Apply Simplifications
**Skill**: `/simplify`
**Purpose**: Fix identified code quality issues
**Command**: `/simplify P:/packages/search-research`
**Output**: Git diff of changes
**Status**: [ ] PENDING
**Depends on**: Phase 3 complete

---

### Step 4.2: Final GTO Re-scan
**Skill**: `/gto`
**Purpose**: Find remaining gaps after fixes
**Command**: `/gto P:/packages/search-research --label post-remediation`
**Output**: `.claude/skills/gto/.evidence/gto-outputs/gto-report-latest.md`
**Status**: [ ] PENDING
**Depends on**: Step 4.1

---

## Output Files Summary

| File | Purpose | Created By |
|------|---------|------------|
| `.claude/skills/gto/.evidence/gto-outputs/gto-report-latest.md` | Gap analysis | Step 1.1, 4.2 |
| `.claude/analysis/arch-assessment.md` | Architecture review | Step 1.2 |
| RSN (stdout — no file write) | Feature verification findings | Step 2.1 |
| `.claude/analysis/test-coverage-report.md` | Test coverage | Step 2.2 |
| `.claude/analysis/code-quality-report.md` | Code quality | Step 3.1 |
| `.claude/.evidence/critique/critique-*/` | Adversarial review | Step 3.2 |

**Note**: Step 2.1 (/verify) now outputs RSN format to stdout instead of writing to `.claude/analysis/` files, avoiding path hook confusion across skills.

---

## Execution Order (Optimal)

```
1. /gto     → Map the territory (what's broken/missing)
2. /arch    → Validate design decisions (focused on GTO-flagged areas)
3. /verify  → Confirm features work (focused on GTO-flagged areas)
4. /t       → Validate test coverage
5. /analyze → Deep code quality (if needed)
6. /simplify → Apply fixes
7. /gto     → Re-scan for remaining gaps
```

---

## Success Criteria

- [ ] All critical features verified working
- [ ] Test coverage > 80% for core modules
- [ ] No high-priority gaps remaining
- [ ] Code quality issues resolved
- [ ] Documentation updated to reflect changes

---

## Notes

- Run steps sequentially (each depends on previous findings)
- Skip Step 3.2 (adversarial-review) if Phase 1-2 show no major issues
- Save all outputs to tracked files for implementation follow-up
- Mark each step complete as you progress
