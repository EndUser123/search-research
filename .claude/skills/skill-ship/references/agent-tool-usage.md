# Agent Tool Usage Best Practices

This document contains detailed guidance on using the Agent/Task tool correctly when spawning subagents from skills.

## CRITICAL: subagent_type vs model Parameter

When using the `Agent` tool to spawn subagents from skills, understand the difference:

**❌ WRONG:**
```markdown
Launch subagents (haiku model):
```
This gets misinterpreted as `subagent_type="haiku"` → **ERROR** (haiku is not an agent type)

**✅ CORRECT:**
```markdown
Launch subagents with model="haiku":
```
This correctly passes `model: "haiku"` → Works as expected

## Parameter Reference

| Parameter | Purpose | Valid Values | Required |
|-----------|---------|--------------|----------|
| `subagent_type` | Specifies which specialized agent to use | `general-purpose`, `Explore`, `Plan`, `feature-dev:code-architect`, etc. | **Yes** |
| `model` | Override the default model for this subagent | `sonnet`, `opus`, `haiku` | No (defaults to inherited) |
| `prompt` | What the subagent should do | Free text instructions | **Yes** |
| `description` | Short summary for task tracking | 3-5 word summary | **Yes** |

## When to Specify model Parameter

Only specify `model` when you need:
- **Speed optimization**: Use `model="haiku"` for simple tasks (bash commands, file checks, basic reporting)
- **Quality override**: Use `model="opus"` for complex reasoning when default would be sonnet
- **Cost optimization**: Use `model="haiku"` for high-volume, low-complexity operations

## Example from /p skill (detection phase)

```markdown
Launch 2 parallel Task subagents with model="haiku":

Subagent 1 — Test Detection:
Run these commands and report all output:
  pytest --collect-only -q 2>&1 | head -5
  python -c "import subprocess; ..."

Subagent 2 — File & Marker Detection:
Run these commands and report all output:
  ls README.md LICENSE 2>&1
  ls .github/workflows/*.yml 2>&1
```

This correctly uses `model="haiku"` for fast, simple command execution.

## Common Mistakes

1. **Using model name as subagent_type**: `subagent_type: "haiku"` → ERROR
2. **Omitting required parameters**: Missing `description` → Silent no-op
3. **Confusing model selection with agent type**: Model is about capability/cost, agent type is about specialization

## Task Tool All Parameters

The Task tool requires these parameters:

- **subagent_type** (required): Which specialized agent to use
- **prompt** (required): What the agent should do
- **description** (required): Short summary for task tracking

Optional parameters:
- **model**: Override default model (sonnet/opus/haiku)
- **name**: Custom name for the agent (for team coordination)
- **team_name**: Spawn agent into specific team
- **mode**: Permission mode (acceptEdits, bypassPermissions, etc.)

## Dynamic Agent Discovery

**Always discover current agents at runtime** — the static list below is incomplete (104 agents exist across 4 sources).

```bash
# Full list with descriptions
python scripts/list_agents.py --json

# Just names, one per line
python scripts/list_agents.py --names

# Filter by keyword (name or description)
python scripts/list_agents.py --filter "tdd" --names
python scripts/list_agents.py --filter "quality" --names
python scripts/list_agents.py --filter "security" --names
```

**Sources scanned:**
1. `P:/.claude/agents/` — user agents (bare name)
2. `~/.claude/agents/` — user agents (bare name)
3. `P:/.claude/plugins/cache/*/agents/` — plugin agents (`namespace:name`)
4. `~/.claude/plugins/cache/*/agents/` — plugin agents (`namespace:name`)
5. Builtins — loaded from `~/.claude/skills/skill-ship/config/builtins.json` at runtime (not hardcoded)

## Subagent Type Quick Reference

Use `scripts/list_agents.py --filter <keyword> --names` for the authoritative current list. Key categories:

| Category | Agents |
|----------|--------|
| TDD | `tdd-test-writer`, `tdd-implementer`, `tdd-refactorer` |
| Quality/Review | `quality-gate`, `csf-nip-quality`, `gto-quality`, `adversarial-quality`, `pr-test-analyzer`, `code-reviewer` |
| Testing | `test-analyzer`, `qa-engineer`, `adversarial-qa`, `adversarial-testing` |
| Code Analysis | `code-critic`, `gto-code-critic`, `Explore`, `analyzer` |
| Security | `adversarial-security`, `csf-nip-security` |
| Hooks/Architecture | `hook-analyzer`, `csf-nip-architect`, `csf-nip-explorer` |
| Planning | `Plan`, `plan_reviewer`, `csf-nip-planning-command` |
| Research/Retro | `researcher`, `retro-analyzer` |
| Python | `python-core`, `python-modernization`, `python-simplifier`, `python-web` |
| Skill Development | `csf-nip-development`, `skill-reviewer`, `gitbatch-worker` |
| Adversarial | `adversarial-critic`, `adversarial-compliance`, `adversarial-logic`, `adversarial-security`, `adversarial-failure-modes`, `adversarial-qa`, `adversarial-state-machine` |

**White space — agent types with no coverage:**
- Skill/workflow **selection/routing** agent (chooses best skill for a task)
- **Token efficiency** agent (context compression, progressive disclosure)
- **Documentation** agent (README generation, API docs, code-to-doc sync)
- **Onboarding** agent (codebase tour, developer orientation)

## Best Practices

1. **Always provide all 3 required parameters**: subagent_type, prompt, description
2. **Use model parameter thoughtfully**: Default is usually best, override only for specific optimization needs
3. **Choose specialized agents**: Use domain-specific agents (Explore, Plan) over general-purpose when appropriate
4. **Clear descriptions**: Make descriptions actionable and specific for task tracking
5. **Parallel execution**: Launch multiple agents in parallel for independent work
