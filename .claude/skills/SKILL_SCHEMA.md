# Skill Frontmatter Schema

Skills declare their execution specifications in YAML frontmatter (between `---` markers) and provide complete context in the body.

---

## Part 1: Frontmatter Schema

```yaml
---
name: skill-name
description: One line description
category: category-name
triggers:
  - /skill-name
  - /alias
  - "phrase trigger"
aliases:
  - /skill-name
  - /alias

suggest:
  - /related-skill-1
  - /related-skill-2

# Execution specification (machine-readable)
execution:
  directive: |
    Brief instruction of what to do when invoked.
    Can be multi-line.
  default_args: ""
  examples:
    - "/skill-name target --flag"
    - "/skill-name . --verbose"

# Prohibited actions (optional)
# REASON: Skills inject execution directives into Claude's context.
# CONSEQUENCE: Descriptive text causes Claude to summarize instead of execute.
do_not:
  - summarize this skill
  - describe what it does
  - use alternative approaches

# Output template (optional - for skills with structured output)
output_template: |
  ## Section 1
  [content]

  ## Section 2
  [content]
---
```

## Part 2: Body Template Structure

After the frontmatter, skills should follow this structure for completeness:

```markdown
# Skill Name

## Purpose
[One-sentence summary of what this skill does]

## Project Context
[Reference relevant project guidelines that constrain this skill's behavior]

### Constitution / Constraints
- [Key principles from CLAUDE.md that apply]
- [Solo-dev or team-specific constraints]
- [Prohibited patterns for this skill]

### Technical Context
- [Relevant tech stack from SPECS.md or project]
- [Integration points to be aware of]

### Architecture Alignment
- [Patterns from ARCHITECTURE.md to follow]
- [Module boundaries to respect]

## Your Workflow
[Numbered steps for how this skill operates]
1. First step
2. Second step
3. ...

## Validation Rules
[Explicit constraints for this skill's operations]
- When [condition]: do [action]
- Before [operation]: verify [requirement]
- After [operation]: check [outcome]

## When to Use
[Triggers or situations where this skill applies]

## Examples
[Concrete usage examples if helpful]

## Integration Points
- [Related skills]
- [Hooks or validators that interact with this skill]
- [Dependencies on other systems]
```

---

## Part 3: Field Reference

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Skill identifier (used for registry lookup) |
| `description` | Yes | One-line summary |
| `category` | No | Category grouping |
| `triggers` | No | List of trigger phrases/commands |
| `aliases` | No | Alternative command names |
| `suggest` | No | Related skills to suggest |
| `execution.directive` | No | What to execute (fallback: regex extraction) |
| `execution.default_args` | No | Default arguments when none provided |
| `execution.examples` | No | Usage examples |
| `do_not` | No | Prohibited action patterns |
| `output_template` | No | Required output format (for template-based skills) |

### Body Sections

| Section | Required | Purpose |
|---------|----------|---------|
| `## Purpose` | Yes | Clear summary of skill's function |
| `## Project Context` | Recommended | Carries project constraints with skill |
| `## Your Workflow` | Recommended | Step-by-step execution pattern |
| `## Validation Rules` | Recommended | Explicit constraints (beyond `do_not`) |
| `## When to Use` | No | Usage triggers and examples |
| `## Integration Points` | No | Related skills and dependencies |

---

## Part 4: External CLI Documentation Convention

When a skill documents how to invoke an external CLI tool (flags, subcommands, invocation patterns), it MUST:

1. **Include a verification step**: Show the command that confirms the interface (e.g., `tool --help`, `tool --version`, `tool health`).

2. **Annotate with version evidence**: Tag the documented patterns with the version they were verified against:
   `Verified against <tool> v<version> on <date>`

3. **Position the verification step first**: The `--help`/verification check must appear BEFORE the usage patterns, as "Step 0" or equivalent. Models that skip Step 0 are trusting documentation over the live tool.

**Rationale**: External CLI tools evolve independently of this codebase. Documentation written from assumption (rather than from `--help` output) is a hypothesis, not a fact. Weaker models will treat documented patterns as authoritative. This convention forces verification before trust, regardless of model tier.

**Examples of compliant skills**: `ai-groq` (has `health --sanity` verification), `cks` (has `pip show` verification).
**Examples of non-compliant skills**: `ai-models`, `git` skill (have no interface verification step).
