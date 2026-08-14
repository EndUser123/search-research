---
title: "qodo-skills @ claude-plugins-official
  Scope: user
  Version: 0.3.0
  Shift-left code review skills that bring Qodo'"
date: "2026-03-05"
mode: "COPILOT"
uuid: "2843e45d-8286-443a-9717-a96b6b30036c"
entry_count: 1
---

## Human

qodo-skills @ claude-plugins-official
  Scope: user
  Version: 0.3.0
  Shift-left code review skills that bring Qodo's quality standards and code review capabilities into your local
  development workflow. Catch issues before commit, enforce organizational standards, and resolve PR feedback directly in
   your agent.

  Author: Qodo.ai
  Status: Enabled

  Installed components:
  • Skills: get-qodo-rules, qodo-pr-resolver
  • Hooks: SessionStart

In Claude Code, what are the best use cases for this? How do I get maximum value from it?

## Assistant

**Qodo-skills enhances Claude Code with shift-left code review via two main components: get-qodo-rules and qodo-pr-resolver.**[1][2]

These integrate Qodo.ai's quality standards directly into your local workflow, catching issues pre-commit and resolving PR feedback in-agent.[2][1]

## Best Use Cases

- **Pre-writing code alignment**: Invoke `/get-qodo-rules` at session start or before implementing features to load repo/org-specific rules (security, standards, conventions). This ensures Claude generates compliant code from the outset, reducing rework.[1][2]
- **PR remediation loops**: Use `/qodo-pr-resolver` on PRs with Qodo reviews. It fetches blocking issues (prioritized by HIGH/MEDIUM/LOW severity), auto-fixes in batch or interactively, commits changes, and auto-replies to inline comments with resolutions. Ideal for complex PRs (e.g., 8-12 issues) or quick ones (one-shot fixes).[2][1]
- **Multi-agent workflows**: Combine with Claude's SessionStart hook for automatic rule loading on project open, enforcing standards across monorepos or team projects.[1]

## Maximizing Value

- **Setup prerequisites**: Ensure GitHub CLI (`gh`), Qodo account, and Python 3.6+. The plugin is at user scope v0.3.0, so run `npx skills add qodo-ai/qodo-skills` if not installed. Authenticate via Qodo for repo access.[3][2][1]
- **Workflow integration**: Start sessions with `/get-qodo-rules` for context; post-Qodo-review, chain `/qodo-pr-resolver` immediately. Use auto-fix for routine issues, interactive for edge cases needing judgment. Track via commit-per-issue and PR summaries.[2][1]
- **Advanced tips**: In multi-terminal setups, run resolver in a dedicated terminal for parallel fixes. Customize via Qodo's Rule System for your org standards. Test on real PRs to benchmark resolution rates (e.g., 90%+ auto-fixed in experiments).[1][2]

This fits your AI-assisted dev focus, optimizing Claude Code for quality gates without context switches.[2]
