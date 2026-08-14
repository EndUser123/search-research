---
title: "Please look up these two articles and tell me what they are."
date: "2026-03-23"
mode: "COPILOT"
uuid: "90a39a7b-6e4c-45ea-88f9-20a1d5200ba1"
entry_count: 2
---

## Human

Please look up these two articles and tell me what they are.

## Assistant

**Both provided links lead to non-existent pages.** The GitHub repository at https://github.com/skills/kzieminski-shannon-framework-context-preservation returns a 404 error, indicating it does not exist.[1]

**Likely related to Shannon Framework.** This appears connected to the "Shannon Framework" by krzemienski, a Claude Code plugin for quantitative AI-assisted development with context preservation features, available at https://github.com/krzemienski/shannon-framework. A LobeHub skills marketplace entry describes "context-preservation" as implementing zero-context-loss via checkpoints and metadata, possibly intended as https://lobehub.com/skills/krzemienski-shannon-framework-context-preservation.[2][1]

**Medium article also missing.** The link https://medium.com/codedeploy/your-claude-md-is-a-suggest-hook-make-it shows a 404 page. It likely discusses turning CLAUDE.md files into "suggest hooks" in Claude Code, a feature for automating workflows via shell commands or prompts at lifecycle points like PreToolUse.[3][4][5][6]

## Human

How does LobeHub's Skills Market work

## Assistant

LobeHub's Skills Market is the largest marketplace for AI agent skills, hosting over 233,000 self-contained instruction sets (primarily SKILL.md bundles with resources) that teach agents specialized capabilities like PDF processing, cloud deployment, or Claude Code hooks.[1][2]

## Core Workflow
Agents search for skills by keyword when facing unfamiliar tasks, evaluate via previews (name, description, stars, installs), download ZIP packages, read SKILL.md instructions, execute the task, then rate/comment for quality feedback.[2][3][1]

## CLI Commands
Interaction uses `@lobehub/market-cli` exclusively (handles auth/retries; no raw API calls):
- Search: `npx -y @lobehub/market-cli skills search --q "KEYWORD"`
- Install: `npx -y @lobehub/market-cli skills install <identifier> [--agent claude-code]`
- Rate: `npx -y @lobehub/market-cli skills rate <identifier> --score 1-5`[4][5][1]

## Claude Code Integration
Skills install to `~/.claude/skills/` or project `./.claude/skills/`, enabling hook-based or task-specific activation in your workflows (e.g., Shannon framework context-preservation skill). Uncertainty: Exact install paths may vary by agent config; verify via CLI. Next step: Run `npx -y @lobehub/market-cli skills search --q "shannon"` to test.[6][5]
