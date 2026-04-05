# Implementation Plan: Merge portfolio-media into media-pipeline

**Created:** 2026-03-07
**Status:** DRAFT
**Objective:** Consolidate portfolio-media functionality into media-pipeline, deprecate portfolio-media as separate package

---

## 1. Problem Statement

**Current State:**
- Two packages with overlapping functionality: `portfolio-media` and `media-pipeline`
- `portfolio-media` depends on `media-pipeline>=0.1.0` (discovered in pyproject.toml:13)
- User confusion about which package to use
- Maintenance overhead for two packages with 80% functional overlap

**Desired State:**
- Single unified package (`media-pipeline`) containing all functionality
- `portfolio-media` deprecated with migration guide
- All unique functionality preserved (asset assessment, Perplexity provider)
- Clear CLI entry points for all use cases

**Success Criteria:**
- ✅ All portfolio-media functionality available in media-pipeline
- ✅ Migration guide published for existing users
- ✅ No breaking changes to media-pipeline's existing API
- ✅ All tests passing (including migrated assessment and Perplexity tests)

---

## 2. Context Analysis

### Dependency Relationship

```
portfolio-media (0.1.0)
  └─ depends on → media-pipeline (>=0.1.0)
```

**Evidence:** `P:/packages/portfolio-media/pyproject.toml:13` shows `"media-pipeline>=0.1.0"` as a dependency.

### Functional Overlap Analysis

| Feature | portfolio-media | media-pipeline | Action |
|---------|-----------------|----------------|--------|
| Logo generation | ✅ | ✅ | Keep media-pipeline, migrate CLI |
| Diagram generation | ✅ | ✅ | Keep media-pipeline, migrate CLI |
| Screenshot capture | ✅ | ✅ | Keep media-pipeline, migrate CLI |
| Video generation | ✅ | ✅ | Keep media-pipeline, migrate CLI |
| Repository analysis | ❌ | ✅ | Keep media-pipeline |
| Asset planning | ❌ | ✅ | Keep media-pipeline |
| Execution engine | ❌ | ✅ | Keep media-pipeline |
| Media verification | ❌ | ✅ | Keep media-pipeline |
| Mindmap rendering | ❌ | ✅ | Keep media-pipeline |
| **Asset assessment** | ✅ (304 lines) | ❌ | **MIGRATE to media-pipeline** |
| **Perplexity provider** | ✅ (2.8KB) | ❌ | **MIGRATE to media-pipeline** |

### Allowed APIs

**From source code analysis:**

**media-pipeline exports:**
```python
from media_pipeline.classifier import analyze_repo, classify_repo
from media_pipeline.config import MediaConfig
from media_pipeline.executor import Executor
from media_pipeline.models import PlannedAsset, RepoInfo, RepoType
from media_pipeline.planning import plan_assets, validate_plan
```

**portfolio-media exports (to migrate):**
```python
from portfolio_media.assessment import AssetAssessment, assess_package
from portfolio_media.providers.perplexity import PerplexityProvider
```

### Anti-Patterns to Avoid

- ❌ Breaking existing media-pipeline imports
- ❌ Removing portfolio-media CLI commands without migration path
- ❌ Assuming Perplexity provider has same interface as other providers
- ❌ Forgetting to migrate tests for assessment and Perplexity modules

---

## 3. Existing Implementation Discovery

### Portfolio-Media Structure

**Core modules to migrate:**
```
P:/packages/portfolio-media/src/portfolio_media/
├── assessment.py          # 304 lines - Asset gap detection
├── providers/
│   ├── perplexity.py      # 2,848 bytes - Prompt optimization
│   ├── claude.py          # Already in media-pipeline (skip)
│   ├── gemini.py          # Already in media-pipeline (skip)
│   ├── glm.py             # Already in media-pipeline (skip)
│   ├── notebooklm.py      # Already in media-pipeline (skip)
│   └── openrouter.py      # Already in media-pipeline (skip)
├── cli.py                 # Multiple entry points (refactor, not migrate)
├── logo_generator.py      # Wrapper around media-pipeline (skip)
├── diagram_generator.py   # Wrapper around media-pipeline (skip)
├── screenshot_capture.py  # Wrapper around media-pipeline (skip)
└── video_generator.py     # Wrapper around media-pipeline (skip)
```

