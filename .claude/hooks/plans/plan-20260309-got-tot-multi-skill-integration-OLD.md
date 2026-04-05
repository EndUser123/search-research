# Implementation Plan: GoT/ToT Integration Across 7 Phases

**Created:** 2026-03-09
**Last Updated:** 2026-03-09 (Adversarial Review Improvements Applied)
**Status:** READY-FOR-IMPLEMENTATION (All 46 findings addressed)
**Estimated Total Effort:** 174-232 hours across 9 skills
**Revised Timeline:** 16-20 weeks

---

## 1. Problem Statement

**What we're solving:**

Integrate Graph-of-Thought (GoT) and Tree-of-Thought (ToT) reasoning enhancements across 9 additional skills following a 7-phase implementation plan. The `/code` skill (Phase 2, Item 3) has been successfully integrated with GoT in Phase 4 (PLAN) and ToT in Phase 8 (TRACE), establishing a reference pattern for multi-skill rollout.

**Why this matters:**

- **Quality-First Philosophy**: GoT/ToT enhancements are opt-out by default, aligning with /code's mandatory TRACE philosophy
- **Architectural Intelligence**: GoT reveals hidden dependencies and conflicts in plans
- **Branch Coverage**: ToT systematically explores execution paths that manual TRACE misses
- **Consistent Patterns**: Reusing `got_planner.py` and `tot_tracer.py` ensures uniform quality
- **Comprehensive Testing**: 60 tests passing in /code provides proven test patterns

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
- **Phase 3-7**: Additional skills and infrastructure (future phases)

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
Skill Enhancement Flow:
1. Read existing SKILL.md to understand workflow phases
2. Identify integration points for GoT (architecture analysis) and ToT (branching logic)
3. Create/adapt utils modules for domain-specific needs
4. Update SKILL.md with new steps (GoT: Step X.Y, ToT: Step Z.W)
5. Add opt-out flags to argument-hint
6. Create test suite following /code pattern
7. Run tests and validate integration
```

**Dependency Context:**

- **Utils Reuse**: Adapt `P:\.claude\skills\code\utils\got_planner.py` and `tot_tracer.py`
- **Test Framework**: Follow `/code` test structure (pytest, fixtures, mocks)
- **Documentation**: Update SKILL.md for each target skill
- **Opt-Out Philosophy**: Both enhancements enabled by default, disabled via flags

---

## 3. Existing Implementation Discovery

**What Already Exists:**

### `/code` Skill (Reference Implementation)
**Location**: `P:\.claude\skills\code\`
**Status**: ✅ Complete (v2.22.0)

**Key Components:**
- `utils/got_planner.py`: GotPlanner, GotEdgeAnalyzer classes
  - Node extraction: constraints, ideas, risks from plan.md Architecture section
  - Edge analysis: supports, contradicts, unrelated relationships
  - Cycle detection: DFS-based algorithm for circular dependencies
- `utils/tot_tracer.py`: BranchGenerator, Branch classes
  - Branch generation: 2-3 branches per conditional statement
  - Branch scoring: sure/maybe/unlikely classification
  - Branch pruning: removes unlikely branches
  - Hierarchical tracking: parent-child relationships for nested branches
- `tests/test_got_tot_integration.py`: 10 integration tests
- `tests/test_opt_out_flags.py`: 10 flag behavior tests
- `GOT_TOT_INTEGRATION.md`: Comprehensive integration summary

### Target Skills Analysis

**Phase 1 Skills (High Readiness):**

1. **`/trace`** (`P:\.claude\skills\trace\`)
   - **Structure**: Domain modes (code, skill, workflow, document)
   - **Core**: `core/tracer.py` (38KB), `core/tracer_enhanced.py` (24KB)
   - **Integration Point**: Step 4 (Define Scenarios) → Add ToT branching
   - **Readiness**: High (85%) - Clear 3-scenario framework, ToT naturally extends
   - **Gap**: No utils directory, needs creation

2. **`/debugRCA`** (`P:\.claude\skills\debugRCA\`)
   - **Structure**: Multi-agent reasoning, evidence tiers, 6 phases
   - **Core**: Hypothesis generation with multi-agent reasoning
   - **Integration Point**: Phase 2 (Isolate) → Add ToT hypothesis branching
   - **Readiness**: Medium (70%) - Multi-agent complexity, ToT fits hypotheses
   - **Gap**: No utils directory, needs creation

**Phase 2 Skills (Medium-High Readiness):**

3. **`/arch`** (`P:\.claude\skills\arch\`)
   - **Structure**: Template-based routing, ADF delegation
   - **Core**: Templates loaded from `resources/{template}.md`
   - **Integration Point**: Stage 1 (Classify Intent) → Add GoT architecture analysis
   - **Readiness**: Medium (75%) - Template system provides extension points
   - **Gap**: No utils directory, needs creation

4. **`/plan-workflow`** (`P:\.claude\skills\plan-workflow\`)
   - **Structure**: 7-section plan structure, Build/Review modes
   - **Core**: Plan creation and verification workflow
   - **Integration Points**:
     - Review mode → Add GoT plan comparison
     - Section 3 (Discovery) → Add ToT scenario exploration
   - **Readiness**: Medium-High (80%) - Clear sections, both GoT/ToT fit
   - **Gap**: No utils directory, needs creation

5. **`/p`** (`P:\.claude\skills\p\`)
   - **Structure**: 7 phases (P0-P6), HALT on blocking errors
   - **Core**: Build, Review, Validate, Publish, Certify, Security pipeline
   - **Integration Point**: P2 (Review) → Add ToT code path analysis
   - **Readiness**: High (85%) - Clear phases, existing lib/ directory
   - **Gap**: Needs ToT utilities in lib/

6. **`/q`** (`P:\.claude\skills\q\`)
   - **Structure**: 6 phases (Q1-Q6), parallel subagents
   - **Core**: Scope, Collection, Analysis, Report, Persist, Handoff
   - **Integration Points**:
     - Q2 (Collection) → Add GoT requirement analysis
     - Q3 (Analyze) → Add ToT question branching
   - **Readiness**: Medium (70%) - Parallel subagents, GoT/ToT fit strategic analysis
   - **Gap**: No utils directory, needs creation

7. **`/r`** (`P:\.claude\skills\r\`)
   - **Structure**: Deterministic remember/refine pass, DUF checks
   - **Core**: Omission checklist, SRPI protocol, library-first checks
   - **Integration Points**:
     - Step 2 (Omission Checklist) → Add GoT memory refinement
     - Step 4 (DUF Checks) → Add ToT reflection paths
   - **Readiness**: Medium-High (78%) - Clear workflow, deterministic checks
   - **Gap**: No utils directory, needs creation

8. **`/s`** (`P:\.claude\skills\s\`)
   - **Structure**: Strategy brainstorming, convergence, subsystems
   - **Core**: `lib/orchestrator.py` (48KB), `lib/brainstorm_cmd.py` (19KB)
   - **Integration Points**:
     - Strategy Generation → Add GoT strategy option analysis
     - Outcome Exploration → Add ToT outcome branching
   - **Readiness**: High (82%) - Well-structured lib/, subsystems clear
   - **Gap**: Needs GoT/ToT utilities in lib/

9. **`/t`** (`P:\.claude\skills\t\`) - **CONFIRMED** ✅
   - **Location**: `P:\.claude\skills\t\` (symlink)
   - **Version**: 2.1.0
   - **Status**: Context-aware adaptive testing with code flow tracing
   - **Key Features**: Multi-phase orchestration, risk scoring, incremental testing (400+ sec savings)
   - **Integration Point**: Phase 2 (Task 2.6) - ToT branching enhances code flow tracing
   - **Readiness**: High (90%) - Clear structure, existing tests, pr-review-toolkit integrated
   - **Gap**: Needs ToT utilities in appropriate location
   - **Note**: HALT-001 RESOLVED - /t skill confirmed and ready for integration

**Common Gaps Across Skills:**
- Most lack utils directories (need creation - EDGE-003 addressed)
- Most lack existing test suites (need creation following /code pattern - HALT-002 addressed)
- Baseline regression tests needed before integration (HALT-002: move Task 5.2 → Phase 0)
- GoT/ToT utilities need domain-specific adaptation
- SKILL.md documentation needs updates for each skill (MAINT-004: template will be created)
- Skill structure assumptions need validation (EDGE-002: read SKILL.md first)
- Python version compatibility needs verification (EDGE-005: check Python 3.14+ requirement)

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

**Test Categories:**

1. **GoT Node Extraction Tests** (8 tests):
   - Extract constraints from sample plan
   - Extract ideas from sample plan
   - Extract risks from sample plan
   - Handle minimal plan
   - Handle empty architecture
   - Node IDs are unique
   - Node IDs follow pattern
   - Source lines are tracked

2. **GoT Edge Analysis Tests** (9 tests):
   - Analyze supporting relationships
   - Analyze contradictory relationships
   - Analyze unrelated node pairs
   - Detect circular dependencies
   - Handle complex node graphs
   - Empty graph handling
   - Self-loop detection
   - Transitive relationship detection
   - Edge classification accuracy

3. **ToT Branch Generation Tests** (11 tests):
   - Generate branches for linear trace
   - Generate branches for conditional trace
   - Generate branches for nested traces
   - Branch scoring classification
   - Branch pruning removes unlikely branches
   - Branch pruning preserves hierarchy
   - Generate 2-3 branches per decision
   - Branch description quality
   - Branch IDs are unique
   - Handle empty trace
   - Handle trace without branching

4. **ToT Branch Scoring Tests** (12 tests):
   - Sure branches score correctly
   - Unlikely branches score correctly
   - Maybe branches score correctly
   - Scoring consistency
   - All branches have valid scores
   - Scoring based on keywords
   - Scoring based on path type
   - Edge case scoring
   - Nested scoring
   - Scoring with loops
   - Scoring with try/except
   - Confidence levels

5. **Opt-Out Flag Tests** (10 tests):
   - GoT enabled by default
   - ToT enabled by default
   - --no-got flag disables GoT
   - --no-tot flag disables ToT
   - Flags are independent
   - Default behavior quality-first
   - --no-got does not affect ToT
   - --no-tot does not affect GoT
   - Flag parsing conceptual
   - GoT/ToT integration workflow

6. **Integration Tests** (10 tests):
   - End-to-end GoT then ToT
   - GoT constraints influence ToT branching
   - GoT risks detected in ToT branches
   - GoT/ToT consistency
   - Quality improvement with both enabled
   - Workflow integration
   - Disabled GoT/ToT fallback
   - Memory consistency across phases
   - Complex plan analysis
   - Empty plan and code handling

**Target Skill Test Requirements:**

Each target skill needs a test suite adapted to its domain. **Revised test counts (TEST-002, TEST-004):**

**Realistic Test Coverage (per skill):**
- **Critical path tests**: 15-20 tests (not 60 - TEST-002 revision)
- **Coverage thresholds**:
  - New domain-specific code: 60% (TEST-004: realistic for brownfield)
  - GoT/ToT utility modules: 80% (core logic quality)
  - Overall skill coverage: No specific threshold (avoid unrealistic 80%)

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
- `tests/test_cross_skill_flag_interactions.py` - Test opt-out flags across skills
- `tests/test_cross_skill_got_tot_interactions.py` - Test GoT in skill A + ToT in skill B
- `tests/test_multi_skill_enhancements.py` - Test both enhancements enabled across skills

**Test Success Criteria (TEST-005 - TDD per task, not batch QA):**
- All tests pass (pytest)
- Coverage thresholds met (60% new code, 80% GoT/ToT utils)
- Opt-out flags work independently (SPEC-002, SPEC-003)
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
   - **Approach**: Task 5.2 moved to Phase 0, before any integration

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

**Architecture:**

```
GoT/ToT Multi-Skill Integration Architecture

