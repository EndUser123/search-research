---
title: "what repo has /ln-200-scope?"
date: "2026-04-09"
mode: "COPILOT"
uuid: "739e8f92-f9c4-43bf-b6b2-83c7d11ff7ab"
entry_count: 2
---

## Human

what repo has /ln-200-scope?

## Assistant

**https://github.com/levnikolaevich/claude-code-skills contains the `/ln-200-scope-decomposer` skill directory (likely matching `/ln-200-scope`).**[1][2]

## Repo Details
This is a Claude Code skills plugin suite (358 stars, 53 forks as of Apr 2026). 
It automates Agile workflows including scope decomposition via `ln-200-scope-decomposer`, which orchestrates scope → Epics → Stories.[2]

## Path Evidence
Root dir lists folders like `.claude`, `docs`, `mcp`; no explicit `/ln-200-scope` in top-level table, but skill tree and docs reference it under agile-workflow plugin (e.g., `ln-2XX-*` planning skills).[3][1]
404 on `/tree/main/ln-200-scope-decomposer` suggests branch is `master` or nested (e.g., `.claude-plugin` or `skills-catalog`).[4]

## Next Steps
- Clone: `git clone https://github.com/levnikolaevich/claude-code-skills`
- Search locally: `find . -path '*/ln-200-scope*' -type d` (high confidence: 95%, matches your Claude Code workflows).[5]
- Install skill: `/plugin marketplace add levnikolaevich/claude-code-skills` then `/plugin install agile-workflow@levnikolaevich-skills-marketplace`.

## Human

What other skills are in claude-code-skills repo

## Assistant

**The levnikolaevich/claude-code-skills repo contains 84 production-ready Claude Code skills, organized into 7 categories (0XX-7XX) for full Agile workflows.** 

## Categories & Key Skills
Skills follow Orchestrator-Worker patterns with Mermaid diagrams; all integrate Linear tasks. 

| Category | Skills Count | Examples |
|----------|--------------|----------|
| 0XX Shared Workers | 2 | ln-001-standards-researcher, ln-002-best-practices-researcher  |
| 1XX Documentation | 14 | ln-100-documents-pipeline (L1), ln-110-project-docs-coordinator, ln-150-presentation-creator  |
| 2XX Planning | 7 | ln-200-scope-decomposer, ln-210-epic-coordinator, ln-230-story-prioritizer  |
| 3XX Task Mgmt | 6 | ln-300-task-coordinator, ln-310-story-validator, ln-301-task-creator  |
| 4XX Execution | 5 | ln-400-story-executor, ln-401-task-executor, ln-404-test-executor  |
| 5XX Quality | 5 | ln-500-story-quality-gate, ln-510-test-planner, ln-503-manual-tester  |
| 6XX Audit | 17 | ln-600-docs-auditor, ln-620-codebase-auditor (9 L3), ln-630-test-auditor (5 L3)  |
| 7XX Bootstrap | 30+ | ln-700-project-bootstrap (L1), ln-710-dependency-upgrader (8 L2/L3)  |

## Install & Verify
Run `/plugin install full-development-workflow-skills@levnikolaevich-skills-marketplace` then `/skills` (requires Linear API opt.). 
Confidence: 100% (direct from README); dir structure: `x-skill-name/SKILL.md + diagram.html`.