**CLI entry points (portfolio-media/pyproject.toml:43-47):**
```toml
portfolio-media = "portfolio_media.cli:main"
portfolio-media-logo = "portfolio_media.logo_generator:generate_logo_cli"
portfolio-media-diagram = "portfolio_media.diagram_generator:generate_diagram_cli"
portfolio-media-screenshot = "portfolio_media.screenshot_capture:capture_screenshot_cli"
```

**Tests to migrate:**
```
P:/packages/portfolio-media/tests/
├── test_assessment.py     # Migrate to media-pipeline/tests/
└── test_perplexity.py     # Migrate to media-pipeline/tests/
```

### Media-Pipeline Structure

**Target location for migrated modules:**
```
P:/packages/media-pipeline/src/media_pipeline/
├── assessment.py          # NEW - from portfolio-media
├── providers/
│   └── perplexity.py      # NEW - from portfolio-media
```

**Target location for tests:**
```
P:/packages/media-pipeline/tests/
├── test_assessment.py     # NEW - from portfolio-media
└── test_perplexity.py     # NEW - from portfolio-media
```

---

## 4. Test Discovery

### Existing Tests

**Portfolio-media tests:**
```bash
# Location: P:/packages/portfolio-media/tests/
test_assessment.py         # Tests for AssetAssessment class
test_perplexity.py         # Tests for Perplexity provider
```

**Media-pipeline tests:**
```bash
# Location: P:/packages/media-pipeline/tests/
test_classifier.py         # Tests for repository analysis
test_planning.py           # Tests for asset planning
test_executor.py           # Tests for execution engine
```

### Test Coverage Requirements

**Must test after migration:**
1. Asset assessment gap detection (logo, banner, diagrams, screenshots, videos)
2. Asset assessment quality scoring
3. Asset assessment recommendations generation
4. Perplexity provider API integration
5. Perplexity provider prompt optimization
6. CLI entry points (new `gen-media-*` commands)
7. Backward compatibility of existing media-pipeline API

---

## 5. Proposed Solution

### Architecture Decision: Merge INTO media-pipeline

**Rationale:**
1. portfolio-media is already dependent on media-pipeline
2. media-pipeline has 80% of functionality (verification, planning, execution)
3. Only 2 unique modules to migrate (assessment.py, perplexity.py)
4. Smaller codebase disruption (preserve media-pipeline structure)

### Module Migration Strategy

**Phase 1: Code Migration**
```python
# Migrate assessment module
P:/packages/media-pipeline/src/media_pipeline/assessment.py
  └─ Copy from P:/packages/portfolio-media/src/portfolio_media/assessment.py
  └─ Update imports to use media_pipeline namespace

# Migrate Perplexity provider
P:/packages/media-pipeline/src/media_pipeline/providers/perplexity.py
  └─ Copy from P:/packages/portfolio-media/src/portfolio_media/providers/perplexity.py
  └─ Update to match provider registry interface
```

**Phase 2: CLI Entry Points**
```toml
# Add to media-pipeline/pyproject.toml [project.scripts]
gen-media-assess = "media_pipeline.assessment:cli"
gen-media-logo = "media_pipeline.providers.logo_providers:cli"
gen-media-diagram = "media_pipeline.providers.notebooklm:cli"
gen-media-screenshot = "media_pipeline.executor:screenshot_cli"
```

**Phase 3: API Updates**
```python
# Add to media_pipeline/__init__.py
from media_pipeline.assessment import AssetAssessment, assess_package
from media_pipeline.providers.perplexity import PerplexityProvider
```

**Phase 4: Deprecation**
```toml
# Add to portfolio-media/pyproject.toml
[project.deprecated]
message = "DEPRECATED: Use media-pipeline instead. Migration guide: https://github.com/media-pipeline/MIGRATING.md"
replacement = "media-pipeline>=0.2.0"
```

---

## 5.5. Verification Review Improvements

**Date:** 2026-03-07
**Reviewer:** Implementation Plan Verifier (PHASE 0-7)
**Status:** All improvements incorporated

### Review Summary

