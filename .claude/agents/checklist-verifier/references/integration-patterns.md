# Integration Patterns

## From /verify Skill (Tier 0)

The `/verify` skill uses checklist verification as fast-fail Tier 0:

```python
from tiers.tier0_checklist import run_checklist_verification

result = run_checklist_verification("skill", "P:/.claude/skills/arch")

# If status == "fail": Stop verification, don't run Tiers 1-3
# If status in ["pass", "partial"]: Continue to Tier 1
```

## From /plan-workflow (Review Mode)

The `/plan-workflow` skill uses checklist verification to validate plans:

```python
from skills.verification.checklists import SkillChecklist

checklist = SkillChecklist()
result = checklist.verify_target(plan_path)

# Use findings to populate "Plan Quality" section
```

## From /code Skill (Pre-Implementation)

The `/code` skill can use checklist verification before starting implementation:

```python
from skills.verification.checklists import HookChecklist

# Before implementing new hook, verify it will integrate correctly
checklist = HookChecklist()
result = checklist.verify_target("P:/.claude/hooks/NewHook*.py")

# If registration check fails: Warn user before implementation starts
```

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
