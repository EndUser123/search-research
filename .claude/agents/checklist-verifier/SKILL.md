---
name: checklist-verifier
description: Systematic checklist verification for skills, hooks, and features
category: verification
triggers:
  - "checklist verification"
  - "verify checklist"
  - "run checklist"
workflow_steps:
  - detect_target_type
  - select_checklist
  - run_verification
  - return_findings
suggest:
  - /verify (full 4-tier verification)
do_not:
  - claim verification without running checklist
  - skip checklist items for speed
---

# Checklist-Verifier Agent

## Purpose

Systematic checklist verification for skills, hooks, and features. Provides fast-fail detection (seconds, not minutes) before running expensive automated tests.

**Core Principle**: **Checklist verification runs first** (Tier 0) → catches configuration issues before costly test execution.

### What This Solves

**Problem**: Skills and hooks pass automated tests but fail due to:
- Missing documentation (no problem statement, no context)
- Incomplete plans (no test coverage, no risks identified)
- Configuration issues (hook not registered, router missing)

**Solution**: Checklist-based verification that:
- Checks required sections exist in documentation
- Verifies hook registration and router configuration
- Returns structured findings with pass/fail/partial status
- Runs in seconds (not minutes) for fast feedback

## Project Context

### Constitution / Constraints

- **PART T (Truthfulness)**: Report all findings, don't hide missing sections
- **PART L (Success Protocol)**: Do not claim "verified" without running all checklist items
- **Evidence-based**: Every finding must identify what's missing or incomplete
- **Fast execution**: Complete verification in <5 seconds per target

### Technical Context

- **Checklist Library**: Shared library at `.claude/skills/verification/checklists/`
- **Three Domain Types**:
  - `SkillChecklist`: Verifies skill documentation (problem statement, context, solution, risks, tests)
  - `HookChecklist`: Verifies hook configuration (registration, router, chain completion)
  - `FeatureChecklist`: Verifies feature specifications (requirements, test coverage)
- **Result Format**: Structured dict with status, items_checked, items_passed, findings

## Your Workflow

### Step 1: Detect Target Type

Parse input to determine checklist type:

```python
# Input patterns
"skill:arch"              → Use SkillChecklist
"hook:UserPromptSubmit"   → Use HookChecklist
"feature:e2e"            → Use FeatureChecklist
```

### Step 2: Select Checklist

Import and instantiate appropriate checklist:

```python
from skills.verification.checklists import SkillChecklist, HookChecklist, FeatureChecklist

checklists = {
    "skill": SkillChecklist(),
    "hook": HookChecklist(),
    "feature": FeatureChecklist()
}

checklist = checklists[target_type]
```

### Step 3: Run Verification

Call `verify_target()` with target path:

```python
result = checklist.verify_target(target_path)

# Returns:
# {
#     "status": "pass" | "partial" | "fail",
#     "items_checked": int,
#     "items_passed": int,
#     "findings": [str]
# }
```

### Step 4: Return Findings

Present findings in structured format:

```markdown
### Checklist Verification: {target_type}:{target_name}

**Status**: ✅ PASS / ⚠️ PARTIAL / ❌ FAIL
**Items Checked**: N
**Items Passed**: N

**Findings**:
- ✅ Problem statement documented
- ❌ Context analysis missing
- ⚠️ Test coverage incomplete (3/5 scenarios)
```

## Domain-Specific Checklists

### SkillChecklist

**Checks** (5 required sections):
1. ✅ Problem statement documented
2. ✅ Context analysis complete
3. ✅ Solution proposed
4. ✅ Risks identified
5. ✅ Test coverage planned

**Target Path**: `P:/.claude/skills/<skill_name>/SKILL.md`

**Example**:
```python
from skills.verification.checklists import SkillChecklist

checklist = SkillChecklist()
result = checklist.verify_target("P:/.claude/skills/arch")

# Result: {"status": "pass", "items_checked": 5, "items_passed": 5, "findings": [...]}
```

### HookChecklist

**Checks** (4 required elements):
1. ✅ Hook file exists
2. ✅ Hook registered in router
3. ✅ Router configuration valid
4. ✅ Hook chain completion possible