Reference Layer:
├── P:\.claude\skills\code\utils\got_planner.py (14KB)
├── P:\.claude\skills\code\utils\tot_tracer.py (12KB)
└── P:\.claude\skills\code\GOT_TOT_INTEGRATION.md (reference docs)

Skill Adaptation Layer:
├── /trace: utils/tot_scenario_generator.py
├── /debugRCA: utils/tot_hypothesis_brancher.py
├── /arch: utils/got_architecture_analyzer.py
├── /plan-workflow: utils/got_plan_comparator.py, utils/tot_scenario_explorer.py
├── /p: lib/tot_code_analyzer.py
├── /q: utils/got_requirement_analyzer.py, utils/tot_question_brancher.py
├── /r: utils/got_memory_refiner.py, utils/tot_reflection_path.py
├── /s: lib/got_strategy_analyzer.py, lib/tot_outcome_explorer.py
└── /t: (after discovery)

Integration Layer:
├── SKILL.md updates for each skill
├── Opt-out flags (--no-got, --no-tot)
├── Argument-hint updates
└── Version bumps

Test Layer:
├── Unit tests for each utility class
├── Integration tests for workflow enhancements
├── Opt-out flag tests
└── Regression tests to protect existing functionality
```

**Solution Components:**

### Component 1: GoT/ToT Utils Adaptation (Copy-Adapt Strategy)

**Approach:**
- **Copy and Adapt**: Copy `got_planner.py` and `tot_tracer.py` from `/code/utils/` to each target skill
- **Domain-Specific Customization**: Adapt for each skill's domain (tracing, RCA, architecture, planning, etc.)
- **Reuse Patterns**: Maintain node extraction, edge analysis, branch generation, branch scoring logic
- **Test-Driven**: Create utils tests following `/code` pattern (TDD: RED → GREEN → REFACTOR)

**HALT-003 Resolution: Copy-Adapt Throughout**
- **Decision**: NO shared library in Phase 4 - copy-adapt for all 9 skills
- **Rationale**: Avoids rework from copy → shared library refactoring (MAINT-001)
- **Trade-off**: Acceptable code duplication (9 skills × 26KB = 234KB total)
- **Synchronization**: Documented in Phase 6 (Task 6.1) - manual propagation strategy

**EDGE-003 Resolution: Utils/ Creation Strategy**
- **Check existing structure**: Use `lib/` if skill already has it (/p, /s), else create `utils/`
- **Never assume**: Always verify directory structure before creating (EDGE-002)
- **Read SKILL.md first**: Validate skill structure assumptions (EDGE-002)

**Implementation Strategy (TDD per task):**
1. Read target skill's SKILL.md to validate structure (EDGE-002)
2. Create `utils/` or `lib/` directories if missing (check existing first)
3. Copy base classes from `/code/utils/`
4. Adapt for domain-specific needs (e.g., ToT for hypotheses vs. code branches)
5. Add domain-specific node types (e.g., "strategy options" for `/s`, "requirements" for `/q`)
6. **TDD workflow**:
   - RED: Write failing tests for utility class
   - GREEN: Implement utility class to pass tests
   - REFACTOR: Clean up while keeping tests green
   - VERIFY: Independent verifier checks quality

### Component 2: Workflow Integration

**Approach:**
- **Phase Mapping**: Identify which workflow phases benefit from GoT/ToT
- **Step Insertion**: Add new steps (e.g., "Step 4.7: GoT Enhancement") at appropriate points
- **Opt-Out Flags**: Add `--no-got` and `--no-tot` to argument-hint
- **Documentation**: Update SKILL.md with usage examples

**Integration Patterns:**

**GoT Integration Points:**
- Architecture analysis phases (PLAN, design, strategy generation)
- Requirement constraint analysis
- Memory refinement (relationship analysis between items)
- Plan comparison (alternative evaluation)

**ToT Integration Points:**
- Scenario generation (TRACE paths)
- Hypothesis branching (RCA alternative root causes)
- Code path analysis (review phases)
- Question branching (strategic inquiry)
- Reflection paths (what-if scenarios)
- Outcome exploration (strategy evaluation)
- Test scenario generation (adaptive testing)

### Component 3: Test Suite Creation

**Approach:**
- **Follow `/code` Pattern**: Use 60 tests as template
- **Domain-Specific Tests**: Adapt test fixtures and scenarios for each skill
- **Unit Tests**: Test each utility class method
- **Integration Tests**: Test GoT/ToT enhancements in workflow context
- **Opt-Out Tests**: Verify flags work independently
- **Regression Tests**: Ensure existing functionality isn't broken

**Test Creation Workflow:**
1. Create test directory structure
2. Write unit tests for utility classes (RED phase)
3. Implement utilities (GREEN phase)
4. Refactor for quality (REFACTOR phase)
5. Write integration tests
6. Write opt-out flag tests
7. Verify all tests pass

### Component 4: Documentation Updates

**Approach:**
- **SKILL.md Updates**: Add new steps with GoT/ToT enhancements
- **Usage Examples**: Show how to use enhancements in typical workflows
- **Opt-Out Documentation**: Explain when to disable enhancements
- **Version Bumps**: Update skill versions after integration

**Documentation Pattern (from `/code`):**

```markdown
### Step X.Y: Graph-of-Thought (GoT) Enhancement (NEW)

