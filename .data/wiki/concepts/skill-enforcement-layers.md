---
type: concept
title: "Claude Code Skill Enforcement: Layer Analysis"
created: 2026-04-18
source: ~/Downloads/hooks_implementation_plan 2.md
hash: 6e29ef00e690d59f033409a9927f886e4ecb9cf6f1f961f98e4f3576801f3566
host: claude
tags:
  - claude-code
  - hooks
  - skill-enforcement
  - architecture
summary: "Comprehensive analysis of Claude Code's 3-layer skill enforcement model: PreToolUse (blocks non-skill tools), UserPromptSubmit (injects instructions ~50% effective), and Stop hook (100% backstop)."

> **CROSS-HOST NOTICE (updated 2026-08-06):** This concept describes
> **Claude Code's** skill enforcement model. It does NOT apply to Grok
> Build. On Grok Build, UserPromptSubmit is verified non-functional for
> model injection (stdout/stderr/exit-2 all ignored). The Grok Build
> enforcement landscape is documented in
> [[skill-step-enforcement-architecture-grok-build]] and
> [[ship-pipeline-enforcement-pretooluse-phase-state-hooks]].
---

# Claude Code Skill Enforcement: Layer Analysis

## The 3-Layer Enforcement Model

| Layer | Mechanism | Effectiveness |
|-------|----------|---------------|
| **Layer 0** (PreToolUse) | Blocks non-Skill tools | ✓ 100% — fires only when model calls a tool |
| **Layer 1** (UserPromptSubmit) | Injects instruction text | ✗ ~50% — model can ignore advisory context |
| **Layer 2** (Stop hook) | Blocks prose bypass | ✓ 100% — fires when model bypasses with no tool call |

## Why Layer 1 Fails ~50% of the Time

UserPromptSubmit injection is **just context**. The model has autonomy over its first action — it can choose prose over a tool call, and no amount of "INSTRUCTION:" framing changes that.

```
User: /arch
Injected: "INSTRUCTION: Execute skill arch..."
Model choice: Ignore instruction, respond with prose ← This is the failure
```

**Root cause**: Cannot force first-turn tool use via context text. Only the API's `tool_choice` parameter can do that — hooks don't have access to it.

## Why PreToolUse (Layer 0) Doesn't Help Either

PreToolUse only fires when the model **calls a tool**. If the model responds with prose instead, no tool call ever happens, so there's nothing to block pre-hoc.

## Fixes That Remove Stop-Hook Dependency

### Option 1 — Inline Skill Content (BEST)
Have `UserPromptSubmit` read `SKILL.md` and inject its body as `additionalContext` wrapped in `<system-reminder>`. The model doesn't need to call `Skill()` — the procedure is already in context.

```python
# Instead of:
"INSTRUCTION: Execute skill arch\nStep 1: Call Skill('arch')..."

# Do:
skill_content = (SKILLS_DIR / "arch" / "SKILL.md").read_text()
injection = f"""<system-reminder>
You are executing the **{skill_name}** skill. Follow it step by step.
{skill_content}
</system-reminder>"""
```

### Option 2 — Native Slash Commands
Put skill launchers in `.claude/commands/arch.md`. Claude Code's harness expands native slash commands **deterministically before the model sees the turn** — not advisory, it's substitution.

### Option 3 — Rewrite the Prompt
`UserPromptSubmit` can replace the prompt entirely. Transform `/arch <task>` into a prompt that is the skill's first step.

### Option 4 — Stronger Injection Framing
`<system-reminder>` with explicit "this overrides default behavior" language lifts compliance meaningfully — but still not to 100%.

## Superpowers Comparison: Why It Works Better

Superpowers enforces skill use through **structural positioning + psychological pressure**, not advisory text:

1. **Structural placement** — skill is a mandatory first-action tool call, not injectable context
2. **Pressure scenario TDD** — iteratively test and strengthen instruction language until compliance is near-100%
3. **Mandatory language** — "YOU MUST USE IT", "IF A SKILL APPLIES TO YOUR TASK, YOU DO NOT HAVE A CHOICE"
4. **Rationalization naming** — explicit red flags like "'I know what that means'" catch bypass attempts
5. **Post-hoc deletion** — if model skips TDD, the framework deletes the code (not a suggestion)

## Recommended Architecture

| Layer | Implementation | Purpose |
|-------|----------------|---------|
| **Dispatch** | Native `.claude/commands/{skill}.md` | Deterministic routing — no advisory text |
| **Execution** | `skill_enforcer.py` + SKILL.md | Execute correctly once called |
| **Resilience** | Superpowers principles → SKILL.md | Strengthen instructions via testing |
| **Backstop** | Stop hook | Fire alarm — keep it, measure when it fires |

## Skill Classification for Enforcement

| Skill type | Enforcement model | Strategy |
|-----------|-----------------|----------|
| Workflow-bound (arch, plan, review) | Inline content via `<system-reminder>` | Full SKILL.md injected, no tool call needed |
| Advisory/exploratory (research, brainstorm) | Prompt shaping only | Light context, no enforcement |
| Gated/critical (deploy, migrate, delete) | Inline + Stop always | Both layers mandatory |

Set `enforcement: {inline, advisory, gated}` in SKILL.md frontmatter and have the hook branch on it.

## Key Fix: Move Skill Dispatch to Native Commands

```
.claude/commands/arch.md
→ Invokes skill_enforcer("arch")
→ Reads .claude/skills/arch/SKILL.md
→ Executes workflow

Later: Claude calls Skill("arch") directly (skill is registered)
Both paths go through skill_enforcer.
```

## Commands vs Skills Naming

- `.claude/commands/arch.md` + `.claude/skills/arch/SKILL.md` can coexist
- Command is the dispatcher; skill is the implementation
- **Bug**: sharing the same name can cause "only Claude can invoke" behavior — don't rely on both for parallel user invocation

## disable-model-invocation Note

Setting `disable-model-invocation: true` means **only the user** can invoke via `/arch` — Claude cannot auto-invoke. Use only if you want explicit user-triggered dispatch. If you want Claude to use skills when appropriate, leave this off.

## Claude Code v2.1.112+ Features Relevant to Enforcement

- **1-hour prompt caching** (`ENABLE_PROMPT_CACHING_1H`) — reduces repeated SKILL.md injection cost
- **Built-in slash command discovery** — `/arch` discoverable at model level
- **TaskCreated hook** — audit trail for skill-initiated subtasks
- **Session recap** — compliance metrics across sessions

## Session Recap for Enforcement Visibility

Session recap shows which skills were invoked and how often. Use it to measure:
- `(skills_executed / skills_requested) * 100` — if below 95%, that skill needs strengthening
- Which skills fire the Stop hook most often — those need Layer 1 improvement

## Related

- [[wiki/concepts/skill-enforcement-deep-dive]] — the ~50% Layer 1 failure analysis
- [[wiki/concepts/opencode-sqlite-parallelism]] — opencode concurrency and SQLite locking
- [[wiki/concepts/pi-agent-harness]] — Pi agent vs opencode vs Claude Code tradeoffs
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
