# Domain-Specific Checklist Details

## SkillChecklist

**Checks** (5 required sections):
1. Problem statement documented
2. Context analysis complete
3. Solution proposed
4. Risks identified
5. Test coverage planned

**Target Path**: `P:/.claude/skills/<skill_name>/SKILL.md`

**Example**:
```python
from skills.verification.checklists import SkillChecklist

checklist = SkillChecklist()
result = checklist.verify_target("P:/.claude/skills/arch")

# Result: {"status": "pass", "items_checked": 5, "items_passed": 5, "findings": [...]}
```

## HookChecklist

**Checks** (4 required elements):
1. Hook file exists
2. Hook registered in router
3. Router configuration valid
4. Hook chain completion possible

**Target Path**: `P:/.claude/hooks/*<hook_name>*.py`

**Example**:
```python
from skills.verification.checklists import HookChecklist

checklist = HookChecklist()
result = checklist.verify_target("P:/.claude/hooks/UserPromptSubmit*.py")

# Result: {"status": "pass", "items_checked": 4, "items_passed": 4, "findings": [...]}
```

## FeatureChecklist

**Checks** (3 required elements):
1. Feature requirements documented
2. Success criteria defined
3. Test scenarios outlined

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
    "Problem statement documented",      # Passed check
    "Context analysis missing",          # Failed check
    "Test coverage incomplete (3/5)"     # Partial check
]
```
