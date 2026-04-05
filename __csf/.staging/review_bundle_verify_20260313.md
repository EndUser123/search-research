# Review Bundle: /verify Verification Orchestrator

**Generated**: 2026-03-13
**Scope**: P:/.claude/skills/verify/ + associated integration points
**File Count**: 49 files in verify skill + 2 external dependencies
**Execution Mode**: 2-agent parallel (49 files total)

---

## 1. PROJECT CONTEXT

### Bundle Metadata
- **Generated**: 2026-03-13
- **Scope**: `/verify` skill and associated files
- **File Count**: 49 files in verify skill, 2 external dependencies
- **Execution Mode**: 2-agent parallel (Explorer + Core Reader)

### Domain & Purpose
The `/verify` skill is a unified verification orchestrator that combines automated testing and manual verification into a systematic 4-tier process. It catches integration and end-to-end issues that component tests miss, with fast-fail checklist verification to catch configuration issues early. The system serves as the quality gate for skills, hooks, and features in the CSF ecosystem.

### Scale Metrics
- **LOC**: ~3,500 lines of Python code (estimated)
- **Major subsystems**: 6 (core orchestrator, 4 verification tiers, post-hoc analyzer, test suite)
- **Deployment scope**: Local development environment, invoked via slash command
- **Change frequency**: Active development (TASK-005, TASK-011 completed recently)

### Your Environment
- **OS and shell**: Windows 11, bash
- **Primary languages and frameworks**: Python 3.12+, pytest for testing, standard library only (no external deps for core)
- **Package managers and build tools**: None (stdlib-only hooks requirement)
- **Databases or external services**: None for core; post-hoc mode reads plan artifacts and evidence ledger JSON files

---

## 2. ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────┐
│                     /verify Skill                            │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  core/verifier.py (Verifier orchestrator)          │    │
│  │  - Detects target type (skill/hook/feature/code)   │    │
│  │  - Routes to real-time or post-hoc verification    │    │
│  └────┬───────────────────────────────────────┬───────┘    │
│       │                                       │            │
│       │ Real-time mode                        │ Post-hoc    │
│       │ (4-tier sequential)                    │ mode        │
│       ▼                                       ▼            │
│  ┌─────────────────────┐          ┌──────────────────────┐│
│  │ Tier 0: Checklist   │          │ post_hoc_analyzer.py  ││
│  │ (tier0_checklist)   │          │ - Generate RTM        ││
│  │ - Fast-fail         │          │ - Calculate TSR       ││
│  │ - Config validation │          │ - Evaluate completeness││
│  └─────────┬───────────┘          └──────────────────────┘│
│       │ FAIL?                                          │    │
│       │ Yes → Stop (fast-fail)                         │    │
│       │ No → Continue                                  │    │
│       ▼                                               │    │
│  ┌─────────────────────┐                               │    │
│  │ Tier 1: Component   │                               │    │
│  │ (tier1_component)   │                               │    │
│  │ - Unit tests (pytest)│                              │    │
│  └─────────┬───────────┘                               │    │
│            ▼                                           │    │
│  ┌─────────────────────┐                               │    │
│  │ Tier 2: Integration │                               │    │
│  │ (tier2_integration) │                               │    │
│  │ - Hook chains       │                               │    │
│  │ - Router execution  │                               │    │
│  └─────────┬───────────┘                               │    │
│            ▼                                           │    │
│  ┌─────────────────────┐                               │    │
│  │ Tier 3: E2E         │                               │    │
│  │ (tier3_e2e)         │                               │    │
│  │ - Full workflow     │                               │    │
│  └─────────┬───────────┘                               │    │
│            │                                           │    │
│            └─────────────────────┬─────────────────────┘│
│                                    ▼                      │
│                       ┌──────────────────────┐            │
│                       │ report.py             │            │
│                       │ - Generate report     │            │
│                       │ - Evidence artifacts  │            │
│                       └──────────────────────┘            │
└─────────────────────────────────────────────────────────────┘
         │                                      │
         │ External dependencies                │
         ▼                                      ▼
