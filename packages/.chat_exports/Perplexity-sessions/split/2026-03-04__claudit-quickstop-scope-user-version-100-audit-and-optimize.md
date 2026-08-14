---
title: "' claudit @ quickstop
 Scope: user
 Version: 1.0.0
 Audit and optimize Claude Code configurations with dynamic best-p"
date: "2026-03-04"
mode: "COPILOT"
uuid: "935bfa42-54d5-487e-94cc-04c58cb46c8d"
entry_count: 1
---

## Human

" claudit @ quickstop
 Scope: user
 Version: 1.0.0
 Audit and optimize Claude Code configurations with dynamic best-practice research

 Author: quickstop
 Status: Enabled

 Installed components:
 • Agents: audit-ecosystem, audit-global, audit-project, research-core, research-ecosystem, research-optimization
 • Skills: claudit"

/mv

## Assistant

Claudit is a Claude Code plugin by quickstop that audits and optimizes your configurations using research agents to fetch latest best practices from Anthropic docs and elsewhere. Your installed version 1.0.0 includes agents like audit-ecosystem, audit-global, audit-project, research-core, research-optimization, and research-ecosystem, plus the claudit skill, for comprehensive setup grading across categories like context efficiency and over-engineering.[1][2]

## Key Components
- **Audit Agents**: audit-ecosystem (ecosystem checks), audit-global (global config), audit-project (project-specific rules); they evaluate CLAUDE.md, .claude/rules, MCP servers, and skills for issues like bloat or conflicts.[3][4]
- **Research Agents**: research-core (core docs pull), research-ecosystem (tool integrations), research-optimization (performance tuning); dynamically research 2026 updates like Sonnet 4.6 preferences or context rot fixes.[5][1]
- **claudit Skill**: Core SKILL.md handler for invocation, likely via `/claudit`, triggering agent orchestration.[6]

## Optimization Tips
Keep `~/.claude/CLAUDE.md` concise (bullet points only, <700 words total across files) to avoid instruction ignoring; use path-specific rules in `.claude/rules/`. Limit MCP servers to 2-3 core ones globally, lazy-load others; run `/clear` or `/context` frequently to fight rot; start in plan mode (`claude --permission-mode plan`).[4][7][3]

## Running an Audit
Invoke with `/claudit` or `/plugin claudit@quickstop` if not active—it spawns agents to grade your setup (e.g., error handling, cross-triggers) and suggest fixes like skill consolidation. For your multi-terminal, git worktree flows, it should flag ecosystem overlaps with Claude Code v2.1+ hooks.[8][2][1]