**Purpose**: Apply Graph-of-Thought reasoning to [domain-specific purpose].

**When**: [When in workflow this runs]

**What**: [What it does]

**How**: [How to use it]

**Opt-out**: Use `--no-got` flag to disable

**Execution**:
1. [Step 1]
2. [Step 2]
3. [Step 3]
4. [Step 4]
```

**Integration Notes:**
- GoT enhancement is **enabled by default** (quality-first design)
- Use `--no-got` flag to disable for [specific use cases]
- GoT findings complement [existing analysis]
- For [simple cases], GoT may be skipped with explicit note

---

## 6. Implementation Plan

**Phase 0: Infrastructure and Discovery (Weeks 1-3)**
**Priority**: CRITICAL (must complete before Phase 1)
**Estimated Effort**: 38-56 hours

**Purpose**: Establish foundation with baseline tests, performance benchmarks, and discovery to prevent blocking issues during implementation.

### Task 0.1: `/t` Skill Discovery and Validation
**Effort**: 2-4 hours
**Dependencies**: None
**Acceptance Criteria**:
- [x] `/t` skill location confirmed: `P:\.claude\skills\t\` (HALT-001 RESOLVED)
- [ ] SKILL.md read and validated
- [ ] Integration points identified (ToT for adaptive testing scenarios)
- [ ] Existing test structure analyzed
- [ ] GoT/ToT adaptation approach defined
- [ ] Test strategy outlined

**Implementation Steps**:
1. ✅ Search confirmed `/t` at `P:\.claude\skills\t\`
2. Read SKILL.md to understand workflow (multi-phase: Discovery → Plan → Execute → Verify)
3. Identify ToT integration point (enhances code flow tracing in Execution phase)
4. Analyze existing test structure (tests/ directory exists)
5. Define adaptation approach (ToT branching for adaptive test scenarios)
6. Outline test strategy (15-18 tests for ToT integration)

**EDGE-001 Resolution**: ✅ Complete - `/t` skill found and validated

### Task 0.2: Baseline Regression Test Suite
**Effort**: 20-30 hours
**Dependencies**: None
**Acceptance Criteria**:
- [ ] Each target skill has baseline test suite capturing current behavior
- [ ] Regression test infrastructure established
- [ ] Baseline measurements recorded (execution time, memory usage)
- [ ] Test fixtures created for common scenarios
- [ ] CI/CD integration verified (if applicable)
- [ ] Documentation created

**Implementation Steps**:
1. For each of 9 target skills:
   - Read SKILL.md to understand current functionality
   - Create `tests/` directory if missing
   - Write baseline tests for core workflows (3-5 critical tests per skill)
   - Record baseline execution times and memory usage
   - Create test fixtures for common scenarios (MAINT-003: real tests first, templates later)
2. Establish regression test infrastructure:
   - Create `P:\.claude\skills\shared\tests\fixtures.py` for common fixtures
   - Create `P:\.claude\skills\shared\tests\helpers.py` for test helpers
   - Configure coverage reporting (pytest-cov)
3. Document baseline test results

**HALT-002 Resolution**: Complete - Baseline tests created before any integration

### Task 0.3: Performance Benchmarks (Using /code Skill Data)
**Effort**: 8-12 hours
**Dependencies**: None
**Acceptance Criteria**:
- [ ] `/code` skill ToT overhead measured and documented
- [ ] Performance baseline established
- [ ] Rollback triggers defined (>50% overhead = rollback)
- [ ] Performance targets set for other skills
- [ ] Benchmark methodology documented

**Implementation Steps**:
1. Benchmark `/code` skill ToT branching:
   - Run `/code` workflow with ToT enabled vs disabled
   - Measure execution time, memory usage, CPU usage
   - Calculate overhead percentage
2. Establish baseline:
   - Document typical execution times (ToT: 3-8 minutes for typical files)
   - Document branch generation rates (5-20 branches per file)
   - Document pruning effectiveness (2-5 unlikely branches removed)
3. Define rollback triggers:
   - >50% overhead = rollback trigger
   - >30 seconds per file = performance concern
   - OOM errors = memory leak investigation
4. Set performance targets for other skills:
   - `/trace`: <5 minutes ToT overhead
   - `/debugRCA`: <8 minutes ToT overhead (multi-agent complexity)
   - `/arch`, `/plan-workflow`, `/p`, `/q`, `/r`, `/s`, `/t`: <6 minutes ToT overhead
5. Document benchmark methodology in `GOT_TOT_PERFORMANCE_BENCHMARKS.md`

**PERF-001/PERF-005 Resolution**: Complete - Performance benchmarks moved to Phase 0, baseline established

### Task 0.4: Python Version Compatibility Validation
**Effort**: 4-6 hours
**Dependencies**: None
**Acceptance Criteria**:
- [ ] All target skills checked for Python version requirements
- [ ] Python 3.14+ requirements validated
- [ ] Compatibility issues documented
- [ ] Migration strategy defined (if needed)
- [ ] Test environment configured

**Implementation Steps**:
1. Check each target skill:
   - Read SKILL.md for Python version requirements
   - Check `pyproject.toml`, `requirements.txt`, or equivalent
   - Test Python 3.14+ compatibility if not specified
2. Document compatibility:
   - Create matrix: skill × current Python version × required version
   - Identify skills needing Python upgrades
3. Define migration strategy:
   - If skill uses Python <3.14, plan upgrade path
   - Document breaking changes in Python versions
   - Ensure GoT/ToT utils work with skill's Python version
4. Configure test environment:
   - Set up Python 3.14+ for testing
   - Create virtual environment with required versions

**EDGE-005 Resolution**: Complete - Python version compatibility validated

---

**Phase 1: Quick Wins (Weeks 4-5)**
**Priority**: HIGH
**Estimated Effort**: 20-28 hours
**Note**: Effort estimates refined (LOGIC-002: actual sum, not underestimate)

### Task 1.1: `/trace` - ToT Integration
**Effort**: 8-12 hours
**Dependencies**: Task 0.2 (baseline tests), Task 0.6 (opt-out validation)
**Acceptance Criteria**:
- [ ] SKILL.md read and validated (EDGE-002)
- [ ] Existing test structure analyzed
- [ ] `utils/` directory created (or validated if exists)
- [ ] `utils/tot_scenario_generator.py` created and tested (TDD: RED → GREEN → REFACTOR)
- [ ] SKILL.md Step 4 (Define Scenarios) enhanced with ToT branching
- [ ] SKILL.md Step 5 (Create State Table) enhanced with branch tracking
- [ ] Opt-out flag `--no-tot` added to argument-hint
- [ ] Test suite created: `tests/test_tot_scenario_generation.py` (12-15 tests)
- [ ] Test suite created: `tests/test_trace_tot_integration.py` (8-10 tests)
- [ ] All tests pass (pytest)
- [ ] Version bumped
- [ ] Integration verified with `/code` skill ToT patterns

**Implementation Steps (TDD Workflow)**:
1. **Pre-implementation validation** (EDGE-002):
   - Read `P:\.claude\skills\trace\SKILL.md` to understand workflow
   - Validate existing structure (domains: code, skill, workflow, document)
   - Check if `utils/` exists (if not, create it)
2. **RED Phase**: Write failing tests:
   - Create `tests/test_tot_scenario_generator.py` with failing tests
   - Create `tests/test_trace_tot_integration.py` with failing tests
3. **GREEN Phase**: Implement utilities:
   - Copy `P:\.claude\skills\code\utils\tot_tracer.py` to `utils/tot_scenario_generator.py`
   - Adapt `BranchGenerator` for scenario generation (domain-specific)
   - Implement just enough to pass tests
4. **REFACTOR Phase**: Clean up implementation:
   - Refactor for quality while keeping tests green
   - Add documentation
5. **Integration**:
   - Add ToT branching logic to Step 4 (Define Scenarios)
   - Add branch tracking columns to Step 5 (Create State Table)
   - Update argument-hint: `argument-hint: <domain> <file> [--no-tot]`
6. **Verification**:
   - Run all tests and ensure they pass
   - Verify opt-out flag works (Task 0.6 baseline)
   - Check performance against Task 0.3 benchmarks (<5 minutes overhead)

**EDGE-002/EDGE-003 Resolution**: Validate structure first, create utils/ only if needed

### Task 1.2: `/debugRCA` - ToT Integration
**Effort**: 12-16 hours
**Dependencies**: None
**Acceptance Criteria**:
- [ ] `utils/tot_hypothesis_brancher.py` created and tested
- [ ] Phase 2 (Isolate) enhanced with ToT hypothesis branching
- [ ] Branch scoring integrated with evidence tier system
- [ ] Opt-out flag `--no-tot` added to argument-hint
- [ ] Test suite created: `test_tot_hypothesis_generation.py`, `test_debugrca_tot_integration.py`
- [ ] All tests pass
- [ ] Version bumped

**Implementation Steps**:
1. Create `P:\.claude\skills\debugRCA\utils\` directory
2. Copy `P:\.claude\skills\code\utils\tot_tracer.py` to `utils/tot_hypothesis_brancher.py`
3. Extend ToT for hypothesis trees (domain-specific branching logic)
4. Integrate branch scoring with evidence tier system (sure=multiple sources, maybe=single source, unlikely=no evidence)
5. Add ToT branching to Phase 2 (Isolate)
6. Update argument-hint: `argument-hint: <query> [--no-tot]`
7. Create test suite following `/code` pattern
8. Run tests and validate integration

---

**Phase 2: Medium Value (Weeks 3-5)**
**Priority**: MEDIUM
**Estimated Effort**: 42-62 hours

### Task 2.1: `/arch` - GoT Integration
**Effort**: 6-10 hours
**Dependencies**: None
**Acceptance Criteria**:
- [ ] `utils/got_architecture_analyzer.py` created and tested
- [ ] Stage 1 (Classify Intent) enhanced with GoT architecture analysis
- [ ] Architecture alternatives compared (supports, contradicts, unrelated)
- [ ] Opt-out flag `--no-got` added to argument-hint
- [ ] Test suite created: `test_got_architecture_analysis.py`, `test_arch_got_integration.py`
- [ ] All tests pass
- [ ] Version bumped

### Task 2.2: `/plan-workflow` - GoT/ToT Integration
**Effort**: 8-12 hours
**Dependencies**: None
**Acceptance Criteria**:
- [ ] `utils/got_plan_comparator.py` created and tested
- [ ] `utils/tot_scenario_explorer.py` created and tested
- [ ] Review mode enhanced with GoT plan comparison
- [ ] Section 3 (Discovery) enhanced with ToT scenario exploration
- [ ] Opt-out flags `--no-got`, `--no-tot` added to argument-hint
- [ ] Test suite created: `test_got_plan_comparison.py`, `test_tot_scenario_exploration.py`
- [ ] All tests pass
- [ ] Version bumped

### Task 2.3: `/p` - ToT Integration
**Effort**: 6-10 hours
**Dependencies**: None
**Acceptance Criteria**:
- [ ] `lib/tot_code_analyzer.py` created and tested
- [ ] P2 (Review) enhanced with ToT code path analysis
- [ ] Branching scenarios validated in P3 (Validate)
- [ ] Opt-out flag `--no-tot` added to argument-hint
- [ ] Test suite created: `test_tot_code_path_analysis.py`, `test_p_tot_integration.py`
- [ ] All tests pass
- [ ] Version bumped

### Task 2.4: `/s` - GoT/ToT Integration
**Effort**: 8-12 hours
**Dependencies**: None
**Acceptance Criteria**:
- [ ] `lib/got_strategy_analyzer.py` created and tested
- [ ] `lib/tot_outcome_explorer.py` created and tested
- [ ] Strategy generation enhanced with GoT strategy option analysis
- [ ] Outcome exploration enhanced with ToT outcome branching
- [ ] Opt-out flags `--no-got`, `--no-tot` added to argument-hint
- [ ] Test suite created: `test_got_strategy_analysis.py`, `test_tot_outcome_exploration.py`
- [ ] All tests pass
- [ ] Version bumped

### Task 2.5: `/q` - GoT/ToT Integration
**Effort**: 6-10 hours
**Dependencies**: None
**Acceptance Criteria**:
- [ ] `utils/got_requirement_analyzer.py` created and tested
- [ ] `utils/tot_question_brancher.py` created and tested
- [ ] Q2 (Collection) enhanced with GoT requirement analysis
- [ ] Q3 (Analyze) enhanced with ToT question branching
- [ ] Opt-out flags `--no-got`, `--no-tot` added to argument-hint
- [ ] Test suite created: `test_got_requirement_analysis.py`, `test_tot_question_branching.py`
- [ ] All tests pass
- [ ] Version bumped

### Task 2.6: `/r` - GoT/ToT Integration
**Effort**: 6-10 hours
**Dependencies**: None
**Acceptance Criteria**:
- [ ] `utils/got_memory_refiner.py` created and tested
- [ ] `utils/tot_reflection_path.py` created and tested
- [ ] Step 2 (Omission Checklist) enhanced with GoT memory refinement
- [ ] Step 4 (DUF Checks) enhanced with ToT reflection paths
- [ ] Opt-out flags `--no-got`, `--no-tot` added to argument-hint
- [ ] Test suite created: `test_got_memory_refinement.py`, `test_tot_reflection_paths.py`
- [ ] All tests pass
- [ ] Version bumped

---

**Phase 3: Discovery and Planning (Week 6)**
**Priority**: MEDIUM
**Estimated Effort**: 4-8 hours

### Task 3.1: `/t` Skill Discovery
**Effort**: 2-4 hours
**Dependencies**: None
**Acceptance Criteria**:
- [ ] `/t` skill location confirmed
- [ ] Skill structure analyzed
- [ ] Integration points identified
- [ ] GoT/ToT adaptation approach defined
- [ ] Test strategy outlined

**Implementation Steps**:
1. Search for `/t` skill in `P:\.claude\skills\`
2. If not found, investigate if it's an alias or different skill name
3. Read SKILL.md to understand workflow
4. Identify integration points for ToT (adaptive testing scenarios)
5. Create sub-plan for `/t` integration

### Task 3.2: Phases 3-7 Planning
**Effort**: 2-4 hours
**Dependencies**: Task 3.1
**Acceptance Criteria**:
- [ ] Phases 3-7 skills identified from original plan
- [ ] Integration approach defined for each phase
- [ ] Test strategies outlined
- [ ] Effort estimates refined
- [ ] Dependencies mapped

**Implementation Steps**:
1. Review original 7-phase plan from "oT+logic.md"
2. Identify skills in Phases 3-7
3. Assess readiness of each skill
4. Create integration sub-plans
5. Estimate effort and dependencies

---

**Phase 4: Infrastructure (Week 7)**
**Priority**: MEDIUM
**Estimated Effort**: 8-12 hours

### Task 4.1: Shared Utils Library
**Effort**: 4-6 hours
**Dependencies**: All Phase 1-2 tasks
**Acceptance Criteria**:
- [ ] Common GoT/ToT patterns extracted to shared library
- [ ] `P:\.claude\skills\shared\utils\got_core.py` created
- [ ] `P:\.claude\skills\shared\utils\tot_core.py` created
- [ ] Skills refactored to use shared utils where appropriate
- [ ] Tests updated to use shared utils
- [ ] Documentation updated

**Implementation Steps**:
1. Create `P:\.claude\skills\shared\utils\` directory
2. Extract common GoT logic (node extraction, edge analysis) to `got_core.py`
3. Extract common ToT logic (branch generation, scoring) to `tot_core.py`
4. Update skill-specific utils to inherit from or compose shared utils
5. Update tests to validate shared utils
6. Document shared library patterns

### Task 4.2: Test Infrastructure
**Effort**: 4-6 hours
**Dependencies**: Task 4.1
**Acceptance Criteria**:
- [ ] Test infrastructure templates created
- [ ] Test fixtures extracted to `P:\.claude\skills\shared\tests\fixtures.py`
- [ ] Test helpers created for common assertions
- [ ] Coverage reporting configured
- [ ] CI/CD integration updated (if applicable)
- [ ] Documentation updated

**Implementation Steps**:
1. Create test templates for GoT/ToT integration
2. Extract common fixtures (sample plans, code snippets, test data)
3. Create test helper functions (assert_node_count, assert_branch_score, etc.)
4. Configure coverage reporting (pytest-cov)
5. Update CI/CD pipelines if applicable
6. Document test infrastructure

---

**Phase 5: Quality Assurance (Week 8)**
**Priority**: HIGH
**Estimated Effort**: 12-16 hours

### Task 5.1: Cross-Skill Integration Testing
**Effort**: 6-8 hours
**Dependencies**: All Phase 1-4 tasks
**Acceptance Criteria**:
- [ ] Integration tests across all enhanced skills
- [ ] Opt-out flags validated across all skills
- [ ] Performance benchmarks run (ToT branching overhead)
- [ ] Memory usage validated
- [ ] Error handling tested
- [ ] Documentation completeness verified

**Implementation Steps**:
1. Create cross-skill integration test suite
2. Test opt-out flags work independently and together
3. Run performance benchmarks (ToT branching overhead)
4. Validate memory usage (GoT/ToT not causing bloat)
5. Test error handling (graceful degradation when GoT/ToT fail)
6. Verify documentation completeness

### Task 5.2: Regression Testing
**Effort**: 6-8 hours
**Dependencies**: Task 5.1
**Acceptance Criteria**:
- [ ] All existing functionality still works
- [ ] No breaking changes introduced
- [ ] Backward compatibility maintained
- [ ] Migration paths documented (if needed)
- [ ] Rollback strategies tested

**Implementation Steps**:
1. Run full test suite for each enhanced skill
2. Test existing workflows without GoT/ToT enhancements
3. Test existing workflows with GoT/ToT enhancements
4. Verify opt-out flags restore original behavior
5. Document any breaking changes
6. Test rollback strategies

---

**Phase 6: Documentation and Training (Week 9)**
**Priority**: LOW
**Estimated Effort**: 8-12 hours

### Task 6.1: Integration Documentation
**Effort**: 4-6 hours
**Dependencies**: All Phase 1-5 tasks
**Acceptance Criteria**:
- [ ] Integration guide created
- [ ] Best practices documented
- [ ] Troubleshooting guide created
- [ ] Migration guide created (for existing users)
- [ ] Example workflows documented

**Implementation Steps**:
1. Create `GOT_TOT_MULTI_SKILL_INTEGRATION.md`
2. Document best practices for GoT/ToT usage
3. Create troubleshooting guide
4. Document migration path for existing users
5. Provide example workflows
6. Update README files

### Task 6.2: User Training Materials
**Effort**: 4-6 hours
**Dependencies**: Task 6.1
**Acceptance Criteria**:
- [ ] Tutorial created for each enhanced skill
- [ ] Video demonstrations (optional)
- [ ] Example use cases documented
- [ ] FAQ created
- [ ] Community support resources identified

**Implementation Steps**:
1. Create tutorial for each enhanced skill
2. Record video demonstrations (optional)
3. Document example use cases
4. Create FAQ
5. Identify community support resources

---

**Phase 7: Deployment and Monitoring (Week 10)**
**Priority**: HIGH
**Estimated Effort**: 8-12 hours

### Task 7.1: Staged Rollout
**Effort**: 4-6 hours
**Dependencies**: All Phase 1-6 tasks
**Acceptance Criteria**:
- [ ] Phase 1 skills rolled out to internal users
- [ ] Feedback collected and issues addressed
- [ ] Phase 2 skills rolled out
- [ ] Phases 3-7 skills rolled out
- [ ] Monitoring configured

**Implementation Steps**:
1. Roll out Phase 1 skills (/trace, /debugRCA) to internal users
2. Collect feedback and address issues
3. Roll out Phase 2 skills in batches
4. Roll out Phases 3-7 skills
5. Configure monitoring and alerting

### Task 7.2: Success Metrics
**Effort**: 4-6 hours
**Dependencies**: Task 7.1
**Acceptance Criteria**:
- [ ] Metrics defined (bug detection rate, user satisfaction)
- [ ] Baseline measurements taken
- [ ] Ongoing monitoring configured
- [ ] Success criteria defined
- [ ] Retrospective scheduled

**Implementation Steps**:
1. Define success metrics (bug detection rate, user satisfaction)
2. Take baseline measurements
3. Configure ongoing monitoring
4. Define success criteria (e.g., 20% improvement in logic bug detection)
5. Schedule retrospective after 3 months

---

## Task Summary

**Total Tasks:** 22 tasks across 7 phases
**Total Estimated Effort:** 80-120 hours
**Timeline:** 10 weeks (with parallel execution possible)

**Quick Wins** (can start immediately):
- Task 1.1: `/trace` - ToT Integration (8-12 hours)
- Task 1.2: `/debugRCA` - ToT Integration (12-16 hours)

**Medium Priority** (after Quick Wins):
- Task 2.1-2.6: Phase 2 skills (42-62 hours)

**Investigation Needed**:
- Task 3.1: `/t` Skill Discovery (2-4 hours)

**Infrastructure** (after core integrations):
- Task 4.1-4.2: Shared utils and test infrastructure (8-12 hours)

---

## 7. Risks, Success Criteria, Dependencies

### Top Risks

1. **Multi-Agent Complexity** (MEDIUM risk)
   - GoT/ToT enhancements may conflict with existing multi-agent reasoning in `/debugRCA` and `/q`
   - **Mitigation**: Careful integration testing, graceful degradation when conflicts detected
   - **Owner**: Lead (to validate during Phase 5)

2. **Performance Overhead** (MEDIUM risk)
   - ToT branching may significantly increase execution time for complex workflows
   - **Mitigation**: Performance benchmarks in Phase 5, opt-out flags for users who need speed
   - **Owner**: Lead (to validate during Phase 5)

3. **Test Infrastructure Gaps** (HIGH risk)
   - Most target skills lack existing test suites, making regression testing difficult
   - **Mitigation**: Create test infrastructure early (Task 4.2), use `/code` test patterns
   - **Owner**: Lead (to address in Phase 4)

### Success Criteria

**Must Have** (blocking):
- [ ] All 9 target skills have GoT/ToT enhancements integrated
- [ ] All tests pass (unit + integration + regression)
- [ ] Opt-out flags work independently for each skill
- [ ] Existing functionality not broken (regression tests pass)
- [ ] Documentation updated for each skill
- [ ] Version bumped for each skill

**Should Have** (important but not blocking):
- [ ] Performance overhead < 20% for typical workflows
- [ ] User satisfaction > 4/5 for enhanced workflows
- [ ] Code coverage > 80% for new utilities
- [ ] Integration guide and best practices documented

**Nice to Have** (future enhancements):
- [ ] Video demonstrations created
- [ ] Community adoption metrics tracked
- [ ] Success metrics show > 20% improvement in logic bug detection
- [ ] Shared utils library created
- [ ] CI/CD integration updated

### Dependencies

**Technical Dependencies:**
- **Reference Implementation**: `/code` skill v2.22.0 with GoT/ToT integration complete
- **Utils Modules**: `got_planner.py` (14KB) and `tot_tracer.py` (12KB) from `/code/utils/`
- **Test Framework**: pytest, pytest-cov, fixtures, helpers
- **Python 3.14+**: All utils modules use modern Python patterns

**Skill Dependencies:**
- **Phase 1 Skills** (`/trace`, `/debugRCA`): No dependencies on other target skills
- **Phase 2 Skills** (`/arch`, `/plan-workflow`, `/p`, `/q`, `/r`, `/s`): No dependencies on each other
- **Phase 3** (`/t`): Discovery required before planning
- **Phases 4-7**: Depend on completion of earlier phases

**External Dependencies:**
- **User Approval**: For breaking changes or workflow modifications
- **Documentation**: "oT+logic.md" Perplexia AI conversation for original plan details
- **Testing Infrastructure**: Time to run comprehensive test suites

**Resource Dependencies:**
- **Development Time**: 80-120 hours estimated across 10 weeks
- **Review Time**: Code review and validation hours
- **Testing Time**: Test execution and validation time
- **Documentation Time**: Documentation creation and update time

### Rollback Strategy

**If Integration Fails:**

1. **Skill-Level Rollback**:
   - Each skill integration is independent
   - Can rollback individual skills without affecting others
   - Git revert to version before GoT/ToT integration

2. **Feature-Level Rollback**:
   - Opt-out flags provide runtime rollback
   - Users can disable GoT/ToT with `--no-got` or `--no-tot`
   - No code changes needed for opt-out

3. **Global Rollback**:
   - If shared utils library (Task 4.1) causes issues, revert to skill-specific utils
   - Revert SKILL.md changes to remove GoT/ToT steps
   - Keep test infrastructure for future use

**Rollback Triggers:**
- Performance overhead > 50%
- Critical bugs in production
- User satisfaction < 3/5
- Breaking changes in existing workflows

---

## Next Steps

1. **Begin Phase 1: Quick Wins**
   - Start with Task 1.1: `/trace` - ToT Integration (8-12 hours)
   - Follow with Task 1.2: `/debugRCA` - ToT Integration (12-16 hours)

2. **Review and Approve Plan**
   - Validate this plan covers all requirements
   - Confirm effort estimates and timeline
   - Approve proceeding to implementation

3. **Execute Implementation**
   - Follow TDD workflow for each task (RED → GREEN → REFACTOR)
   - Create comprehensive test suites
   - Validate integrations before proceeding

4. **Monitor and Adapt**
   - Track progress against timeline
   - Adjust estimates as needed
   - Address blockers promptly

---

**Plan Status:** READY-FOR-IMPLEMENTATION
**Next Review:** After Phase 1 completion (Quick Wins)
**Plan Owner:** Lead (to be assigned)
**Approval Required:** User confirmation to proceed with Phase 1