┌─────────────────────┐              ┌──────────────────────┐
│ plan-workflow skill  │              │ /code skill          │
│ (lib/plan_visualizer)│              │ (evidence ledger)    │
│ - RTM generation     │              │ - TSR tracking       │
│ - Keyword matching   │              │ - TDD evidence       │
└─────────────────────┘              └──────────────────────┘
```

### For each major subsystem:

#### Core Orchestrator (core/verifier.py)
- **Purpose**: Central verification coordinator that routes to appropriate verification mode
- **Files**: core/verifier.py, core/__init__.py
- **Entry points**: `Verifier.run_verification()`, `Verifier.run_post_hoc_verification()`
- **Dependencies**: tiers/* modules (tier0-tier3, post_hoc_analyzer)
- **Critical invariants**: Must complete all 4 tiers for real-time mode; must meet TSR ≥ 95% for post-hoc mode

#### Tier 0: Checklist Verification (tiers/tier0_checklist.py)
- **Purpose**: Fast-fail verification to catch configuration issues before expensive tests
- **Files**: tiers/tier0_checklist.py, tiers/tests/test_tier0_checklist.py
- **Entry points**: `run_checklist_verification(target_type, target_path)`
- **Dependencies**: None (stdlib only)
- **Critical invariants**: If checklist fails, verification stops immediately (fast-fail behavior)

#### Tier 1: Component Tests (tiers/tier1_component.py)
- **Purpose**: Run unit tests for target component
- **Files**: tiers/tier1_component.py
- **Entry points**: `Tier1Component.run_tests()`
- **Dependencies**: pytest
- **Critical invariants**: All unit tests must pass

#### Tier 2: Integration Check (tiers/tier2_integration.py)
- **Purpose**: Verify hook chains and router integration
- **Files**: tiers/tier2_integration.py
- **Entry points**: `Tier2Integration.verify_integration()`
- **Dependencies**: Hook infrastructure
- **Critical invariants**: Hook chains must execute without errors

#### Tier 3: E2E Tests (tiers/tier3_e2e.py)
- **Purpose**: Execute full workflow end-to-end
- **Files**: tiers/tier3_e2e.py
- **Entry points**: `Tier3E2E.run_e2e_test()`
- **Dependencies**: Skill/hook invocation infrastructure
- **Critical invariants**: Complete workflow must execute successfully

#### Post-Hoc Analyzer (tiers/post_hoc_analyzer.py)
- **Purpose**: Analyze completed work through chat history artifacts (RTM + TSR + LLM-as-Judge)
- **Files**: tiers/post_hoc_analyzer.py, tests/test_post_hoc.py, tests/test_integration_post_hoc.py
- **Entry points**: `PostHocAnalyzer.run_analysis()`
- **Dependencies**: plan-workflow/lib/plan_visualizer.py (RTM), /code skill evidence ledger (TSR)
- **Critical invariants**: Must meet all three criteria: requirements coverage ≥ 95%, TSR ≥ 95%, evidence quality ≥ 95%

---

## 3. EXECUTION AND DATA FLOW

### Execution Sequences

#### Real-Time Verification Mode (default)
```
User invokes: /verify skill:arch
        ↓
Verifier.detect_verification_target()
        ↓
Parse target type (skill/hook/feature/code)
        ↓
Verifier.run_verification()
        ↓
┌─────────────────────────────────────┐
│ SEQUENTIAL 4-TIER EXECUTION         │
├─────────────────────────────────────┤
│ 1. Tier 0: Checklist (fast-fail)   │ ← If FAIL → STOP
│ 2. Tier 1: Component tests         │
│ 3. Tier 2: Integration check        │
│ 4. Tier 3: E2E test                 │
└─────────────────────────────────────┘
        ↓
report.generate_verification_report()
        ↓
Output: JSON + markdown report with evidence
```

#### Post-Hoc Verification Mode (--post-hoc flag)
```
User invokes: /verify --post-hoc --plan <plan_path> --evidence-ledger <ledger_path>
        ↓
Verifier.run_post_hoc_verification()
        ↓
PostHocAnalyzer.__init__(plan_path, evidence_ledger_path)
        ↓
┌─────────────────────────────────────┐
│ PARALLEL 3-PHASE ANALYSIS          │
├─────────────────────────────────────┤
│ 1. Generate RTM (keyword matching) │ ← PlanVisualizer
│ 2. Calculate TSR (evidence ledger) │ ← TDD evidence
│ 3. Evaluate completeness (LLM)     │ ← Weighted scoring
└─────────────────────────────────────┘
        ↓
