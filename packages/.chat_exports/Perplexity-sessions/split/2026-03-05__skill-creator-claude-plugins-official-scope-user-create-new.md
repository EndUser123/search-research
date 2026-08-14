---
title: "skill-creator @ claude-plugins-official
  Scope: user
  Create new skills, improve existing skills, and measure skill "
date: "2026-03-05"
mode: "COPILOT"
uuid: "9ee7a266-0dd7-4811-8ee9-e4161faeb7c0"
entry_count: 1
---

## Human

skill-creator @ claude-plugins-official
  Scope: user
  Create new skills, improve existing skills, and measure skill performance. Use when users want to create a skill from
  scratch, update or optimize an existing skill, run evals to test a skill, or benchmark skill performance with variance
  analysis.

  Author: Anthropic
  Status: Enabled

  Installed components:
  • Skills: skill-creator

In Claude Code, what are the best use cases for this? How do I get maximum value from it?

## Assistant

The skill-creator from claude-plugins-official in Claude Code is an AI-powered toolkit for rapidly building, refining, and evaluating custom skills to extend Claude's capabilities in your workflows.  It shines in agentic development by automating SKILL.md generation, frontmatter optimization, and iterative improvements based on real usage.[1][2][3]

## Top Use Cases
- **New skill creation from scratch**: Describe a workflow (e.g., "RCA debugging loop for Python monorepos") and let it generate a full skill folder with SKILL.md, description, triggers, and supporting files like examples or templates. Ideal for your multi-agent systems or hook integrations.[3][4]
- **Optimizing existing skills**: Feed in a failing SKILL.md or chat transcript with edge cases; it flags issues like vague triggers or over-invocation, then suggests refined versions with better auto-activation.[3]
- **Performance evals and benchmarking**: Run variance analysis on skill outputs across test cases, measuring reliability in tasks like code review or prompt engineering—pairs with your TDD/verify loops.[2]

## Maximizing Value
Invoke via `/skill-creator` or naturally ("Use skill-creator to build a skill for...") in Claude Code sessions.  Start with concrete examples from your transcripts (thousands available in your setup), iterate in 15-30 minutes per skill, and test in git worktrees for quick validation.[1][5][3]

Chain with plugin-dev for full plugins or claudit for audits, and store in `~/.claude/skills/` for personal reuse across projects.  Focus on micro-skills (e.g., one for semantic search, one for graph-of-thoughts prompting) that compose via subagents for 50-70% workflow speedups.[6][1][5]

Do you have a specific workflow or existing skill to create/optimize first?