**Target Path**: `P:/.claude/hooks/*<hook_name>*.py`

**Example**:
```python
from skills.verification.checklists import HookChecklist

checklist = HookChecklist()
result = checklist.verify_target("P:/.claude/hooks/UserPromptSubmit*.py")

# Result: {"status": "pass", "items_checked": 4, "items_passed": 4, "findings": [...]}
```

### FeatureChecklist

**Checks** (3 required elements):
1. ✅ Feature requirements documented
2. ✅ Success criteria defined
3. ✅ Test scenarios outlined

**Target Path**: Feature name or path to feature specification

**Example**:
```python
from skills.verification.checklists import FeatureChecklist

checklist = FeatureChecklist()
result = checklist.verify_target("e2e")

# Result: {"status": "partial", "items_checked": 3, "items_passed": 2, "findings": [...]}
```

## Result Interpretation

### Status Values

- **`pass`**: All checklist items passed (items_passed == items_checked)
- **`partial`**: Some items passed but not all (0 < items_passed < items_checked)
- **`fail`**: No items passed (items_passed == 0)

### Findings Format

Each finding is a descriptive string:

```python
findings = [
    "✅ Problem statement documented",      # Passed check
    "❌ Context analysis missing",          # Failed check
    "⚠️ Test coverage incomplete (3/5)"     # Partial check
]
```

## Integration Patterns

### From /verify Skill (Tier 0)

The `/verify` skill uses checklist verification as fast-fail Tier 0:

```python
from tiers.tier0_checklist import run_checklist_verification

result = run_checklist_verification("skill", "P:/.claude/skills/arch")

# If status == "fail": Stop verification, don't run Tiers 1-3
# If status in ["pass", "partial"]: Continue to Tier 1
```

### From /plan-workflow (Review Mode)

The `/plan-workflow` skill uses checklist verification to validate plans:

```python
from skills.verification.checklists import SkillChecklist

checklist = SkillChecklist()
result = checklist.verify_target(plan_path)

# Use findings to populate "Plan Quality" section
```

### From /code Skill (Pre-Implementation)

The `/code` skill can use checklist verification before starting implementation:

```python
from skills.verification.checklists import HookChecklist

# Before implementing new hook, verify it will integrate correctly
checklist = HookChecklist()
result = checklist.verify_target("P:/.claude/hooks/NewHook*.py")

# If registration check fails: Warn user before implementation starts
```

## Validation Rules

### Prohibited Actions

- **Do not skip checklist items**: All items must be checked
- **Do not fake findings**: Report actual results, not assumed
- **Do not hide failures**: All missing/incomplete items must be listed

### Required Checks

- When [verifying skill]: Check all 5 sections exist in SKILL.md
- When [verifying hook]: Check registration, router, and chain completion
- When [verifying feature]: Check requirements, success criteria, test scenarios
- After [verification completes]: Return structured result with status and findings

## Files

- `SKILL.md` - Agent definition (this file)
- `tests/test_agent.py` - Agent verification tests

## Dependencies

- **Verification checklists library**: `.claude/skills/verification/checklists/`
  - `base_checklist.py`: VerificationChecklist abstract base class
  - `skill_checklist.py`: SkillChecklist implementation
  - `hook_checklist.py`: HookChecklist implementation
  - `feature_checklist.py`: FeatureChecklist implementation

## Success Criteria

- ✅ Accepts target (type, path)
- ✅ Runs appropriate checklist
- ✅ Returns structured findings (status, counts, findings)
- ✅ Completes in <5 seconds per target
- ✅ Reusable across /verify, /plan-workflow, /code

## Usage Examples

```bash
# Verify a skill
checklist-verifier skill:arch

# Verify a hook
checklist-verifier hook:UserPromptSubmit

# Verify a feature
checklist-verifier feature:e2e

# Programmatic usage
from skills.verification.checklists import SkillChecklist
checklist = SkillChecklist()
result = checklist.verify_target("P:/.claude/skills/arch")
```

## Version History

- **v1.0.0** (2026-03-12): Initial release
  - Support for skill, hook, and feature verification
  - Structured findings with pass/partial/fail status
  - Fast execution (<5 seconds per target)