report.generate_post_hoc_report()
        ↓
Output: JSON report with RTM, TSR, evaluation, summary
```

### Mandatory Ordering Constraints

**Real-time mode**: Sequential execution (Tier 0 → 1 → 2 → 3)
- Tier 0 MUST run first (fast-fail checkpoint)
- Tier 1, 2, 3 run in sequence (each tier builds on previous)
- Cannot skip tiers or run out of order

**Post-hoc mode**: Parallel phase execution (RTM + TSR can run independently)
- RTM generation and TSR calculation are independent
- Evaluation phase requires both RTM and TSR to complete
- All three phases must complete before report generation

### State Management

**State stores**: In-memory Python objects during execution
- No persistent state in /verify skill itself
- Post-hoc mode reads external state: plan artifacts (.md) and evidence ledger (.json)

**Consistency model**: Ephemeral state
- Each verification run is independent
- No cross-run state persistence
- Evidence artifacts stored in report output

**Isolation boundaries**: Each tier is isolated
- Tier modules do not share state
- Each tier returns result dictionary
- Verifier orchestrator aggregates results

### Error Handling

**Fail-open vs fail-closed policy**: Fail-closed
- **Tier 0**: Fast-fail (if checklist fails, verification stops)
- **Tier 1-3**: Any failure → overall verification FAIL
- **Post-hoc mode**: TSR < 95% → overall FAIL

**Retry/timeout behavior**: No automatic retry
- Failed verification requires manual fix and re-run
- No built-in retry logic
- Timeout not configured (uses default pytest/hook execution timeouts)

---

## 4. COMPONENT INVENTORY

### Core Logic

#### core/verifier.py
- **Path**: P:/.claude/skills/verify/core/verifier.py
- **Key classes**: `Verifier`
- **Responsibilities**:
  - Detect verification mode (real-time vs post-hoc)
  - Route to appropriate verification workflow
  - Aggregate results from all tiers
  - Generate final verification status
- **Inputs**: Target type (skill/hook/feature/code), target name/path, optional plan/evidence paths
- **Outputs**: Verification report (dict with status, tier results, evidence)
- **Known limitations**:
  - Does not use subagents (synchronous design)
  - No automatic retry on failure
  - Limited to 4 predefined tiers (not extensible)

#### tiers/post_hoc_analyzer.py
- **Path**: P:/.claude/skills/verify/tiers/post_hoc_analyzer.py
- **Key classes**: `PostHocAnalyzer`
- **Responsibilities**:
  - Generate RTM from plan artifacts (via PlanVisualizer)
  - Calculate TSR from evidence ledger
  - Evaluate conversation completeness using LLM-as-Judge
  - Detect orphan requirements (requirements with no mapped tasks)
- **Inputs**: Plan file path (.md), evidence ledger path (.json)
- **Outputs**: Post-hoc analysis report (RTM, TSR, evaluation, summary)
- **Known limitations**:
  - **RTM uses 20% keyword overlap threshold** (can miss requirements if terminology doesn't match)
  - No semantic understanding of requirement intent
  - Heuristic-based (not guaranteed completeness)
  - Depends on external PlanVisualizer from plan-workflow skill

#### tiers/tier0_checklist.py
- **Path**: P:/.claude/skills/verify/tiers/tier0_checklist.py
- **Key functions**: `run_checklist_verification(target_type, target_path)`
- **Responsibilities**:
  - Run checklist-based verification for skills/hooks/features
  - Fast-fail if critical items missing
  - Return structured findings
- **Inputs**: Target type, target path
- **Outputs**: Checklist result (status, items_checked, items_passed, findings)
- **Known limitations**:
  - Checklist items are hardcoded
  - No dynamic checklist generation
  - Limited to predefined target types

#### tiers/tier1_component.py
- **Path**: P:/.claude/skills/verify/tiers/tier1_component.py
- **Key classes**: `Tier1Component`
- **Responsibilities**:
  - Run pytest on target component
  - Return test results
- **Inputs**: Target path
- **Outputs**: Test results (status, passed, failed, output)
- **Known limitations**:
  - Assumes pytest is available
  - No test result caching

#### tiers/tier2_integration.py
- **Path**: P:/.claude/skills/verify/tiers/tier2_integration.py
- **Key classes**: `Tier2Integration`
- **Responsibilities**:
  - Verify hook chain execution
  - Check router integration
- **Inputs**: Target path, target type
- **Outputs**: Integration results (status, findings)
- **Known limitations**:
  - Hook-specific logic
  - Limited integration test scenarios

#### tiers/tier3_e2e.py
- **Path**: P:/.claude/skills/verify/tiers/tier3_e2e.py
- **Key classes**: `Tier3E2E`
- **Responsibilities**:
  - Execute full workflow end-to-end
  - Verify complete execution
- **Inputs**: Target path, target type
- **Outputs**: E2E test results (status, output)
- **Known limitations**:
  - Requires full workflow setup
  - May be slow for complex workflows

### Utilities/Helpers

#### report.py
- **Path**: P:/.claude/skills/verify/report.py
- **Key functions**: `generate_verification_report()`, `generate_post_hoc_report()`
- **Responsibilities**:
  - Format verification results into reports
  - Generate both JSON and markdown outputs
- **Inputs**: Verification results dictionary
- **Outputs**: Formatted report (JSON + markdown)
- **Known limitations**:
  - Report format is hardcoded
  - No customization options

#### verify_docs.py
- **Path**: P:/.claude/skills/verify/verify_docs.py
- **Key functions**: Documentation quality verification
- **Responsibilities**:
  - Verify documentation sections meet quality criteria
  - Check line counts, code blocks, subheadings
- **Inputs**: List of (file_path, section_title) tuples
- **Outputs**: Status report (PASS/REVIEW) with metrics
- **Known limitations**:
  - Simple heuristics (line count, code block count)
  - Does not check documentation quality

### Configuration

#### SKILL.md
- **Path**: P:/.claude/skills/verify/SKILL.md
- **Purpose**: Skill documentation and workflow definition
- **Key sections**: Purpose, workflow steps, tier details, troubleshooting
- **Triggers**: `/verify`, `/verify <target>`, `/verify --post-hoc`
- **Known limitations**:
  - Documentation may not always match implementation
  - No automatic validation that docs are up-to-date

### Test Suite

#### tests/test_post_hoc.py
- **Path**: P:/.claude/skills/verify/tests/test_post_hoc.py
- **Purpose**: Unit tests for post-hoc analyzer
- **Coverage**: RTM generation, TSR calculation, evaluation logic
- **Known limitations**:
  - Uses fixtures (may not cover all real-world scenarios)

#### tests/test_integration_post_hoc.py
- **Path**: P:/.claude/skills/verify/tests/test_integration_post_hoc.py
- **Purpose**: Integration tests for post-hoc workflow
- **Coverage**: Full workflow with realistic plan/evidence artifacts
- **Known limitations**:
  - Test fixtures may not reflect production complexity

#### tests/test_verifier_tier0.py
- **Path**: P:/.claude/skills/verify/tests/test_verifier_tier0.py
- **Purpose**: Unit tests for Tier 0 checklist verification
- **Coverage**: Checklist logic for skills/hooks/features
- **Known limitations**:
  - May not test all checklist items

### Infrastructure

#### __main__.py
- **Path**: P:/.claude/skills/verify/__main__.py
- **Purpose**: Entry point for running verifier as CLI tool
- **Key functions**: `main()` with argument parsing
- **Inputs**: CLI arguments (--target, --post-hoc, --plan, --evidence-ledger)
- **Outputs**: Verification report to stdout
- **Known limitations**:
  - Limited CLI argument options
  - No interactive mode

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars

1. **4-Tier Sequential Verification**: Real-time mode MUST execute all 4 tiers in sequence (Tier 0 → 1 → 2 → 3)
2. **Fast-Fail Principle**: Tier 0 checklist runs first; if it fails, verification stops immediately
3. **Evidence-Based Verification**: Every tier MUST show actual test/execution output (no trust without evidence)
4. **Post-Hoc Completeness**: Post-hoc mode MUST meet ALL three criteria (requirements ≥ 95%, TSR ≥ 95%, evidence ≥ 95%)

### Technology Constraints

1. **Standard Library Only**: Core /verify skill uses NO external dependencies (stdlib-only requirement for hooks)
2. **Pytest for Testing**: Tier 1 component tests use pytest (assumed available in environment)
3. **No Subagents**: /verify does NOT use subagents (synchronous design is appropriate for verification use case)
4. **JSON Evidence Storage**: Evidence ledgers stored as JSON (TSR tracking from /code skill)
5. **Markdown Plan Artifacts**: Plans stored as Markdown (RTM generation via PlanVisualizer)

### Performance SLAs

1. **Tier 0 Fast-Fail**: Checklist verification MUST complete in seconds (< 5s typical)
2. **Tier 1-3 Execution**: Component/integration/E2E tests complete in minutes (varies by target)
3. **Post-Hoc Analysis**: RTM + TSR + evaluation complete in < 30s typical

### Things That Must NOT Change

1. **4-Tier Structure**: Cannot skip or reorder tiers in real-time mode (architectural invariant)
2. **Fast-Fail Behavior**: Tier 0 failure MUST stop verification (cannot continue to Tier 1-3)
3. **Evidence Requirement**: Cannot claim "verified" without evidence from each tier
4. **TSR 95% Threshold**: Post-hoc mode requires TSR ≥ 95% to pass (cannot lower threshold)
5. **RTM Keyword Matching**: Current implementation uses 20% overlap threshold (documented limitation, not a bug)

---

## 6. KNOWN ISSUES

### Issue #1: RTM Keyword Matching Limitation
- **Scenario**: Requirement says "Implement user authentication" but task says "Add JWT login system"
- **Expected**: Requirement maps to task (semantic understanding)
- **Actual**: Requirement may NOT map if keyword overlap < 20% (line 751 in plan_visualizer.py)
- **Impact**: Post-hoc verification can produce false negatives (requirements implemented but not detected)
- **Current workaround**: Manual review of orphan requirements list in verification report
- **Root cause**: Keyword matching is heuristic-based, not semantic
- **Severity**: MEDIUM (verification ~70-80% effective, not 100%)

### Issue #2: No Subagent Usage
- **Scenario**: Large verification job would benefit from parallel execution
- **Expected**: /verify uses subagents for parallel tier execution
- **Actual**: /verify uses synchronous execution (no subagents)
- **Impact**: Slower verification for large targets (no parallelism)
- **Current workaround**: None (design choice, not a bug)
- **Root cause**: Synchronous design appropriate for verification use case (deterministic execution)
- **Severity**: LOW (design choice, not a bug)

### Issue #3: Post-Hoc Mode Requires Manual Evidence Ledger Path
- **Scenario**: User invokes `/verify --post-hoc --plan <plan>` but forgets `--evidence-ledger` path
- **Expected**: Auto-discover evidence ledger from plan or chat history
- **Actual**: Error or TSR = 0% (no ledger found)
- **Impact**: Poor user experience, requires manual path specification
- **Current workaround**: Always specify both `--plan` and `--evidence-ledger` paths explicitly
- **Root cause**: No auto-discovery mechanism for evidence ledgers
- **Severity**: MEDIUM (UX issue)

### Issue #4: Tier 0 Checklist Hardcoded
- **Scenario**: New target type added (e.g., "workflow") but Tier 0 doesn't support it
- **Expected**: Tier 0 dynamically generates checklist based on target type
- **Actual**: Tier 0 has hardcoded checklist for skill/hook/feature only
- **Impact**: Cannot verify new target types without code changes
- **Current workaround**: Add new target type to tier0_checklist.py
- **Root cause**: Checklist items are hardcoded, not data-driven
- **Severity**: MEDIUM (extensibility issue)

### Issue #5: No Verification Caching
- **Scenario**: Run `/verify skill:arch` twice without changes
- **Expected**: Second run uses cached results (instant)
- **Actual**: Both runs execute full 4-tier workflow (slow)
- **Impact**: Wasted time on repeated verifications
- **Current workaround**: None
- **Root cause**: No caching mechanism implemented
- **Severity**: LOW (performance optimization)

---

## 7. INTEGRATION POINTS

### Where New Solutions Can Plug In

#### Adding a New Verification Tier
- **Interface**: Create new file in `tiers/` directory (e.g., `tiers/tier4_custom.py`)
- **Invocation model**: Import and instantiate in `core/verifier.py`
- **Data exchange**: Return result dictionary with `status`, `findings`, `evidence` keys
- **Output expectations**: Follow same structure as existing tiers

#### Adding Post-Hoc Analysis Phases
- **Interface**: Add new method to `tiers/post_hoc_analyzer.py` (e.g., `analyze_custom_metric()`)
- **Invocation model**: Call from `PostHocAnalyzer.run_analysis()` after RTM/TSR phases
- **Data exchange**: Accept plan/evidence inputs, return custom analysis dict
- **Output expectations**: Include in evaluation dict before weighted scoring

#### Custom Report Formats
- **Interface**: Extend `report.py` with new function (e.g., `generate_custom_report()`)
- **Invocation model**: Call from `Verifier.run_verification()` or `Verifier.run_post_hoc_verification()`
- **Data exchange**: Accept verification results dict, return formatted string
- **Output expectations**: Can output any format (JSON, markdown, HTML, etc.)

#### External Tool Integration
- **Interface**: Create adapter in new file (e.g., `integrations/custom_tool.py`)
- **Invocation model**: Import and call from appropriate tier
- **Data exchange**: Map verification results to tool's input format
- **Output expectations**: Parse tool output and return as verification findings

---

## 8. APPENDIX: SAMPLE RUNS / LOGS

### Sample Real-Time Verification Output

```
### Verification Report: skill:arch
**Overall Status**: ✅ PASS
**Generated**: 2026-03-13 10:30:45