Plan underwent comprehensive 8-phase verification including adversarial stress testing (PHASE 3.5). All 8 phases PASSED with 0 blocking issues and 0 warning issues. Fifteen advisory findings were documented, resulting in 4 actionable improvements below.

### Findings Addressed

**PR-001: Version Increment Strategy** (Priority 2)
- **Issue:** No version increment strategy for media-pipeline after migration
- **Risk:** Users unable to track breaking changes or new features
- **Solution:** Added T-012 to bump version to 0.6.0 (minor) or 1.0.0 (major)
- **Evidence:** Plan now includes version increment with semantic versioning compliance

**PR-002: Perplexity NotImplementedError Documentation** (Priority 3)
- **Issue:** Perplexity provider has `NotImplementedError` for direct image generation (line 48-50)
- **Risk:** Users may encounter unexpected errors without explanation
- **Solution:** Updated T-009 acceptance criteria to document NotImplementedError status
- **Evidence:** Migration guide will now explain which features are not yet implemented

**PR-003: Documentation Ordering** (Priority 2)
- **Issue:** T-008 (README) should precede T-009 (migration guide)
- **Risk:** Users see migration guide before learning about new features
- **Solution:** Execution order updated to sequence README before migration guide
- **Evidence:** Updated execution order diagram shows correct flow

**PR-004: Pre-Archival Announcement** (Priority 3)
- **Issue:** Archiving repository without notice may confuse users
- **Risk:** Sudden loss of issue tracker and PR support
- **Solution:** Added T-013 to create GitHub announcement before archival
- **Evidence:** New task ensures user communication before repository changes

### Adversarial Review Findings (PHASE 3.5)

Stress testing revealed 3 edge cases:
1. **Perplexity NotImplementedError** - addressed in PR-002
2. **No internal dependencies between assessment and Perplexity** - confirmed safe to migrate separately
3. **CLI entry point mapping** - addressed in T-004 with gen-media-* commands

All adversarial findings were below confidence threshold (80%) and addressed through improvements.

### Confidence Level

**Pre-review:** HIGH
**Post-review:** HIGH (maintained)
**Reason:** All improvements incorporated, no blocking issues, comprehensive risk mitigation

---

## 6. Implementation Plan

### Task Breakdown (13 tasks total - includes 2 verification improvements)

**T-001: Migrate assessment module**
- File: `P:/packages/media-pipeline/src/media_pipeline/assessment.py`
- Action: Copy assessment.py from portfolio-media, update imports
- Acceptance:
  - [ ] Module compiles without errors
  - [ ] All imports resolve to media_pipeline namespace
  - [ ] `from media_pipeline import AssetAssessment` works
- Verification: `python -c "from media_pipeline import AssetAssessment; print('OK')"`
- Effort: S (30 minutes)

**T-002: Migrate Perplexity provider**
- File: `P:/packages/media-pipeline/src/media_pipeline/providers/perplexity.py`
- Action: Copy perplexity.py from portfolio-media, register in provider registry
- Acceptance:
  - [ ] Provider compiles without errors
  - [ ] Registered in ProviderRegistry
  - [ ] `from media_pipeline.providers import PerplexityProvider` works
- Verification: `python -c "from media_pipeline.providers import PerplexityProvider; print('OK')"`
- Effort: S (30 minutes)

**T-003: Update media-pipeline exports**
- File: `P:/packages/media-pipeline/src/media_pipeline/__init__.py`
- Action: Add AssetAssessment, assess_package, PerplexityProvider to __all__
- Acceptance:
  - [ ] New exports accessible from top-level module
  - [ ] Existing exports still work
- Verification: `python -c "from media_pipeline import AssetAssessment, assess_package, PerplexityProvider; print('OK')"`
- Effort: S (15 minutes)

**T-004: Add CLI entry points**
- File: `P:/packages/media-pipeline/pyproject.toml`
- Action: Add gen-media-assess, gen-media-logo, gen-media-diagram, gen-media-screenshot
- Acceptance:
  - [ ] Commands available after pip install
  - [ ] `gen-media --help` shows all commands
- Verification: `gen-media --help | grep -E "assess|logo|diagram|screenshot"`
- Effort: S (30 minutes)

