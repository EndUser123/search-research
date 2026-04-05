# Architecture Review: Integrating External Skill Patterns into /code

**Date**: 2026-03-04
**Reviewer**: /arch skill (python template)
**Scope**: Analyzing Forge, workflow-patterns, qcsd-development-swarm, and testing-workflow for integration into /code skill

## Executive Summary

**Objective**: Identify concrete patterns from external skills that can enhance /code outcomes.

**Key Finding**: Three high-value patterns identified that would have prevented the unverified_stance_detector bugs:
1. **Pattern Validation Framework** (Forge)
2. **Coverage-Driven Verification Gates** (workflow-patterns)
3. **Pre-Done Evidence Checklist** (workflow-patterns + Forge synthesis)

**Impact**: These patterns would catch detector pattern bugs, missing tests, and incomplete implementation before deployment.

---

## Analysis Methodology

**Skills Analyzed**:
- **Forge** (ClawHub, 1619 lines) - Autonomous quality engineering swarm
- **workflow-patterns** (ClawHub, 339 lines) - TDD lifecycle with checkpoints
- **qcsd-development-swarm** (SkillHub) - Quality-driven development swarm
- **testing-workflow** (SkillHub) - Meta-skill orchestration

**Review Focus**:
- Test coverage enforcement mechanisms
- Quality gate implementations
- Verification protocols
- Pattern validation approaches

---

## Pattern 1: Pattern Validation Framework (Forge)

### Source Implementation

**Location**: Forge skill, Quality Gate Enforcer agent

**Architecture**:
```python
# Forge's 7 Quality Gates
QUALITY_GATES = {
    "functional": 100,      # All tests pass
    "behavioral": 100,     # All Gherkin scenarios pass
    "coverage": {
        "overall": 85,      # >=85% overall coverage
        "critical": 95      # >=95% for critical paths
    },
    "security": "PASS",
    "accessibility": "PASS",
    "resilience": "PASS",
    "contract": "PASS"
}
```

**Key Mechanism**: Pattern validation happens BEFORE implementation:
1. Extract detector patterns (regex, keywords, phrases)
2. Validate against known false-positive patterns
3. Test pattern sets against adversarial inputs
4. Store validated patterns in memory with confidence scores

### Integration into /code

**Current Gap**: unverified_stance_detector.py had three preventable bugs:
1. False positive on "blocked" keyword appearing in injected context
2. Empty hedge patterns too broad ("let me verify")
3. Missing test coverage for edge cases

**Proposed Solution**: Add **Step 4.6: Pattern Validation** to /code Phase 4 (PLAN)

**Implementation**:
```python
# New file: P:/.claude/skills/code/scripts/pattern_validation.py

from typing import NamedTuple, List
import re

class PatternIssue(NamedTuple):
    pattern: str
    issue: str
    severity: str  # "critical" | "high" | "medium"
    recommendation: str

def validate_detector_patterns(
    patterns: List[str],
    context_keywords: List[str]
) -> List[PatternIssue]:
    """
    Validate detector patterns against common failure modes.

    Checks:
    1. Pattern conflicts with injected context keywords
    2. Pattern over-matches (too broad)
    3. Pattern under-matches (too narrow)
    4. Regex syntax errors
    """
    issues = []

    for pattern in patterns:
        # Check 1: Context keyword conflicts
        for keyword in context_keywords:
            if keyword.lower() in pattern.lower():
                issues.append(PatternIssue(
                    pattern=pattern,
                    issue=f"Pattern matches injected context keyword '{keyword}'",
                    severity="critical",
                    recommendation=f"Use word boundaries: \\b{pattern}\\b"
                ))

        # Check 2: Over-matching (common words)
        common_words = {"verify", "check", "that", "this"}
        if pattern.lower() in common_words:
            issues.append(PatternIssue(
                pattern=pattern,
                issue="Pattern is too broad (common word)",
                severity="high",
                recommendation="Add surrounding context or use phrase matching"
            ))

        # Check 3: Regex syntax
        try:
            re.compile(pattern)
        except re.error as e:
            issues.append(PatternIssue(
                pattern=pattern,
                issue=f"Invalid regex: {e}",
                severity="critical",
                recommendation="Fix regex syntax"
            ))

    return issues
```

**Integration Point**: Add to `/code` Phase 4 (PLAN) after pre-mortem:

