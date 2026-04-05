# Tree-of-Thought (ToT) Integration Reference

## ToT Phase Branching

**What**: Automatically generate branching scenarios for code maturation phases
**When**: Automatic enhancement during phase transitions and HALT condition analysis (enabled by default)
**Benefit**: Discover alternative maturation paths beyond linear phase progression

**Phase Branch Types**:

**P1 (Build) Scenarios**:
- **sure**: Tests pass cleanly, no issues detected
- **maybe**: Tests pass with warnings, flaky tests detected
- **unlikely**: Tests fail, TDD loop required, blocking errors

**P2 (Review) Scenarios**:
- **sure**: No findings or minor style issues only
- **maybe**: MEDIUM/LOW findings found, fix loop required
- **unlikely**: CRITICAL/HIGH findings found, blocking issues, HALT required

**P3 (Validate) Scenarios**:
- **sure**: All validation checks pass, no warnings
- **maybe**: Non-blocking warnings detected, documentation gaps
- **unlikely**: Blocking validation failures, missing gates, HALT with --publish

**P4-P6 Scenarios**:
- **sure**: Documentation complete, certification passed, security scan clean
- **maybe**: Minor documentation gaps, certification warnings, security notes
- **unlikely**: Blocking publish issues, certification failures, security vulnerabilities

**Opt-out Flag**:
```bash
# Disable ToT enhancement
export P_NO_TOT=true
```

## ToT Detection Path Analysis

**What**: Generate branching detection paths for scope inference and state detection
**When**: Automatic enhancement during Step 0 (Scope Inference) and Step 1 (State Detection)
**Benefit**: Explore alternative detection strategies when signals are ambiguous

**Detection Branch Types**:

**Scope Inference Branches**:
- **sure**: Clear scope from chat context or explicit argument
- **maybe**: Scope from session ledger or natural language resolution
- **unlikely**: No clear scope, must ask user for clarification

**State Detection Branches**:
- **sure**: Unambiguous state (e.g., tests failing, no review markers)
- **maybe**: Conflicting signals (e.g., review markers exist but files changed)
- **unlikely**: Unknown state, missing critical files or markers

## ToT HALT Condition Analysis

**What**: Analyze branching HALT scenarios for each phase
**When**: Automatic enhancement when phase encounters blocking conditions
**Benefit**: Understand why phases halt and explore alternative resolution paths

**HALT Branch Types**:

**P1 HALT Scenarios**:
- **sure**: Tests fail after max TDD loops (3 attempts)
- **maybe**: Flaky tests detected, test infrastructure issues
- **unlikely**: Test suite crashes, pytest unavailable, syntax errors

**P2 HALT Scenarios**:
- **sure**: CRITICAL findings remain after fix loop
- **maybe**: HIGH findings exceed threshold, timeout in fix loop
- **unlikely**: Review agent crashes, no findings generated, parsing errors

**P3 HALT Scenarios**:
- **sure**: Blocking validation failures remain
- **maybe**: Non-blocking warnings with --publish flag (treated as blocking)
- **unlikely**: Validation crashes, missing validation scripts, environment issues

**Resolution Branch Analysis**:
For each HALT scenario, ToT generates:
- **Direct resolution**: Fix the blocking issue (e.g., fix failing tests)
- **Workaround path**: Skip phase with flag (e.g., /p --phase=3 to skip P2)
- **Alternative path**: Different maturation strategy (e.g., /p --quick for light mode)

## ToT Integration Workflow

**Enhanced Phase Transition Flow**:
```
Step 2: Determine Next Action
  |
BranchGenerator generates phase transition scenarios
  |
Score branches: sure/maybe/unlikely
  |
Select most likely path for execution
  |
Run phase with scenario awareness
  |
If HALT: Analyze HALT branches, suggest resolution paths
```

**Example Output**:
```
ToT Analysis: Phase Transition (P2 -> P3)
==========================================

Detection: Tests pass, no review markers
  Branch 1 (sure): Run P2 (Review) - 85% confidence
  Branch 2 (maybe): Re-run P1 (Build) if tests flaky - 10% confidence
  Branch 3 (unlikely): Run P0 (Scaffold) if structure missing - 5% confidence

Selected: Branch 1 (sure)

[P2] Starting Review...

{review executes}

[P2] Complete: Review
   8 findings (2 HIGH, 4 MEDIUM, 2 LOW)

ToT Analysis: HALT Conditions
================================

HIGH findings detected -> HALT likely
  Resolution Path 1 (sure): Fix HIGH findings -> re-run P2 -> continue to P3
  Resolution Path 2 (maybe): Add --quick flag -> skip non-blocking fixes -> continue
  Resolution Path 3 (unlikely): Override with --force -> proceed to P3 (not recommended)

Next Action: /tdd Fix <finding-ids> or /p --quick to continue
```

**What This Catches**:
- Unexplored HALT scenarios that cause pipeline stalls
- Alternative resolution paths when phases block
- Edge cases in detection logic (conflicting signals)
- Performance issues (e.g., flaky tests causing repeated P1 runs)