**T-005: Migrate assessment tests**
- File: `P:/packages/media-pipeline/tests/test_assessment.py`
- Action: Copy test_assessment.py from portfolio-media, update imports
- Acceptance:
  - [ ] All tests pass with pytest
  - [ ] Test coverage ≥80% for assessment module
- Verification: `pytest P:/packages/media-pipeline/tests/test_assessment.py -v`
- Effort: M (1 hour)

**T-006: Migrate Perplexity tests**
- File: `P:/packages/media-pipeline/tests/test_perplexity.py`
- Action: Copy test_perplexity.py from portfolio-media, update imports
- Acceptance:
  - [ ] All tests pass with pytest
  - [ ] Test coverage ≥80% for Perplexity provider
- Verification: `pytest P:/packages/media-pipeline/tests/test_perplexity.py -v`
- Effort: M (1 hour)

**T-007: Run full regression suite**
- Action: Execute all media-pipeline tests
- Acceptance:
  - [ ] All existing tests pass (no regressions)
  - [ ] All new tests pass (assessment, Perplexity)
  - [ ] Test coverage ≥80% overall
- Verification: `pytest P:/packages/media-pipeline/tests/ -v --cov=media_pipeline`
- Effort: S (30 minutes)

**T-008: Update media-pipeline README**
- File: `P:/packages/media-pipeline/README.md`
- Action: Document new assessment CLI and Perplexity provider
- Acceptance:
  - [ ] Asset assessment section added with examples
  - [ ] Perplexity provider mentioned in provider list
  - [ ] CLI reference updated with new commands
- Verification: `grep -E "assessment|Perplexity|gen-media-assess" P:/packages/media-pipeline/README.md`
- Effort: M (1 hour)

**T-009: Create migration guide**
- File: `P:/packages/media-pipeline/MIGRATING.md`
- Action: Document migration from portfolio-media to media-pipeline
- Acceptance:
  - [ ] API migration examples (code before/after)
  - [ ] CLI command migration table
  - [ ] Breaking changes documented
  - [ ] Feature parity matrix (all portfolio-media features → media-pipeline)
- Verification: File exists and contains all required sections
- Effort: M (1 hour)

**T-010: Add deprecation notice to portfolio-media**
- File: `P:/packages/portfolio-media/README.md`
- Action: Add prominent deprecation notice at top
- Acceptance:
  - [ ] Notice visible at top of README
  - [ ] Link to migration guide included
  - [ ] Replacement package specified (media-pipeline)
- Verification: `head -20 P:/packages/portfolio-media/README.md | grep -E "DEPRECATED|media-pipeline"`
- Effort: S (15 minutes)

**T-011: Archive portfolio-media repository**
- Action: Set repository to read-only, add archived notice
- Acceptance:
  - [ ] Repository marked as archived on GitHub
  - [ ] Issues disabled
  - [ ] PRs disabled
- Verification: Check GitHub repository settings
- Effort: S (15 minutes)

---

### Verification Review Improvements (Added 2026-03-07)

**T-012: Increment media-pipeline version**
- File: `P:/packages/media-pipeline/pyproject.toml`
- Action: Bump version to 0.6.0 (minor) or 1.0.0 (major) for breaking changes
- Acceptance:
  - [ ] Version updated in pyproject.toml
  - [ ] Version bump justified in CHANGELOG
  - [ ] Semantic versioning followed correctly
- Verification: `grep "version =" P:/packages/media-pipeline/pyproject.toml`
- Depends on: T-007 (after tests pass, before release)
- Effort: S (15 minutes)

**T-013: Create GitHub announcement**
- Action: Create GitHub discussion/issue announcing portfolio-media deprecation
- Acceptance:
  - [ ] Announcement posted to portfolio-media repository
  - [ ] Links to migration guide included
  - [ ] Timeline for archival provided
  - [ ] User questions addressed proactively
- Verification: Check GitHub discussions/issues for announcement
- Depends on: T-010 (deprecation notice)
- Effort: M (30 minutes)

---

### Updated Task Acceptance Criteria

**Modified T-009 (Migration Guide):**
Add acceptance criterion from PR-002:
- [ ] Perplexity provider NotImplementedError status documented
- [ ] Clear explanation of which features are not yet implemented
- [ ] Workarounds provided for missing functionality