### Tier 0: Checklist Verification
**Status**: ✅ PASS
**Duration**: 0.3s
**Items Checked**: 5
**Items Passed**: 5
**Findings**:
- ✅ Problem statement documented
- ✅ Context analysis complete
- ✅ Solution proposed
- ✅ Risks identified
- ✅ Test coverage planned

### Tier 1: Component Tests
**Status**: ✅ PASS
**Command**: pytest .claude/skills/arch/tests/ -v
**Evidence**:
- test_arch_activation PASSED
- test_arch_intent_detection PASSED
- test_arch_fallback PASSED

### Tier 2: Integration Check
**Status**: ✅ PASS
**Findings**:
- ✅ Skill activation works correctly
- ✅ Router integration verified

### Tier 3: E2E Test
**Status**: ✅ PASS
**Command**: /arch "test query"
**Evidence**:
- Skill invoked successfully
- Returned valid architecture advice
```

### Sample Post-Hoc Verification Output

```
### Post-Hoc Verification Report
**Overall Status**: ❌ FAIL
**Overall Score**: 68.5%
**Generated**: 2026-03-13 11:15:30

### RTM (Requirements Traceability Matrix)
**Total Requirements**: 4
**Total Tasks**: 4
**Requirement Coverage**: 75.0%
**Mapped Requirements**: 3/4
**Orphan Requirements**: 1 (REQ-003: "LLM-as-Judge evaluation of completeness")

