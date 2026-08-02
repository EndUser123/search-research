---
title: "Agent Skills and Fleet Patterns for Solo-Director AI Coding (2026)"
created: 2026-08-02
source: session-2026-08-02
tags: [agent-skills, fleet-patterns, coding, python, typescript, reference, research]
summary: >
  Research-grounded overview of the standard architecture for solo-director
  + AI coder fleets in 2026: planner/coder/reviewer role splits with isolated
  contexts, git worktree isolation, open SKILL.md portability, and 5 canonical
  orchestration patterns (Microsoft). Covers Python stack (FastAPI/pytest/Poetry),
  TypeScript ecosystem, front-end design systems, and code review patterns.
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
relations:
  - target: wiki/concepts/tool-failure-lifecycle-llm-agent-fleets.md
    type: related
  - target: wiki/concepts/model-as-orchestrator.md
    type: related
---

# Agent Skills and Fleet Patterns for Solo-Director AI Coding (2026)

## Decision context

**Why this research was needed:** the operator runs a fleet of AI coders and wanted external grounding on best practices, patterns, and skills for Python, TypeScript, front-end, back-end, and fleet orchestration.

**What the research changed:** confirmed that our fleet already implements most of the 2026 standard patterns. Identified two gaps: (1) no formalized isolated-context role split (planner/coder/reviewer with separate context windows), and (2) no front-end design-system skill.

## The standard fleet architecture (2026 consensus)

The field has converged on these patterns across 50 sources:

### Role decomposition
- **Planner → Coder → Reviewer → Tester** with isolated context windows per role (bswen, vibecoding, OpenCode)
- Each agent gets one job; context bleed between roles is the primary quality failure mode

### Orchestration patterns (Microsoft canonical 5)
1. **Sequential** — pipeline (plan → code → review → ship)
2. **Concurrent** — parallel agents on independent tasks
3. **Group Chat** — agents discuss and converge
4. **Handoff** — flexible delegation with contracts
5. **Magentic** — adaptive routing based on task shape

### Isolation
- Git worktrees per agent (parallel work without file conflicts)
- Per-agent workspaces (Freebuff, Augment Code)
- Isolated context windows per role (bswen)

### Skill portability
- Open `SKILL.md` spec — author once, runs on Claude Code, Codex, Cursor, Gemini CLI, OpenCode, Qwen
- Registries: wshobson/agents (203 agents), GuildSkills (2,183 TS skills), skills.sh, ComposioHQ (1000+ skills)

### Autonomy control
- Autonomy slider per agent (Cursor): Cmd+K = manual override, agentic = hands-off
- The solo director controls how much independence each agent gets

## Python-specific skills

| Domain | Skills/tools |
|---|---|
| Web frameworks | FastAPI, Django |
| Testing | pytest, type checking (mypy/pyright) |
| Data science | pandas, NumPy |
| Package management | Poetry, pip-tools |
| Conventions | Idiomatic Python, venv management |

## TypeScript-specific skills

| Domain | Skills/tools |
|---|---|
| Frameworks | Next.js, React |
| Skill ecosystem | 2,183 tagged skills on GuildSkills |
| Full-stack | Next.js app creation via Qwen CLI + MCP + skills |

## Front-end design
- **DESIGN.md portable systems** (Open Design): composable skills + portable design docs that work across any agent
- **UI generation skills** (UI UX Pro Max): prompt → complete design system
- **20 AI design skills** (Kimi): visuals, layouts, creative task automation

## Code review and testing patterns
- **Plan → code → verify → ship** 4-stage loop (Vibecoding)
- **TDD orchestra** pattern (GitHub Copilot): structured TDD across multiple agents
- **Planner-coder-reviewer** with isolated contexts (bswen): eliminates manual refactoring loops

## What this means for our workspace

1. **We already implement most standard patterns.** /go orchestrates plan/code/verify, /review handles code review, worktree isolation is documented, skill portability via SKILL.md is standard.
2. **Gap: isolated-context role split.** Our planner and coder often share context (same session). The standard pattern is separate context windows per role to prevent context pollution. We could formalize this by always spawning subagents for each role rather than doing it inline.
3. **Gap: front-end design skill.** No DESIGN.md or UI generation skill exists in the fleet. Open Design or UI UX Pro Max could fill this.
4. **Cross-vendor skill registries are mature.** wshobson/agents (203 agents, 175 skills) and VoltAgent/awesome-agent-skills (vendor-published by Anthropic, Google, Vercel, Stripe) are worth mining for capability gaps.

## Receipts

- **Role split pattern:** [FACT] bswen.com, vibecoding.app, codecraftersden.com — consistent across 3+ independent sources
- **Microsoft 5 orchestration patterns:** [FACT] learn.microsoft.com Azure Architecture Center
- **Git worktree isolation:** [FACT] aidenapp.org, augmentcode.com — consistent across sources
- **SKILL.md portability:** [FACT] wshobson/agents README, GuildSkills, skills.sh — 203 agents working across 6+ tools
- **Python stack:** [FACT] agensi.io — FastAPI/Django/pytest/pandas/Poetry
- **Netflix health-check stat:** [PRACTITIONER] cited in pre-mortem subagent findings

## Falsifier

This concept is wrong if:
- The field moves away from SKILL.md portability toward vendor-specific formats
- Isolated-context role splits prove unnecessary (shared-context is sufficient)
- The 5 Microsoft orchestration patterns are superseded by a better taxonomy

## Related

- [[tool-failure-lifecycle-llm-agent-fleets]] — tool management for the same fleet
- [[model-as-orchestrator]] — the agent-as-orchestrator framing
- [[inference-in-code-blind-spot]] — session incident context