```markdown
### Step 4.6: Pattern Validation (NEW)

**When to run**: After implementing detector modules with pattern sets

**What to validate**:
- Detector patterns (regex, keyword lists, phrase sets)
- Context injection strings (check for false positives)
- Factual claim indicators (check for over-matching)

**How to validate**:
```bash
python P:/.claude/skills/code/scripts/pattern_validation.py \
  --patterns-file anti_sycophancy/unverified_stance_detector.py \
  --context-keywords "blocked,verification,evidence"
```

**Exit criteria**: No critical or high-severity pattern issues
```

**Evidence Requirement**: All pattern validation checks must pass before proceeding to TDD phase.

---

## Pattern 2: Coverage-Driven Verification Gates (workflow-patterns)

### Source Implementation

**Location**: workflow-patterns skill, Step 6: Verify Coverage

**Architecture**:
```python
# workflow-patterns coverage enforcement
def verify_coverage(module_path: str, threshold: int = 80) -> bool:
    """
    Check test coverage meets the 80% target.

    If coverage is below 80%:
    1. Identify uncovered lines
    2. Add tests for missing paths
    3. Re-run coverage check
    """
    result = subprocess.run([
        "pytest", f"--cov={module_path}",
        "--cov-report=term-missing",
        "--cov-fail-under={threshold}"
    ], capture_output=True)

    if result.returncode != 0:
        # Parse coverage report
        # Identify uncovered lines
        # Generate test recommendations
        return False

    return True
```