**Updated T-011 (Archive Repository):**
Add dependency on T-013:
- Depends on: T-013 (announcement posted before archival)

---

### Updated Execution Order

```
T-001 → T-002 → T-003 → T-004
  ↓       ↓       ↓       ↓
T-005 → T-006 → T-007 ← ← ← ←
  ↓       ↓       ↓       ↓
T-012 → T-008 → T-009 → T-010
  ↓       ↓       ↓       ↓
T-013 → T-011
```

**Critical path:** T-001 through T-009 (code migration + tests + docs)

**Parallelization opportunities:**
- T-001 and T-002 can run in parallel (code migration)
- T-005 and T-006 can run in parallel (test migration)
- T-008, T-009, T-010, T-012 can run in parallel after T-007 (documentation)
- T-013 must follow T-010 (announcement after deprecation notice)
- T-011 must follow T-013 (archive after announcement)

---

## 7. Risks, Success Criteria, Dependencies

### Top Risks

**R1: Breaking existing media-pipeline API**
- **Likelihood:** LOW
- **Impact:** HIGH
- **Mitigation:** Comprehensive regression test suite (T-007)
- **Rollback:** Revert media-pipeline commits, restore from git tag

**R2: Perplexity provider interface incompatibility**
- **Likelihood:** MEDIUM
- **Impact:** MEDIUM
- **Mitigation:** Review provider registry interface before migration (T-002)
- **Rollback:** Remove Perplexity provider from registry, keep module

**R3: User confusion during transition**
- **Likelihood:** HIGH
- **Impact:** MEDIUM
- **Mitigation:** Clear migration guide (T-009), deprecation notice (T-010)
- **Rollback:** Update documentation with clarification

**R4: Test failures after migration**
- **Likelihood:** MEDIUM
- **Impact:** MEDIUM
- **Mitigation:** Run full regression suite before release (T-007)
- **Rollback:** Fix failing tests, skip migration if critical

### Success Criteria

- ✅ All portfolio-media functionality available in media-pipeline
- ✅ Migration guide published with clear examples
- ✅ No breaking changes to media-pipeline's existing API
- ✅ All tests passing (existing + migrated)
- ✅ Test coverage ≥80% for migrated modules
- ✅ portfolio-media deprecated with clear notice

### Dependencies

**Required:**
- Python 3.10+ (already required by both packages)
- pytest (already in dev dependencies)
- media-pipeline repository access
- portfolio-media repository access

**External:**
- None (no new dependencies introduced)

### Rollback Strategy

**If migration fails:**
1. Revert commits to media-pipeline (T-001 through T-008)
2. Restore portfolio-media from git tag
3. Remove deprecation notice
4. Document failure reason for future retry

**Rollback triggers:**
- Critical test failures that can't be fixed in 1 hour
- Breaking changes to media-pipeline API
- User reports of data loss or corruption

---

## Next Actions

1. **Start code migration** (T-001, T-002): Copy assessment and Perplexity modules
2. **Update exports and CLI** (T-003, T-004): Add entry points to media-pipeline
3. **Migrate tests** (T-005, T-006): Ensure test coverage for migrated code
4. **Run regression suite** (T-007): Verify no breaking changes
5. **Version increment** (T-012): Bump media-pipeline version to 0.6.0 or 1.0.0
6. **Update documentation** (T-008, T-009, T-010): README + migration guide + deprecation notice
7. **GitHub announcement** (T-013): Public notice of portfolio-media deprecation
8. **Archive portfolio-media** (T-011): Set repository to read-only

**Estimated Total Effort:** 7-8 hours (increased from 6-7 hours due to verification improvements)

**Blocking Issues:** None identified

**Confidence:** HIGH - Code migration is straightforward, dependencies clear, rollback strategy defined

**Recent Updates (2026-03-07):**
- Added T-012: Version increment strategy (PR-001 from verification review)
- Added T-013: GitHub announcement before archival (PR-004 from verification review)
- Updated T-009: Include Perplexity NotImplementedError documentation (PR-002)
- Updated execution order: T-012 inserted after T-007, T-013 before T-011 (PR-003)