### TSR (Task Success Rate)
**Total Attempted**: 4 tasks
**Completed**: 2 tasks (all 4 evidence types)
**Failed**: 2 tasks (partial evidence)
**Blocked**: 0 tasks
**TSR**: 50.0%

### Evaluation (LLM-as-Judge)
**Overall Score**: 68.5%
- Requirements Coverage: 75.0% (below 95% threshold)
- Task Completion: 50.0% (below 95% threshold)
- Evidence Quality: 100.0% (all tasks have acceptance criteria)

### Findings
**HIGH**: Task Success Rate (TSR) is 50.0%, below 95% threshold
**Details**:
  - TASK-003: "Update documentation" → Only RED, GREEN evidence present
  - TASK-004: "Write unit tests" → Only RED evidence present
  - Missing: REFACTOR, VERIFY evidence

**HIGH**: Requirements coverage is 75.0%, below 95% threshold
**Details**:
  - REQ-003: "LLM-as-Judge evaluation of completeness" → No mapped tasks
  - Recommendation: Add task for LLM-as-Judge implementation

### Summary
**Total Findings**: 2
**High Severity**: 2
**Medium Severity**: 0
**Low Severity**: 0

**Recommendation**: Complete TASK-003 and TASK-004 (add REFACTOR, VERIFY evidence), add task for REQ-003 (LLM-as-Judge)
```

---

## END OF REVIEW BUNDLE

**Next Steps**:
1. Use this bundle as context for LLM question-answering about /verify
2. Refer to "Known Issues" section for current limitations
3. Refer to "Integration Points" section for extension points
4. Refer to sample runs for expected output formats
