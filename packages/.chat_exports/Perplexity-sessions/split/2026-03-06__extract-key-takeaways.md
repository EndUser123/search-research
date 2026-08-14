---
title: "Extract key takeaways"
date: "2026-03-06"
mode: "COPILOT"
uuid: "5e05fb4c-aa2b-4af0-a9ae-65791f2d7b79"
entry_count: 1
---

## Human

Extract key takeaways

## Assistant

**Overstory demonstrates a powerful agent swarm for autonomous coding.** In one hour with a single prompt, 21 agents coordinated by one orchestrator fixed 9 issues and merged 26 commits into the main branch.[1]

## Core Architecture
A coordinator agent orchestrates the swarm, delegating tasks to team leads that spawn specialized builders and reviewers. Agents operate in isolated git worktrees, communicating via mail and tools like Beads for issue tracking. The system enforces delegation: leads cannot edit code directly, preventing context overload by handing off to focused builders.[1]

## Self-Improvement in Action
During the run, agents implemented a new mandatory review protocol, which the coordinator then recognized and applied to subsequent tasks—allowing the swarm to evolve its own processes in real-time. Reviewers, builders, and leads scaled dynamically up to 22 agents, with automatic merges back to main after reviews. New issues created mid-run were delegated instantly, sustaining progress autonomously.[1]

## Practical Workflow
Jaymin West boots the coordinator (`overstory coordinator start`), dashboard (`overstory dashboard`), inspect (`overstory inspect <agent>`), and watch commands for monitoring. One prompt lists issues; the swarm handles context gathering, execution, and cleanup without further input.[1]

## Key Tools and Limits
Relies on Claude Code, Tmux, Beads (issue tracking), and Mulch (insights logging); costs ~$20-30 per run via API credits. Highly experimental—requires trust in agents, as behavior is unpredictable but effective for large-scale autonomy.[1]
