# Skill Validation Checklist

> Extracted from `/testing-skills` - Quality gate for validating new skills

## Purpose

Validate that skills work correctly before deployment. Catch issues early, prevent broken skills from reaching production.

**Core Principle**: **Test before you trust.** Skills must demonstrate they work before being used.

---

## Validation Workflow

1. **Receive skill validation request** - User asks to test a skill
2. **Read the skill file** - Load SKILL.md to understand structure
3. **Check frontmatter completeness** - Verify name, description, triggers exist
4. **Validate trigger phrases** - Ensure activation phrases actually invoke the skill
5. **Check description length** - Descriptions >100 chars get truncated (known constraint)
6. **Verify constitution links** - Ensure skill declares which PARTs it extends
7. **Test execution paths** - Walk through the skill's workflow steps
8. **Generate test report** - Show what passed/failed with evidence
9. **Recommend fixes** - Provide specific, actionable corrections

---

## Validation Rules

### Prohibited Actions

- **Do not skip activation tests** - Skills that look good but don't activate are failures
- **Do not approve without verification** - "Looks correct" is insufficient validation
- **Do not ignore constitution links** - Skills without PART references are orphaned
- **Do not waive description length check** - 100-char limit is enforced by registry

### Required Checks

| Check | Description |
|-------|-------------|
| Trigger validation | Verify trigger phrases actually invoke the skill |
| Description length | Check description length <= 100 characters |
| Frontmatter completeness | Ensure id, category, and triggers are present |
| Constitution links | Ensure skill declares which PARTs it extends |
| Path integrity | Verify all referenced file paths in SKILL.md exist |
| Fix recommendations | Provide specific fix recommendations with file paths |

### Quality Levels

| Level | Criteria |
|-------|----------|
| **PRODUCTION** | All checks pass, triggers work, constitution linked |
| **DEVELOPMENT** | Minor issues found, non-blocking |
| **FAILED** | Critical issues prevent deployment |

---

## Active Constraints

- **Description Truncation**: Descriptions > 100 chars get cut off in registry
  - Always check description length before deploying
- **Skipping Activation Tests**: Skills that look good but don't activate
  - Always test trigger phrases actually invoke the skill
- **Missing Constitution Links**: Skills without PART references are orphaned
  - Always declare which PARTs the skill extends

---

## Response Format

When performing skill validation, prefix responses with `[SKILL-VALIDATION]` to indicate validation is active.

Example: `[SKILL-VALIDATION] Validating skill activation and execution...`

---

## Constitution Compliance

This validation extends:
- **PART C (Truthfulness)** - Report test failures honestly
- **PART P (Testing Workflow)** - Systematic validation before deployment
- **PART L (Success Protocol)** - Don't claim "ready" without evidence
