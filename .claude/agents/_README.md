---
name: readme
description: Documentation for the agent expertise files directory. Not an executable agent.
tools: Read
model: inherit
permissionMode: plan
---

# Agent Expertise Files

This directory contains expertise files for different agent types in the Persistent Learning Agent Ecosystem.

## Agent Frontmatter Structure

Every agent file starts with YAML frontmatter:

```markdown
---
name: agent-name
description: Brief description of what this agent does
tools: Read, Glob, Grep, Write, Edit, Bash, TodoWrite
---

# Agent Name

Purpose description...

## Mandatory Process

1. **Step 1**: What to do first
2. **Step 2**: What to do next
3. **Step 3**: Verification step

## Return Format

What the agent should return when complete.

## Do NOT

- ❌ Bad thing to avoid
- ❌ Another bad thing
```

## File Organization

- Files should be organized by agent type or domain
- Use descriptive names that clearly indicate the agent's purpose
- Include documentation and examples where appropriate

## Best Practices Reference

When creating agents for yt-fts development:

- **Refactoring patterns**: `P:/worktrees/w1t2/projects/yt-fts/docs/REFACTORING.md`
- **Test patterns**: `P:/worktrees/w1t2/projects/yt-fts/docs/TEST_PATTERNS.md`
- **TDD workflow**: `P:/.claude/skills/tdd/skill.md` (PARALLEL subagent delegation)

## Example Agents

Good examples to study:
- `tdd-test-writer.md` - Simple phase-based agent with clear steps
- `tdd-refactorer.md` - Agent with verification checklist
- `architect.md` - Complex domain expert agent
