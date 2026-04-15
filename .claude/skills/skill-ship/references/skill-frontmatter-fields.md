---
type: core
load_when: [creation, quality]
priority: mandatory
estimated_lines: 80
---

# SKILL.md Frontmatter Fields

Complete reference for all required and optional frontmatter fields in SKILL.md files.

## Required Fields

All skills MUST include these fields in their YAML frontmatter:

```yaml
---
name: my-skill
description: Brief description (one sentence, <1024 chars)
version: 1.0.0
category: orchestration
triggers:
  - /my-skill
  - "my skill trigger phrase"
aliases:
  - /my-skill
  - /ms
suggest:
  - /related-skill
depends_on_skills: []
workflow_steps:
  - step_one: Description of first workflow step
  - step_two: Description of second workflow step
---
```

## Enforcement Tier (REQUIRED)

**Valid values:** `strict`, `advisory`, `none`

**Purpose:** Determines how strictly the skill's workflow_steps are enforced

```yaml
enforcement: strict  # or 'advisory' or 'none'
```

### Tier Definitions

| Tier | Behavior | When to Use |
|------|----------|-------------|
| `strict` | Blocks on violation | High-stakes skills where bypassing causes significant problems |
| `advisory` | Warns but allows | Low-stakes skills where flexibility is valuable |
| `none` | No enforcement | Skills that don't need workflow enforcement |

### Selection Criteria

**Use `strict` when:**
- Bypassing the skill causes security issues, data loss, or system corruption
- The skill has complex multi-step workflows that must be followed exactly
- Users frequently try to bypass the skill

**Use `advisory` when:**
- The skill provides convenience features but direct tool usage is acceptable
- Blocking would interrupt legitimate workflows
- The skill is primarily for guidance/suggestions

**Use `none` when:**
- The skill is a knowledge skill (no execution workflow)
- The skill is a lightweight utility with no complex workflow

### Examples

```yaml
# High-stakes workflow skill - strict enforcement
enforcement: strict

# Convenience skill - advisory enforcement
enforcement: advisory

# Knowledge skill - no enforcement needed
enforcement: none
```

## Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✅ | Skill identifier (kebab-case) |
| `description` | string | ✅ | One-sentence description, <1024 chars |
| `version` | string | ✅ | Semantic version (e.g., 1.0.0) |
| `category` | string | ✅ | Skill category (orchestration, analysis, testing, etc.) |
| `triggers` | list | ✅ | Phrases that trigger this skill |
| `aliases` | list | ✅ | Alternative names/shortcuts for this skill |
| `suggest` | list | ✅ | Related skills to suggest |
| `depends_on_skills` | list | ✅ | Skills this skill depends on |
| `workflow_steps` | list | ✅ | Required workflow steps for this skill |
| `enforcement` | string | ✅ | `strict`, `advisory`, or `none` |
| `effort` | string | No | Optional reasoning depth override: `low`, `medium`, `high`, or `max` |
| `allowed_first_tools` | list | No | Allowed tool types for the first executable action when the workflow has a deterministic start |
| `required_first_command_patterns` | list | No | Regex patterns for the first backend command when ordering matters |
| `required_first_command_hint` | string | No | Short human-readable reminder for the required first command |
| `status` | string | No | Optional metadata only; do not add unless local tooling or repo conventions actually use it |

## Effort (OPTIONAL)

**Valid values:** `low`, `medium`, `high`, `max`

**Purpose:** Overrides the session `/effort` default while this skill is active.

```yaml
effort: high
```

### Selection Criteria

**Use `low` when:**
- The skill mostly performs rote deterministic edits or formatting
- Speed and low overhead matter more than deep reasoning

**Use `medium` when:**
- The skill does normal implementation, repair, or bounded analysis
- The work benefits from some reasoning depth but is not primarily architectural

**Use `high` when:**
- The skill does RCA, architecture, policy, routing, safety, or cross-boundary reasoning
- Missed nuance would create expensive downstream mistakes

## Command Contract Fields (OPTIONAL)

Use these when a workflow has a deterministic first backend action or when command ordering must be machine-readable.

### `allowed_first_tools`

List the tool types allowed for the first executable action.

```yaml
allowed_first_tools:
  - Bash
```

Use when:
- the first action is always a concrete command or script invocation
- you want the validator to fail closed before later tools run out of order

### `required_first_command_patterns`

Regex patterns for the canonical first backend command.

```yaml
required_first_command_patterns:
  - '^csf-source\\s+sync(?:\\s|$)'
```

Use when:
- the workflow has a stable first backend command
- the skill body contains command ordering rules that should be enforced mechanically
- the skill docs need to stop relying on prose-only sequencing

### `required_first_command_hint`

Short human-readable reminder for the required first command.

```yaml
required_first_command_hint: Use `csf-source sync` first, then list or fetch as needed.
```

Use when:
- the first-command contract may be violated by model variance
- you want the hook or validator to show a useful remediation hint

**Use `max` when:**
- The work is unusually ambiguous and high-stakes
- The extra reasoning cost is justified by risk reduction

**Guidance:**
- Configure `effort` deliberately; do not raise it by default for every skill
- Prefer matching reasoning depth to the skill's primary job

## Status (OPTIONAL)

`status:` is not part of the required frontmatter contract here.

Use it only when:
- local tooling reads it
- the repo has a documented convention that depends on it

Do not invent `status: draft` as a placeholder just because a skill is newly created. Readiness should be conveyed by the workflow result and the completed validation phases, not by ad hoc metadata.

## Validation

The `enforcement_tier_validator` hook automatically validates SKILL.md files:

- **Validates**: Enforcement field is present and contains a valid value
- **Default**: If not specified, defaults to `strict` (safer default)
- **Action**: Warns when SKILL.md is written/edited without valid enforcement tier

## Quick Reference

**Quick template for new skills:**

```yaml
---
name: my-new-skill
description: Brief one-sentence description of what this skill does
version: 1.0.0
category: orchestration
triggers:
  - /my-new-skill
  - "my skill trigger phrase"
aliases:
  - /my-new-skill
  - /mns
suggest:
  - /related-skill
depends_on_skills: []
workflow_steps:
  - step_one: Description of first workflow step
  - step_two: Description of second workflow step
enforcement: strict  # Choose: strict, advisory, or none
---
```

## Related Documentation

- **Enforcement Tier System**: `P:/.claude/hooks/CLAUDE.md#enforcement-tier-system-v50---2026-03-18`
- **Skill-Based Hooks**: `P:/.claude/hooks/CLAUDE.md#skill-enforcement-enhancement-v35---2026-03-12`
- **Quality Gates**: `P:/.claude/skills/skill-ship/references/skill-quality-gates.md`
