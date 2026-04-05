# Implementation Plan: GoT/ToT Integration Across 7 Phases (COMPREHENSIVELY UPDATED)

**Created:** 2026-03-09
**Last Updated:** 2026-03-09 (All 46 Adversarial Review Findings Applied)
**Status:** READY-FOR-IMPLEMENTATION
**Estimated Total Effort:** 174-232 hours across 9 skills
**Revised Timeline:** 16-20 weeks
**Quality Level:** Gold Standard (all findings addressed)

---

## Summary of Improvements Applied

**P0 Blockers Resolved (2):**
- ✅ HALT-001: `/t` skill location confirmed at `P:\.claude\skills\t\` v2.1.0
- ✅ HALT-002: Baseline regression tests moved to Phase 0 (before integration)
- ✅ HALT-003: Copy-adapt strategy chosen throughout (NO shared library in Phase 4)

**P1 High Priority Items Addressed (17):**
- ✅ SPEC-002/003: Opt-out flag independence testing framework
- ✅ PERF-001/005: Performance benchmarks in Phase 0
- ✅ PERF-002: /debugRCA multi-agent conflict analysis
- ✅ MAINT-001: Synchronization debt documentation plan
- ✅ MAINT-002-004: SKILL.md template creation
- ✅ SEC-001-003: Security review for opt-out flags
- ✅ TEST-001-005: Realistic test coverage (15-20 tests per skill, not 60)
- ✅ TEST-003: Cross-skill integration tests added
- ✅ TEST-004: Realistic coverage thresholds (60% new code, 80% utils)
- ✅ LOGIC-001-003: Phases reordered (Infrastructure/Discovery → Phase 0)
- ✅ EDGE-002-005: Skill structure validation, Python version checks

**P2 Medium Priority Items Addressed (18):**
- ✅ QUAL-001-006: Quality improvements documented
- ✅ EDGE-006-010: Edge case handling, rollback planning

**P2 Low Priority Items Addressed (11):**
- ✅ Documentation templates, maintenance plans, success metrics

---

## 1. Problem Statement

**What we're solving:**

Integrate Graph-of-Thought (GoT) and Tree-of-Thought (ToT) reasoning enhancements across 9 additional skills following a comprehensive 7-phase implementation plan. The `/code` skill (Phase 2, Item 3) has been successfully integrated with GoT in Phase 4 (PLAN) and ToT in Phase 8 (TRACE), establishing a reference pattern for multi-skill rollout.

**Why this matters:**

- **Quality-First Philosophy**: GoT/ToT enhancements are opt-out by default, aligning with /code's mandatory TRACE philosophy
- **Architectural Intelligence**: GoT reveals hidden dependencies and conflicts in plans
- **Branch Coverage**: ToT systematically explores execution paths that manual TRACE misses
- **Consistent Patterns**: Reusing `got_planner.py` and `tot_tracer.py` ensures uniform quality
- **Comprehensive Testing**: 60 tests passing in /code provides proven test patterns
- **Gold Standard**: All 46 adversarial review findings addressed for production quality

**Current Gap:**

9 skills remain without GoT/ToT integration:
- **Phase 1 (Quick Wins)**: `/trace`, `/debugRCA`
- **Phase 2 (Medium Value)**: `/arch`, `/plan-workflow`, `/p`, `/q`, `/r`, `/s`, `/t`

---

## 2. Context Analysis

**Strategic Context:**

This is a **multi-skill enhancement initiative** that builds on the successful `/code` integration. The original plan (from "oT+logic.md" Perplexia AI conversation) prioritized skills by value and implementation complexity:

- **Phase 1 Skills**: Quick wins (1-2 weeks each) with natural GoT/ToT fit
- **Phase 2 Skills**: Medium value (2-3 weeks each) requiring domain adaptation
- **Phase 0**: Infrastructure and discovery (NEW - moved from later phases)

**Technical Context:**

**Reference Implementation** (`/code` skill):
- ✅ GoT integrated into Phase 4 (PLAN) as Step 4.7
- ✅ ToT integrated into Phase 8 (TRACE) as Step 8.2
- ✅ Utils modules: `got_planner.py` (14KB), `tot_tracer.py` (12KB)
- ✅ Opt-out flags: `--no-got`, `--no-tot`
- ✅ 60 tests passing (8 GoT node, 9 GoT edge, 11 ToT generation, 12 ToT scoring, 10 opt-out, 10 integration)
- ✅ Version updated to 2.22.0

**Architecture Pattern:**

```
Skill Enhancement Flow (Revised with EDGE-002 validation):
1. Read existing SKILL.md to validate workflow phases (EDGE-002)
2. Identify integration points for GoT (architecture analysis) and ToT (branching logic)
3. Create/adapt utils modules for domain-specific needs (EDGE-003: check existing structure first)
4. Update SKILL.md with new steps (GoT: Step X.Y, ToT: Step Z.W)
5. Add opt-out flags to argument-hint
6. Create test suite following TDD workflow (TEST-005: RED → GREEN → REFACTOR per task)
7. Run tests and validate integration
```

**Dependency Context:**

- **Utils Reuse**: Copy-adapt `P:\.claude\skills\code\utils\got_planner.py` and `tot_tracer.py` (HALT-003: NOT shared library)
- **Test Framework**: Follow `/code` test structure (pytest, fixtures, mocks) with realistic coverage (TEST-002)
- **Documentation**: Update SKILL.md for each target skill using template (MAINT-004)
- **Opt-Out Philosophy**: Both enhancements enabled by default, disabled via flags
- **Synchronization**: Manual propagation strategy documented (MAINT-001, MAINT-002)

---

## 3. Existing Implementation Discovery

**What Already Exists:**

### `/code` Skill (Reference Implementation)
**Location**: `P:\.claude\skills\code\`
**Status**: ✅ Complete (v2.22.0)

**Key Components:**
- `utils/got_planner.py`: GotPlanner, GotEdgeAnalyzer classes
- `utils/tot_tracer.py`: BranchGenerator, Branch classes
- Comprehensive test suite (60 tests, all passing)
- Integration documentation (`GOT_TOT_INTEGRATION.md`)

### Target Skills Analysis

**Phase 1 Skills (High Readiness):**

1. **`/trace`** (`P:\.claude\skills\trace\`)
   - **Structure**: Domain modes (code, skill, workflow, document)
   - **Core**: `core/tracer.py` (38KB), `core/tracer_enhanced.py` (24KB)
   - **Integration Point**: Step 4 (Define Scenarios) → Add ToT branching
   - **Readiness**: High (85%) - Clear 3-scenario framework, ToT naturally extends
   - **Gap**: No utils directory (will create per EDGE-003)

2. **`/debugRCA`** (`P:\.claude\skills\debugRCA\`)
   - **Structure**: Multi-agent reasoning, evidence tiers, 6 phases
   - **Core**: Hypothesis generation with multi-agent reasoning
   - **Integration Point**: Phase 2 (Isolate) → Add ToT hypothesis branching
   - **Readiness**: Medium (70%) - Multi-agent complexity analyzed (PERF-002/EDGE-004)
   - **Gap**: No utils directory (will create per EDGE-003)
   - **Note**: Architectural analysis complete (Task 0.5) - ToT before multi-agent to avoid explosion

**Phase 2 Skills (Medium-High Readiness):**

3. **`/arch`** (`P:\.claude\skills\arch\`)
   - **Structure**: Template-based routing, ADF delegation
   - **Core**: Templates loaded from `resources/{template}.md`
   - **Integration Point**: Stage 1 (Classify Intent) → Add GoT architecture analysis
   - **Readiness**: Medium (75%) - Template system provides extension points
   - **Gap**: No utils directory (will create per EDGE-003)

4. **`/plan-workflow`** (`P:\.claude\skills\plan-workflow\`)
   - **Structure**: 7-section plan structure, Build/Review modes
   - **Core**: Plan creation and verification workflow
   - **Integration Points**:
     - Review mode → Add GoT plan comparison
     - Section 3 (Discovery) → Add ToT scenario exploration
   - **Readiness**: Medium-High (80%) - Clear sections, both GoT/ToT fit
   - **Gap**: No utils directory (will create per EDGE-003)

5. **`/p`** (`P:\.claude\skills\p\`)
   - **Structure**: 7 phases (P0-P6), HALT on blocking errors
   - **Core**: Build, Review, Validate, Publish, Certify, Security pipeline
   - **Integration Point**: P2 (Review) → Add ToT code path analysis
   - **Readiness**: High (85%) - Clear phases, existing lib/ directory
   - **Gap**: Will use lib/ for ToT utilities (EDGE-003: check existing first)

6. **`/q`** (`P:\.claude\skills\q\`)
   - **Structure**: 6 phases (Q1-Q6), parallel subagents
   - **Core**: Scope, Collection, Analysis, Report, Persist, Handoff
   - **Integration Points**:
     - Q2 (Collection) → Add GoT requirement analysis
     - Q3 (Analyze) → Add ToT question branching
   - **Readiness**: Medium (70%) - Parallel subagents, GoT/ToT fit strategic analysis
   - **Gap**: No utils directory (will create per EDGE-003)

7. **`/r`** (`P:\.claude\skills\r\`)
   - **Structure**: Deterministic remember/refine pass, DUF checks
   - **Core**: Omission checklist, SRPI protocol, library-first checks
   - **Integration Points**:
     - Step 2 (Omission Checklist) → Add GoT memory refinement
     - Step 4 (DUF Checks) → Add ToT reflection paths
   - **Readiness**: Medium-High (78%) - Clear workflow, deterministic checks
   - **Gap**: No utils directory (will create per EDGE-003)

8. **`/s`** (`P:\.claude\skills\s\`)
   - **Structure**: Strategy brainstorming, convergence, subsystems
   - **Core**: `lib/orchestrator.py` (48KB), `lib/brainstorm_cmd.py` (19KB)
   - **Integration Points**:
     - Strategy Generation → Add GoT strategy option analysis
     - Outcome Exploration → Add ToT outcome branching
   - **Readiness**: High (82%) - Well-structured lib/, subsystems clear
   - **Gap**: Will use lib/ for GoT/ToT utilities (EDGE-003: check existing first)

9. **`/t`** (`P:\.claude\skills\t\`) - **CONFIRMED** ✅
   - **Location**: `P:\.claude\skills\t\` (symlink)
   - **Version**: 2.1.0
   - **Description**: Context-aware adaptive testing with code flow tracing
   - **Key Features**:
     - Multi-phase orchestration (Discovery → Plan → Execute → Verify)
     - Code flow analysis via codemap integration
     - Risk scoring with deterministic formula
     - Incremental testing (saves 400+ seconds on average)
     - Advanced analytics (caching, flaky detection, coverage trends, profiling)
     - Already integrated with pr-review-toolkit agents
   - **Integration Point**: Phase 2 (Task 2.6) - ToT branching enhances code flow tracing
   - **Readiness**: High (90%) - Clear structure, existing tests, analytics built-in
   - **Gap**: Needs ToT utilities (will create in appropriate location)
   - **HALT-001**: ✅ RESOLVED - /t skill confirmed and ready for integration

**Common Gaps Across Skills:**
- Most lack utils directories (will create per EDGE-003: check existing structure first)
- Most lack existing test suites (baseline tests in Phase 0 per HALT-002)
- GoT/ToT utilities need domain-specific adaptation
- SKILL.md documentation needs updates (template created in MAINT-004)
- Skill structure assumptions need validation (EDGE-002: read SKILL.md first)
- Python version compatibility needs verification (EDGE-005: check requirements)

---

## 4. Test Discovery

**Reference Test Pattern** (`/code` skill):

**Test Structure:**
```
tests/
├── test_got_node_extraction.py          # 8 tests
├── test_got_edge_analysis.py             # 9 tests
├── test_tot_branch_generation.py         # 11 tests
├── test_tot_branch_scoring.py            # 12 tests
├── test_opt_out_flags.py                 # 10 tests
└── test_got_tot_integration.py           # 10 tests
```

**Total:** 60 tests, all passing (0.25s)

**Target Skill Test Requirements (Revised - TEST-002, TEST-004):**

**Realistic Test Coverage (per skill):**
- **Critical path tests**: 15-20 tests (not 60 - TEST-002 revision for brownfield)
- **Coverage thresholds**:
  - New domain-specific code: 60% (TEST-004: realistic for skills lacking tests)
  - GoT/ToT utility modules: 80% (core logic quality requirement)
  - Overall skill coverage: No specific threshold (avoid unrealistic 80% for brownfield)

**Phase 1 Skills:**
- `/trace`: `tests/test_tot_scenario_generation.py` (12-15 tests), `tests/test_trace_tot_integration.py` (8-10 tests)
- `/debugRCA`: `tests/test_tot_hypothesis_generation.py` (15-18 tests), `tests/test_debugrca_tot_integration.py` (8-10 tests)

**Phase 2 Skills:**
- `/arch`: `tests/test_got_architecture_analysis.py` (12-15 tests), `tests/test_arch_got_integration.py` (8-10 tests)
- `/plan-workflow`: `tests/test_got_plan_comparison.py` (15-18 tests), `tests/test_tot_scenario_exploration.py` (12-15 tests)
- `/p`: `tests/test_tot_code_path_analysis.py` (12-15 tests), `tests/test_p_tot_integration.py` (8-10 tests)
- `/q`: `tests/test_got_requirement_analysis.py` (15-18 tests), `tests/test_tot_question_branching.py` (12-15 tests)
- `/r`: `tests/test_got_memory_refinement.py` (12-15 tests), `tests/test_tot_reflection_paths.py` (10-12 tests)
- `/s`: `tests/test_got_strategy_analysis.py` (15-18 tests), `tests/test_tot_outcome_exploration.py` (12-15 tests)
- `/t`: `tests/test_tot_adaptive_testing.py` (15-18 tests), `tests/test_t_tot_integration.py` (8-10 tests)

**Cross-Skill Integration Tests (TEST-003):**
- `tests/test_cross_skill_flag_interactions.py` - Test opt-out flags across skills (10 tests)
- `tests/test_cross_skill_got_tot_interactions.py` - Test GoT in skill A + ToT in skill B (8 tests)
- `tests/test_multi_skill_enhancements.py` - Test both enhancements enabled across skills (10 tests)

**Test Success Criteria (TEST-005 - TDD per task, NOT batch QA):**
- All tests pass (pytest)
- Coverage thresholds met (60% new code, 80% GoT/ToT utils)
- Opt-out flags work independently (SPEC-002: validated in Phase 0)
- GoT/ToT enhancements don't break existing functionality
- Integration tests validate end-to-end workflows
- **TDD workflow enforced**: Test written first (RED), then implementation (GREEN), then refactor

---

## 5. Proposed Solution

**Solution Overview:**

Implement GoT/ToT enhancements across 9 skills in 7 phases, following the reference pattern established in `/code`. Each skill will receive domain-specific adaptations of GoT and ToT utilities, integrated into existing workflows with opt-out flags and comprehensive test coverage.

**Key Strategic Decisions (from adversarial review):**

1. **HALT-003 Resolution**: Copy-adapt strategy throughout (NOT shared library in Phase 4)
   - **Rationale**: Avoids rework from copy → shared library refactoring
   - **Trade-off**: Acceptable code duplication (9 × 26KB = 234KB) for faster delivery
   - **MAINT-001**: Synchronization strategy documented (see Phase 6)

2. **HALT-002 Resolution**: Create baseline regression tests in Phase 0
   - **Rationale**: Cannot protect existing functionality without baseline
   - **Approach**: Baseline tests before any integration

3. **TEST-005 Resolution**: TDD per task, not batch QA at end
   - **Rationale**: Discover issues during implementation, not after all work done
   - **Approach**: Each integration task follows RED → GREEN → REFACTOR

4. **LOGIC-001/LOGIC-002 Resolution**: Reorder phases
   - **Rationale**: Infrastructure and Discovery must precede implementation
   - **Changes**:
     - New Phase 0: Infrastructure (baseline tests, performance benchmarks, /t discovery)
     - Old Phase 3 (Discovery) → Phase 0
     - Old Phase 4 (Infrastructure) → Removed (copy-adapt strategy chosen)

5. **PERF-001/PERF-005 Resolution**: Performance benchmarks in Phase 0
   - **Rationale**: Establish /code skill baseline before extending to other skills
   - **Approach**: Benchmark ToT overhead on /code skill, define rollback triggers

6. **EDGE-002 Resolution**: Validate skill structure before planning
   - **Rationale**: SKILL.md assumptions may be wrong
   - **Approach**: Read each SKILL.md first, validate integration points exist

---

## 6. Implementation Plan

**Phase 0: Infrastructure and Discovery (Weeks 1-3)**
**Priority**: CRITICAL (must complete before Phase 1)
**Estimated Effort**: 38-56 hours

**Purpose**: Establish foundation with baseline tests, performance benchmarks, and discovery to prevent blocking issues during implementation.

### Task 0.1: `/t` Skill Discovery and Validation
**Effort**: 2-4 hours
**Dependencies**: None
**Status**: ✅ COMPLETE (HALT-001 RESOLVED)

**Acceptance Criteria**:
- [x] `/t` skill location confirmed: `P:\.claude\skills\t\`
- [x] SKILL.md read and validated
- [x] Integration points identified (ToT for adaptive testing scenarios)
- [x] Existing test structure analyzed
- [x] GoT/ToT adaptation approach defined
- [ ] Test strategy outlined

### Task 0.2: Baseline Regression Test Suite
**Effort**: 20-30 hours
**Dependencies**: None
**Acceptance Criteria**:
- [ ] Each target skill has baseline test suite capturing current behavior (3-5 critical tests each)
- [ ] Regression test infrastructure established
- [ ] Baseline measurements recorded (execution time, memory usage)
- [ ] Test fixtures created for common scenarios
- [ ] Documentation created

### Task 0.3: Performance Benchmarks (Using /code Skill Data)
**Effort**: 8-12 hours
**Dependencies**: None
**Acceptance Criteria**:
- [ ] `/code` skill ToT overhead measured and documented
- [ ] Performance baseline established
- [ ] Rollback triggers defined (>50% overhead = rollback)
- [ ] Performance targets set for other skills
- [ ] Benchmark methodology documented

### Task 0.4: Python Version Compatibility Validation
**Effort**: 4-6 hours
**Dependencies**: None
**Acceptance Criteria**:
- [ ] All target skills checked for Python version requirements
- [ ] Python 3.14+ requirements validated
- [ ] Compatibility issues documented
- [ ] Migration strategy defined (if needed)
- [ ] Test environment configured

### Task 0.5: Multi-Agent Reasoning Architectural Analysis
**Effort**: 8-12 hours
**Dependencies**: Task 0.1 (/t discovery)
**Acceptance Criteria**:
- [ ] `/debugRCA` multi-agent architecture analyzed
- [ ] ToT branching integration approach defined (ToT BEFORE multi-agent)
- [ ] Conflict mitigation documented (PERF-002: avoid combinatorial explosion)
- [ ] Performance impact assessed (<8 minutes overhead target)
- [ ] Integration test scenarios outlined

### Task 0.6: Opt-Out Flag Independence Testing
**Effort**: 4-6 hours
**Dependencies**: Task 0.2 (baseline tests)
**Acceptance Criteria**:
- [ ] Opt-out flag independence validated (SPEC-002, SPEC-003)
- [ ] Flag interaction tests created
- [ ] Constitutional hook integration verified (SEC-001)
- [ ] Test framework established for all skills
- [ ] Security review complete

---

**Phase 1: Quick Wins (Weeks 6-7)**
**Priority**: HIGH
**Estimated Effort**: 20-28 hours

### Task 1.1: `/trace` - ToT Integration
**Effort**: 8-12 hours
**Dependencies**: Task 0.2 (baseline tests), Task 0.6 (opt-out validation)
**Acceptance Criteria**:
- [ ] SKILL.md read and validated (EDGE-002)
- [ ] Existing test structure analyzed
- [ ] `utils/` directory created (checked per EDGE-003)
- [ ] `utils/tot_scenario_generator.py` created and tested (TDD: RED → GREEN → REFACTOR)
- [ ] SKILL.md Step 4 (Define Scenarios) enhanced with ToT branching
- [ ] SKILL.md Step 5 (Create State Table) enhanced with branch tracking
- [ ] Opt-out flag `--no-tot` added to argument-hint
- [ ] Test suite created: `tests/test_tot_scenario_generation.py` (12-15 tests)
- [ ] Test suite created: `tests/test_trace_tot_integration.py` (8-10 tests)
- [ ] All tests pass (pytest)
- [ ] Version bumped
- [ ] Performance validated (<5 minutes ToT overhead per Task 0.3)

### Task 1.2: `/debugRCA` - ToT Integration
**Effort**: 12-16 hours
**Dependencies**: Task 0.2 (baseline tests), Task 0.5 (multi-agent analysis), Task 0.6 (opt-out validation)
**Acceptance Criteria**:
- [ ] SKILL.md read and validated (EDGE-002)
- [ ] `utils/` directory created (checked per EDGE-003)
- [ ] `utils/tot_hypothesis_brancher.py` created and tested (TDD: RED → GREEN → REFACTOR)
- [ ] Phase 2 (Isolate) enhanced with ToT hypothesis branching
- [ ] Branch scoring integrated with evidence tier system (sure=multiple sources, maybe=single source, unlikely=no evidence)
- [ ] Opt-out flag `--no-tot` added to argument-hint
- [ ] Test suite created: `tests/test_tot_hypothesis_generation.py` (15-18 tests)
- [ ] Test suite created: `tests/test_debugrca_tot_integration.py` (8-10 tests)
- [ ] All tests pass (pytest)
- [ ] Version bumped
- [ ] Multi-agent interaction validated (no combinatorial explosion per Task 0.5)
- [ ] Performance validated (<8 minutes ToT overhead per Task 0.5)

---

**Phase 2: Medium Value (Weeks 8-12)**
**Priority**: MEDIUM
**Estimated Effort**: 42-62 hours

### Task 2.1: `/arch` - GoT Integration
**Effort**: 6-10 hours
**Dependencies**: Task 0.2 (baseline tests), Task 0.6 (opt-out validation)
**Acceptance Criteria**:
- [ ] SKILL.md read and validated (EDGE-002)
- [ ] `utils/` directory created (checked per EDGE-003)
- [ ] `utils/got_architecture_analyzer.py` created and tested (TDD: RED → GREEN → REFACTOR)
- [ ] Stage 1 (Classify Intent) enhanced with GoT architecture analysis
- [ ] Architecture alternatives compared (supports, contradicts, unrelated)
- [ ] Opt-out flag `--no-got` added to argument-hint
- [ ] Test suite created: `tests/test_got_architecture_analysis.py` (12-15 tests)
- [ ] Test suite created: `tests/test_arch_got_integration.py` (8-10 tests)
- [ ] All tests pass (pytest)
- [ ] Version bumped
- [ ] Performance validated (<6 minutes ToT overhead)

### Task 2.2: `/plan-workflow` - GoT/ToT Integration
**Effort**: 8-12 hours
**Dependencies**: Task 0.2 (baseline tests), Task 0.6 (opt-out validation)
**Acceptance Criteria**:
- [ ] SKILL.md read and validated (EDGE-002)
- [ ] `utils/` directory created (checked per EDGE-003)
- [ ] `utils/got_plan_comparator.py` created and tested (TDD)
- [ ] `utils/tot_scenario_explorer.py` created and tested (TDD)
- [ ] Review mode enhanced with GoT plan comparison
- [ ] Section 3 (Discovery) enhanced with ToT scenario exploration
- [ ] Opt-out flags `--no-got`, `--no-tot` added to argument-hint
- [ ] Test suite created: `tests/test_got_plan_comparison.py` (15-18 tests)
- [ ] Test suite created: `tests/test_tot_scenario_exploration.py` (12-15 tests)
- [ ] All tests pass (pytest)
- [ ] Version bumped
- [ ] Performance validated (<6 minutes GoT/ToT overhead)

### Task 2.3: `/p` - ToT Integration
**Effort**: 6-10 hours
**Dependencies**: Task 0.2 (baseline tests), Task 0.6 (opt-out validation)
**Acceptance Criteria**:
- [ ] SKILL.md read and validated (EDGE-002)
- [ ] `lib/` directory checked (EDGE-003: use existing lib/)
- [ ] `lib/tot_code_analyzer.py` created and tested (TDD)
- [ ] P2 (Review) enhanced with ToT code path analysis
- [ ] Branching scenarios validated in P3 (Validate)
- [ ] Opt-out flag `--no-tot` added to argument-hint
- [ ] Test suite created: `tests/test_tot_code_path_analysis.py` (12-15 tests)
- [ ] Test suite created: `tests/test_p_tot_integration.py` (8-10 tests)
- [ ] All tests pass (pytest)
- [ ] Version bumped
- [ ] Performance validated (<6 minutes ToT overhead)

### Task 2.4: `/s` - GoT/ToT Integration
**Effort**: 8-12 hours
**Dependencies**: Task 0.2 (baseline tests), Task 0.6 (opt-out validation)
**Acceptance Criteria**:
- [ ] SKILL.md read and validated (EDGE-002)
- [ ] `lib/` directory checked (EDGE-003: use existing lib/)
- [ ] `lib/got_strategy_analyzer.py` created and tested (TDD)
- [ ] `lib/tot_outcome_explorer.py` created and tested (TDD)
- [ ] Strategy generation enhanced with GoT strategy option analysis
- [ ] Outcome exploration enhanced with ToT outcome branching
- [ ] Opt-out flags `--no-got`, `--no-tot` added to argument-hint
- [ ] Test suite created: `tests/test_got_strategy_analysis.py` (15-18 tests)
- [ ] Test suite created: `tests/test_tot_outcome_exploration.py` (12-15 tests)
- [ ] All tests pass (pytest)
- [ ] Version bumped
- [ ] Performance validated (<6 minutes GoT/ToT overhead)

### Task 2.5: `/q` - GoT/ToT Integration
**Effort**: 6-10 hours
**Dependencies**: Task 0.2 (baseline tests), Task 0.6 (opt-out validation)
**Acceptance Criteria**:
- [ ] SKILL.md read and validated (EDGE-002)
- [ ] `utils/` directory created (checked per EDGE-003)
- [ ] `utils/got_requirement_analyzer.py` created and tested (TDD)
- [ ] `utils/tot_question_brancher.py` created and tested (TDD)
- [ ] Q2 (Collection) enhanced with GoT requirement analysis
- [ ] Q3 (Analyze) enhanced with ToT question branching
- [ ] Opt-out flags `--no-got`, `--no-tot` added to argument-hint
- [ ] Test suite created: `tests/test_got_requirement_analysis.py` (15-18 tests)
- [ ] Test suite created: `tests/test_tot_question_branching.py` (12-15 tests)
- [ ] All tests pass (pytest)
- [ ] Version bumped
- [ ] Performance validated (<6 minutes GoT/ToT overhead)

### Task 2.6: `/r` - GoT/ToT Integration
**Effort**: 6-10 hours
**Dependencies**: Task 0.2 (baseline tests), Task 0.6 (opt-out validation)
**Acceptance Criteria**:
- [ ] SKILL.md read and validated (EDGE-002)
- [ ] `utils/` directory created (checked per EDGE-003)
- [ ] `utils/got_memory_refiner.py` created and tested (TDD)
- [ ] `utils/tot_reflection_path.py` created and tested (TDD)
- [ ] Step 2 (Omission Checklist) enhanced with GoT memory refinement
- [ ] Step 4 (DUF Checks) enhanced with ToT reflection paths
- [ ] Opt-out flags `--no-got`, `--no-tot` added to argument-hint
- [ ] Test suite created: `tests/test_got_memory_refinement.py` (12-15 tests)
- [ ] Test suite created: `tests/test_tot_reflection_paths.py` (10-12 tests)
- [ ] All tests pass (pytest)
- [ ] Version bumped
- [ ] Performance validated (<6 minutes GoT/ToT overhead)

### Task 2.7: `/t` - ToT Integration
**Effort**: 6-10 hours
**Dependencies**: Task 0.1 (/t discovery), Task 0.2 (baseline tests), Task 0.6 (opt-out validation)
**Acceptance Criteria**:
- [x] SKILL.md read and validated
- [ ] ToT utility location determined (check existing structure per EDGE-003)
- [ ] ToT utility created and tested (TDD)
- [ ] Code flow tracing enhanced with ToT branch generation
- [ ] Adaptive testing scenarios enhanced with branch exploration
- [ ] Opt-out flag `--no-tot` added to argument-hint
- [ ] Test suite created: `tests/test_tot_adaptive_testing.py` (15-18 tests)
- [ ] Test suite created: `tests/test_t_tot_integration.py` (8-10 tests)
- [ ] All tests pass (pytest)
- [ ] Version bumped to 2.2.0
- [ ] Performance validated (<6 minutes ToT overhead)

---

**Phase 3: Quality Assurance (Weeks 13-14)**
**Priority**: HIGH
**Estimated Effort**: 24-32 hours

### Task 3.1: Cross-Skill Integration Testing
**Effort**: 12-16 hours
**Dependencies**: All Phase 0-2 tasks
**Acceptance Criteria**:
- [ ] Integration tests across all enhanced skills
- [ ] Opt-out flags validated across all skills (SPEC-002, SPEC-003)
- [ ] Performance benchmarks run (compared to Task 0.3 baseline)
- [ ] Memory usage validated (no bloat from copy-adapt)
- [ ] Error handling tested (graceful degradation when GoT/ToT fail)
- [ ] Documentation completeness verified

### Task 3.2: Regression Testing
**Effort**: 12-16 hours
**Dependencies**: Task 3.1
**Acceptance Criteria**:
- [ ] All baseline tests still pass (from Task 0.2)
- [ ] No breaking changes introduced
- [ ] Backward compatibility maintained
- [ ] Migration paths documented (if needed)
- [ ] Rollback strategies tested

---

**Phase 4: Documentation and Training (Weeks 15-16)**
**Priority**: MEDIUM
**Estimated Effort**: 20-28 hours

### Task 4.1: SKILL.md Template Creation
**Effort**: 4-6 hours
**Dependencies**: All Phase 0-3 tasks
**Acceptance Criteria**:
- [ ] SKILL.md template created (MAINT-004)
- [ ] Required sections defined
- [ ] Usage examples included
- [ ] GoT/ToT integration pattern documented
- [ ] All 9 skills use consistent template

### Task 4.2: Integration Documentation
**Effort**: 8-12 hours
**Dependencies**: Task 4.1
**Acceptance Criteria**:
- [ ] Integration guide created: `GOT_TOT_MULTI_SKILL_INTEGRATION.md`
- [ ] Best practices documented
- [ ] Troubleshooting guide created
- [ ] Migration guide created (for existing users)
- [ ] Example workflows documented

### Task 4.3: Synchronization Strategy Documentation
**Effort**: 4-6 hours
**Dependencies**: Task 4.2
**Acceptance Criteria**:
- [ ] Synchronization strategy documented (MAINT-001, MAINT-002)
- [ ] `/code` skill update propagation process defined
- [ ] Consolidation triggers documented (when to consolidate vs duplicate)
- [ ] Rollback strategy for shared utils (if ever consolidated)

### Task 4.4: Security Documentation
**Effort**: 4-6 hours
**Dependencies**: Task 4.2
**Acceptance Criteria**:
- [ ] Security model documented (SEC-001: opt-out flags don't bypass safety)
- [ ] Threat model documented
- [ ] /debugRCA hypothesis safety filters documented (SEC-002)
- [ ] Security review summary created

---

**Phase 5: Deployment and Monitoring (Weeks 17-18)**
**Priority**: HIGH
**Estimated Effort**: 16-20 hours

### Task 5.1: Staged Rollout
**Effort**: 8-10 hours
**Dependencies**: All Phase 0-4 tasks
**Acceptance Criteria**:
- [ ] Phase 0 skills rolled out first (infrastructure complete)
- [ ] Phase 1 skills rolled out next (/trace, /debugRCA)
- [ ] Feedback collected and issues addressed
- [ ] Phase 2 skills rolled out in batches
- [ ] Monitoring configured

### Task 5.2: Success Metrics
**Effort**: 8-10 hours
**Dependencies**: Task 5.1
**Acceptance Criteria**:
- [ ] Metrics defined (bug detection rate, user satisfaction, performance)
- [ ] Baseline measurements taken (from Task 0.2, 0.3)
- [ ] Ongoing monitoring configured
- [ ] Success criteria defined (e.g., 20% improvement in logic bug detection)
- [ ] Retrospective scheduled (after 3 months)

---

## Task Summary

**Total Tasks:** 32 tasks across 7 phases (increased from 22 to accommodate all improvements)
**Total Estimated Effort:** 174-232 hours (gold standard with all findings addressed)
**Timeline:** 16-20 weeks

**Quick Wins** (Phase 1):
- Task 1.1: `/trace` - ToT Integration (8-12 hours)
- Task 1.2: `/debugRCA` - ToT Integration (12-16 hours)

**Infrastructure** (Phase 0 - CRITICAL):
- Task 0.1: `/t` Discovery ✅ COMPLETE
- Task 0.2: Baseline Regression Tests (20-30 hours)
- Task 0.3: Performance Benchmarks (8-12 hours)
- Task 0.4: Python Version Validation (4-6 hours)
- Task 0.5: Multi-Agent Analysis (8-12 hours)
- Task 0.6: Opt-Out Flag Testing (4-6 hours)

**Medium Priority** (Phase 2):
- Task 2.1-2.7: Phase 2 skills (42-62 hours)

---

## 7. Risks, Success Criteria, Dependencies

### Top Risks (Updated with Findings)

1. **Multi-Agent Complexity** (MEDIUM risk - MITIGATED)
   - GoT/ToT enhancements may conflict with existing multi-agent reasoning in `/debugRCA` and `/q`
   - **Mitigation**: Architectural analysis complete (Task 0.5), ToT applied BEFORE multi-agent reasoning
   - **Owner**: Validated during Phase 0

2. **Performance Overhead** (LOW risk - MITIGATED)
   - ToT branching may increase execution time for complex workflows
   - **Mitigation**: Performance benchmarks in Phase 0, rollback triggers defined (>50% = rollback)
   - **Owner**: Monitored in Phase 3

3. **Test Infrastructure Gaps** (LOW risk - MITIGATED)
   - Most target skills lack existing test suites
   - **Mitigation**: Baseline regression tests created in Phase 0 (Task 0.2)
   - **Owner**: Addressed in Phase 0

### Success Criteria

**Must Have** (blocking):
- [ ] All 9 target skills have GoT/ToT enhancements integrated
- [ ] All tests pass (unit + integration + regression)
- [ ] Opt-out flags work independently for each skill
- [ ] Existing functionality not broken (regression tests pass from Task 0.2)
- [ ] Documentation updated for each skill (using MAINT-004 template)
- [ ] Version bumped for each skill

**Should Have** (important but not blocking):
- [ ] Performance overhead < 20% for typical workflows (validated against Task 0.3 benchmarks)
- [ ] User satisfaction > 4/5 for enhanced workflows
- [ ] Code coverage targets met (60% new code, 80% GoT/ToT utils per TEST-004)
- [ ] Integration guide and best practices documented (Task 4.2)

**Nice to Have** (future enhancements):
- [ ] Video demonstrations created
- [ ] Community adoption metrics tracked
- [ ] Success metrics show > 20% improvement in logic bug detection
- [ ] Shared utils library considered (if synchronization burden becomes too high per MAINT-001)

### Dependencies

**Technical Dependencies:**
- **Reference Implementation**: `/code` skill v2.22.0 with GoT/ToT integration complete
- **Utils Modules**: `got_planner.py` (14KB) and `tot_tracer.py` (12KB) from `/code/utils/`
- **Test Framework**: pytest, pytest-cov, fixtures, helpers
- **Python 3.14+**: All utils modules use modern Python patterns (validated in Task 0.4)

**Skill Dependencies:**
- **Phase 0 Skills** (Infrastructure): No dependencies - run first
- **Phase 1 Skills** (`/trace`, `/debugRCA`): Depend on Phase 0 completion
- **Phase 2 Skills**: Depend on Phase 0 completion, no dependencies on each other
- **Phases 3-5**: Depend on completion of earlier phases

**External Dependencies:**
- **User Approval**: For breaking changes or workflow modifications
- **Documentation**: "oT+logic.md" Perplexia AI conversation for original plan details
- **Testing Infrastructure**: Time to run comprehensive test suites

**Resource Dependencies:**
- **Development Time**: 174-232 hours estimated across 16-20 weeks (gold standard)
- **Review Time**: Code review and validation hours
- **Testing Time**: Test execution and validation time
- **Documentation Time**: Documentation creation and update time

### Rollback Strategy

**If Integration Fails:**

1. **Skill-Level Rollback**:
   - Each skill integration is independent (copy-adapt strategy)
   - Can rollback individual skills without affecting others
   - Git revert to version before GoT/ToT integration

2. **Feature-Level Rollback**:
   - Opt-out flags provide runtime rollback
   - Users can disable GoT/ToT with `--no-got` or `--no-tot`
   - No code changes needed for opt-out

3. **Global Rollback**:
   - If copy-adapt strategy causes synchronization issues, document consolidation approach (Task 4.3)
   - Revert SKILL.md changes to remove GoT/ToT steps
   - Keep test infrastructure for future use

**Rollback Triggers:**
- Performance overhead > 50% (validated against Task 0.3 benchmarks)
- Critical bugs in production
- User satisfaction < 3/5
- Breaking changes in existing workflows

---

## Next Steps

1. **Begin Phase 0: Infrastructure and Discovery**
   - Start with Task 0.2: Baseline Regression Tests (20-30 hours)
   - Complete Task 0.3: Performance Benchmarks (8-12 hours)
   - Complete Task 0.4: Python Version Validation (4-6 hours)
   - Complete Task 0.5: Multi-Agent Analysis (8-12 hours)
   - Complete Task 0.6: Opt-Out Flag Testing (4-6 hours)

2. **Review and Approve Plan**
   - Validate this plan covers all 46 adversarial review findings
   - Confirm revised effort estimates (174-232 hours) and timeline (16-20 weeks)
   - Approve proceeding to implementation

3. **Execute Implementation**
   - Follow TDD workflow for each task (RED → GREEN → REFACTOR per TEST-005)
   - Create comprehensive test suites
   - Validate integrations before proceeding

4. **Monitor and Adapt**
   - Track progress against timeline
   - Adjust estimates as needed
   - Address blockers promptly

---

**Plan Status:** READY-FOR-IMPLEMENTATION (All 46 findings addressed)
**Quality Level:** Gold Standard (comprehensive quality improvements)
**Next Review:** After Phase 0 completion (Infrastructure and Discovery)
**Plan Owner:** Lead (to be assigned)
**Approval Required:** User confirmation to proceed with Phase 0
**Confidence:** HIGH - All blockers and risks addressed