**Key Mechanism**: Coverage verification is MANDATORY before marking task complete:
- Step 6: Verify Coverage (80% threshold)
- Step 7: Document Deviations (if coverage can't be met)
- Step 8: Commit Implementation (only if coverage passes)

### Integration into /code

**Current Gap**: /code Phase 5 (TDD) lacks explicit coverage enforcement.

**Proposed Solution**: Add **coverage verification gates** to TDD phase

**Implementation**: Create `scripts/verify_plan_compliance.py`

```python
#!/usr/bin/env python3
"""
Verify plan.md compliance with test coverage.

Ensures every task in plan.md has:
1. Corresponding test file
2. Failing tests written (RED phase complete)
3. Coverage threshold met (GREEN phase complete)
"""

import ast
import sys
from pathlib import Path
import re

def extract_tasks_from_plan(plan_path: Path) -> list[dict]:
    """Parse plan.md and extract task definitions."""
    content = plan_path.read_text()

    # Match task format: - [ ] **Task X.Y**: Description
    task_pattern = r'- \[(x| |~)\] \*\*Task ([\d.]+)\*\*: (.+)'
    matches = re.findall(task_pattern, content)

    tasks = []
    for status, task_id, description in matches:
        tasks.append({
            "id": task_id,
            "description": description,
            "status": "pending" if status == " " else status
        })

    return tasks

def find_test_file(task_id: str, test_dir: Path) -> Path | None:
    """Find test file corresponding to task."""
    # Pattern: test_<task_name>.py or test_<module>.py
    candidates = list(test_dir.glob(f"test_*{task_id.split('.')[1]}*.py"))
    return candidates[0] if candidates else None

def verify_test_coverage(test_file: Path) -> dict:
    """Verify test file covers its target adequately."""
    if not test_file.exists():
        return {"exists": False, "coverage": 0}

    content = test_file.read_text()

    # Count test functions
    test_functions = len(re.findall(r'def test_\w+', content))

    # Check for RED phase evidence (failing tests)
    has_failing_tests = any([
        'pytest.raises' in content,
        'assert False' in content,
        '# TODO' in content or '# FIXME' in content
    ])

    # Estimate coverage (simplified - actual coverage uses pytest-cov)
    coverage_estimate = min(100, test_functions * 20)  # 5 tests ≈ 100%

    return {
        "exists": True,
        "test_count": test_functions,
        "has_red_phase": has_failing_tests,
        "coverage_estimate": coverage_estimate
    }

def main():
    plan_path = Path("plan.md")
    test_dir = Path("tests")

    if not plan_path.exists():
        print("ERROR: plan.md not found")
        sys.exit(1)

    tasks = extract_tasks_from_plan(plan_path)

    compliance_report = []
    non_compliant = []

    for task in tasks:
        test_file = find_test_file(task["id"], test_dir)
        coverage = verify_test_coverage(test_file) if test_file else {"exists": False}

        task_compliant = (
            coverage.get("exists", False) and
            coverage.get("coverage_estimate", 0) >= 80
        )

        report_entry = {
            "task_id": task["id"],
            "description": task["description"],
            "has_tests": coverage.get("exists", False),
            "coverage": coverage.get("coverage_estimate", 0),
            "compliant": task_compliant
        }

        compliance_report.append(report_entry)

        if not task_compliant:
            non_compliant.append(task["id"])

    # Output report
    print("## Plan Compliance Report")
    print(f"Total tasks: {len(tasks)}")
    print(f"Compliant: {len(tasks) - len(non_compliant)}")
    print(f"Non-compliant: {len(non_compliant)}")

    if non_compliant:
        print("\n### Non-Compliant Tasks")
        for entry in compliance_report:
            if not entry["compliant"]:
                print(f"- Task {entry['task_id']}: {entry['description']}")
                print(f"  Has tests: {entry['has_tests']}")
                print(f"  Coverage: {entry['coverage']}%")

        sys.exit(1)
    else:
        print("\n✅ All tasks compliant with test coverage requirements")
        sys.exit(0)

if __name__ == "__main__":
    main()
```

**Integration Point**: Add to `/code` Phase 5 (TDD) Dispatch Rules

```markdown
### Coverage Gate (NEW)

**After each task completes**:
```bash
python P:/.claude/skills/code/scripts/verify_plan_compliance.py
```

**If gate fails**:
- Task not marked as DONE
- Verifier requires additional tests
- Re-run task implementation until coverage >= 80%
```

---

## Pattern 3: Pre-Done Evidence Checklist (workflow-patterns + Forge)

### Source Implementation

**workflow-patterns** - Phase Completion Protocol:
```markdown
### 5. WAIT for User Approval

Present checklist:
1. [x] Test suite passes (automated)
2. [x] Coverage meets target (automated)
3. [ ] Manual verification items (requires human)
```

**Forge** - Quality Gate Enforcer:
```markdown
After each fix cycle, evaluate ALL 7 quality gates:
- GATE 1 — FUNCTIONAL (100% required)
- GATE 2 — BEHAVIORAL (100% of targeted scenarios)
- GATE 3 — COVERAGE (>=85% overall, >=95% critical paths)
...
```

### Integration into /code

**Current Gap**: /code Phase 9 (DONE) lacks explicit evidence checklist before claiming complete.

**Proposed Solution**: Add **Pre-Done Checklist** to Phase 9

**Implementation**:

```markdown
### Phase 9: DONE — Final Certification

#### 9.0 Pre-Done Checklist (MANDATORY)

Before claiming `/code` complete, verify ALL items:

**Automated Checks** (run via scripts):
- [ ] `python scripts/verify_plan_compliance.py` passes
- [ ] `python scripts/validate_skip_governance.py --ledger <ledger>` passes
- [ ] `python scripts/validate_done_claim.py --plan plan.md --ledger <ledger>` passes
- [ ] Full test suite passes (`pytest tests/ -v`)
- [ ] Coverage threshold met (>=80% overall, >=90% critical code)

**Manual Evidence Checks** (require explicit evidence in conversation):
- [ ] RED phase evidence: Failing test output shown
- [ ] GREEN phase evidence: Tests pass after implementation
- [ ] REFACTOR phase evidence: Tests still pass after cleanup
- [ ] VERIFY phase evidence: Independent verifier PASS
- [ ] TRACE phase evidence: Manual code trace-through completed
- [ ] Spec alignment: All acceptance criteria from plan.md met
- [ ] No regressions: Existing functionality still works
- [ ] Residual risks documented: Confidence calibration included

**If any item fails**:
- Do NOT claim done
- Address the failure
- Re-run failed checks
- Only proceed when ALL items pass

#### 9.1 Build Verification
[... existing build verification ...]
```

**Script Integration**: Update `validate_done_claim.py` to enforce checklist:

```python
def validate_pre_done_checklist(ledger: dict, plan: dict) -> tuple[bool, list[str]]:
    """Verify all pre-done checklist items are complete."""

    failures = []

    # Check 1: RED evidence exists for each task
    for task_id, task_data in ledger.get("tasks", {}).items():
        if not task_data.get("red_evidence"):
            failures.append(f"Task {task_id}: Missing RED phase evidence")

    # Check 2: GREEN evidence exists
    for task_id, task_data in ledger.get("tasks", {}).items():
        if not task_data.get("green_evidence"):
            failures.append(f"Task {task_id}: Missing GREEN phase evidence")

    # Check 3: VERIFY evidence exists
    for task_id, task_data in ledger.get("tasks", {}).items():
        if task_data.get("status") != "verify":
            failures.append(f"Task {task_id}: Not in VERIFY status")

    # Check 4: Plan compliance
    # (calls verify_plan_compliance.py internally)

    # Check 5: Full test suite passed
    # (checks ledger for test_suite_pass evidence)

    return len(failures) == 0, failures
```

---

## Priority Implementation Roadmap

### Phase 1: Critical (Prevents Recurrence)

**Priority 1**: Pattern Validation Framework (Step 4.6)
- **Impact**: Would have prevented unverified_stance_detector false positives
- **Effort**: 4-6 hours (script + integration)
- **Risk**: Low (new module, no changes to existing flow)

**Priority 2**: Plan Compliance Verification (scripts/verify_plan_compliance.py)
- **Impact**: Would have caught missing test coverage for detector
- **Effort**: 6-8 hours (script + ledger integration)
- **Risk**: Medium (requires ledger format changes)

### Phase 2: High (Improves Quality)

**Priority 3**: Pre-Done Checklist (Phase 9.0)
- **Impact**: Ensures all evidence collected before claiming done
- **Effort**: 4-6 hours (documentation + script updates)
- **Risk**: Low (documentation + validation script)

**Priority 4**: Coverage Gates (TDD phase integration)
- **Impact**: Enforces 80% coverage threshold
- **Effort**: 6-8 hours (threshold enforcement + gating logic)
- **Risk**: Medium (changes TDD flow, may need user override)

### Phase 3: Medium (Enhanced Capabilities)

**Priority 5**: Defect Prediction System (Forge pattern)
- **Impact**: Learns from past failures, predicts risky areas
- **Effort**: 12-16 hours (memory system + prediction algorithm)
- **Risk**: High (requires infrastructure, complex integration)

**Priority 6**: Multi-Agent Quality Swarm (Forge pattern)
- **Impact**: Parallel verification by specialized agents
- **Effort**: 16-20 hours (agent orchestration + routing)
- **Risk**: High (requires multi-agent infrastructure)

---

## Implementation Recommendations

### Immediate Actions (This Session)

**Option A**: Implement Priority 1 (Pattern Validation Framework)
- Create `scripts/pattern_validation.py`
- Add Step 4.6 to Phase 4 (PLAN)
- Test against unverified_stance_detector.py patterns
- **Time estimate**: 4-6 hours

**Option B**: Implement Priority 2 (Plan Compliance Verification)
- Create `scripts/verify_plan_compliance.py`
- Integrate with ledger system
- Add compliance gate to Phase 5 (TDD)
- **Time estimate**: 6-8 hours

**Option C**: Implement Priority 1 + 2 (Both critical patterns)
- Sequential implementation
- Test integration end-to-end
- **Time estimate**: 10-14 hours

### Future Considerations

**Forge's Autonomous Agent Swarm**: Consider adopting multi-agent verification model after:
1. Single-agent patterns proven reliable
2. Task list coordination robust
3. Model routing infrastructure in place

**Defect Prediction Memory System**: High-value but requires:
1. Persistent memory backend (CKS integration)
2. Historical failure data collection
3. Prediction algorithm validation

---

## Alternative Approaches Considered

### Alternative 1: Adopt Forge wholesale
**Rejected**: Forge is 1619 lines, tightly integrated, assumes multi-agent infrastructure
**Reason**: /code has different architecture (9-phase workflow, single-agent focus)

### Alternative 2: Adopt workflow-patterns wholesale
**Rejected**: workflow-patterns assumes git-commit-per-task workflow
**Reason**: /code has different commit pattern (batch commits at phase completion)

### Alternative 3: Create hybrid skill
**Rejected**: Would require maintaining forked skill
**Reason**: Pattern extraction and selective integration is more maintainable

---

## Conclusion

**Three high-value patterns identified** from Forge and workflow-patterns that directly address unverified_stance_detector bugs:

1. **Pattern Validation Framework** - Validates detector patterns before use
2. **Plan Compliance Verification** - Ensures tests exist for all tasks
3. **Pre-Done Evidence Checklist** - Collects all evidence before claiming done

**Recommended next step**: Implement Priority 1 (Pattern Validation Framework) as it would have prevented the specific bugs we saw.

---

## References

- Forge skill: https://clawhub.ai/skills/forge (1619 lines)
- workflow-patterns skill: https://clawhub.ai/skills/workflow-patterns (339 lines)
- unverified_stance_detector bugs: P:\.claude\hooks\anti_sycophancy\unverified_stance_detector.py
- /code skill: P:\.claude\skills\code\SKILL.md

---

**Reviewed by**: /arch skill (python template)
**Date**: 2026-03-04
**Status**: Ready for implementation decision
